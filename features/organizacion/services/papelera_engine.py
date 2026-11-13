"""Papelera de la organización: listar y restaurar lo retirado (sala ADPA: Organización). ¤rbac-tenant ¤seguridad

ORG-20 · R1. Nada se borra desde la aplicación: retirar marca `retirado_en` y restaurar la vuelve a NULL.
Hoy solo tienen papelera las entidades de la sala que ya tienen la marca de retiro (sedes y clientes por
encargo); cada sala añade la suya en su propia ficha y se suma a `ENTIDADES`. La organización sale del
contexto de la sesión; todas las consultas filtran por ella además de la RLS.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.errors import ErrorNegocio
from features.organizacion.domain.errores import (
    CLIENTE_DUPLICADO,
    PAPELERA_ELEMENTO_NO_ENCONTRADO,
    PAPELERA_ENTIDAD_DESCONOCIDA,
)
from features.organizacion.services.contexto_tenant import fijar_tenant

# entidad -> (tabla, columna de retiro, columna de nombre, etiqueta en español). Valores fijos: nunca del cliente.
ENTIDADES: dict[str, tuple[str, str, str, str]] = {
    "sedes": ("sedes", "retirada_en", "nombre", "Sedes"),
    "clientes": ("clientes_encargo", "retirado_en", "razon_social", "Clientes por encargo"),
}


def entidades_con_papelera() -> list[dict[str, str]]:
    return [{"entidad": k, "etiqueta": v[3]} for k, v in ENTIDADES.items()]


def _definicion(entidad: str) -> tuple[str, str, str, str]:
    if entidad not in ENTIDADES:
        raise ErrorNegocio(PAPELERA_ENTIDAD_DESCONOCIDA)
    return ENTIDADES[entidad]


async def listar_papelera(session: AsyncSession, tenant_id: str, entidad: str | None = None) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id)
    claves = [entidad] if entidad else list(ENTIDADES)
    registros: list[dict[str, Any]] = []
    for clave in claves:
        tabla, retiro, nombre, _ = _definicion(clave)
        filas = (await session.execute(
            text(f"SELECT id, {nombre} AS nombre, {retiro} AS retirado_en FROM {tabla} "  # noqa: S608 (nombres fijos)
                 f"WHERE tenant_id = :t AND {retiro} IS NOT NULL ORDER BY {retiro} DESC"),
            {"t": tenant_id},
        )).mappings().all()
        registros += [
            {"entidad": clave, "id": f["id"], "nombre": f["nombre"], "retirado_en": f["retirado_en"].isoformat()}
            for f in filas
        ]
    registros.sort(key=lambda r: r["retirado_en"], reverse=True)
    return {"registros": registros, "entidades": entidades_con_papelera()}


async def restaurar(session: AsyncSession, tenant_id: str, user_id: str, entidad: str, registro_id: str) -> dict[str, Any]:
    await fijar_tenant(session, tenant_id, user_id)
    tabla, retiro, _, _ = _definicion(entidad)
    ajuste = ""
    if entidad == "sedes":
        # Si ya hay otra principal vigente, la restaurada vuelve sin serlo (una sola principal, ORG-18 R1).
        ajuste = (", es_principal = (es_principal AND NOT EXISTS (SELECT 1 FROM sedes o WHERE o.tenant_id = :t "
                  "AND o.es_principal AND o.retirada_en IS NULL AND o.id <> :id))")
    try:
        async with session.begin_nested():
            hecho = (await session.execute(
                text(f"UPDATE {tabla} SET {retiro} = NULL{ajuste}, actualizado_en = now() "  # noqa: S608
                     f"WHERE id = :id AND tenant_id = :t AND {retiro} IS NOT NULL RETURNING id"),
                {"id": registro_id, "t": tenant_id},
            )).first()
    except IntegrityError as exc:
        raise ErrorNegocio(CLIENTE_DUPLICADO) from exc
    if hecho is None:
        raise ErrorNegocio(PAPELERA_ELEMENTO_NO_ENCONTRADO)
    await registrar_evento(
        session=session, tenant_id=tenant_id, entity_type=f"papelera_{entidad}", entity_id=registro_id,
        action="restaurado", user_id=user_id, payload=None,
    )
    return {"entidad": entidad, "id": registro_id, "restaurado": True}
