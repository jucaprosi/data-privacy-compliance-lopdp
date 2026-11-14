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
- M4. Cambiar un dígito de HUELLA_INSTANTANEA_ANTERIOR, o una de las cuatro entradas de LINEAS_QUITADAS:
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


# Las cuatro líneas que se quitaron: una por operación de las tres rutas antiguas (la ruta de vínculos tiene
# operación PATCH). Referencia congelada aquí: no depende de git ni de origin/main.
LINEAS_QUITADAS = (
    ("/api/v1/evidencias", "get"),
    ("/api/v1/evidencias", "post"),
    ("/api/v1/evidencias/verificar/{sha256}", "get"),
    ("/api/v1/evidencias/{evidencia_id}/vinculos", "patch"),
)


def _reponer_valor_antiguo(instantanea):
    """Copia que repone `"default": "tenant-default"` en la cabecera x-tenant-id; devuelve (copia, sitios)."""
    copia = json.loads(json.dumps(instantanea))
    sitios = []
    for ruta, operaciones in copia.items():
        for metodo, operacion in operaciones.items():
            for parametro in operacion.get("parameters", []):
                if parametro.get("in") == "header" and parametro.get("name") == "x-tenant-id":
                    assert "default" not in parametro["schema"]
                    parametro["schema"]["default"] = VALOR_ANTIGUO
                    sitios.append((ruta, metodo))
    return copia, tuple(sitios)


def test_instantanea_solo_pierde_el_valor_por_defecto():
    texto = SNAPSHOT.read_text(encoding="utf-8")
    assert VALOR_ANTIGUO not in texto
    repuesta, sitios = _reponer_valor_antiguo(json.loads(texto))
    assert sorted(sitios) == sorted(LINEAS_QUITADAS)  # exactamente cuatro, y estas
    canonico = json.dumps(repuesta, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    # Con las cuatro líneas repuestas, la instantánea nueva es idéntica a la anterior (huella congelada).
    assert hashlib.sha256(canonico.encode("utf-8")).hexdigest() == HUELLA_INSTANTANEA_ANTERIOR
