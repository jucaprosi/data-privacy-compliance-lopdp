# ¤rbac-tenant ¤rat ¤arbitro
"""Filas de la matriz de permisos de RAT-06 (exportación del RAT).

Contrato: governance/especificaciones/RAT-06.md §2. Formato documentado en tests/matriz/__init__.py.
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("exportar_rat", "GET", "/api/v1/rat/exportar", {"implementador", "coordinador", "dpo", "admin_organizacion"}),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
