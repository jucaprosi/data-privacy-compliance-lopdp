# ¤adpa ¤rbac-tenant
# ¤¤developer-architect
"""Motor de plantillas de la cuenta profesional (BIB-401).

Tercera capa de plantillas entre la maestra publicada (SMARTCIDI) y la de la organización.
Permite al implementador mantener copias con marca y criterio propios utilizables
en las organizaciones donde actúa como implementador (ORG-15).
Aislamiento por RLS de cuenta_id (app.current_user_id).
"""
from __future__ import annotations

import difflib
import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.errors import ErrorNegocio


class PlantillaCuenta(BaseModel):
    """Contrato de la copia de plantilla de cuenta profesional."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    cuenta_id: str
    maestra_codigo: str
    maestra_version: str
    contenido_key: Optional[str] = None
    contenido: Optional[str] = None
    marca: Optional[dict[str, Any]] = None
    estado: str = "vigente"
    creado_por: str
    creado_en: datetime
    actualizado_en: datetime


class PlantillaCuentaCreate(BaseModel):
    """Entrada para crear una copia de plantilla de cuenta profesional."""
    maestra_codigo: str
    marca: Optional[dict[str, Any]] = None
    contenido: Optional[str] = None


class PlantillaCuentaUpdate(BaseModel):
    """Entrada para editar la copia de plantilla de cuenta profesional."""
    contenido: Optional[str] = None
    marca: Optional[dict[str, Any]] = None
    estado: Optional[str] = None


class DiffMaestra(BaseModel):
    """Respuesta de diferencias entre la copia y la maestra vigente."""
    maestra_vigente: str
    cambios: list[str]


# ¤adpa
async def fijar_contexto_cuenta(session: AsyncSession, usuario_id: str) -> None:
    """Fija la variable de sesión para que PostgreSQL RLS aísle por cuenta_id."""
    await session.execute(
        text("SELECT set_config('app.current_user_id', :u, true)"),
        {"u": usuario_id},
    )


def _mapear_fila(fila: dict[str, Any]) -> PlantillaCuenta:
    """Convierte fila SQL a entidad PlantillaCuenta."""
    contenido = fila.get("contenido_key")
    marca = fila.get("marca")
    if isinstance(marca, str):
        try:
            marca = json.loads(marca)
        except Exception:
            marca = {}
    return PlantillaCuenta(
        id=fila["id"],
        cuenta_id=fila["cuenta_id"],
        maestra_codigo=fila["maestra_codigo"],
        maestra_version=str(fila["maestra_version"]),
        contenido_key=contenido,
        contenido=contenido,
        marca=marca or {},
        estado=fila["estado"],
        creado_por=fila["creado_por"],
        creado_en=fila["creado_en"],
        actualizado_en=fila["actualizado_en"],
    )


# ¤adpa
async def crear_plantilla_cuenta(
    session: AsyncSession,
    usuario_id: str,
    entrada: PlantillaCuentaCreate | dict[str, Any],
) -> PlantillaCuenta:
    """Crea una copia de la maestra publicada para la cuenta profesional del implementador."""
    if isinstance(entrada, dict):
        entrada = PlantillaCuentaCreate(**entrada)

    await fijar_contexto_cuenta(session, usuario_id)

    # 1. Buscar la maestra publicada correspondiente
    sql_maestra = """
        SELECT id, codigo, version, cuerpo_md
        FROM biblioteca_versiones
        WHERE codigo = :codigo AND estado = 'publicada'
        ORDER BY creada_en DESC
        LIMIT 1
    """
    res_maestra = (await session.execute(text(sql_maestra), {"codigo": entrada.maestra_codigo})).mappings().first()
    if res_maestra is None:
        raise ErrorNegocio("BIB_NO_ENCONTRADA", f"Maestra {entrada.maestra_codigo} no publicada o inexistente.")

    nuevo_id = str(uuid4())
    version_origen = str(res_maestra["version"])
    cuerpo = entrada.contenido if entrada.contenido is not None else (res_maestra["cuerpo_md"] or "")
    marca_dict = entrada.marca or {}
    marca_json = json.dumps(marca_dict)

    sql_insert = """
        INSERT INTO biblioteca_plantillas_cuenta (
            id, cuenta_id, maestra_codigo, maestra_version, contenido_key, marca, estado, creado_por, creado_en, actualizado_en
        ) VALUES (
            :id, :cuenta_id, :codigo, :version, :contenido, CAST(:marca AS jsonb), 'vigente', :creado_por, now(), now()
        )
    """
    await session.execute(
        text(sql_insert),
        {
            "id": nuevo_id,
            "cuenta_id": usuario_id,
            "codigo": entrada.maestra_codigo,
            "version": version_origen,
            "contenido": cuerpo,
            "marca": marca_json,
            "creado_por": usuario_id,
        },
    )

    return await obtener_plantilla_cuenta(session, usuario_id, nuevo_id)


# ¤adpa
async def listar_plantillas_cuenta(
    session: AsyncSession,
    usuario_id: str,
) -> list[PlantillaCuenta]:
    """Lista las copias de plantilla que pertenecen a la cuenta del implementador."""
    await fijar_contexto_cuenta(session, usuario_id)

    sql = """
        SELECT id, cuenta_id, maestra_codigo, maestra_version, contenido_key, marca, estado, creado_por, creado_en, actualizado_en
        FROM biblioteca_plantillas_cuenta
        WHERE cuenta_id = :u
        ORDER BY creado_en DESC
    """
    filas = (await session.execute(text(sql), {"u": usuario_id})).mappings().all()

    # Comprobar si alguna copia vigente quedó desactualizada frente a la maestra publicada actual
    resultado: list[PlantillaCuenta] = []
    for f in filas:
        item = _mapear_fila(dict(f))
        if item.estado == "vigente":
            sql_check = """
                SELECT version FROM biblioteca_versiones
                WHERE codigo = :cod AND estado = 'publicada'
                ORDER BY creada_en DESC LIMIT 1
            """
            v_act = (await session.execute(text(sql_check), {"cod": item.maestra_codigo})).scalar_one_or_none()
            if v_act is not None and str(v_act) != item.maestra_version:
                # Actualizar estado a desactualizada conservando el contenido intacto (R2)
                await session.execute(
                    text("UPDATE biblioteca_plantillas_cuenta SET estado = 'desactualizada', actualizado_en = now() WHERE id = :id"),
                    {"id": item.id},
                )
                item.estado = "desactualizada"
        resultado.append(item)

    return resultado


# ¤adpa
async def obtener_plantilla_cuenta(
    session: AsyncSession,
    usuario_id: str,
    id_: str,
) -> PlantillaCuenta:
    """Obtiene una copia de plantilla por id; verifica pertenencia y RLS."""
    await fijar_contexto_cuenta(session, usuario_id)

    sql = """
        SELECT id, cuenta_id, maestra_codigo, maestra_version, contenido_key, marca, estado, creado_por, creado_en, actualizado_en
        FROM biblioteca_plantillas_cuenta
        WHERE id = :id AND cuenta_id = :u
    """
    fila = (await session.execute(text(sql), {"id": id_, "u": usuario_id})).mappings().first()
    if fila is None:
        raise ErrorNegocio("BIB_NO_ENCONTRADA", f"Plantilla de cuenta {id_} no encontrada.")

    item = _mapear_fila(dict(fila))
    if item.estado == "vigente":
        sql_check = """
            SELECT version FROM biblioteca_versiones
            WHERE codigo = :cod AND estado = 'publicada'
            ORDER BY creada_en DESC LIMIT 1
        """
        v_act = (await session.execute(text(sql_check), {"cod": item.maestra_codigo})).scalar_one_or_none()
        if v_act is not None and str(v_act) != item.maestra_version:
            await session.execute(
                text("UPDATE biblioteca_plantillas_cuenta SET estado = 'desactualizada', actualizado_en = now() WHERE id = :id"),
                {"id": item.id},
            )
            item.estado = "desactualizada"

    return item


# ¤adpa
async def actualizar_plantilla_cuenta(
    session: AsyncSession,
    usuario_id: str,
    id_: str,
    entrada: PlantillaCuentaUpdate | dict[str, Any],
) -> PlantillaCuenta:
    """Actualiza contenido o marca de la copia de plantilla de cuenta."""
    if isinstance(entrada, dict):
        entrada = PlantillaCuentaUpdate(**entrada)

    actual = await obtener_plantilla_cuenta(session, usuario_id, id_)

    nuevo_contenido = entrada.contenido if entrada.contenido is not None else actual.contenido_key
    nueva_marca = entrada.marca if entrada.marca is not None else actual.marca
    nuevo_estado = entrada.estado if entrada.estado is not None else actual.estado

    sql_upd = """
        UPDATE biblioteca_plantillas_cuenta
        SET contenido_key = :contenido,
            marca = CAST(:marca AS jsonb),
            estado = :estado,
            actualizado_en = now()
        WHERE id = :id AND cuenta_id = :u
    """
    await session.execute(
        text(sql_upd),
        {
            "id": id_,
            "u": usuario_id,
            "contenido": nuevo_contenido,
            "marca": json.dumps(nueva_marca or {}),
            "estado": nuevo_estado,
        },
    )

    return await obtener_plantilla_cuenta(session, usuario_id, id_)


# ¤adpa
async def obtener_diff_maestra(
    session: AsyncSession,
    usuario_id: str,
    id_: str,
) -> DiffMaestra:
    """Calcula la diferencia textual entre la copia de la cuenta y la maestra publicada actual."""
    copia = await obtener_plantilla_cuenta(session, usuario_id, id_)

    sql_maestra = """
        SELECT version, cuerpo_md
        FROM biblioteca_versiones
        WHERE codigo = :codigo AND estado = 'publicada'
        ORDER BY creada_en DESC
        LIMIT 1
    """
    maestra = (await session.execute(text(sql_maestra), {"codigo": copia.maestra_codigo})).mappings().first()
    if maestra is None:
        raise ErrorNegocio("BIB_NO_ENCONTRADA", f"Maestra {copia.maestra_codigo} no publicada.")

    lineas_copia = (copia.contenido_key or "").splitlines()
    lineas_maestra = (maestra["cuerpo_md"] or "").splitlines()

    cambios = list(
        difflib.unified_diff(
            lineas_copia,
            lineas_maestra,
            fromfile=f"cuenta/{copia.maestra_codigo} (v{copia.maestra_version})",
            tofile=f"maestra/{copia.maestra_codigo} (v{maestra['version']})",
            lineterm="",
        )
    )

    return DiffMaestra(maestra_vigente=str(maestra["version"]), cambios=cambios)


# ¤adpa
async def aplicar_maestra(
    session: AsyncSession,
    usuario_id: str,
    id_: str,
) -> PlantillaCuenta:
    """Aplica la última versión de la maestra publicada a la copia de cuenta, dejándola vigente."""
    copia = await obtener_plantilla_cuenta(session, usuario_id, id_)

    sql_maestra = """
        SELECT version, cuerpo_md
        FROM biblioteca_versiones
        WHERE codigo = :codigo AND estado = 'publicada'
        ORDER BY creada_en DESC
        LIMIT 1
    """
    maestra = (await session.execute(text(sql_maestra), {"codigo": copia.maestra_codigo})).mappings().first()
    if maestra is None:
        raise ErrorNegocio("BIB_NO_ENCONTRADA", f"Maestra {copia.maestra_codigo} no publicada.")

    v_maestra = str(maestra["version"])
    if copia.estado == "vigente" and copia.maestra_version == v_maestra:
        # Error 409 si ya está al día
        raise ErrorNegocio("BIB_SUSTITUCION_REQUERIDA", "La copia ya se encuentra al día con la maestra publicada.")

    sql_aplica = """
        UPDATE biblioteca_plantillas_cuenta
        SET maestra_version = :version,
            contenido_key = :contenido,
            estado = 'vigente',
            actualizado_en = now()
        WHERE id = :id AND cuenta_id = :u
    """
    await session.execute(
        text(sql_aplica),
        {
            "id": id_,
            "u": usuario_id,
            "version": v_maestra,
            "contenido": maestra["cuerpo_md"] or "",
        },
    )

    return await obtener_plantilla_cuenta(session, usuario_id, id_)
