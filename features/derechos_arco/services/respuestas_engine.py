# ¤evidencias ¤rbac-tenant
"""DER-01: verificación de identidad, modelos de respuesta y la respuesta como evidencia.

Contrato: governance/especificaciones/DER-01.md. La custodia de la evidencia es de otra sala y llega como
parámetro (`custodiar`, la capacidad `custodiar_documento_generado` del pasillo de evidencias): esta sala
no importa `features.evidencias`. No hace commit: la transacción es de quien llama. Sin plazos (REG-01).
"""
from __future__ import annotations

import re
from typing import Any, Awaitable, Callable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.errors import ErrorNegocio

METODOS = ("documento", "correo", "presencial")
RESULTADOS = ("concedido", "denegado", "parcial")
ROLES_VERIFICAN = ("coordinador", "responsable_area", "admin_organizacion", "implementador")
ROLES_RESPONDEN = ("admin_organizacion", "implementador")
TIPO_EVIDENCIA = "respuesta_derecho"
# Control 23 del banco: «Procedimiento de atención de derechos».
CONTROLES_RESPUESTA = ["P23"]
TIPO_MIME = "text/plain"

_VARIABLE = re.compile(r"\{\{\s*([a-z_][a-z0-9_]*)\s*\}\}")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")

Custodiar = Callable[..., Awaitable[dict[str, Any]]]


def variables_de(texto: str) -> list[str]:
    """Nombres de las variables `{{nombre}}` del modelo, sin repetir y en orden de aparición."""
    vistas: list[str] = []
    for nombre in _VARIABLE.findall(texto):
        if nombre not in vistas:
            vistas.append(nombre)
    return vistas


def resolver_texto(texto: str, variables: dict[str, str]) -> str:
    """Texto del modelo con sus variables; falta o vacía alguna → VARIABLES_INCOMPLETAS."""
    faltan = [n for n in variables_de(texto) if not str(variables.get(n, "")).strip()]
    if faltan:
        raise ErrorNegocio("VARIABLES_INCOMPLETAS")
    return _VARIABLE.sub(lambda m: str(variables[m.group(1)]).strip(), texto)


async def _solicitud(session: AsyncSession, tenant_id: str, solicitud_id: str) -> dict[str, Any]:
    fila = (await session.execute(
        text(
            "SELECT id::text AS id, tipo_solicitud::text AS derecho, estado::text AS estado, "
            "identidad_verificada_en, identidad_metodo, identidad_verificada_por, resultado, respondida_en, "
            "evidencia_respuesta_hash FROM derechos_arco_solicitudes "
            "WHERE id::text = :i AND tenant_id_texto = :t FOR UPDATE"
        ),
        {"i": solicitud_id, "t": tenant_id},
    )).mappings().first()
    if fila is None:
        raise ErrorNegocio("SOLICITUD_NO_ENCONTRADA")
    return dict(fila)


async def verificar_identidad(
    session: AsyncSession, tenant_id: str, user_id: str, solicitud_id: str, metodo: str
) -> dict[str, Any]:
    """Registra método, quién verificó y cuándo. Una solicitud ya respondida no se vuelve a verificar."""
    if metodo not in METODOS:
        raise ValueError("método de verificación no admitido")
    actual = await _solicitud(session, tenant_id, solicitud_id)
    if actual["respondida_en"] is not None:
        raise ErrorNegocio("SOLICITUD_RESPONDIDA")
    await session.execute(
        text(
            "UPDATE derechos_arco_solicitudes SET identidad_verificada_en = now(), identidad_metodo = :m, "
            "identidad_verificada_por = :u WHERE id::text = :i AND tenant_id_texto = :t"
        ),
        {"m": metodo, "u": user_id, "i": solicitud_id, "t": tenant_id},
    )
    await registrar_evento(
        session, tenant_id, "derechos_solicitud", solicitud_id, "verificar_identidad", user_id, {"metodo": metodo}
    )
    return await _solicitud(session, tenant_id, solicitud_id)


async def listar_modelos(
    session: AsyncSession, tenant_id: str, derecho: str | None = None, resultado: str | None = None
) -> list[dict[str, Any]]:
    filas = (await session.execute(
        text(
            "SELECT id, derecho, resultado, texto, version FROM derechos_modelos "
            "WHERE tenant_id = :t AND (CAST(:d AS TEXT) IS NULL OR derecho = :d) "
            "AND (CAST(:r AS TEXT) IS NULL OR resultado = :r) ORDER BY derecho, resultado, version DESC"
        ),
        {"t": tenant_id, "d": derecho, "r": resultado},
    )).mappings().all()
    return [{**f, "variables": variables_de(f["texto"])} for f in filas]


async def responder(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    solicitud_id: str,
    modelo_id: str,
    variables: dict[str, str],
    resultado: str,
    custodiar: Custodiar,
) -> dict[str, Any]:
    """Custodia la respuesta y pasa la solicitud a CONTESTADA en la misma transacción (R1, R2, R3, R3a).

    El hash lo calcula la custodia en el servidor; si no devuelve un sha256 la solicitud no cambia.
    """
    if resultado not in RESULTADOS:
        raise ValueError("resultado no admitido")
    actual = await _solicitud(session, tenant_id, solicitud_id)
    if actual["respondida_en"] is not None or actual["estado"] == "CONTESTADA":
        raise ErrorNegocio("SOLICITUD_RESPONDIDA")
    if actual["identidad_verificada_en"] is None:
        raise ErrorNegocio("IDENTIDAD_NO_VERIFICADA")
    modelo = (await session.execute(
        text(
            "SELECT id, texto, version FROM derechos_modelos WHERE id = :m AND tenant_id = :t "
            "AND derecho = :d AND resultado = :r"
        ),
        {"m": modelo_id, "t": tenant_id, "d": actual["derecho"], "r": resultado},
    )).mappings().first()
    if modelo is None:
        raise ErrorNegocio("MODELO_NO_ENCONTRADO")
    cuerpo = resolver_texto(modelo["texto"], variables)

    # Punto de guardado: si la custodia o el cambio de estado fallan, no queda nada de esta respuesta.
    async with session.begin_nested():
        try:
            custodia = await custodiar(
                session, tenant_id, user_id,
                contenido=cuerpo.encode("utf-8"), tipo_mime=TIPO_MIME, tipo_evidencia=TIPO_EVIDENCIA,
                control_refs=list(CONTROLES_RESPUESTA), nombre=f"respuesta-{solicitud_id[:8]}.txt",
            )
        except Exception as exc:  # falla cerrada: sin custodia confirmada no hay respuesta
            raise ErrorNegocio("RESPUESTA_SIN_EVIDENCIA") from exc
        hash_respuesta = custodia.get("sha256") if isinstance(custodia, dict) else None
        if not isinstance(hash_respuesta, str) or not _SHA256.fullmatch(hash_respuesta):
            raise ErrorNegocio("RESPUESTA_SIN_EVIDENCIA")
        cambiadas = await session.execute(
            text(
                "UPDATE derechos_arco_solicitudes SET estado = 'CONTESTADA', resultado = :r, "
                "respondida_en = now(), evidencia_respuesta_hash = :h "
                "WHERE id::text = :i AND tenant_id_texto = :t AND respondida_en IS NULL "
                "AND estado::text <> 'CONTESTADA' RETURNING id"
            ),
            {"r": resultado, "h": hash_respuesta, "i": solicitud_id, "t": tenant_id},
        )
        if cambiadas.first() is None:
            raise ErrorNegocio("SOLICITUD_RESPONDIDA")
    await registrar_evento(
        session, tenant_id, "derechos_solicitud", solicitud_id, "responder", user_id,
        {"modelo_id": modelo_id, "modelo_version": modelo["version"], "resultado": resultado,
         "evidencia_respuesta_hash": hash_respuesta},
    )
    return {"evidencia_respuesta_hash": hash_respuesta}
