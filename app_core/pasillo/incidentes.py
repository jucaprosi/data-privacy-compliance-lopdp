# ¤adpa
"""Capacidades de la sala incidentes para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === CCTV-02 ===
# === fin CCTV-02 ===

# === DPO-03 ===
# === fin DPO-03 ===

# === INC-02 ===
# === fin INC-02 ===

# === ORG-24 ===

async def contar_vulneraciones_para_ficha(session, tenant_id, user_id):
    from features.incidentes import incidentes_service

    return await incidentes_service.contar_vulneraciones_para_ficha(session, tenant_id)
# === fin ORG-24 ===

# === INC-03 ===
# === fin INC-03 ===
