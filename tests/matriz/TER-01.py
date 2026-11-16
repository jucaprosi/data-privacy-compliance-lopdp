# ¤rbac-tenant ¤hallazgos ¤arbitro
"""Filas de la matriz de permisos de TER-01 (contrato y garantía de terceros).

Contrato: governance/especificaciones/TER-01.md §2. Formato documentado en tests/matriz/__init__.py.
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "listar_garantias_terceros",
        "GET",
        "/api/v1/terceros/garantias",
        {"implementador", "coordinador", "dpo", "admin_organizacion", "auditor"},
    ),
    (
        "actualizar_garantias_tercero",
        "PUT",
        "/api/v1/terceros/{tercero_id}/garantias",
        {"implementador", "coordinador"},
    ),
    (
        "evaluar_terceros",
        "POST",
        "/api/v1/terceros/evaluar",
        {"implementador"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
