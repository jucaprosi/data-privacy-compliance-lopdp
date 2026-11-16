# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de ORG-17 (inventario de activos, soportes y personas).

Contrato: governance/tareas/ORG-17.md. Formato documentado en tests/matriz/__init__.py.
Leen los cuatro roles de gestión; escriben admin_organizacion, implementador y coordinador (el `dpo` no, D-2).
"""

_LEEN = {"admin_organizacion", "implementador", "coordinador", "dpo"}
_ESCRIBEN = {"admin_organizacion", "implementador", "coordinador"}
_BASE = "/api/v1/organizacion/inventario"

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_activos_inventario", "GET", f"{_BASE}/activos", _LEEN),
    ("crear_activo_inventario", "POST", f"{_BASE}/activos", _ESCRIBEN),
    ("editar_activo_inventario", "PATCH", f"{_BASE}/activos/{{activo_id}}", _ESCRIBEN),
    ("vincular_tratamientos_inventario", "PUT", f"{_BASE}/activos/{{activo_id}}/tratamientos", _ESCRIBEN),
    ("listar_tratamientos_inventario", "GET", f"{_BASE}/tratamientos", _LEEN),
    ("listar_personas_inventario", "GET", f"{_BASE}/personas", _LEEN),
    ("crear_persona_inventario", "POST", f"{_BASE}/personas", _ESCRIBEN),
    ("editar_persona_inventario", "PATCH", f"{_BASE}/personas/{{persona_id}}", _ESCRIBEN),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
