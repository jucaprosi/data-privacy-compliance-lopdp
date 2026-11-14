# ¤adpa
"""Capacidades de la sala transferencias para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === DPO-03 ===
# === fin DPO-03 ===

# === TER-02 ===
# === fin TER-02 ===

# === TER-01 ===
# ¤hallazgos ¤transferencias Contrato y garantía de cada tercero, como diccionarios planos.
async def listar_garantias_terceros(session, tenant_id: str, user_id: str) -> list[dict]:
    from features.transferencias import transferencias_service

    return await transferencias_service.listar_garantias_terceros(session, tenant_id, user_id)


async def obtener_garantias_tercero(session, tenant_id: str, user_id: str, tercero_id: str):
    from features.transferencias import transferencias_service

    return await transferencias_service.obtener_garantias_tercero(session, tenant_id, user_id, tercero_id)


async def actualizar_garantias_tercero(session, tenant_id: str, user_id: str, tercero_id: str, campos: dict):
    from features.transferencias import transferencias_service

    return await transferencias_service.actualizar_garantias_tercero(session, tenant_id, user_id, tercero_id, campos)
# === fin TER-01 ===
