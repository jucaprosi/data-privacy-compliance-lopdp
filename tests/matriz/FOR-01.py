# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de FOR-01 (Formación y Capacitación).

Contrato: governance/especificaciones/FOR-01.md §2.
"""

_ESCRIBEN = {"implementador", "coordinador", "admin_organizacion"}
_LEEN = _ESCRIBEN | {"auditor", "dpo", "responsable_area"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("crear_contenido_formacion", "POST", "/api/v1/formacion/contenidos", _ESCRIBEN),
    ("listar_contenidos_formacion", "GET", "/api/v1/formacion/contenidos", _LEEN),
    ("crear_pregunta_formacion", "POST", "/api/v1/formacion/contenidos/{id}/preguntas", _ESCRIBEN),
    ("listar_preguntas_formacion", "GET", "/api/v1/formacion/contenidos/{id}/preguntas", _ESCRIBEN),
    ("crear_accion_formacion", "POST", "/api/v1/formacion/acciones", _ESCRIBEN),
    ("listar_acciones_formacion", "GET", "/api/v1/formacion/acciones", _LEEN),
    ("anadir_participantes_formacion", "POST", "/api/v1/formacion/acciones/{id}/participantes", _ESCRIBEN),
    ("listar_participantes_formacion", "GET", "/api/v1/formacion/acciones/{id}/participantes", _LEEN),
    ("obtener_cobertura_formacion", "GET", "/api/v1/formacion/cobertura", _LEEN),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
