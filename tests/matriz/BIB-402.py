# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de BIB-402 (vínculos de un documento).

Contrato: governance/especificaciones/BIB-402.md §2. Escriben `implementador` y `coordinador`; leen todos.
"""

_TODOS = {"implementador", "coordinador", "dpo", "admin_organizacion", "responsable_area"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_vinculos_documento", "GET", "/api/v1/biblioteca/documentos/{documento_id}/vinculos", _TODOS),
    ("reemplazar_vinculos_documento", "PUT", "/api/v1/biblioteca/documentos/{documento_id}/vinculos",
     {"implementador", "coordinador"}),
    ("listar_documentos_de_tratamiento", "GET", "/api/v1/biblioteca/tratamientos/{tratamiento_id}/documentos", _TODOS),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
