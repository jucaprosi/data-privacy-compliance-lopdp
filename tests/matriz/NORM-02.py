# ¤rbac-tenant ¤inteligencia-normativa ¤arbitro
"""Filas de la matriz de permisos de NORM-02 (Centro de Vigilancia Normativa).

El corpus es global: lo leen todos los roles de una organización. Disparar el monitoreo y revisar el estado son
solo del operador de la plataforma (`require_operador`, no un `require_role`): el inspector estático de la matriz
no los entiende, así que los cubre `tests/test_norm02_centro_vigilancia.py::test_organizacion_no_homologa`.
"""

_LECTORES = {"dpo", "coordinador", "implementador", "admin_organizacion", "auditor", "responsable_area"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_resoluciones_normativas", "GET", "/api/v1/normativa/resoluciones", _LECTORES),
    ("detalle_resolucion_normativa", "GET", "/api/v1/normativa/resoluciones/{id_resolucion}", _LECTORES),
    ("original_resolucion_normativa", "GET", "/api/v1/normativa/resoluciones/{id_resolucion}/original", _LECTORES),
    ("bitacora_monitoreo_normativo", "GET", "/api/v1/normativa/monitoreo", _LECTORES),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
