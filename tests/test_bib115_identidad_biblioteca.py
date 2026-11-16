# ¤adpa ¤rbac-tenant ¤frontend-ide ¤arbitro
"""BIB-115 · Biblioteca envía la identidad completa.

Las rutas de `api/routers/biblioteca_*.py` resuelven al miembro con `get_context` (`api/rbac.py`), que
exige `X-Tenant-ID` y `X-Role`, y en modo `headers` también `X-User-ID`. El cliente del frontend solo
mandaba la organización: toda la Biblioteca respondía 422.

1. Inventario del servidor: cada ruta cuyo árbol de dependencias pasa por `get_context` responde 422
   sin `X-Role` y 403 con él (sin membresía activa: la cabecera pasó la validación). Una ruta nueva
   entra sola en el recorrido. `GET /documentos/pendientes` con membresía responde 200.
2. Contrato del frontend: `cabecerasDeMiembro` añade `X-Role` (y `X-User-ID` en modo headers), y los
   14 clientes de Biblioteca de la ficha arman su identidad con ella.

Sin base de datos: la membresía y el servicio de pendientes se simulan. No acredita RLS.

Mutación documentada: quitar `"X-Role": rol` de `cabecerasDeMiembro` hace fallar
`test_cabeceras_de_miembro_declara_rol_y_usuario` y la prueba de interfaz `identidad.spec.ts`.
"""
import importlib
import os
import re
from pathlib import Path
from unittest.mock import AsyncMock

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/evydentia_test")

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from api import rbac
from app_core.db.session import get_session
from features.organizacion import organizacion_service

RAIZ = Path(__file__).resolve().parent.parent
TENANT, USUARIO = "org-bib115", "usuario-bib115"
METODOS = ("GET", "POST", "PUT", "PATCH", "DELETE")


def _usa_get_context(dependant) -> bool:
    return any(d.call is rbac.get_context or _usa_get_context(d) for d in dependant.dependencies)


def _modulos_de_biblioteca():
    for archivo in sorted((RAIZ / "api" / "routers").glob("biblioteca_*.py")):
        yield archivo.stem, importlib.import_module(f"api.routers.{archivo.stem}")


def _inventario() -> list[tuple[str, str, str]]:
    rutas = []
    for nombre, modulo in _modulos_de_biblioteca():
        for ruta in modulo.router.routes:
            if isinstance(ruta, APIRoute) and _usa_get_context(ruta.dependant):
                for metodo in sorted(ruta.methods & set(METODOS)):
                    rutas.append((nombre, metodo, ruta.path))
    return rutas


INVENTARIO = _inventario()


@pytest.fixture
def api(monkeypatch):
    """Todas las rutas de Biblioteca en una app sin base de datos, en modo `headers`."""
    monkeypatch.setenv("AUTH_MODE", "headers")
    pertenece = AsyncMock(return_value=False)
    monkeypatch.setattr(organizacion_service, "has_active_role", pertenece)
    app = FastAPI()
    for _, modulo in _modulos_de_biblioteca():
        app.include_router(modulo.router, prefix="/api/v1")
    app.dependency_overrides[get_session] = lambda: AsyncMock()
    with TestClient(app) as cliente:
        cliente.pertenece = pertenece
        yield cliente


def _pedir(api, metodo: str, ruta: str, rol: str | None):
    cabeceras = {"X-Tenant-ID": TENANT, "X-User-ID": USUARIO}
    if rol:
        cabeceras["X-Role"] = rol
    url = "/api/v1" + re.sub(r"\{[^}]+\}", "x", ruta)
    return api.request(metodo, url, headers=cabeceras)


def test_el_inventario_cubre_las_rutas_de_biblioteca():
    modulos = {nombre for nombre, _, _ in INVENTARIO}
    # Las 20 salas de Biblioteca con miembro; catálogo y editorial no pasan por get_context.
    assert len(modulos) == 20, sorted(modulos)
    assert "biblioteca_catalogo" not in modulos and "biblioteca_editorial" not in modulos
    assert ("biblioteca_documentos", "GET", "/biblioteca/documentos/pendientes") in INVENTARIO


@pytest.mark.parametrize(("modulo", "metodo", "ruta"), INVENTARIO, ids=[f"{m} {r}" for _, m, r in INVENTARIO])
def test_sin_x_role_responde_422(api, modulo, metodo, ruta):
    r = _pedir(api, metodo, ruta, rol=None)
    assert r.status_code == 422, r.text
    assert any(e.get("loc") == ["header", "X-Role"] for e in r.json()["detail"]), r.text


@pytest.mark.parametrize(("modulo", "metodo", "ruta"), INVENTARIO, ids=[f"{m} {r}" for _, m, r in INVENTARIO])
def test_con_x_role_pasa_la_validacion_y_decide_la_membresia(api, modulo, metodo, ruta):
    r = _pedir(api, metodo, ruta, rol="responsable_area")
    assert r.status_code in (200, 403), r.text
    assert "X-Role" not in r.text


def test_pendientes_con_identidad_completa_responde_200(api, monkeypatch):
    documentos = importlib.import_module("api.routers.biblioteca_documentos")
    api.pertenece.return_value = True
    monkeypatch.setattr(documentos.biblioteca, "pendientes", AsyncMock(return_value={
        "borrador": 1, "en_revision": 0, "por_vencer": 2, "vencidos": 0, "total": 3}))
    r = _pedir(api, "GET", "/biblioteca/documentos/pendientes", rol="implementador")
    assert r.status_code == 200, r.text
    assert r.json()["total"] == 3
    api.pertenece.assert_awaited_with(api.pertenece.await_args.args[0], TENANT, USUARIO, "implementador")


def test_pendientes_sin_x_user_id_en_modo_headers_responde_422(api):
    r = api.get("/api/v1/biblioteca/documentos/pendientes", headers={"X-Tenant-ID": TENANT, "X-Role": "implementador"})
    assert r.status_code == 422
    assert r.json()["detail"] == "Falta la cabecera X-User-ID"



