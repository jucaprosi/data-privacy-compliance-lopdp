# ¤rat ¤evidencias ¤rbac-tenant
"""Colectivos de titulares y registro agregado de consentimientos (RAT-07); la transacción es del llamador.

R2: el total es la suma de cantidades en el rango; nunca se lista a una persona.
"""
from datetime import date
from uuid import uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_COLECTIVO = "id, tratamiento_id, nombre, base_legitimacion, texto_version, creado_por, creado_en"
_REGISTRO = "id, colectivo_id, fecha, canal, cantidad, texto_version, registrado_por, registrado_en"


async def existe_tratamiento(session: AsyncSession, tenant_id: str, tratamiento_id: str) -> bool:
    return (await session.execute(
        text("SELECT 1 FROM rat_actividades WHERE tenant_id=:t AND id=:i"), {"t": tenant_id, "i": tratamiento_id},
    )).first() is not None


async def listar_colectivos(session: AsyncSession, tenant_id: str, tratamiento_id: str) -> list[dict]:
    filas = await session.execute(
        text(f"SELECT {_COLECTIVO} FROM colectivos_titulares WHERE tenant_id=:t AND tratamiento_id=:r "
             "ORDER BY creado_en, id"), {"t": tenant_id, "r": tratamiento_id})
    return [dict(f) for f in filas.mappings().all()]


async def leer_colectivo(session: AsyncSession, tenant_id: str, colectivo_id: str) -> dict | None:
    fila = (await session.execute(
        text(f"SELECT {_COLECTIVO} FROM colectivos_titulares WHERE tenant_id=:t AND id=:i"),
        {"t": tenant_id, "i": colectivo_id})).mappings().first()
    return dict(fila) if fila else None


async def crear_colectivo(session: AsyncSession, tenant_id: str, tratamiento_id: str, datos: dict,
                          user_id: str | None) -> dict:
    fila = (await session.execute(
        text(f"INSERT INTO colectivos_titulares (id, tenant_id, tratamiento_id, nombre, base_legitimacion, "
             f"texto_version, creado_por) VALUES (:i,:t,:r,:n,:b,:v,:u) RETURNING {_COLECTIVO}"),
        {"i": str(uuid4()), "t": tenant_id, "r": tratamiento_id, "n": datos["nombre"],
         "b": datos["base_legitimacion"], "v": datos.get("texto_version"), "u": user_id})).mappings().one()
    return dict(fila)


async def actualizar_colectivo(session: AsyncSession, tenant_id: str, colectivo_id: str, datos: dict) -> dict | None:
    fila = (await session.execute(
        text(f"UPDATE colectivos_titulares SET nombre=:n, base_legitimacion=:b, texto_version=:v "
             f"WHERE tenant_id=:t AND id=:i RETURNING {_COLECTIVO}"),
        {"i": colectivo_id, "t": tenant_id, "n": datos["nombre"], "b": datos["base_legitimacion"],
         "v": datos.get("texto_version")})).mappings().first()
    return dict(fila) if fila else None


async def registrar_consentimiento(session: AsyncSession, tenant_id: str, colectivo_id: str, datos: dict,
                                   user_id: str | None) -> dict:
    fila = (await session.execute(
        text(f"INSERT INTO consentimientos_registro (id, tenant_id, colectivo_id, fecha, canal, cantidad, "
             f"texto_version, registrado_por) VALUES (:i,:t,:c,:f,:k,:n,:v,:u) RETURNING {_REGISTRO}"),
        {"i": str(uuid4()), "t": tenant_id, "c": colectivo_id, "f": datos["fecha"], "k": datos["canal"],
         "n": datos["cantidad"], "v": datos.get("texto_version"), "u": user_id})).mappings().one()
    return dict(fila)


async def listar_registros(session: AsyncSession, tenant_id: str, colectivo_id: str,
                           desde: date | None, hasta: date | None) -> dict:
    """Registros del rango y su total (R2: suma de cantidades)."""
    filas = (await session.execute(
        text(f"SELECT {_REGISTRO} FROM consentimientos_registro WHERE tenant_id=:t AND colectivo_id=:c "
             "AND (CAST(:d AS date) IS NULL OR fecha >= :d) AND (CAST(:h AS date) IS NULL OR fecha <= :h) "
             "ORDER BY fecha, registrado_en, id"),
        {"t": tenant_id, "c": colectivo_id, "d": desde, "h": hasta})).mappings().all()
    registros = [dict(f) for f in filas]
    return {"registros": registros, "total": sum(r["cantidad"] for r in registros)}
