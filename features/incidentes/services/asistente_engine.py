# ¤incidentes ¤hallazgos ¤rbac-tenant
"""Asistente de vulneración en PostgreSQL (INC-02): todo se agrega, nada se actualiza ni se borra (R6).

Guardar una sección inserta la versión siguiente; dos guardados simultáneos chocan en
UNIQUE (incidente_id, seccion, version) y el segundo recibe 409. Las lecciones de la sección 6 se
registran como hallazgos por el puerto `PuertoHallazgos`; sin la capacidad en el pasillo de la hoja de
ruta, el puerto falla cerrado (503) y la sección no se guarda.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, Protocol

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.audit import registrar_evento
from app_core.db.session import fijar_contexto_rls
from app_core.errors import ErrorNegocio
from features.incidentes.domain.estado import IncidenteNoEncontrado
from features.incidentes.domain.vulneracion import (
    DESTINOS,
    SECCION_DECISION,
    SECCION_INFORMES,
    EstadoAsistente,
    destinos_de,
    exigir_rol,
    normalizar_seccion,
)

SEVERIDAD_LECCION = "media"


class PuertoHallazgos(Protocol):
    async def registrar(
        self, session: AsyncSession, tenant_id: str, user_id: str, origen_ref: str, titulo: str
    ) -> str: ...


class HallazgosPorPasillo:
    """Adaptador real: la capacidad `registrar_hallazgo_incidente` del pasillo de la hoja de ruta.

    Mientras esa sección no exista en `app_core/pasillo/roadmap.py`, falla cerrado.
    """

    async def registrar(self, session, tenant_id, user_id, origen_ref, titulo) -> str:
        from app_core.pasillo import roadmap

        capacidad = getattr(roadmap, "registrar_hallazgo_incidente", None)
        if capacidad is None:
            raise ErrorNegocio("LECCIONES_NO_DISPONIBLES")
        hallazgo_id, _ = await capacidad(
            session, tenant_id, user_id, origen_ref=origen_ref, severidad=SEVERIDAD_LECCION, titulo=titulo
        )
        return hallazgo_id


async def _titulo_de(session: AsyncSession, tenant_id: str, incidente_id: str) -> dict:
    fila = (
        await session.execute(
            text("SELECT titulo, afecta_datos_personales FROM incidentes WHERE id = :i AND tenant_id = :t"),
            {"i": incidente_id, "t": tenant_id},
        )
    ).mappings().first()
    if fila is None:
        raise IncidenteNoEncontrado(incidente_id)
    return dict(fila)


async def _ultimas_versiones(session: AsyncSession, tenant_id: str, incidente_id: str) -> dict[int, dict]:
    filas = (
        await session.execute(
            text(
                "SELECT DISTINCT ON (seccion) seccion, version, datos, registrado_por, registrado_en "
                "FROM incidentes_asistente_secciones WHERE incidente_id = :i AND tenant_id = :t "
                "ORDER BY seccion, version DESC"
            ),
            {"i": incidente_id, "t": tenant_id},
        )
    ).mappings().all()
    return {int(f["seccion"]): dict(f) for f in filas}


async def _estado(session: AsyncSession, tenant_id: str, incidente_id: str) -> EstadoAsistente:
    versiones = await _ultimas_versiones(session, tenant_id, incidente_id)
    informes = (
        await session.execute(
            text("SELECT DISTINCT destino FROM incidentes_informes WHERE incidente_id = :i AND tenant_id = :t"),
            {"i": incidente_id, "t": tenant_id},
        )
    ).scalars().all()
    notificados = (
        await session.execute(
            text("SELECT DISTINCT destino FROM incidentes_notificaciones WHERE incidente_id = :i AND tenant_id = :t"),
            {"i": incidente_id, "t": tenant_id},
        )
    ).scalars().all()
    return EstadoAsistente(
        secciones={n: v["datos"] for n, v in versiones.items()},
        informes=frozenset(informes),
        notificados=frozenset(notificados),
    )


async def estado_asistente(session: AsyncSession, tenant_id: str, user_id: str, incidente_id: str) -> EstadoAsistente:
    await fijar_contexto_rls(session, tenant_id, user_id)
    await _titulo_de(session, tenant_id, incidente_id)
    return await _estado(session, tenant_id, incidente_id)


async def resumen_asistentes(session: AsyncSession, tenant_id: str, user_id: str) -> dict[str, dict]:
    """Sección actual de cada incidente de la organización, para la lista."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    ids = (await session.execute(text("SELECT id FROM incidentes WHERE tenant_id = :t"), {"t": tenant_id})).scalars().all()
    salida = {}
    for incidente_id in ids:
        estado = await _estado(session, tenant_id, incidente_id)
        salida[incidente_id] = {"seccion_actual": estado.seccion_actual, "decision": estado.decision}
    return salida


async def _insertar_version(
    session: AsyncSession, tenant_id: str, user_id: str, incidente_id: str, seccion: int, datos: dict
) -> int:
    version = (
        await session.execute(
            text(
                "SELECT coalesce(max(version), 0) + 1 FROM incidentes_asistente_secciones "
                "WHERE incidente_id = :i AND tenant_id = :t AND seccion = :s"
            ),
            {"i": incidente_id, "t": tenant_id, "s": seccion},
        )
    ).scalar_one()
    try:
        async with session.begin_nested():
            await session.execute(
                text(
                    "INSERT INTO incidentes_asistente_secciones "
                    "(id, tenant_id, incidente_id, seccion, version, datos, registrado_por, registrado_en) "
                    "VALUES (:id, :t, :i, :s, :v, CAST(:d AS JSONB), :u, :en)"
                ),
                {
                    "id": str(uuid.uuid4()), "t": tenant_id, "i": incidente_id, "s": seccion, "v": version,
                    "d": json.dumps(datos, ensure_ascii=False), "u": user_id, "en": datetime.now(timezone.utc),
                },
            )
    except IntegrityError as exc:
        if "uq_inc_secciones_version" in str(exc.orig):
            raise ErrorNegocio("ASISTENTE_CAMBIO_CONCURRENTE") from exc
        raise
    return int(version)


async def _agregar_tratamientos(session, tenant_id, user_id, incidente_id, tratamiento_ids: list[str]) -> None:
    previos = set(
        (
            await session.execute(
                text("SELECT tratamiento_id FROM incidentes_tratamientos WHERE incidente_id = :i AND tenant_id = :t"),
                {"i": incidente_id, "t": tenant_id},
            )
        ).scalars().all()
    )
    for tratamiento_id in tratamiento_ids:
        if tratamiento_id in previos:
            continue
        previos.add(tratamiento_id)
        await session.execute(
            text(
                "INSERT INTO incidentes_tratamientos (id, tenant_id, incidente_id, tratamiento_id, registrado_por) "
                "VALUES (:id, :t, :i, :tr, :u)"
            ),
            {"id": str(uuid.uuid4()), "t": tenant_id, "i": incidente_id, "tr": tratamiento_id, "u": user_id},
        )


async def _agregar_lecciones(
    session, tenant_id, user_id, incidente_id, lecciones: list[str], hallazgos: PuertoHallazgos
) -> int:
    """Cada lección nueva (por texto) es una fila y un hallazgo `incidente` (R4). Devuelve cuántas se agregaron."""
    previas = (
        await session.execute(
            text("SELECT numero, texto FROM incidentes_lecciones WHERE incidente_id = :i AND tenant_id = :t"),
            {"i": incidente_id, "t": tenant_id},
        )
    ).mappings().all()
    textos = {f["texto"] for f in previas}
    numero = max((f["numero"] for f in previas), default=0)
    nuevas = 0
    for leccion in lecciones:
        if leccion in textos:
            continue
        textos.add(leccion)
        numero += 1
        hallazgo_id = await hallazgos.registrar(
            session, tenant_id, user_id, f"{incidente_id}:leccion:{numero}", f"Lección de vulneración: {leccion}"[:200]
        )
        await session.execute(
            text(
                "INSERT INTO incidentes_lecciones (id, tenant_id, incidente_id, numero, texto, hallazgo_id, registrado_por) "
                "VALUES (:id, :t, :i, :n, :tx, :h, :u)"
            ),
            {
                "id": str(uuid.uuid4()), "t": tenant_id, "i": incidente_id, "n": numero, "tx": leccion,
                "h": hallazgo_id, "u": user_id,
            },
        )
        nuevas += 1
    return nuevas


async def guardar_seccion(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    rol: str,
    incidente_id: str,
    seccion: int,
    datos: Any,
    hallazgos: Optional[PuertoHallazgos] = None,
) -> EstadoAsistente:
    """Valida y agrega una versión de la sección 1 a 7 (la 8 se registra con `registrar_notificacion`)."""
    exigir_rol(seccion, rol)
    limpio = normalizar_seccion(seccion, datos)
    await fijar_contexto_rls(session, tenant_id, user_id)
    await _titulo_de(session, tenant_id, incidente_id)
    estado = await _estado(session, tenant_id, incidente_id)
    if seccion == SECCION_DECISION:
        estado.exigir_previas(SECCION_DECISION)
    version = await _insertar_version(session, tenant_id, user_id, incidente_id, seccion, limpio)
    if seccion == 2:
        await _agregar_tratamientos(session, tenant_id, user_id, incidente_id, limpio["tratamiento_ids"])
    if seccion == 6 and limpio["lecciones"]:
        await _agregar_lecciones(
            session, tenant_id, user_id, incidente_id, limpio["lecciones"], hallazgos or HallazgosPorPasillo()
        )
    await registrar_evento(
        session, tenant_id, "incidente", incidente_id, "asistente_seccion_guardada", user_id,
        {"seccion": seccion, "version": version, "decision": limpio.get("decision")},
    )
    return await _estado(session, tenant_id, incidente_id)


async def registrar_notificacion(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    rol: str,
    incidente_id: str,
    destino: str,
    notificado_en: datetime,
    evidencia_sha256: str,
    custodiado,
) -> EstadoAsistente:
    """Sección 8: fecha y evidencia (ya custodiada) de una notificación. La fecha no se compara con plazos."""
    exigir_rol(SECCION_INFORMES, rol)
    if destino not in DESTINOS:
        raise ErrorNegocio("SECCION_INCOMPLETA", detail="Destino no admitido.")
    await fijar_contexto_rls(session, tenant_id, user_id)
    await _titulo_de(session, tenant_id, incidente_id)
    estado = await _estado(session, tenant_id, incidente_id)
    estado.exigir_previas(SECCION_INFORMES)
    if destino not in destinos_de(estado.decision):
        raise ErrorNegocio("INFORME_NO_PEDIDO")
    if destino not in estado.informes:
        raise ErrorNegocio("SECCION_ANTERIOR_INCOMPLETA", detail="Genera el informe antes de registrar la notificación.")
    huella = await custodiado(session, tenant_id, user_id, evidencia_sha256)
    if huella is None:
        raise ErrorNegocio("EVIDENCIA_NO_CUSTODIADA")
    await session.execute(
        text(
            "INSERT INTO incidentes_notificaciones "
            "(id, tenant_id, incidente_id, destino, notificado_en, evidencia_sha256, registrado_por) "
            "VALUES (:id, :t, :i, :d, :en, :h, :u)"
        ),
        {
            "id": str(uuid.uuid4()), "t": tenant_id, "i": incidente_id, "d": destino, "en": notificado_en,
            "h": huella, "u": user_id,
        },
    )
    await registrar_evento(
        session, tenant_id, "incidente", incidente_id, "notificacion_registrada", user_id,
        {"destino": destino, "evidencia_sha256": huella, "rol": rol},
    )
    return await _estado(session, tenant_id, incidente_id)


async def tiene_decision(session: AsyncSession, tenant_id: str, incidente_id: str) -> bool:
    """¿Hay al menos una versión de la sección 7? (precondición de cierre, R7). El contexto RLS ya está fijado."""
    fila = (
        await session.execute(
            text(
                "SELECT 1 FROM incidentes_asistente_secciones "
                "WHERE incidente_id = :i AND tenant_id = :t AND seccion = :s LIMIT 1"
            ),
            {"i": incidente_id, "t": tenant_id, "s": SECCION_DECISION},
        )
    ).first()
    return fila is not None


async def notificaciones_por_implementador(session: AsyncSession, tenant_id: str, user_id: str) -> list[dict]:
    """Notificaciones que marcó un implementador, para la bandeja del DPO (decisión del CTO 2026-11-13)."""
    await fijar_contexto_rls(session, tenant_id, user_id)
    filas = (
        await session.execute(
            text(
                "SELECT n.incidente_id, i.titulo, n.destino, n.notificado_en, n.registrado_por, n.registrado_en "
                "FROM incidentes_notificaciones n JOIN incidentes i ON i.id = n.incidente_id AND i.tenant_id = n.tenant_id "
                "JOIN user_tenant_roles r ON r.user_id = n.registrado_por AND r.tenant_id = n.tenant_id "
                "AND r.role = 'implementador' WHERE n.tenant_id = :t ORDER BY n.registrado_en DESC"
            ),
            {"t": tenant_id},
        )
    ).mappings().all()
    return [dict(f) for f in filas]


async def datos_para_informe(session: AsyncSession, tenant_id: str, incidente_id: str) -> tuple[str, EstadoAsistente]:
    incidente = await _titulo_de(session, tenant_id, incidente_id)
    return incidente["titulo"], await _estado(session, tenant_id, incidente_id)


__all__ = [
    "HallazgosPorPasillo",
    "PuertoHallazgos",
    "datos_para_informe",
    "estado_asistente",
    "guardar_seccion",
    "notificaciones_por_implementador",
    "registrar_notificacion",
    "resumen_asistentes",
    "tiene_decision",
]
