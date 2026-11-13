# ¤rbac-tenant ¤seguridad-tenant ¤arbitro
"""Filas de la matriz de permisos de SEC-23 (asistente de implementación).

Contrato: governance/tareas/SEC-23.md. Las dos rutas exigen token y membresía activa en la organización
(`obtener_tenant_id_actual`); cualquier rol de la organización las usa, incluido el auditor (ORG-22): las
rutas no llevan require_role y la consulta no cambia datos.
"""

_TODOS = {"implementador", "coordinador", "dpo", "admin_organizacion", "responsable_area", "auditor"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("estado_asistente_implementacion", "GET", "/api/v1/ai_copilot/estado", set(_TODOS)),
    ("consultar_asistente_implementacion", "POST", "/api/v1/ai_copilot/consulta", set(_TODOS)),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
