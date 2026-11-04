# -*- coding: utf-8 -*-
# ¤adpa ¤rbac-tenant ¤arbitro
"""BIB-401 · Matriz de permisos: plantillas de la cuenta profesional."""

FILAS: list[tuple[str, str, str, set[str]]] = [
    (
        "listar_plantillas_cuenta",
        "GET",
        "/api/v1/biblioteca/plantillas-cuenta",
        {"implementador"},
    ),
    (
        "crear_plantilla_cuenta",
        "POST",
        "/api/v1/biblioteca/plantillas-cuenta",
        {"implementador"},
    ),
    (
        "obtener_plantilla_cuenta",
        "GET",
        "/api/v1/biblioteca/plantillas-cuenta/{id}",
        {"implementador"},
    ),
    (
        "actualizar_plantilla_cuenta",
        "PUT",
        "/api/v1/biblioteca/plantillas-cuenta/{id}",
        {"implementador"},
    ),
    (
        "diff_plantilla_cuenta",
        "GET",
        "/api/v1/biblioteca/plantillas-cuenta/{id}/diff",
        {"implementador"},
    ),
    (
        "aplicar_maestra_plantilla_cuenta",
        "POST",
        "/api/v1/biblioteca/plantillas-cuenta/{id}/aplicar-maestra",
        {"implementador"},
    ),
]

FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
