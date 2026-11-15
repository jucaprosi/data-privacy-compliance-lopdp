# -*- coding: utf-8 -*-
# ¤adpa ¤rbac-tenant ¤arbitro
"""DER-01 · Matriz de permisos: verificación de identidad, modelos y respuesta de solicitudes de titulares."""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "verificar_identidad_solicitud",
        "POST",
        "/api/v1/derechos/solicitudes/{solicitud_id}/verificar-identidad",
        {"coordinador", "responsable_area", "admin_organizacion", "implementador"},
    ),
    (
        "responder_solicitud",
        "POST",
        "/api/v1/derechos/solicitudes/{solicitud_id}/respuesta",
        {"admin_organizacion", "implementador"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
