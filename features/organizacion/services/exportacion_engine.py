"""Exportación completa de los datos de la organización (sala ADPA: Organización). ¤rbac-tenant ¤seguridad

ORG-20 · R2-R4. ZIP con un JSON por entidad con datos y `MANIFIESTO.sha256`, que declara `incluidas` y
`no_incluidas`: una exportación a la que le falten entidades no es «completa» (`exportaciones.completa`) y
no sirve para cerrar la organización (R4). El ZIP se sube por el puerto `AlmacenExportaciones`; el adaptador
real llega con EVI-04 y hasta entonces falla cerrado. La descarga va en streaming por el backend, con
autorización del admin y evento de auditoría. Toda consulta filtra por `tenant_id` además de la RLS.
"""
from __future__ import annotations

import hashlib
import io
import json
import zipfile
from datetime import datetime, timedelta, timezone
from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import bindparam, column, select, table, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.errors import ErrorNegocio
from features.organizacion.domain.errores import (
    ALMACEN_EXPORTACION_NO_DISPONIBLE,
    EXPORTACION_CADUCADA,
    EXPORTACION_EN_CURSO,
    EXPORTACION_INCOMPLETA,
    EXPORTACION_NO_ENCONTRADA,
    EXPORTACION_NO_LISTA,
)
from features.organizacion.services.contexto_tenant import fijar_tenant

VIGENCIA_ENLACE = timedelta(days=7)
VIGENCIA_PARA_CIERRE = timedelta(days=30)

# Entidades de la sala que la exportación lee hoy: nombre en el ZIP -> tabla (todas con tenant_id).
ENTIDADES_INCLUIDAS: dict[str, str] = {
    "areas": "areas",
    "cargos_organicos": "cargos_organicos",
    "designaciones_formales": "designaciones_formales",
    "sedes": "sedes",
    "clientes_encargo": "clientes_encargo",
    "inventario_activos": "inventario_activos",
    "inventario_activos_tratamientos": "inventario_activos_tratamientos",
    "inventario_personas": "inventario_personas",
    "roles_de_usuarios": "user_tenant_roles",
    "excepciones_sod": "sod_exceptions",
}
# Entidades de otras salas: se suman cuando su pasillo exponga la lectura (una sección #ORG-20 por sala).
ENTIDADES_NO_INCLUIDAS: tuple[str, ...] = (
    "rat", "terceros_y_transferencias", "evidencias_y_documentos", "biblioteca", "diagnostico",
    "incidentes", "derechos_arco", "roadmap", "mtge", "auditoria",
)
_COLUMNAS_SECRETAS = ("token", "secret", "password", "hash_clave")


class AlmacenExportaciones(Protocol):
    """Puerto del almacén de exportaciones; el adaptador real (EVI-04) lo implementa."""

    async def subir(self, tenant_id: str, clave: str, contenido: bytes) -> None: ...

    async def leer(self, tenant_id: str, clave: str) -> bytes: ...


class AlmacenNoDisponible:
    """Adaptador por omisión: falla cerrado hasta que EVI-04 entregue el real."""

    async def subir(self, tenant_id: str, clave: str, contenido: bytes) -> None:
        raise ErrorNegocio(ALMACEN_EXPORTACION_NO_DISPONIBLE)

    async def leer(self, tenant_id: str, clave: str) -> bytes:
        raise ErrorNegocio(ALMACEN_EXPORTACION_NO_DISPONIBLE)


def _jsonable(valor: Any) -> Any:
    return valor.isoformat() if hasattr(valor, "isoformat") else valor


async def _leer_entidad(session: AsyncSession, tenant_id: str, tabla: str) -> list[dict[str, Any]]:
    columnas = [
        c for c in (await session.execute(
            text("SELECT column_name FROM information_schema.columns "
                 "WHERE table_schema = 'public' AND table_name = :t ORDER BY ordinal_position"),
            {"t": tabla},
        )).scalars().all()
        if not any(s in c.lower() for s in _COLUMNAS_SECRETAS)
    ]
    filas = (await session.execute(
        # Constructor de SQLAlchemy: los identificadores se citan, nunca se interpolan en texto.
        select(*(column(c) for c in columnas)).select_from(table(tabla))
        .where(column("tenant_id") == bindparam("t")),
        {"t": tenant_id},
    )).mappings().all()
    return [{k: _jsonable(v) for k, v in f.items()} for f in filas]


async def construir_zip(session: AsyncSession, tenant_id: str) -> tuple[bytes, dict[str, Any]]:
    """ZIP de la organización y su manifiesto. Solo lee filas de `tenant_id`."""
    await fijar_tenant(session, tenant_id)
    contenidos: dict[str, bytes] = {}
    for nombre, tabla in ENTIDADES_INCLUIDAS.items():
        filas = await _leer_entidad(session, tenant_id, tabla)
        if filas:
            contenidos[f"{nombre}.json"] = json.dumps(filas, ensure_ascii=False, indent=2).encode("utf-8")
    manifiesto = {
        "incluidas": list(ENTIDADES_INCLUIDAS),
        "no_incluidas": list(ENTIDADES_NO_INCLUIDAS),
        "completa": not ENTIDADES_NO_INCLUIDAS,
        "entradas": {n: hashlib.sha256(b).hexdigest() for n, b in contenidos.items()},
    }
    memoria = io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as z:
        for n, b in contenidos.items():
            z.writestr(n, b)
        z.writestr("MANIFIESTO.sha256", json.dumps(manifiesto, ensure_ascii=False, indent=2))
    return memoria.getvalue(), manifiesto


async def solicitar(session: AsyncSession, tenant_id: str, user_id: str) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    export_id = str(uuid4())
    try:
        async with session.begin_nested():
            await session.execute(
                text("INSERT INTO exportaciones (id, tenant_id, solicitado_por) VALUES (:id, :t, :u)"),
                {"id": export_id, "t": tenant_id, "u": user_id},
            )
    except IntegrityError as exc:
        raise ErrorNegocio(EXPORTACION_EN_CURSO) from exc
    await registrar_evento(
        session=session, tenant_id=tenant_id, entity_type="exportacion", entity_id=export_id,
        action="exportacion_solicitada", user_id=user_id, payload=None,
    )
    return {"id": export_id}


async def generar(
    session: AsyncSession, tenant_id: str, user_id: str, export_id: str, almacen: AlmacenExportaciones,
) -> dict[str, Any]:
    """Segundo plano: arma el ZIP, lo sube y deja la exportación lista con su huella y caducidad (R3)."""
    await fijar_tenant(session, tenant_id, user_id)
    fila = (await session.execute(
        text("SELECT estado FROM exportaciones WHERE id = :id AND tenant_id = :t"), {"id": export_id, "t": tenant_id},
    )).first()
    if fila is None:
        raise ErrorNegocio(EXPORTACION_NO_ENCONTRADA)
    contenido, manifiesto = await construir_zip(session, tenant_id)
    clave = f"exportaciones/{tenant_id}/{export_id}.zip"
    await almacen.subir(tenant_id, clave, contenido)
    sha = hashlib.sha256(contenido).hexdigest()
    caduca = datetime.now(timezone.utc) + VIGENCIA_ENLACE
    await session.execute(
        text("UPDATE exportaciones SET estado = 'lista', lista_en = now(), r2_key = :k, sha256 = :s, caduca_en = :c, "
             "completa = :ok WHERE id = :id AND tenant_id = :t"),
        {"k": clave, "s": sha, "c": caduca, "ok": manifiesto["completa"], "id": export_id, "t": tenant_id},
    )
    await registrar_evento(
        session=session, tenant_id=tenant_id, entity_type="exportacion", entity_id=export_id,
        action="exportacion_generada", user_id=user_id, payload=None,
    )
    return {"id": export_id, "estado": "lista", "sha256": sha, "completa": manifiesto["completa"]}


async def _obtener(session: AsyncSession, tenant_id: str, export_id: str) -> Any:
    fila = (await session.execute(
        text("SELECT id, estado, sha256, caduca_en, r2_key, completa FROM exportaciones "
             "WHERE id = :id AND tenant_id = :t"),
        {"id": export_id, "t": tenant_id},
    )).mappings().first()
    if fila is None:
        raise ErrorNegocio(EXPORTACION_NO_ENCONTRADA)
    if fila["estado"] == "lista" and fila["caduca_en"] <= datetime.now(timezone.utc):
        await session.execute(
            text("UPDATE exportaciones SET estado = 'caducada' WHERE id = :id AND tenant_id = :t"),
            {"id": export_id, "t": tenant_id},
        )
        fila = {**fila, "estado": "caducada"}
    return fila


async def consultar(session: AsyncSession, tenant_id: str, export_id: str) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id)
    f = await _obtener(session, tenant_id, export_id)
    salida: dict[str, Any] = {"estado": f["estado"], "completa": f["completa"]}
    if f["estado"] == "lista":
        salida.update(sha256=f["sha256"], url=f"/api/v1/organizacion/exportaciones/{export_id}/archivo",
                      caduca_en=f["caduca_en"].isoformat())
    return salida


async def descargar(
    session: AsyncSession, tenant_id: str, user_id: str, export_id: str, almacen: AlmacenExportaciones,
) -> bytes:
    await fijar_tenant(session, tenant_id, user_id)
    f = await _obtener(session, tenant_id, export_id)
    if f["estado"] == "caducada":
        raise ErrorNegocio(EXPORTACION_CADUCADA)
    if f["estado"] != "lista":
        raise ErrorNegocio(EXPORTACION_NO_LISTA)
    contenido = await almacen.leer(tenant_id, f["r2_key"])
    await registrar_evento(
        session=session, tenant_id=tenant_id, entity_type="exportacion", entity_id=export_id,
        action="exportacion_descargada", user_id=user_id, payload=None,
    )
    return contenido


async def exigir_exportacion_para_cierre(session: AsyncSession, tenant_id: str) -> str:
    """R4 (la invoca `plataforma_service` al cerrar): exige una exportación completa y lista de los últimos 30 días."""
    await fijar_tenant(session, tenant_id)
    fila = (await session.execute(
        text("SELECT id FROM exportaciones WHERE tenant_id = :t AND estado = 'lista' AND completa "
             "AND lista_en >= :desde ORDER BY lista_en DESC LIMIT 1"),
        {"t": tenant_id, "desde": datetime.now(timezone.utc) - VIGENCIA_PARA_CIERRE},
    )).first()
    if fila is None:
        raise ErrorNegocio(EXPORTACION_INCOMPLETA)
    return fila[0]
