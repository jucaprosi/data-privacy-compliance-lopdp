# ¤seguridad-tenant ¤arbitro
"""SEC-24: la cabecera X-Tenant-ID de la dependencia común no tiene valor por defecto.

Sin base de datos y sin `import yaml`. Solo valores simulados.

Mutaciones ejecutadas (cada una dejó en rojo la prueba indicada; se restauró):
- M1. Volver a poner `Header(default="tenant-default")` en `obtener_tenant_id_actual`:
  `test_firma_sin_valor_por_defecto`, `test_headers_sin_cabecera_400` y
  `test_las_rutas_antiguas_conservan_exactamente_su_forma_en_openapi` (el OpenAPI vivo vuelve a declararlo).
- M2. En la instantánea nueva, cambiar un método, una ruta, el nombre de un parámetro o un esquema:
  `test_las_rutas_antiguas_conservan_exactamente_su_forma_en_openapi` y
  `test_instantanea_solo_pierde_el_valor_por_defecto`.
- M3. En modo oidc, no exigir la cabecera: `test_oidc_sin_cambios`.

La instantánea `tests/snapshots/openapi_evidencias_antiguas.json` (de EVI-01, cedida a SEC-24) se regeneró una
sola vez, con la dependencia ya sin valor por defecto, desde esta rama (DATABASE_URL de relleno):
    import json, sys; sys.path.insert(0, "tests"); import test_evidencias_rutas_estables as t
    e = t.app.openapi(); a = {r: t._resolver(e["paths"][r], e) for r in t.RUTAS_ANTIGUAS}
    json.dumps(a, indent=1, sort_keys=True, ensure_ascii=False) + "\n"   # UTF-8, saltos \n
El diff perdió exactamente cuatro líneas `"default": "tenant-default"`.
"""
import hashlib
import inspect
import json
from pathlib import Path
from unittest.mock import AsyncMock

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from api import dependencies
from api.dependencies import obtener_tenant_id_actual

SNAPSHOT = Path(__file__).parent / "snapshots" / "openapi_evidencias_antiguas.json"
VALOR_ANTIGUO = "tenant-default"
# SHA-256 del JSON canónico (claves ordenadas, sin espacios) de la instantánea tal como estaba en `main`
# antes de SEC-24, es decir, con el valor por defecto de la cabecera.
HUELLA_INSTANTANEA_ANTERIOR = "fa7c12f76a17b97c0da56006efdbda5c4bf2c233452a7aea4dd97f13c1065e73"
MENSAJE_400 = "Encabezado X-Tenant-ID obligatorio para resolver contexto de aislamiento."


def _cliente() -> TestClient:
    app = FastAPI()

    @app.get("/probe")
    async def probe(tenant: str = Depends(obtener_tenant_id_actual)):
        return {"tenant": tenant}

    return TestClient(app)


def test_firma_sin_valor_por_defecto():
    parametro = inspect.signature(obtener_tenant_id_actual).parameters["x_tenant_id"]
    por_defecto = parametro.default.default  # FieldInfo de Header(...)
    assert por_defecto != VALOR_ANTIGUO
    assert por_defecto in (None, ...)
    assert VALOR_ANTIGUO not in inspect.getsource(obtener_tenant_id_actual)


def test_headers_sin_cabecera_400(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    r = _cliente().get("/probe")
    assert r.status_code == 400
    assert r.json()["detail"] == MENSAJE_400
    vacia = _cliente().get("/probe", headers={"X-Tenant-ID": "   "})
    assert vacia.status_code == 400
    con = _cliente().get("/probe", headers={"X-Tenant-ID": "org-simulada"})
    assert con.status_code == 200 and con.json() == {"tenant": "org-simulada"}


def test_oidc_sin_cambios(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "oidc")
    autenticar = AsyncMock(side_effect=HTTPException(403, "Sin membresía activa"))
    monkeypatch.setattr(dependencies, "autenticar_en_tenant", autenticar)
    cliente = _cliente()
    sin = cliente.get("/probe", headers={"Authorization": "Bearer simulado"})
    assert sin.status_code == 400 and sin.json()["detail"] == MENSAJE_400
    assert autenticar.await_count == 0
    sin_membresia = cliente.get(
        "/probe", headers={"Authorization": "Bearer simulado", "X-Tenant-ID": "org-simulada"}
    )
    assert sin_membresia.status_code == 403
    assert autenticar.await_count == 1


def _con_valor_antiguo(nodo):
    """Copia que repone `default` en cada parámetro de cabecera x-tenant-id."""
    if isinstance(nodo, dict):
        copia = {k: _con_valor_antiguo(v) for k, v in nodo.items()}
        if copia.get("in") == "header" and copia.get("name") == "x-tenant-id":
            assert "default" not in copia["schema"]
            copia["schema"]["default"] = VALOR_ANTIGUO
        return copia
    if isinstance(nodo, list):
        return [_con_valor_antiguo(x) for x in nodo]
    return nodo


def test_instantanea_solo_pierde_el_valor_por_defecto():
    texto = SNAPSHOT.read_text(encoding="utf-8")
    assert VALOR_ANTIGUO not in texto
    repuesta = _con_valor_antiguo(json.loads(texto))
    assert json.dumps(repuesta, sort_keys=True).count(f'"default": "{VALOR_ANTIGUO}"') == 4
    canonico = json.dumps(repuesta, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    assert hashlib.sha256(canonico.encode("utf-8")).hexdigest() == HUELLA_INSTANTANEA_ANTERIOR
