# ¤adpa
"""Capacidades de la sala Biblioteca para otras salas, y sus adaptadores hacia otras salas."""
from sqlalchemy.ext.asyncio import AsyncSession


# === BIB-402 ===
class ReferenciasVinculos:
    """Adaptador de `PuertoReferencias` (BIB-402 R3) sobre las compuertas de RAT y Hoja de Ruta."""

    async def tratamiento_existe(self, session: AsyncSession, tenant_id: str, ref: str) -> bool:
        from app_core.pasillo import rat as pasillo_rat

        return any(a.id == ref for a in await pasillo_rat.listar_actividades_resumen(session, tenant_id))

    async def tarea_existe(self, session: AsyncSession, tenant_id: str, ref: str) -> bool:
        from features.roadmap import roadmap_service

        return await roadmap_service.obtener_accion_para_enlace(session, tenant_id, ref) is not None


class HallazgosVinculos:
    """Adaptador de `PuertoHallazgos` (BIB-402 R2): hallazgo `rat` de severidad media por documento."""

    async def registrar(self, session: AsyncSession, tenant_id: str, actor: str, origen_ref: str,
                        titulo: str) -> None:
        from app_core.pasillo import roadmap as pasillo_roadmap

        await pasillo_roadmap.registrar_hallazgo_rat(
            session, tenant_id, actor, origen_ref, "media", titulo, None, None,
        )


class EvidenciasVinculos:
    """Adaptador de `PuertoEvidencias` (BIB-402 R1): registra evidencia pendiente; no toca el estado de la tarea."""

    async def adjuntar(self, session: AsyncSession, tenant_id: str, actor: str, tarea_id: str,
                       documento_id: str, sha256: str) -> None:
        from features.roadmap import roadmap_service

        await roadmap_service.register_evidence_upload(
            session, tenant_id, actor, tarea_id, f"biblioteca/documentos/{documento_id}/{sha256}",
            "text/markdown", 0, file_hash=sha256,
        )


async def al_aprobar_documento(session: AsyncSession, tenant_id: str, user_id: str, documento_id: str) -> int:
    """Para quien aprueba un documento (BIB-301): adjunta su evidencia a las tareas vinculadas."""
    from features.biblioteca import biblioteca_service

    return await biblioteca_service.al_aprobar_documento(
        session, tenant_id, user_id, documento_id, EvidenciasVinculos())


async def al_cambiar_tratamiento(session: AsyncSession, tenant_id: str, user_id: str, tratamiento_id: str) -> list[str]:
    """Para RAT (versión nueva o baja de una ficha): marca sus documentos «revisar» con un hallazgo cada uno."""
    from features.biblioteca import biblioteca_service

    return await biblioteca_service.al_cambiar_tratamiento(
        session, tenant_id, user_id, tratamiento_id, HallazgosVinculos())
# === fin BIB-402 ===
