# ¤rbac-tenant ¤inteligencia-normativa ¤arbitro
"""Filas de la matriz de permisos de NORM-02 (Centro de Vigilancia Normativa).

El corpus es global: lo leen todos los roles de una organización; disparar el monitoreo y revisar el estado son
solo del operador de la plataforma (ningún rol de organización).
"""

_LECTORES = {"dpo", "coordinador", "implementador", "admin_organizacion", "auditor"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_resoluciones_normativas", "GET", "/api/v1/normativa/resoluciones", _LECTORES),
    ("detalle_resolucion_normativa", "GET", "/api/v1/normativa/resoluciones/{id_resolucion}", _LECTORES),
    ("original_resolucion_normativa", "GET", "/api/v1/normativa/resoluciones/{id_resolucion}/original", _LECTORES),
    ("bitacora_monitoreo_normativo", "GET", "/api/v1/normativa/monitoreo", _LECTORES),
    ("disparar_monitoreo_normativo", "POST", "/api/v1/normativa/monitoreo", set()),
    ("revisar_resolucion_normativa", "POST", "/api/v1/normativa/resoluciones/{id_resolucion}/revision", set()),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
