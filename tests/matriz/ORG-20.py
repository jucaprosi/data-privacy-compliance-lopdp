# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de ORG-20 (papelera y exportación completa).

Contrato: governance/especificaciones/ORG-20.md §2. Formato documentado en tests/matriz/__init__.py.
La papelera la usan admin_organizacion e implementador; la exportación, solo admin_organizacion.
"""

_PAPELERA = {"admin_organizacion", "implementador"}
_EXPORTA = {"admin_organizacion"}
_BASE = "/api/v1/organizacion"

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_papelera", "GET", f"{_BASE}/papelera", _PAPELERA),
    ("restaurar_de_papelera", "POST", f"{_BASE}/papelera/{{entidad}}/{{registro_id}}/restaurar", _PAPELERA),
    ("solicitar_exportacion", "POST", f"{_BASE}/exportaciones", _EXPORTA),
    ("consultar_exportacion", "GET", f"{_BASE}/exportaciones/{{export_id}}", _EXPORTA),
    ("descargar_exportacion", "GET", f"{_BASE}/exportaciones/{{export_id}}/archivo", _EXPORTA),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
