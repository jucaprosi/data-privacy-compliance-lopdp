# -*- coding: utf-8 -*-
"""FIRMA-02 · Matriz de permisos: aceptación simple con acuse.

Formato de FILAS: (id_accion, metodo, ruta_con_prefijo_api_v1, conjunto_roles_permitidos).
Rutas públicas sin autenticación declaradas en FUERA_DE_MATRIZ.

`tests/test_matriz_permisos.py` importa FILAS y ejecuta cada caso.
"""
# ¤¤qa-engineer
# ¤firma-electronica ¤arbitro

FILAS: list[tuple[str, str, str, set[str]]] = [
    # POST /firma/aceptaciones — solo escritura, requiere rol de gestión
    (
        "crear_enlaces_aceptacion",
        "POST",
        "/api/v1/firma/aceptaciones",
        {"implementador", "coordinador", "admin_organizacion"},
    ),
    # GET /firma/aceptaciones — lectura, cualquier rol autenticado
    (
        "listar_aceptaciones",
        "GET",
        "/api/v1/firma/aceptaciones",
        {"responsable_area", "coordinador", "dpo", "implementador", "admin_organizacion"},
    ),
    # POST /firma/verificar — verificación de hash, cualquier rol autenticado
    (
        "verificar_hash_documento",
        "POST",
        "/api/v1/firma/verificar",
        {"responsable_area", "coordinador", "dpo", "implementador", "admin_organizacion"},
    ),
]

# Las rutas públicas /api/v1/aceptar/{token} no caen bajo los prefijos monitoreados por la
# matriz de permisos (/api/v1/roadmaps, /api/v1/organizacion, /api/v1/areas), por lo que no
# se declaran aquí (test_cobertura_exhaustiva_rutas_api no las inspeccionaría de todos modos).
FUERA_DE_MATRIZ: dict[tuple[str, str], str] = {}
