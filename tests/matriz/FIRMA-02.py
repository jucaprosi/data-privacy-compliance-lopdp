# -*- coding: utf-8 -*-
"""FIRMA-02 · Matriz de permisos: aceptación simple con acuse.

Columnas: (método, ruta, rol, esperado)
  método  : "POST" | "GET"
  ruta    : cadena relativa al prefijo del router
  rol     : nombre del role o "" para pública
  esperado: código HTTP esperado con ese rol

`tests/test_matriz_permisos.py` importa FILAS y ejecuta cada caso.
"""
# ¤¤qa-engineer
# ¤firma-electronica ¤arbitro

FILAS: list[tuple[str, str, str, set[str]]] = [
    # POST /firma/aceptaciones — solo escritura
    ("POST", "/firma/aceptaciones", "implementador", {201, 409, 503}),
    ("POST", "/firma/aceptaciones", "coordinador", {201, 409, 503}),
    ("POST", "/firma/aceptaciones", "admin_organizacion", {201, 409, 503}),
    ("POST", "/firma/aceptaciones", "dpo", {403}),
    ("POST", "/firma/aceptaciones", "responsable_area", {403}),
    # GET /firma/aceptaciones — lectura, cualquier rol
    ("GET", "/firma/aceptaciones", "implementador", {200}),
    ("GET", "/firma/aceptaciones", "coordinador", {200}),
    ("GET", "/firma/aceptaciones", "admin_organizacion", {200}),
    ("GET", "/firma/aceptaciones", "dpo", {200}),
    # POST /firma/verificar — lectura, cualquier rol
    ("POST", "/firma/verificar", "implementador", {200}),
    ("POST", "/firma/verificar", "coordinador", {200}),
    ("POST", "/firma/verificar", "admin_organizacion", {200}),
    # GET /aceptar/{token} — público
    ("GET", "/aceptar/{token}", "", {200, 404, 410}),
    # POST /aceptar/{token} — público
    ("POST", "/aceptar/{token}", "", {200, 404, 410, 422}),
]
