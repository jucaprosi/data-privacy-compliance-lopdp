# ¤rbac-tenant ¤dlp-muestreo ¤arbitro
"""Filas de la matriz de permisos de DLP-01 (descubrimiento DLP muestreado).

Formato documentado en tests/matriz/__init__.py. Escanean quienes pueden ver el dato de origen; el DPO y el
auditor solo leen los escaneos de su organización (tipos y conteos); al RAT vincula solo el coordinador.
"""

_ESCANEO = {"admin_organizacion", "coordinador", "implementador"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("escanear_muestra_dlp", "POST", "/api/v1/dlp-discovery/escanear-muestra", _ESCANEO),
    ("listar_escaneos_dlp", "GET", "/api/v1/dlp-discovery/escaneos", _ESCANEO | {"dpo", "auditor"}),
    ("vincular_escaneo_dlp_rat", "POST", "/api/v1/dlp-discovery/escaneos/{escaneo_id}/vincular-rat", {"coordinador"}),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
