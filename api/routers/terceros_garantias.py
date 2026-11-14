# ¤hallazgos ¤evidencias ¤rbac-tenant
"""Contrato y garantía de terceros con hallazgos automáticos (TER-01).

Contrato: governance/especificaciones/TER-01.md §2. Organización y autor salen del contexto autenticado.
Los adaptadores de abajo conectan la sala terceros con transferencias (tabla) y roadmap (hallazgos) por el\npasillo central (secciones TER-01), y con evidencias por su compuerta: la huella se busca en la tabla\nevidencias_documentos, la misma que lista GET /evidencias/documentos (deuda 3 del #767).
"""
from __future__ import annotations

from datetime import date
from typing import Optional, Sequence

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.rbac import require_role
from app_core.db.session import get_session
from app_core.pasillo import roadmap as pasillo_roadmap
from app_core.pasillo import transferencias as pasillo_transferencias
from features.evidencias import evidencias_service
from features.terceros import terceros_service

AUTO_REGISTRO = True
router = APIRouter(prefix="/terceros", tags=["Terceros - Garantías"])

ROLES_CONSULTA = ("implementador", "coordinador", "dpo", "admin_organizacion", "auditor")
ROLES_GESTION = ("implementador", "coordinador")
ROLES_EVALUACION = ("implementador",)

_consulta = require_role(*ROLES_CONSULTA)
_gestion = require_role(*ROLES_GESTION)
_evaluacion = require_role(*ROLES_EVALUACION)


class _Terceros:
    def __init__(self, session: AsyncSession, tenant_id: str, user_id: str):
        self.s, self.t, self.u = session, tenant_id, user_id

    async def listar(self) -> Sequence[terceros_service.TerceroGarantias]:
        filas = await pasillo_transferencias.listar_garantias_terceros(self.s, self.t, self.u)
        return [terceros_service.tercero_desde_fila(f) for f in filas]

    async def obtener(self, tercero_id: str) -> Optional[terceros_service.TerceroGarantias]:
        fila = await pasillo_transferencias.obtener_garantias_tercero(self.s, self.t, self.u, tercero_id)
        return terceros_service.tercero_desde_fila(fila) if fila else None

    async def actualizar(self, tercero_id: str, campos: dict) -> Optional[terceros_service.TerceroGarantias]:
        fila = await pasillo_transferencias.actualizar_garantias_tercero(self.s, self.t, self.u, tercero_id, campos)
        return terceros_service.tercero_desde_fila(fila) if fila else None


class _Hallazgos:
    def __init__(self, session: AsyncSession, tenant_id: str, user_id: str):
        self.s, self.t, self.u = session, tenant_id, user_id

    async def listar(self) -> Sequence[terceros_service.HallazgoExistente]:
        hallazgos = await pasillo_roadmap.listar_hallazgos_tercero(self.s, self.t, self.u)
        return [terceros_service.HallazgoExistente(h.id, h.origen_ref, h.estado) for h in hallazgos]

    async def abrir(self, origen_ref: str, severidad: str, titulo: str) -> str:
        hallazgo_id, _ = await pasillo_roadmap.registrar_hallazgo_tercero(
            self.s, self.t, self.u, origen_ref, severidad, titulo
        )
        return hallazgo_id

    async def reabrir(self, hallazgo_id: str) -> None:
        await pasillo_roadmap.reabrir_hallazgo(self.s, self.t, self.u, hallazgo_id)

    async def cerrar(self, hallazgo_id: str) -> None:
        await pasillo_roadmap.cerrar_hallazgo(self.s, self.t, self.u, hallazgo_id)


class _Evidencias:
    """Huella de un documento custodiado: la misma fuente que GET /evidencias/documentos (tabla evidencias_documentos)."""

    def __init__(self, session: AsyncSession, tenant_id: str, user_id: str):
        self.s, self.t, self.u = session, tenant_id, user_id

    async def existe(self, sha256: str) -> Optional[str]:
        huella = sha256.strip().lower()
        documentos = await evidencias_service.listar_documentos(self.s, self.t, self.u)
        return huella if any(d.sha256 == huella for d in documentos) else None


def _puertos(session: AsyncSession, ctx: dict):
    return _Terceros(session, ctx["tenant_id"], ctx["user_id"]), _Hallazgos(session, ctx["tenant_id"], ctx["user_id"])


@router.get("/garantias")
async def listar(ctx: dict = Depends(_consulta), session: AsyncSession = Depends(get_session)):
    terceros, hallazgos = _puertos(session, ctx)
    return {
        "terceros": await terceros_service.listar_terceros_con_hallazgos(terceros, hallazgos),
        # Solo para mostrar u ocultar acciones; cada ruta vuelve a exigir su rol.
        "permisos": {"gestionar": ctx["role"] in ROLES_GESTION, "evaluar": ctx["role"] in ROLES_EVALUACION},
    }


@router.put("/{tercero_id}/garantias")
async def actualizar(
    tercero_id: str,
    payload: terceros_service.GarantiasEntrada,
    ctx: dict = Depends(_gestion),
    session: AsyncSession = Depends(get_session),
):
    terceros, hallazgos = _puertos(session, ctx)
    resultado = await terceros_service.actualizar_garantias(
        tercero_id, payload, terceros, hallazgos, _Evidencias(session, ctx["tenant_id"], ctx["user_id"]), date.today()
    )
    return resultado


@router.post("/evaluar")
async def evaluar(ctx: dict = Depends(_evaluacion), session: AsyncSession = Depends(get_session)):
    terceros, hallazgos = _puertos(session, ctx)
    resultado = await terceros_service.evaluar_terceros(terceros, hallazgos, date.today())
    return resultado
