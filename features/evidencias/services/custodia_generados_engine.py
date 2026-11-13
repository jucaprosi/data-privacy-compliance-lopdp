# ¤evidencias
"""EVI-04: custodia de documentos que genera el servidor (constancias, actas, informes) como evidencia.

El llamador YA AUTORIZÓ la acción (rol, estado del flujo): esta función es una escritura del sistema,
no de un usuario, y NO se expone por ningún router. Exige `tenant_id` y `user_id` (el actor queda en
el evento de auditoría) y trabaja en la transacción del llamador: no hace commit; si algo falla se
propaga la excepción y el llamador hace rollback, de modo que no queda registro.

`tipo_evidencia` no tiene columna: se valida contra una lista cerrada, viaja en el payload del evento
de auditoría y se devuelve en el resultado. No es consultable por tipo; la columna es otra ficha.
El vínculo al control se comprueba por `evidencias_vinculos`.

La clave del objeto lleva el tenant y el SHA-256 (`<tenant>/<sha256>`): el mismo contenido en dos
organizaciones da dos objetos y dos registros. La escritura es única; si un intento anterior dejó el
objeto huérfano (subió y la transacción se deshizo), el reintento lo reconoce por su huella.
"""
from __future__ import annotations

import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.errors import ErrorNegocio
from app_core.storage import gcs
from app_core.storage.r2 import motivo_de_rechazo
from features.evidencias.domain import errores as _e
from features.evidencias.domain.models import NORMATIVA_POR_DEFECTO, EvidenciaError, validar_control_id
from features.evidencias.domain.retencion import retencion_dias
from features.evidencias.services import evidencias_engine as _motor

TIPOS_EVIDENCIA = (
    "capacitacion",
    "acta_auditoria",
    "informe_incidente",
    "respuesta_derecho",
    "asesoria_dpo",
    "exportacion",
)
_PATRON_REFERENCIA = re.compile(r"^P([0-9]{1,4})$")
_REINTENTOS_CODIGO = 3


class CustodiaInvalida(EvidenciaError):
    """Los datos de la custodia no cumplen la precondición (organización, actor, tipo o controles)."""


def _controles(control_refs: list[str]) -> list[int]:
    if not control_refs:
        raise CustodiaInvalida("Toda custodia vincula al menos un control.")
    ids: list[int] = []
    for ref in control_refs:
        coincide = _PATRON_REFERENCIA.fullmatch(ref) if isinstance(ref, str) else None
        if coincide is None:
            raise CustodiaInvalida(f"Referencia de control inválida: {ref!r}")
        control = validar_control_id(int(coincide.group(1)))
        if control not in ids:
            ids.append(control)
    return ids


async def _vincular(
    session: AsyncSession, tenant_id: str, user_id: str, documento_id: str, controles: list[int]
) -> None:
    for control in controles:
        insertado = await session.execute(
            text(
                "INSERT INTO evidencias_vinculos (id, tenant_id, documento_id, control_id, vinculado_por) "
                "VALUES (:id, :t, :d, :c, :u) ON CONFLICT (documento_id, control_id) DO NOTHING RETURNING id"
            ),
            {"id": str(uuid.uuid4()), "t": tenant_id, "d": documento_id, "c": control, "u": user_id},
        )
        if insertado.first() is not None:
            await registrar_evento(
                session, tenant_id, "evidencia_vinculo", documento_id, "vincular", user_id, {"control_id": control}
            )


def _subir_una_vez(almacen: gcs.Almacen, clave: str, contenido: bytes, tipo_mime: str, huella: str) -> None:
    try:
        almacen.subir(clave, contenido, tipo_mime)
    except gcs.ObjetoYaExiste:
        # Huérfano de un intento deshecho: vale solo si es exactamente el mismo contenido.
        previo = almacen.descargar(clave, _MAXIMO_BYTES)
        if previo is None:
            raise ErrorNegocio(_e.ARCHIVO_INVALIDO)
        if _motor.calcular_hash_sha256(previo) != huella:
            raise ErrorNegocio(_e.HUELLA_NO_COINCIDE)


_MAXIMO_BYTES = _motor.TAMANO_MAXIMO_BYTES


async def custodiar_documento_generado(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    contenido: bytes,
    tipo_mime: str,
    tipo_evidencia: str,
    control_refs: list[str],
    nombre: str,
    almacen: gcs.Almacen | None = None,
) -> dict[str, Any]:
    """Sube, retiene, registra y vincula un documento generado, todo en la transacción del llamador.

    Devuelve {evidencia_id, sha256, tipo_evidencia}. Si la huella ya estaba registrada en la
    organización no vuelve a subir: devuelve ese documento y añade los vínculos que falten.
    """
    if not isinstance(tenant_id, str) or not tenant_id.strip() or not isinstance(user_id, str) or not user_id.strip():
        raise CustodiaInvalida("La custodia exige organización y actor.")
    if tipo_evidencia not in TIPOS_EVIDENCIA:
        raise CustodiaInvalida(f"Tipo de evidencia no admitido: {tipo_evidencia!r}")
    controles = _controles(control_refs)
    if not isinstance(contenido, bytes) or not contenido:
        raise ErrorNegocio(_e.ARCHIVO_INVALIDO)
    tipo_mime = (tipo_mime or "").strip().lower()
    rechazo = motivo_de_rechazo(nombre, tipo_mime, len(contenido))
    if rechazo is not None:
        codigo, motivo = rechazo
        raise ErrorNegocio(codigo, detail=motivo)
    if not _motor.firma_de_formato_valida(tipo_mime, contenido):
        raise ErrorNegocio(_e.ARCHIVO_INVALIDO)

    huella = _motor.calcular_hash_sha256(contenido)
    clave = f"{tenant_id}/{huella}"
    await _motor._fijar_rls(session, tenant_id, user_id)
    previo = await _motor._documento_existente(session, tenant_id, huella, NORMATIVA_POR_DEFECTO, clave)
    if previo is not None:
        await _vincular(session, tenant_id, user_id, previo.id, controles)
        await registrar_evento(
            session, tenant_id, "evidencia_documento", previo.id, "custodiar", user_id,
            {"sha256": huella, "tipo_evidencia": tipo_evidencia, "duplicada": True},
        )
        return {"evidencia_id": previo.id, "sha256": previo.sha256, "tipo_evidencia": tipo_evidencia}

    almacen = almacen if almacen is not None else _motor.almacen_de_evidencias()
    _subir_una_vez(almacen, clave, contenido, tipo_mime, huella)
    dias = retencion_dias(tenant_id)
    try:
        almacen.fijar_retencion(clave, datetime.now(timezone.utc) + timedelta(days=dias))
    except Exception as exc:  # falla cerrada: sin retención no se registra
        raise ErrorNegocio(_e.RETENCION_NO_FIJADA) from exc

    documento_id = str(uuid.uuid4())
    codigo_evd = ""
    for intento in range(_REINTENTOS_CODIGO):
        codigo_evd = await _motor._siguiente_codigo_en_base(session, tenant_id)
        try:
            async with session.begin_nested():
                await session.execute(
                    text(
                        "INSERT INTO evidencias_documentos (id, tenant_id, codigo, nombre_archivo, tipo_mime, "
                        "tamano_bytes, sha256, normativa, clave_almacen, subido_por, retencion_dias) "
                        "VALUES (:id, :t, :cod, :nom, :mime, :tam, :sha, :norm, :clave, :u, :dias)"
                    ),
                    {
                        "id": documento_id, "t": tenant_id, "cod": codigo_evd, "nom": nombre.strip(),
                        "mime": tipo_mime, "tam": len(contenido), "sha": huella,
                        "norm": NORMATIVA_POR_DEFECTO, "clave": clave, "u": user_id, "dias": dias,
                    },
                )
            break
        except IntegrityError:
            carrera = await _motor._documento_existente(session, tenant_id, huella, NORMATIVA_POR_DEFECTO, clave)
            if carrera is not None:
                documento_id = carrera.id
                break
            if intento == _REINTENTOS_CODIGO - 1:
                raise
    await _vincular(session, tenant_id, user_id, documento_id, controles)
    await registrar_evento(
        session, tenant_id, "evidencia_documento", documento_id, "custodiar", user_id,
        {"codigo": codigo_evd, "sha256": huella, "tipo_evidencia": tipo_evidencia},
    )
    return {"evidencia_id": documento_id, "sha256": huella, "tipo_evidencia": tipo_evidencia}
