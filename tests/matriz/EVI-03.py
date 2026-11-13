# ¤rbac-tenant ¤evidencias ¤arbitro
"""Filas de la matriz de permisos de EVI-03 (vigencia, visibilidad y paquete de inspección de evidencias).

Formato documentado en tests/matriz/__init__.py. Los roles son los de hoy; el auditor se declara aparte en
tests/matriz/roles/auditor.py (lecturas en True, definir atributos en False).
"""

_LECTORES = {"dpo", "coordinador", "implementador", "admin_organizacion"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_atributos_evidencias", "GET", "/api/v1/evidencias/atributos", _LECTORES),
    ("definir_atributos_evidencia", "PUT", "/api/v1/evidencias/documentos/{documento_id}/atributos", _LECTORES),
    ("descargar_archivo_evidencia", "GET", "/api/v1/evidencias/documentos/{documento_id}/archivo", _LECTORES),
    ("descargar_paquete_inspeccion", "GET", "/api/v1/evidencias/paquete-inspeccion", _LECTORES),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
