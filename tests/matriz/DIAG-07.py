# ¤rbac-tenant ¤diagnostico ¤dpo-independencia ¤arbitro
"""Filas de la matriz de permisos de DIAG-07 (objeciones del DPO a las respuestas del diagnóstico).

Contrato: governance/especificaciones/DIAG-07.md §2. Objeta solo el `dpo`; las consultan quienes responden o
revisan; la grilla de revisión la lee solo el `dpo`. `PUT /diagnostico/respuestas` no usa `require_role`: su
compuerta rechaza al `dpo` y el motor decide por dimensión (tests/test_diagnostico_quien_responde.py).
"""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "objetar_respuesta_diagnostico",
        "POST",
        "/api/v1/diagnostico/objeciones",
        {"dpo"},
    ),
    (
        "listar_objeciones_diagnostico",
        "GET",
        "/api/v1/diagnostico/objeciones",
        {"dpo", "admin_organizacion", "implementador", "coordinador", "responsable_area"},
    ),
    (
        "revisar_diagnostico",
        "GET",
        "/api/v1/diagnostico/revision",
        {"dpo"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
