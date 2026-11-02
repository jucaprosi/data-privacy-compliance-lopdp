# ¤rbac-tenant ¤controles-periodicos ¤arbitro
"""Filas de la matriz de permisos de CAPA-02 (controles periódicos).

Contrato: governance/especificaciones/CAPA-02.md §2. Formato documentado en tests/matriz/__init__.py.
En `verificaciones` la matriz comprueba el paso por rol: el `dpo` nunca; que el control sea del usuario lo
exige el motor y lo prueba tests/test_controles_periodicos.py.
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "listar_controles_periodicos",
        "GET",
        "/api/v1/auditoria-capa/controles",
        {"implementador", "coordinador", "dpo", "admin_organizacion", "responsable_area"},
    ),
    (
        "crear_control_periodico",
        "POST",
        "/api/v1/auditoria-capa/controles",
        {"implementador", "coordinador"},
    ),
    (
        "verificar_control_periodico",
        "POST",
        "/api/v1/auditoria-capa/controles/{control_id}/verificaciones",
        {"implementador", "coordinador", "admin_organizacion", "responsable_area"},
    ),
    (
        "retirar_control_periodico",
        "POST",
        "/api/v1/auditoria-capa/controles/{control_id}/retirar",
        {"implementador", "coordinador"},
    ),
    (
        "vencer_controles_periodicos",
        "POST",
        "/api/v1/auditoria-capa/controles/vencer",
        {"implementador"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
