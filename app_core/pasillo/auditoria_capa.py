# ¤adpa
"""Capacidades de la sala auditoria_capa para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === CAPA-03 ===
# ¤controles-periodicos Reabre los controles cuya última evidencia venció (para tareas programadas u otras salas).
async def reabrir_controles_por_evidencia_vencida(session, tenant_id: str, user_id: str) -> dict:
    from features.auditoria_capa import auditoria_capa_service

    resultado = await auditoria_capa_service.reabrir_por_evidencia_vencida(session, tenant_id, user_id)
    return resultado.a_dict()
# === fin CAPA-03 ===

# === CAPA-04 ===
# === fin CAPA-04 ===

# === DPO-03 ===
# === fin DPO-03 ===
