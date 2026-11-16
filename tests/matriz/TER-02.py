# ¤rbac-tenant ¤seguridad ¤arbitro
"""Filas de la matriz de permisos de TER-02 (cuestionario de garantías del encargado).

Contrato: governance/especificaciones/TER-02.md §2. Formato documentado en tests/matriz/__init__.py.
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "crear_enlace_cuestionario",
        "POST",
        "/api/v1/terceros/{id}/cuestionarios",
        {"implementador", "coordinador"},
    ),
    (
        "listar_cuestionarios",
        "GET",
        "/api/v1/terceros/{id}/cuestionarios",
        {"implementador", "coordinador", "dpo", "admin_organizacion", "auditor"},
    ),
    (
        "revisar_cuestionario",
        "POST",
        "/api/v1/terceros/cuestionarios/{id}/revision",
        {"implementador", "coordinador"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
