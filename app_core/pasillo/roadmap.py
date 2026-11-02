# ¤adpa
"""Capacidades de la sala Hoja de Ruta para otras salas."""
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession


async def registrar_hallazgo_de_control_vencido(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    titulo: str,
    control_ref: Optional[str],
) -> tuple[str, bool]:
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.control_periodico.value,
        origen_ref=origen_ref,
        severidad=roadmap_service.SeveridadHallazgo.alta.value,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=control_ref,
    )


async def cerrar_hallazgo(session: AsyncSession, tenant_id: str, user_id: str, hallazgo_id: str) -> None:
    from features.roadmap import roadmap_service

    await roadmap_service.cerrar_hallazgo(session, tenant_id, user_id, hallazgo_id)


# === RAT-05 ===
async def registrar_hallazgo_rat(
    session: AsyncSession,
    tenant_id: str,
    user_id: str,
    origen_ref: str,
    severidad: str,
    titulo: str,
    control_ref: Optional[str],
    dimension: Optional[str],
) -> tuple[str, bool]:
    from features.roadmap import roadmap_service

    return await roadmap_service.registrar_hallazgo(
        session,
        tenant_id,
        user_id,
        origen=roadmap_service.OrigenHallazgo.rat.value,
        origen_ref=origen_ref,
        severidad=severidad,
        titulo=titulo[:roadmap_service.TITULO_MAX],
        control_ref=control_ref,
        dimension=dimension,
    )


async def listar_hallazgos_rat(session: AsyncSession, tenant_id: str, user_id: str) -> list:
    from features.roadmap import roadmap_service

    return await roadmap_service.listar_hallazgos(
        session, tenant_id, user_id, origen=roadmap_service.OrigenHallazgo.rat.value
    )


async def reabrir_hallazgo(session: AsyncSession, tenant_id: str, user_id: str, hallazgo_id: str) -> None:
    from features.roadmap import roadmap_service

    await roadmap_service.reabrir_hallazgo(session, tenant_id, user_id, hallazgo_id)
# === fin RAT-05 ===
