# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa
"""Capacidades de la sala formacion para otras salas (pasillo central, ADPA §3).

Cada función importa la compuerta en su cuerpo; aquí no hay lógica de negocio.
Cada tarea escribe solo dentro de su sección reservada.
"""

# === ADPA-09 ===
# Andamiaje del pasillo de esta sala: secciones reservadas abajo.
# === fin ADPA-09 ===

# === DPO-03 ===
# === fin DPO-03 ===

# === FOR-01 ===
async def crear_contenido(session, tenant_id: str, user_id: str, **kwargs):
    from features.formacion import formacion_service

    return await formacion_service.crear_contenido(session, tenant_id, user_id, **kwargs)


async def listar_contenidos(session, tenant_id: str, user_id: str):
    from features.formacion import formacion_service

    return await formacion_service.listar_contenidos(session, tenant_id, user_id)


async def crear_pregunta(session, tenant_id: str, user_id: str, **kwargs):
    from features.formacion import formacion_service

    return await formacion_service.crear_pregunta(session, tenant_id, user_id, **kwargs)


async def listar_preguntas(session, tenant_id: str, user_id: str, contenido_id: str):
    from features.formacion import formacion_service

    return await formacion_service.listar_preguntas(session, tenant_id, user_id, contenido_id)


async def crear_accion(session, tenant_id: str, user_id: str, **kwargs):
    from features.formacion import formacion_service

    return await formacion_service.crear_accion(session, tenant_id, user_id, **kwargs)


async def listar_acciones(session, tenant_id: str, user_id: str):
    from features.formacion import formacion_service

    return await formacion_service.listar_acciones(session, tenant_id, user_id)


async def anadir_participantes(session, tenant_id: str, user_id: str, **kwargs):
    from features.formacion import formacion_service

    return await formacion_service.anadir_participantes(session, tenant_id, user_id, **kwargs)


async def listar_participaciones_accion(session, tenant_id: str, user_id: str, accion_id: str):
    from features.formacion import formacion_service

    return await formacion_service.listar_participaciones_accion(session, tenant_id, user_id, accion_id)


async def obtener_examen_participacion(session, tenant_id: str, user_id: str, **kwargs):
    from features.formacion import formacion_service

    return await formacion_service.obtener_examen_participacion(session, tenant_id, user_id, **kwargs)


async def iniciar_examen_participacion(session, tenant_id: str, user_id: str, **kwargs):
    from features.formacion import formacion_service

    return await formacion_service.iniciar_examen_participacion(session, tenant_id, user_id, **kwargs)


async def calificar_y_terminar_examen(session, tenant_id: str, user_id: str, **kwargs):
    from features.formacion import formacion_service

    return await formacion_service.calificar_y_terminar_examen(session, tenant_id, user_id, **kwargs)


async def calcular_cobertura(session, tenant_id: str, user_id: str):
    from features.formacion import formacion_service

    return await formacion_service.calcular_cobertura(session, tenant_id, user_id)
# === fin FOR-01 ===
