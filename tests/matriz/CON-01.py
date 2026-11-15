# ¤rbac-tenant ¤conservacion ¤arbitro
"""Filas de la matriz de permisos de CON-01 (políticas de conservación).

Formato documentado en tests/matriz/__init__.py. Crea y registra la ejecución la persona administradora o el
implementador; el DPO, el coordinador y el auditor solo leen (decisión del CTO, 2026-11-15).
"""

PREFIJOS: tuple[str, ...] = ("/api/v1/conservacion",)

_EJECUTAN = {"admin_organizacion", "implementador"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_politicas_conservacion", "GET", "/api/v1/conservacion/politicas", _EJECUTAN | {"dpo", "coordinador", "auditor"}),
    ("crear_politica_conservacion", "POST", "/api/v1/conservacion/politicas", _EJECUTAN),
    ("ejecutar_politica_conservacion", "POST", "/api/v1/conservacion/politicas/{politica_id}/ejecutar", _EJECUTAN),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
