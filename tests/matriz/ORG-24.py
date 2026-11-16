# ¤rbac-tenant ¤arbitro
"""Fila de la matriz de permisos de ORG-24 (ficha de la organización activa).

Cualquier rol vigente en el tenant del contexto la lee; lo que cambia con el rol son los nombres del DPO y del
implementador, que `nombres_visibles` oculta (prueba en tests/test_org24_ficha_organizacion.py).
"""

_TODOS = {"implementador", "coordinador", "dpo", "admin_organizacion", "responsable_area"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("ficha_organizacion", "GET", "/api/v1/organizacion/ficha", _TODOS),
]
