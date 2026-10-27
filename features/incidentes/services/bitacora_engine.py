# ¤incidentes ¤rbac-tenant ¤seguridad
"""Registro y consulta de la bitácora de incidentes en PostgreSQL (INC-01).

Quién registra es el usuario autenticado y la hora la pone el servidor: el navegador no fija
autoría, plazos, huellas ni fechas de registro. La aplicación (lopdp_app) solo puede leer e
insertar; por eso los registros de una organización se serializan con un candado de transacción
y no con SELECT ... FOR UPDATE, que exige permiso de actualización.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from features.incidentes.domain.models import HUELLA_GENESIS, FechaDeteccionFutura, Incidente

# Margen por la diferencia de relojes entre el navegador y el servidor.
MARGEN_RELOJ = timedelta(minutes=1)

_COLUMNAS = (
    "id, tenant_id, secuencia, fecha_deteccion, titulo, descripcion, severidad, "
    "afecta_datos_personales, categorias_datos, medidas_inmediatas, registrado_por, registrado_en, "
    "huella_anterior, huella"
)


def calcular_huella(contenido: dict[str, Any]) -> str:
    crudo = json.dumps(contenido, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(crudo.encode("utf-8")).hexdigest()


def _en_utc(valor: datetime) -> datetime:
    return (valor if valor.tzinfo else valor.replace(tzinfo=timezone.utc)).astimezone(timezone.utc)


def _fila_a_incidente(fila: dict[str, Any]) -> Incidente:
    return Incidente(
        id=fila["id"],
        tenant_id=fila["tenant_id"],
        secuencia=int(fila["secuencia"]),
        fecha_deteccion=_en_utc(fila["fecha_deteccion"]),
        titulo=fila["titulo"],
        descripcion=fila["descripcion"],
        severidad=fila["severidad"],
        afecta_datos_personales=bool(fila["afecta_datos_personales"]),
        categorias_datos=list(fila["categorias_datos"]),
        medidas_inmediatas=fila["medidas_inmediatas"],
        registrado_por=fila["registrado_por"],
        registrado_en=_en_utc(fila["registrado_en"]),
        huella_anterior=fila["huella_anterior"],
        huella=fila["huella"],
    )


async def listar_incidentes(session: AsyncSession, tenant_id: str, user_id: str) -> list[Incidente]:
    """Incidentes de la organización en el orden en que se registraron."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = await session.execute(
        text(f"SELECT {_COLUMNAS} FROM incidentes WHERE tenant_id = :t ORDER BY secuencia"),
        {"t": tenant_id},
    )
    return [_fila_a_incidente(dict(f)) for f in filas.mappings().all()]


def primer_incidente_alterado(incidentes: list[Incidente]) -> Optional[Incidente]:
    """Recorre la cadena en orden y devuelve el primer incidente que no cuadra, o None."""
    anterior = HUELLA_GENESIS
    for incidente in incidentes:
        if incidente.huella_anterior != anterior or calcular_huella(incidente.contenido()) != incidente.huella:
            return incidente
        anterior = incidente.huella
    return None


async def registrar_incidente(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    *,
    fecha_deteccion: datetime,
    titulo: str,
    descripcion: str,
    severidad: str,
    afecta_datos_personales: bool,
    categorias_datos: list[str],
    medidas_inmediatas: str,
) -> Incidente:
    """Registra un incidente encadenando su huella a la del anterior de la organización."""
    ahora = datetime.now(timezone.utc)
    deteccion = _en_utc(fecha_deteccion)
    if deteccion > ahora + MARGEN_RELOJ:
        raise FechaDeteccionFutura("La fecha de detección no puede ser posterior al momento del registro.")

    await fijar_contexto_rls(session, tenant_id, user_id)
    await session.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:clave))"),
        {"clave": f"incidentes:{tenant_id}"},
    )
    ultimo = (
        await session.execute(
            text(
                "SELECT secuencia, huella, registrado_en FROM incidentes "
                "WHERE tenant_id = :t ORDER BY secuencia DESC LIMIT 1"
            ),
            {"t": tenant_id},
        )
    ).mappings().first()
    if ultimo is not None and ahora <= ultimo["registrado_en"]:
        ahora = _en_utc(ultimo["registrado_en"]) + timedelta(microseconds=1)

    incidente = Incidente(
        id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        secuencia=(int(ultimo["secuencia"]) + 1) if ultimo else 1,
        fecha_deteccion=deteccion,
        titulo=titulo,
        descripcion=descripcion,
        severidad=severidad,
        afecta_datos_personales=afecta_datos_personales,
        categorias_datos=list(categorias_datos),
        medidas_inmediatas=medidas_inmediatas,
        registrado_por=user_id,
        registrado_en=ahora,
        huella_anterior=str(ultimo["huella"]) if ultimo else HUELLA_GENESIS,
    )
    incidente.huella = calcular_huella(incidente.contenido())

    await session.execute(
        text(
            f"INSERT INTO incidentes ({_COLUMNAS}) VALUES "
            "(:id, :tenant_id, :secuencia, :fecha_deteccion, :titulo, :descripcion, :severidad, "
            ":afecta_datos_personales, CAST(:categorias_datos AS jsonb), :medidas_inmediatas, "
            ":registrado_por, :registrado_en, :huella_anterior, :huella)"
        ),
        {
            "id": incidente.id,
            "tenant_id": tenant_id,
            "secuencia": incidente.secuencia,
            "fecha_deteccion": incidente.fecha_deteccion,
            "titulo": incidente.titulo,
            "descripcion": incidente.descripcion,
            "severidad": incidente.severidad,
            "afecta_datos_personales": incidente.afecta_datos_personales,
            "categorias_datos": json.dumps(incidente.categorias_datos, ensure_ascii=False),
            "medidas_inmediatas": incidente.medidas_inmediatas,
            "registrado_por": user_id,
            "registrado_en": incidente.registrado_en,
            "huella_anterior": incidente.huella_anterior,
            "huella": incidente.huella,
        },
    )
    await registrar_evento(
        session,
        tenant_id,
        "incidente",
        incidente.id,
        "incidente_registrado",
        user_id,
        {
            "secuencia": incidente.secuencia,
            "severidad": incidente.severidad,
            "afecta_datos_personales": incidente.afecta_datos_personales,
            "huella": incidente.huella,
        },
    )
    return incidente
