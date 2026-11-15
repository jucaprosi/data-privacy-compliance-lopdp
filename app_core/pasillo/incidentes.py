# ¤adpa
"""Capacidades de la sala incidentes para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-06 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-06 ===

# === CCTV-02 ===
async def existe_incidente(session, tenant_id: str, incidente_id: str) -> bool:
    """Verifica si el incidente existe para el tenant (CCTV-02)."""
    from sqlalchemy import text

    try:
        fila = (await session.execute(
            text("SELECT 1 FROM incidentes WHERE id = :i AND tenant_id = :t LIMIT 1"),
            {"i": str(incidente_id), "t": tenant_id},
        )).scalar_one_or_none()
        return fila is not None
    except Exception:
        return False
# === fin CCTV-02 ===

# === DPO-03 ===
# === fin DPO-03 ===

# === INC-02 ===
# ¤incidentes Notificaciones marcadas por un implementador, para la bandeja del DPO.
async def notificaciones_por_implementador(session, tenant_id, user_id):
    from features.incidentes import incidentes_service

    return await incidentes_service.notificaciones_por_implementador(session, tenant_id, user_id)
# === fin INC-02 ===

# === ORG-24 ===

async def contar_vulneraciones_para_ficha(session, tenant_id, user_id):
    from features.incidentes import incidentes_service

    return await incidentes_service.contar_vulneraciones_para_ficha(session, tenant_id)
# === fin ORG-24 ===

# === INC-03 ===

async def contar_abiertos(session, tenant_id):
    from features.incidentes import incidentes_service

    return await incidentes_service.contar_abiertos(session, tenant_id)
# === fin INC-03 ===
