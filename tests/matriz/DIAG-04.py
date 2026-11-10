# ¤rbac-tenant ¤diagnostico-asignacion ¤arbitro
"""Filas de la matriz de permisos de DIAG-04 (asignación de dominios del assessment).

Contrato: governance/especificaciones/DIAG-04.md §2. Asigna `admin_organizacion`; implementador, coordinador y
`dpo` consultan (D-2) y `responsable_area` ve las asignaciones sin su historial.
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "listar_asignaciones_dominios",
        "GET",
        "/api/v1/diagnostico/asignaciones",
        {"implementador", "coordinador", "dpo", "admin_organizacion", "responsable_area"},
    ),
    (
        "asignar_dominio_diagnostico",
        "PUT",
        "/api/v1/diagnostico/asignaciones/{dimension}",
        {"admin_organizacion"},
    ),
    (
        "historial_asignaciones_dominios",
        "GET",
        "/api/v1/diagnostico/asignaciones/historial",
        {"implementador", "coordinador", "dpo"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
