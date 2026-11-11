# ¤rbac-tenant ¤cartera ¤arbitro
"""Filas de la matriz de permisos de ORG-15 (cartera de organizaciones por pertenencia).

Contrato: governance/especificaciones/ORG-15.md §2. Formato documentado en tests/matriz/__init__.py.
La cartera no se controla por rol: la identidad sale del token y solo devuelve las organizaciones de la persona.
"""

FILAS: list[tuple[str, str, str, set[str]]] = []

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {
    ("GET", "/api/v1/organizacion/cartera"): (
        "Cartera de la persona autenticada (ORG-15); no pertenece a un tenant ni filtra por rol: la lista sale de "
        "mis_organizaciones (ORG-13) y cada fila se calcula con el contexto RLS de su organización."
    ),
}
