# ¤adpa
"""Capacidades de la sala regulacion_rag para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === DIAG-04 ===
# === fin DIAG-04 ===

# === DIAG-07 ===
# === fin DIAG-07 ===

# === NORM-03 ===
# === fin NORM-03 ===

# === REG-01 ===
# ¤paquete-normativo
async def parametros_normativos_publicados(session, codigo: str) -> list:
    """Parámetros del paquete publicado (R4): las salas leen plazo y unidad de aquí, no de una constante."""
    from features.regulacion_rag import regulacion_rag_service

    return await regulacion_rag_service.parametros_publicados(session, codigo)
# === fin REG-01 ===

# === VTX-01 ===
# === fin VTX-01 ===
