# ¤seguridad ¤evidencias ¤arbitro
"""El servidor decide qué archivos se aceptan como evidencia (SEC-05).

FE-04 restringe tipo y tamaño solo en la interfaz; quien llame a la API directamente se las salta.
Estas pruebas fijan las reglas en el servidor, al pedir la URL de subida y al registrar la evidencia.
No usan base de datos ni R2: el permiso y la generación de la URL se simulan.
"""
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app_core.db.session import get_session
from app_core.errors import CATALOGO_ERRORES
from app_core.storage import r2
from features.organizacion import organizacion_service
from features.roadmap import roadmap_service
from main import app

pytestmark = pytest.mark.asyncio

MB = 1024 * 1024
HEADERS = {"X-User-ID": "u-1", "X-Tenant-ID": "t-1", "X-Role": "responsable_area"}
URL_SUBIDA = "/api/v1/roadmaps/tasks/task-1/evidence/upload-url"
URL_REGISTRO = "/api/v1/roadmaps/tasks/task-1/evidence"


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setattr(organizacion_service, "has_active_role", AsyncMock(return_value=True))
    monkeypatch.setattr(roadmap_service, "ensure_task_in_area_scope", AsyncMock(return_value=None))
    monkeypatch.setattr(
        r2, "generate_upload_url", lambda key, mime: {"url": "https://r2.test/x", "key": key, "headers": {}}
    )
    registrar = AsyncMock(return_value={"id": "evd-1"})
    monkeypatch.setattr(roadmap_service, "register_evidence_upload", registrar)
    # Se restaura lo que había: otros módulos de prueba registran overrides al importarse.
    anteriores = dict(app.dependency_overrides)
    app.dependency_overrides[get_session] = lambda: None
    yield registrar
    app.dependency_overrides.clear()
    app.dependency_overrides.update(anteriores)


async def _subir(nombre, mime, tamano):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        return await c.post(URL_SUBIDA, json={"filename": nombre, "mime_type": mime, "file_size": tamano}, headers=HEADERS)


async def _registrar(clave, mime, tamano):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        return await c.post(
            URL_REGISTRO, params={"r2_key": clave, "mime_type": mime, "file_size": tamano}, headers=HEADERS
        )


@pytest.mark.parametrize("mime,nombre", [(m, f"doc{e[0]}") for m, e in r2.TIPOS_PERMITIDOS.items()])
async def test_cada_tipo_permitido_obtiene_url(api, mime, nombre):
    r = await _subir(nombre, mime, 1024)
    assert r.status_code == 200, r.text


@pytest.mark.parametrize(
    "nombre,mime",
    [
        ("virus.exe", "application/x-msdownload"),
        ("pagina.html", "text/html"),
        ("script.js", "application/javascript"),
        ("imagen.svg", "image/svg+xml"),
    ],
)
async def test_tipo_fuera_de_la_lista_blanca_se_rechaza_con_415(api, nombre, mime):
    r = await _subir(nombre, mime, 1024)
    assert r.status_code == 415
    assert r.json()["code"] == "EVIDENCE_TYPE_NOT_ALLOWED"


async def test_extension_que_no_corresponde_al_tipo_se_rechaza(api):
    """Un ejecutable renombrado .pdf declarando application/pdf no entra por la extensión contraria."""
    r = await _subir("informe.exe", "application/pdf", 1024)
    assert r.status_code == 415
    assert r.json()["code"] == "EVIDENCE_TYPE_NOT_ALLOWED"


async def test_el_mime_se_compara_sin_distinguir_mayusculas(api):
    assert (await _subir("a.pdf", "Application/PDF", 1024)).status_code == 200


async def test_tamano_en_el_limite_pasa_y_un_byte_mas_se_rechaza(api):
    assert (await _subir("a.pdf", "application/pdf", r2.TAMANO_MAXIMO_BYTES)).status_code == 200
    r = await _subir("a.pdf", "application/pdf", r2.TAMANO_MAXIMO_BYTES + 1)
    assert r.status_code == 413
    assert r.json()["code"] == "EVIDENCE_TOO_LARGE"


async def test_el_registro_aplica_las_mismas_reglas(api):
    registrar = api
    r = await _registrar("t-1/task-1/abc_virus.exe", "application/x-msdownload", 10)
    assert r.status_code == 415 and r.json()["code"] == "EVIDENCE_TYPE_NOT_ALLOWED"
    r = await _registrar("t-1/task-1/abc_gigante.pdf", "application/pdf", 50 * MB)
    assert r.status_code == 413 and r.json()["code"] == "EVIDENCE_TOO_LARGE"
    registrar.assert_not_awaited()  # lo rechazado no llega al servicio


async def test_el_registro_de_un_archivo_valido_sigue_funcionando(api):
    registrar = api
    r = await _registrar("t-1/task-1/abc_informe.pdf", "application/pdf", 2048)
    assert r.status_code == 201, r.text
    registrar.assert_awaited_once()


async def test_los_codigos_nuevos_estan_en_el_catalogo():
    assert CATALOGO_ERRORES["EVIDENCE_TYPE_NOT_ALLOWED"].status_code == 415
    assert CATALOGO_ERRORES["EVIDENCE_TOO_LARGE"].status_code == 413


async def test_reglas_del_servidor_alineadas_con_las_de_la_interfaz():
    """Si alguien cambia una lista sin la otra, el aviso de la interfaz dejaría de coincidir con el servidor."""
    import os
    import re

    ruta = os.path.join(
        os.path.dirname(__file__), "..", "frontend", "src", "components", "modules", "roadmap", "evidencia", "reglas.ts"
    )
    fuente = open(ruta, encoding="utf-8").read()
    mimes_ui = set(re.findall(r'^\s*"([a-z]+/[^"]+)":\s*\[', fuente, flags=re.M))
    assert mimes_ui == set(r2.TIPOS_PERMITIDOS)
    assert f"{r2.TAMANO_MAXIMO_BYTES // MB} * 1024 * 1024" in fuente
