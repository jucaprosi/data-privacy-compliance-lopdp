# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""Capacidades de la sala dpo_cockpit para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === BOV-04 ===
# --- INICIO BOV-04 ---
async def _contar_politicas_vencidas_dpo(session, tenant_id: str) -> int | None:
    if session is None or not hasattr(session, "begin_nested"):
        return None
    try:
        from app_core.pasillo import conservacion as pasillo_con

        async with session.begin_nested():
            return len(await pasillo_con.listar_politicas_vencidas(session, tenant_id))
    except Exception:
        return None


async def obtener_resumen_orquestador_10d(session, tenant_id: str, *, incluir_metrica_global: bool = False):
    """Resumen multidimensional de las 10 dimensiones LOPDP y Bóveda Cloud para el DPO Cockpit."""
    from features.boveda_cloud import boveda_cloud_service as svc

    vencidas = await _contar_politicas_vencidas_dpo(session, tenant_id)
    return await svc.obtener_resumen_orquestador_10d(
        session,
        tenant_id,
        incluir_metrica_global=incluir_metrica_global,
        politicas_conservacion_vencidas=vencidas,
    )


async def consultar_orquestador_boveda_dpo(session=None, tenant_id: str = "", *, incluir_metrica_global: bool = False):
    """Vista en modo solo lectura para el DPO con actas SHA-256 y clips bajo Hold Legal."""
    from features.boveda_cloud import boveda_cloud_service as svc

    vencidas = await _contar_politicas_vencidas_dpo(session, tenant_id)
    return await svc.consultar_orquestador_boveda_dpo(
        session,
        tenant_id,
        incluir_metrica_global=incluir_metrica_global,
        politicas_conservacion_vencidas=vencidas,
    )
# --- FIN BOV-04 ---
# === fin BOV-04 ===

# === CAPA-03 ===
# === fin CAPA-03 ===

# === CON-01 ===
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class AlertaRetencion:
    """Alerta de vencimiento de retención que muestra el DPO Cockpit; no lleva datos personales."""

    politica_id: str
    actividad_rat_id: str
    accion_vencimiento: str
    fecha_proxima_revision: date


def alerta_retencion_vencida(politica) -> AlertaRetencion:
    return AlertaRetencion(
        politica_id=politica.id,
        actividad_rat_id=politica.actividad_rat_id,
        accion_vencimiento=politica.accion_vencimiento,
        fecha_proxima_revision=politica.fecha_proxima_revision,
    )
# === fin CON-01 ===

# === DER-01 ===
# === fin DER-01 ===

# === DPO-03 ===
# === fin DPO-03 ===

# === FOR-01 ===
# Capacidades de dpo_cockpit disponibles para la sala Formación.
# === fin FOR-01 ===

# === INC-02 ===
# === fin INC-02 ===

# === MTGE-03 ===
# === fin MTGE-03 ===

# === RAT-07 ===
# === fin RAT-07 ===

# === TER-02 ===
async def contar_cuestionarios_pendientes(session, tenant_id: str) -> int:
    """Número de cuestionarios de encargados en estado 'respondido' pendientes de revisión."""
    from features.terceros import terceros_service

    return await terceros_service.contar_pendientes_revision(session, tenant_id)
# === fin TER-02 ===
