# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de INC-03 (cierre y reapertura de incidentes).

Cambian el estado los roles que registran incidentes (ROLES_REGISTRO de INC-01); el DPO consulta y no lo
cambia (art. 49, ORG-01). La prueba de rol contra la base está en tests/test_inc03_estado_incidente.py (m5).
"""

_REGISTRAN = {"admin_organizacion", "coordinador", "responsable_area", "implementador"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("cerrar_incidente", "POST", "/api/v1/incidentes/{incidente_id}/cerrar", _REGISTRAN),
    ("reabrir_incidente", "POST", "/api/v1/incidentes/{incidente_id}/reabrir", _REGISTRAN),
]
