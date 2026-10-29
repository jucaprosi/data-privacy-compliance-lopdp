# ¤rbac-tenant ¤hallazgos ¤arbitro
"""Filas de la matriz de permisos de RM-21 (hallazgos y conversión en tareas).

Contrato: governance/especificaciones/RM-21.md §2. Formato documentado en tests/matriz/__init__.py.
Registra y convierte quien gestiona la hoja de ruta; el `dpo` consulta y no convierte (ORG-13, D-2).
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "listar_hallazgos",
        "GET",
        "/api/v1/roadmaps/hallazgos",
        {"implementador", "coordinador", "dpo", "admin_organizacion"},
    ),
    (
        "registrar_hallazgos_desde_diagnostico",
        "POST",
        "/api/v1/roadmaps/hallazgos/desde-diagnostico",
        {"implementador"},
    ),
    (
        "convertir_hallazgos_en_tareas",
        "POST",
        "/api/v1/roadmaps/{roadmap_id}/hallazgos/convertir",
        {"implementador"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
