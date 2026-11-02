# ¤rbac-tenant ¤roadmap ¤arbitro
"""Filas de la matriz de permisos de RM-23 (recordatorios y cierre de hallazgos).

Contrato: governance/especificaciones/RM-23.md §2. Formato documentado en tests/matriz/__init__.py.
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("ejecutar_recordatorios", "POST", "/api/v1/roadmaps/recordatorios/ejecutar", {"implementador"}),
]
