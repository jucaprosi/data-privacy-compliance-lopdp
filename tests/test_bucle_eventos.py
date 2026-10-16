"""Pruebas unitarias para app_core/bucle_eventos.py y su invocación en main.py.
`¤arbitro` `¤seguridad`

Verifica:
1. Simulación de win32: comprueba que la política WindowsSelectorEventLoopPolicy
   queda fijada de manera efectiva.
2. Idempotencia: invocar la función múltiples veces es seguro y no genera errores ni efectos secundarios.
3. Simulación de otras plataformas (Linux/Darwin): comprueba que la política NO se modifica.
4. Punto de entrada único: comprueba que main.py importa e invoca la función antes de crear la app FastAPI.
"""
import ast
import asyncio
import os
import sys
from unittest.mock import MagicMock, patch

import pytest

from app_core.bucle_eventos import configurar_bucle_eventos

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_configurar_bucle_eventos_simula_win32():
    """Simula plataforma win32 y comprueba que se fija WindowsSelectorEventLoopPolicy."""
    class DummySelectorPolicy:
        pass

    with patch.object(asyncio, "WindowsSelectorEventLoopPolicy", DummySelectorPolicy, create=True), \
         patch.object(asyncio, "get_event_loop_policy", return_value=object()) as mock_get_policy, \
         patch.object(asyncio, "set_event_loop_policy") as mock_set_policy:

        cambiado = configurar_bucle_eventos(plataforma="win32")
        assert cambiado is True
        assert mock_set_policy.call_count == 1
        arg = mock_set_policy.call_args[0][0]
        assert isinstance(arg, DummySelectorPolicy)


def test_configurar_bucle_eventos_idempotente():
    """Si la política ya es instancia de WindowsSelectorEventLoopPolicy, no la reasigna."""
    class DummySelectorPolicy:
        pass

    dummy_instance = DummySelectorPolicy()

    with patch.object(asyncio, "WindowsSelectorEventLoopPolicy", DummySelectorPolicy, create=True), \
         patch.object(asyncio, "get_event_loop_policy", return_value=dummy_instance), \
         patch.object(asyncio, "set_event_loop_policy") as mock_set_policy:

        cambiado = configurar_bucle_eventos(plataforma="win32")
        assert cambiado is False
        mock_set_policy.assert_not_called()


def test_configurar_bucle_eventos_otra_plataforma():
    """En plataformas no win32 (linux, darwin), no hace nada ni altera políticas."""
    for plat in ["linux", "darwin", "freebsd"]:
        with patch.object(asyncio, "set_event_loop_policy") as mock_set_policy:
            cambiado = configurar_bucle_eventos(plataforma=plat)
            assert cambiado is False
            mock_set_policy.assert_not_called()


def test_main_invoca_configurar_bucle_eventos_antes_de_app():
    """Analiza sintácticamente main.py para asegurar que configurar_bucle_eventos()
    se llama antes de la instanciación de app = FastAPI(...)."""
    main_path = os.path.join(RAIZ, "main.py")
    with open(main_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=main_path)

    llamada_lineno = None
    app_lineno = None

    for node in tree.body:
        # Detectar llamada a configurar_bucle_eventos()
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            func = node.value.func
            name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
            if name == "configurar_bucle_eventos":
                llamada_lineno = node.lineno
        # Detectar asignación app = FastAPI(...)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "app":
                    app_lineno = node.lineno

    assert llamada_lineno is not None, "configurar_bucle_eventos() no fue invocado en el cuerpo principal de main.py"
    assert app_lineno is not None, "app = FastAPI(...) no encontrado en main.py"
    assert llamada_lineno < app_lineno, (
        f"configurar_bucle_eventos() (línea {llamada_lineno}) debe invocarse antes de app = FastAPI(...) (línea {app_lineno})"
    )


def test_unico_punto_de_entrada_que_invoca_configurar_bucle():
    """Comprueba que main.py es el único punto de entrada de la aplicación que invoca configurar_bucle_eventos."""
    invocadores = []
    carpetas_analizar = ["app_core", "api", "features"]

    for carpeta in carpetas_analizar:
        ruta_carpeta = os.path.join(RAIZ, carpeta)
        for root, _, files in os.walk(ruta_carpeta):
            for file in files:
                if not file.endswith(".py") or file == "bucle_eventos.py":
                    continue
                full_path = os.path.join(root, file)
                with open(full_path, "r", encoding="utf-8") as f:
                    tree = ast.parse(f.read(), filename=full_path)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        func = node.func
                        name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
                        if name == "configurar_bucle_eventos":
                            invocadores.append(os.path.relpath(full_path, RAIZ))

    assert len(invocadores) == 0, (
        f"Se encontraron otros módulos invocando configurar_bucle_eventos: {invocadores}. "
        "main.py debe ser el único punto de entrada que la llama."
    )
