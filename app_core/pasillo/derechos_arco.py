# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""Capacidades de la sala derechos_arco para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === CCTV-02 ===
async def existe_solicitud(session, tenant_id: str, solicitud_id: str) -> bool:
    """Verifica si la solicitud de derecho ARCOP+ existe para el tenant (CCTV-02)."""
    from sqlalchemy import text

    try:
        fila = (await session.execute(
            text("SELECT 1 FROM derechos_arco_solicitudes WHERE id::text = :s AND tenant_id_texto = :t LIMIT 1"),
            {"s": str(solicitud_id), "t": tenant_id},
        )).scalar_one_or_none()
        return fila is not None
    except Exception:
        return False
# === fin CCTV-02 ===

# === DER-01 ===
# === fin DER-01 ===

# === DPO-03 ===
# === fin DPO-03 ===

# === FIRMA-02 ===
# === fin FIRMA-02 ===

# === ORG-24 ===

async def contar_solicitudes_para_ficha(session, tenant_id, user_id):
    from features.derechos_arco import derechos_arco_service

    return await derechos_arco_service.contar_solicitudes_para_ficha(session, tenant_id)
# === fin ORG-24 ===
