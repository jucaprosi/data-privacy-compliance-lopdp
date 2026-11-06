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
import re
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from api import rbac
from app_core.db.session import get_session
from features.organizacion import organizacion_service

RAIZ = Path(__file__).resolve().parent.parent
FRONT = RAIZ / "frontend" / "src" / "lib"
TENANT, USUARIO = "org-bib115", "usuario-bib115"
METODOS = ("GET", "POST", "PUT", "PATCH", "DELETE")
# Los 14 clientes de la propiedad de BIB-115 (plantillasCuenta.ts es de BIB-401).
CLIENTES = ["aplicabilidad", "borradores", "catalogo", "contexto", "documentos", "enlaces", "filas",
            "generacion", "http", "preview", "revisiones", "trabajos", "verificacion", "vinculos"]


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
    # Las 19 salas de Biblioteca con miembro; catálogo y editorial no pasan por get_context.
    assert len(modulos) == 19, sorted(modulos)
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


# ----------------------------------------------------------------------------- contrato del frontend

def _funcion(texto: str, nombre: str) -> str:
    inicio = texto.index(f"export function {nombre}(")
    fin = texto.index("\n}", inicio)
    return texto[inicio:fin]


def test_cabeceras_de_miembro_declara_rol_y_usuario():
    texto = (FRONT / "auth" / "cabeceras.ts").read_text(encoding="utf-8")
    cuerpo = _funcion(texto, "cabecerasDeMiembro")
    assert '"X-Role": rol' in cuerpo
    assert re.search(r'modoAutenticacion\(\) === "headers"\) cabeceras\["X-User-ID"\]', cuerpo)
    assert "leerOrganizacionActiva()" in texto
    assert "throw new SinRolPermitido" in cuerpo
    # cabecerasDeTenant no cambia: los demás clientes siguen igual.
    assert '"X-Role"' not in _funcion(texto, "cabecerasDeTenant")


@pytest.mark.parametrize("cliente", CLIENTES)
def test_los_clientes_de_biblioteca_usan_cabeceras_de_miembro(cliente):
    texto = (FRONT / "biblioteca" / f"{cliente}.ts").read_text(encoding="utf-8")
    assert "cabecerasDeMiembro" in texto
    # Única excepción: la consulta de roles de Organización, que no es una ruta de Biblioteca.
    usos = re.findall(r"fetchAutenticado\(([^;]*?)cabecerasDeTenant\(\)", texto, flags=re.S)
    assert all("/organizacion/me/roles" in uso for uso in usos), usos


def test_las_escrituras_declaran_los_roles_de_su_ruta():
    http = (FRONT / "biblioteca" / "http.ts").read_text(encoding="utf-8")
    editores = importlib.import_module("api.routers.biblioteca_borradores").EDITORES
    assert f"ROLES_EDITORES = {list(editores)}".replace("'", '"') in http.replace(" as const", "")
    for cliente, roles in [("enlaces", "ROLES_GESTION_DOCUMENTAL"), ("verificacion", "ROLES_APORTAR_EVIDENCIA"),
                           ("verificacion", "ROLES_REVISAR_EVIDENCIA"), ("vinculos", "ROLES_QUE_VINCULAN"),
                           ("borradores", "ROLES_GESTION_DOCUMENTAL"), ("aplicabilidad", "ROLES_EDITORES")]:
        texto = (FRONT / "biblioteca" / f"{cliente}.ts").read_text(encoding="utf-8")
        assert f"cabecerasDeMiembro({roles})" in texto, (cliente, roles)
