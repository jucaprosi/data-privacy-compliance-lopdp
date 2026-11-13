# ¤rbac-tenant ¤paquete-normativo ¤arbitro
"""Filas de la matriz de permisos de REG-01 (paquete normativo como dato).

Formato documentado en tests/matriz/__init__.py. La lectura la tiene cualquier usuario autenticado, sea
cual sea su rol en la organización. La escritura no depende de un rol de organización sino de ser operador
de la plataforma (ORG-09): ningún rol la concede, y lo prueba tests/test_paquetes_normativos.py
(un usuario de organización que escribe recibe 403 NO_ES_OPERADOR).
"""

_TODOS = {
    "responsable_area",
    "coordinador",
    "dpo",
    "implementador",
    "admin_organizacion",
    "auditor",
}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_paquetes_normativos", "GET", "/api/v1/plataforma/paquetes", _TODOS),
    ("detalle_paquete_normativo", "GET", "/api/v1/plataforma/paquetes/{paquete_id}", _TODOS),
    ("parametros_paquete_publicado", "GET", "/api/v1/plataforma/paquetes/{codigo}/parametros", _TODOS),
]

# Las escrituras (operador de la plataforma, no rol de organización) quedan fuera de los prefijos de la
# matriz; su frontera la prueba tests/test_paquetes_normativos.py.
FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
