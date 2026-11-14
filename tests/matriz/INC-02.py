# ¤rbac-tenant ¤incidentes ¤arbitro
"""Filas de la matriz de permisos de INC-02 (asistente de vulneración e informes).

Formato documentado en tests/matriz/__init__.py. La dependencia de roles fija estas filas; dentro de la
escritura, el motor separa por sección (implementador y coordinador 1 a 6; implementador y dpo 7 y 8).
"""

_LECTORES = {"implementador", "coordinador", "dpo", "admin_organizacion"}
_ESCRITORES = {"implementador", "coordinador", "dpo"}
_INFORMES = {"implementador", "dpo"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("resumen_asistentes_incidentes", "GET", "/api/v1/incidentes/asistentes", _LECTORES),
    ("leer_asistente_incidente", "GET", "/api/v1/incidentes/{incidente_id}/asistente", _LECTORES),
    ("guardar_seccion_asistente", "PUT", "/api/v1/incidentes/{incidente_id}/asistente/{seccion}", _ESCRITORES),
    ("generar_informe_incidente", "POST", "/api/v1/incidentes/{incidente_id}/informes", _INFORMES),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
