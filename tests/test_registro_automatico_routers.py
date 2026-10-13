# ¤adpa
"""Pruebas unitarias para el auto-registro de routers (RM-00)."""
import importlib
from types import ModuleType, SimpleNamespace
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

import main


def test_autoregistro_descubre_modulos_con_auto_registro_true(monkeypatch):
    """Verifica que descubrir_routers_auto detecte módulos que declaren AUTO_REGISTRO = True."""
    # Simulamos un paquete ficticio con dos módulos
    fake_mod1 = ModuleType("api.routers.fake_auto")
    fake_mod1.AUTO_REGISTRO = True
    fake_mod1.router = APIRouter(prefix="/fake-auto")

    @fake_mod1.router.get("/ping")
    def ping():
        return {"ping": "pong"}

    fake_mod2 = ModuleType("api.routers.fake_no_auto")
    fake_mod2.AUTO_REGISTRO = False
    fake_mod2.router = APIRouter(prefix="/fake-no-auto")

    fake_pkg = ModuleType("api.routers")
    fake_pkg.__path__ = ["fake_path"]

    def fake_iter_modules(path):
        assert path == ["fake_path"]
        return [
            (None, "fake_auto", False),
            (None, "fake_no_auto", False),
        ]

    def fake_import(name):
        if name == "api.routers":
            return fake_pkg
        elif name == "api.routers.fake_auto":
            return fake_mod1
        elif name == "api.routers.fake_no_auto":
            return fake_mod2
        raise ImportError(f"No module named {name}")

    monkeypatch.setattr("pkgutil.iter_modules", fake_iter_modules)

    descubiertos = main.descubrir_routers_auto(paquete="api.routers", importar=fake_import)

    assert descubiertos == [("api.routers.fake_auto", "fake_auto")]


def test_autoregistro_se_monta_bajo_api_v1(monkeypatch):
    """Comprueba que un router con AUTO_REGISTRO se registre bajo /api/v1 sin editar main.py."""
    fake_mod = ModuleType("api.routers.modulo_nuevo")
    fake_mod.AUTO_REGISTRO = True
    router = APIRouter(prefix="/nuevo")

    @router.get("/recurso")
    def recurso():
        return {"data": "ok"}

    fake_mod.router = router

    fake_pkg = ModuleType("api.routers")
    fake_pkg.__path__ = ["fake_path"]

    def fake_iter_modules(path):
        return [(None, "modulo_nuevo", False)]

    def fake_import(name):
        if name == "api.routers":
            return fake_pkg
        if name == "api.routers.modulo_nuevo":
            return fake_mod
        raise ImportError(name)

    monkeypatch.setattr("pkgutil.iter_modules", fake_iter_modules)

    app_test = FastAPI()
    descubiertos = main.descubrir_routers_auto(paquete="api.routers", importar=fake_import)
    cargados, fallidos = main.registrar_routers(app_test, descubiertos, importar=fake_import)

    assert cargados == ["modulo_nuevo"]
    assert fallidos == []

    client = TestClient(app_test)
    resp = client.get("/api/v1/nuevo/recurso")
    assert resp.status_code == 200
    assert resp.json() == {"data": "ok"}


def test_health_incluye_routers_auto_en_total():
    """Valida que get_total_routers() y health_check() reflejen routers_map + auto_routers_map."""
    total = main.get_total_routers()
    assert total == len(main.ROUTERS_MAP) + len(main.AUTO_ROUTERS_MAP)

    r = TestClient(main.app).get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["routers"]["total"] == total
    assert len(data["routers"]["cargados"]) + len(data["routers"]["fallidos"]) == total
