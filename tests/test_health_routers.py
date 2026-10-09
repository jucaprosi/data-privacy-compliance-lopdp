"""/health informa qué routers cargaron y cuáles fallaron (Aporte 91)."""
from types import SimpleNamespace

from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

import main


def _importador(falla: dict[str, Exception]):
    def importar(path: str):
        if path in falla:
            raise falla[path]
        router = APIRouter()

        @router.get(f"/{path.rsplit('.', 1)[-1]}")
        def ruta() -> dict:
            return {"ok": True}

        return SimpleNamespace(router=router)

    return importar


def test_registrar_routers_separa_cargados_y_fallidos():
    app = FastAPI()
    mapa = [("a.uno", "uno"), ("a.dos", "dos"), ("a.tres", "tres")]
    falla = {"a.dos": ModuleNotFoundError("No module named 'secreto_interno'")}

    cargados, fallidos = main.registrar_routers(app, mapa, importar=_importador(falla))

    assert cargados == ["uno", "tres"]
    assert fallidos == [{"router": "dos", "error": "ModuleNotFoundError"}]
    paths = TestClient(app).get("/openapi.json").json()["paths"]
    assert "/api/v1/uno" in paths and "/api/v1/tres" in paths
    assert "/api/v1/dos" not in paths


def test_fallidos_no_exponen_el_mensaje_del_error():
    _, fallidos = main.registrar_routers(
        FastAPI(),
        [("a.uno", "uno")],
        importar=_importador({"a.uno": RuntimeError("postgresql://usuario:clave@host/db")}),
    )
    assert "clave" not in str(fallidos) and fallidos[0]["error"] == "RuntimeError"


def test_health_informa_routers_y_estado_coherente():
    r = TestClient(main.app).get("/health")
    assert r.status_code == 200
    cuerpo = r.json()
    routers = cuerpo["routers"]
    assert routers["total"] == len(main.ROUTERS_MAP)
    assert len(routers["cargados"]) + len(routers["fallidos"]) == routers["total"]
    esperado = "OPERATIONAL" if not routers["fallidos"] else "DEGRADED"
    assert cuerpo["status"] == esperado
