# ¤rbac-tenant ¤diagnostico ¤dpo-independencia ¤arbitro
"""Filas de la matriz de permisos de DIAG-07 (objeciones del DPO a las respuestas del diagnóstico).

Contrato: governance/especificaciones/DIAG-07.md §2. Objeta solo el `dpo`; las consultan quienes responden o
revisan. Las filas de `PUT /diagnostico/respuestas` llegan con el cambio de rol del router (ficha DIAG-07).
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
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
