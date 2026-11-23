# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de BOV-02b (objetos y orquestador de la bóveda cloud).

Formato documentado en tests/matriz/__init__.py. Las URLs firmadas son de `ROLES_OBJETOS` (BOV-02) y la
consulta del orquestador de las 10 dimensiones es de `ROLES_CONSULTA` (BOV-04).
"""

_ROLES_OBJETOS = {"admin_organizacion", "dpo", "coordinador", "implementador", "responsable_area"}
_ROLES_CONSULTA = {"admin_organizacion", "dpo", "coordinador"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "solicitar_url_subida_boveda",
        "POST",
        "/api/v1/boveda-cloud/objetos/url-subida-firmada",
        _ROLES_OBJETOS,
    ),
    (
        "solicitar_url_descarga_boveda",
        "POST",
        "/api/v1/boveda-cloud/objetos/{objeto_id}/url-descarga-firmada",
        _ROLES_OBJETOS,
    ),
    (
        "consultar_orquestador_10d_boveda",
        "GET",
        "/api/v1/boveda-cloud/orquestador-10d",
        _ROLES_CONSULTA,
    ),
]
