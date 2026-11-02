# ¤roadmap ¤hallazgos ¤rbac-tenant
"""Corrida diaria de recordatorios de tareas y cierre de hallazgos de una organización (RM-23).

Contrato: governance/especificaciones/RM-23.md §2. La dispara el `implementador`; organización y autor salen
del contexto autenticado. El cron entre organizaciones se decide aparte, como en CAPA-02. Este router une las
salas `roadmap` y `notificaciones`, que no se importan entre sí (ADPA §3).
"""
import os

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from features.notificaciones import notificaciones_service
from features.roadmap import roadmap_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/roadmaps", tags=["Hoja de Ruta - Recordatorios"])

_gestion = require_role("implementador")


def _enviador(tenant_id: str, notificador: notificaciones_service.Notificador):
    async def enviar(responsable: roadmap_service.Responsable, avisos: list[roadmap_service.Aviso]) -> bool:
        destinatario = notificaciones_service.Destinatario(
            responsable.user_id, responsable.email, responsable.nombre, tenant_id
        )
        items = [
            (
                notificaciones_service.TareaAsignadaItem(a.tarea_id, a.titulo, a.control_ref, a.prioridad, a.fecha_fin),
                a.tipo,
            )
            for a in avisos
        ]
        return await notificaciones_service.enviar_recordatorios(
            destinatario, items, os.environ.get("APP_BASE_URL", ""), notificador
        )

    return enviar


@router.post("/recordatorios/ejecutar")
async def ejecutar(
    ctx: dict = Depends(_gestion),
    session: AsyncSession = Depends(get_session),
    notificador: notificaciones_service.Notificador = Depends(notificaciones_service.notificador_configurado),
):
    resultado = await roadmap_service.ejecutar_recordatorios(
        session, ctx["tenant_id"], ctx["user_id"], _enviador(ctx["tenant_id"], notificador)
    )
    return {"correos": resultado.correos, "hallazgos_cerrados": resultado.hallazgos_cerrados}
