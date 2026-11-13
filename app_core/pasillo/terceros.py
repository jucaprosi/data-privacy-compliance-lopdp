# ¤adpa
"""Capacidades de la sala terceros para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === DPO-03 ===
# === fin DPO-03 ===

# === TER-01 ===
# ¤hallazgos Reglas puras de contrato y garantía para quien muestre el estado de un tercero.
def hallazgos_de_tercero(tercero: dict, hoy) -> list[str]:
    """origen_ref de las reglas que el tercero incumple hoy (R1 y R2 de TER-01), sin tocar la base."""
    from features.terceros import terceros_service
    from features.terceros.services import garantias_engine

    t = terceros_service.tercero_desde_fila(tercero)
    return [c.origen_ref for c, se_cumple in garantias_engine.condiciones(t, hoy) if se_cumple]
# === fin TER-01 ===

# === TER-02 ===
# === fin TER-02 ===
