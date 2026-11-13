# ¤rbac-tenant ¤roadmap ¤arbitro
"""Filas de la matriz de permisos de RM-25a (primera validación de la evidencia). Formato en tests/matriz/__init__.py.

La registra solo el `coordinador`; la validación final sigue siendo el PATCH de roadmaps.py.
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "primera_validacion_evidencia",
        "POST",
        "/api/v1/roadmaps/tasks/{task_id}/evidence/{evidence_id}/primera-validacion",
        {"coordinador"},
    ),
]
