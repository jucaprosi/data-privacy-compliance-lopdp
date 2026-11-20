# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de RM-27 (revisión humana y activación de la hoja de ruta).

Contrato: governance/especificaciones/RM-27.md §2. Formato documentado en tests/matriz/__init__.py.
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "consultar_revision_hoja_ruta",
        "GET",
        "/api/v1/roadmaps/{roadmap_id}/revision",
        {
            "responsable_area",
            "coordinador",
            "dpo",
            "implementador",
            "admin_organizacion",
            "auditor",
        },
    ),
    (
        "activar_hoja_ruta",
        "POST",
        "/api/v1/roadmaps/{roadmap_id}/activar",
        {"coordinador", "dpo"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
