# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de ORG-16 (alta de la organización en siete pasos).

Contrato: governance/especificaciones/ORG-16.md §2. Formato documentado en tests/matriz/__init__.py.
El alta la hacen `admin_organizacion` e `implementador`; el `dpo` no escribe (D-2).
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "ver_estado_alta",
        "GET",
        "/api/v1/organizacion/alta",
        {"admin_organizacion", "implementador", "coordinador", "dpo"},
    ),
    (
        "ver_sugerencias_alta",
        "GET",
        "/api/v1/organizacion/alta/sugerencias",
        {"admin_organizacion", "implementador"},
    ),
    (
        "guardar_paso_alta",
        "POST",
        "/api/v1/organizacion/alta/paso/{paso_id}",
        {"admin_organizacion", "implementador"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
