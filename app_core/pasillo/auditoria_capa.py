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
async def crear_auditoria(session, tenant_id: str, user_id: str, **kwargs):
    from features.auditoria_capa import auditoria_capa_service

    return await auditoria_capa_service.crear_auditoria(session, tenant_id, user_id, **kwargs)


async def listar_auditorias(session, tenant_id: str, user_id: str):
    from features.auditoria_capa import auditoria_capa_service

    return await auditoria_capa_service.listar_auditorias(session, tenant_id, user_id)


async def obtener_auditoria(session, tenant_id: str, user_id: str, auditoria_id: str):
    from features.auditoria_capa import auditoria_capa_service

    return await auditoria_capa_service.obtener_auditoria(session, tenant_id, user_id, auditoria_id)


async def actualizar_fila_auditoria(session, tenant_id: str, user_id: str, **kwargs):
    from features.auditoria_capa import auditoria_capa_service

    return await auditoria_capa_service.actualizar_fila_auditoria(session, tenant_id, user_id, **kwargs)


async def levantar_y_firmar_acta(session, tenant_id: str, user_id: str, **kwargs):
    from features.auditoria_capa import auditoria_capa_service

    return await auditoria_capa_service.levantar_y_firmar_acta(session, tenant_id, user_id, **kwargs)


async def obtener_acta(session, tenant_id: str, user_id: str, **kwargs):
    from features.auditoria_capa import auditoria_capa_service

    return await auditoria_capa_service.obtener_acta(session, tenant_id, user_id, **kwargs)


async def verificar_cierre_hallazgo(session, tenant_id: str, user_id: str, **kwargs):
    from features.auditoria_capa import auditoria_capa_service

    return await auditoria_capa_service.verificar_cierre_hallazgo(session, tenant_id, user_id, **kwargs)


async def listar_cierres_pendientes(session, tenant_id: str, user_id: str):
    from features.auditoria_capa import auditoria_capa_service

    return await auditoria_capa_service.listar_cierres_pendientes(session, tenant_id, user_id)
# === fin CAPA-04 ===

# === DPO-03 ===
# === fin DPO-03 ===
