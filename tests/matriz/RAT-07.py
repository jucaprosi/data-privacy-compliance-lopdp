# ¤rbac-tenant ¤rat ¤arbitro
"""Filas de la matriz de permisos de RAT-07 (colectivos y consentimientos agregados).

Contrato: governance/especificaciones/RAT-07.md §2. Formato documentado en tests/matriz/__init__.py.
Escriben implementador, coordinador y admin_organizacion; el DPO y el responsable de área solo leen.
"""

_ESCRIBEN = {"implementador", "coordinador", "admin_organizacion"}
_LECTORES = _ESCRIBEN | {"dpo", "responsable_area"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("listar_colectivos_rat", "GET", "/api/v1/rat/{rat_id}/colectivos", _LECTORES),
    ("crear_colectivo_rat", "POST", "/api/v1/rat/{rat_id}/colectivos", _ESCRIBEN),
    ("editar_colectivo_rat", "PUT", "/api/v1/rat/colectivos/{colectivo_id}", _ESCRIBEN),
    ("registrar_consentimiento_rat", "POST", "/api/v1/rat/colectivos/{colectivo_id}/consentimientos", _ESCRIBEN),
    ("consultar_consentimientos_rat", "GET", "/api/v1/rat/colectivos/{colectivo_id}/consentimientos", _LECTORES),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
