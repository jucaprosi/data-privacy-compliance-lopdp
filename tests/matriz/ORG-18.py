# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de ORG-18 (sedes y clientes por encargo).

Contrato: governance/especificaciones/ORG-18.md §2. Formato documentado en tests/matriz/__init__.py.
Leen los cuatro roles de gestión; escriben admin_organizacion, implementador y coordinador (el `dpo` no, D-2).
"""

_LEEN = {"admin_organizacion", "implementador", "coordinador", "dpo"}
_ESCRIBEN = {"admin_organizacion", "implementador", "coordinador"}
_BASE = "/api/v1/organizacion"

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_sedes", "GET", f"{_BASE}/sedes", _LEEN),
    ("crear_sede", "POST", f"{_BASE}/sedes", _ESCRIBEN),
    ("editar_sede", "PUT", f"{_BASE}/sedes/{{sede_id}}", _ESCRIBEN),
    ("retirar_sede", "POST", f"{_BASE}/sedes/{{sede_id}}/retirar", _ESCRIBEN),
    ("listar_clientes_encargo", "GET", f"{_BASE}/clientes", _LEEN),
    ("crear_cliente_encargo", "POST", f"{_BASE}/clientes", _ESCRIBEN),
    ("editar_cliente_encargo", "PUT", f"{_BASE}/clientes/{{cliente_id}}", _ESCRIBEN),
    ("retirar_cliente_encargo", "POST", f"{_BASE}/clientes/{{cliente_id}}/retirar", _ESCRIBEN),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
