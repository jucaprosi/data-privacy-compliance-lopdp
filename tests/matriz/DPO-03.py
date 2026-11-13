# ¤rbac-tenant ¤dpo-cockpit ¤arbitro
"""Filas de la matriz de permisos de DPO-03 (consultas de la organización al DPO).

Formato documentado en tests/matriz/__init__.py. Listar, abrir y escribir en el hilo están abiertos a todos
los roles con membresía; la visibilidad (R2) y «autor o dpo» las impone el motor, no la dependencia de roles,
y las prueba tests/test_dpo_consultas.py. Cerrar es exclusivo del dpo (INV_LOPDP_DPO_INDEPENDENCE).
"""

_TODOS = {"dpo", "admin_organizacion", "coordinador", "implementador", "responsable_area", "auditor"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_consultas_dpo", "GET", "/api/v1/dpo/consultas", _TODOS),
    ("crear_consulta_dpo", "POST", "/api/v1/dpo/consultas", _TODOS),
    ("mensaje_consulta_dpo", "POST", "/api/v1/dpo/consultas/{consulta_id}/mensajes", _TODOS),
    ("cerrar_consulta_dpo", "POST", "/api/v1/dpo/consultas/{consulta_id}/cerrar", {"dpo"}),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
