# ¤rbac-tenant ¤riesgos-eipd ¤arbitro
"""Filas de la matriz de permisos de MTGE-03 (EIPD guiada de ocho pasos)."""

_ESCRITURA = {"implementador", "coordinador"}
_LECTORES = {"implementador", "coordinador", "dpo", "admin_organizacion"}  # el auditor, en roles/auditor.py

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("eipd_catalogos", "GET", "/api/v1/eipd/catalogos", _LECTORES),
    ("eipd_crear", "POST", "/api/v1/eipd", _ESCRITURA),
    ("eipd_listar", "GET", "/api/v1/eipd", _LECTORES),
    ("eipd_obtener", "GET", "/api/v1/eipd/{eipd_id}", _LECTORES),
    ("eipd_guardar_paso", "PUT", "/api/v1/eipd/{eipd_id}/paso/{n}", _ESCRITURA),
    ("eipd_cerrar", "POST", "/api/v1/eipd/{eipd_id}/cerrar", {"implementador"}),
    ("eipd_informe", "GET", "/api/v1/eipd/{eipd_id}/informe", _LECTORES),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
