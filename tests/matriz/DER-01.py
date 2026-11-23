# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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
