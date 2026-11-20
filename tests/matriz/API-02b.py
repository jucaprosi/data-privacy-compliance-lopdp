# ¤rbac-tenant ¤arbitro
"""Filas de la matriz de permisos de API-02b (webhooks firmados HMAC-SHA256).

Contrato: governance/especificaciones/API-02b.md.
Solo `admin_organizacion` administra suscripciones y pruebas de webhooks.
El rol `auditor` no tiene permisos sobre los webhooks (espera 403).
"""

PREFIJOS = ("/api/v1/integraciones/webhooks",)

_SOLO_ADMIN = {"admin_organizacion"}

FILAS: list[tuple[str, str, str, set[str]]] = [
    ("crear_webhook_integracion", "POST", "/api/v1/integraciones/webhooks", _SOLO_ADMIN),
    ("listar_webhooks_integracion", "GET", "/api/v1/integraciones/webhooks", _SOLO_ADMIN),
    ("rotar_secreto_webhook", "POST", "/api/v1/integraciones/webhooks/{id}/rotar-secreto", _SOLO_ADMIN),
    ("desactivar_webhook", "POST", "/api/v1/integraciones/webhooks/{id}/desactivar", _SOLO_ADMIN),
    ("probar_webhook", "POST", "/api/v1/integraciones/webhooks/{id}/probar", _SOLO_ADMIN),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
