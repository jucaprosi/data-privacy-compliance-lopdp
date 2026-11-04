# ¤adpa ¤rbac-tenant
"""API BIB-402: vínculos de un documento con tratamientos, controles y tareas."""
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.rbac import get_context, require_role
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as biblioteca

AUTO_REGISTRO = True


# Adaptadores de los puertos del motor sobre las compuertas de RAT y Hoja de Ruta; aquí no hay lógica.
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


router = APIRouter(prefix="/biblioteca", tags=["Biblioteca vínculos"])
Sesion = Annotated[AsyncSession, Depends(get_session)]
Consulta = Annotated[dict, Depends(get_context)]
Gestion = Annotated[dict, Depends(require_role("implementador", "coordinador"))]


@router.get("/documentos/{documento_id}/vinculos", response_model=biblioteca.VinculosDocumento)
async def listar(documento_id: str, session: Sesion, ctx: Consulta):
    return await biblioteca.listar_vinculos(session, ctx["tenant_id"], ctx["user_id"], documento_id)


@router.put("/documentos/{documento_id}/vinculos", response_model=biblioteca.VinculosDocumento)
async def reemplazar(documento_id: str, entrada: biblioteca.EntradaVinculos, session: Sesion, ctx: Gestion):
    return await biblioteca.reemplazar_vinculos(
        session, ctx["tenant_id"], ctx["user_id"], documento_id, entrada, ReferenciasVinculos())


@router.get("/tratamientos/{tratamiento_id}/documentos", response_model=list[biblioteca.DocumentoVinculado])
async def documentos_de_tratamiento(tratamiento_id: str, session: Sesion, ctx: Consulta):
    return await biblioteca.documentos_de_tratamiento(session, ctx["tenant_id"], ctx["user_id"], tratamiento_id)
