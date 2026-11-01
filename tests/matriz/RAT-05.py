# ¤rbac-tenant ¤rat ¤arbitro
"""Filas de la matriz de permisos de RAT-05 (validaciones y versiones de una ficha).

Contrato: governance/especificaciones/RAT-05.md §2. Formato documentado en tests/matriz/__init__.py.
Son consultas: las producen los guardados de la ficha, que siguen siendo del `coordinador` (RAT-01).
"""

_LECTORES = {"implementador", "coordinador", "dpo", "admin_organizacion", "responsable_area"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("consultar_validaciones_rat", "GET", "/api/v1/rat/{rat_id}/validaciones", _LECTORES),
    ("listar_versiones_rat", "GET", "/api/v1/rat/{rat_id}/versiones", _LECTORES),
    ("leer_version_rat", "GET", "/api/v1/rat/{rat_id}/versiones/{numero}", _LECTORES),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
