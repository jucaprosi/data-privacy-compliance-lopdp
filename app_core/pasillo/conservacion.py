# ¤adpa
"""Capacidades de la sala conservacion para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-09 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-09 ===

# === CON-01 ===
from dataclasses import dataclass
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass(frozen=True)
class PoliticaVencida:
    id: str
    actividad_rat_id: str
    accion_vencimiento: str
    fecha_proxima_revision: date


async def listar_politicas_vencidas(session: AsyncSession, tenant_id: str) -> list[PoliticaVencida]:
    """Políticas de retención ACTIVAS cuya fecha de revisión ya llegó (R3, lectura para el DPO Cockpit)."""
    from features.conservacion import conservacion_service

    return [
        PoliticaVencida(p.id, p.actividad_rat_id, p.accion_vencimiento, p.fecha_proxima_revision)
        for p in await conservacion_service.politicas_vencidas(session, tenant_id)
    ]
# === fin CON-01 ===

# === DPO-03 ===
# === fin DPO-03 ===

# === GOVW-01 ===
# === fin GOVW-01 ===

# --- INICIO GOVW-01 ---
async def registrar_purga_satelite_go(resultado_purga: dict, firma: str):
    from app_core.pasillo import go_vault_worker as gvw
    return await gvw.registrar_acta_purga(resultado_purga, firma)
# --- FIN GOVW-01 ---
