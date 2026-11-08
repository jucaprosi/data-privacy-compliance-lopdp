# ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-118: GET /api/v1/biblioteca/capacidades/mias.

Sin capacidades responde 200 con lista vacía (nunca 403), con dos devuelve solo esas dos y nunca las de otra
persona. La persistencia corre como `lopdp_app` contra PostgreSQL local (ARNES_BASE=postgresql_local), en una
transacción que se revierte, con usuarios sintéticos y correos `.invalid`.

Mutación decisiva (BIB-118.md): en `features/biblioteca/services/autorizacion.py::capacidades` quitar
`c.usuario_id=:actor AND` devuelve las capacidades de otras personas cuando la sesión omite la RLS y hace
fallar `test_nunca_devuelve_capacidades_de_otra_persona`.
"""
import os
from uuid import uuid4
import httpx
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from api.rbac import get_usuario_autenticado
from app_core.db.session import get_session
from features.biblioteca import biblioteca_service as bib
from main import app

PRODUCCION = "ep-late-hall-b50bpbk5"
RUTA = "/api/v1/biblioteca/capacidades/mias"


# ¤arbitro
def test_ruta_publicada_solo_get_y_la_compuerta_la_expone():
    from api.routers import biblioteca_capacidades as router
    assert router.AUTO_REGISTRO is True
    assert set(app.openapi()["paths"][RUTA]) == {"get"}
    assert "capacidades_propias" in bib.__all__


# ¤arbitro
@pytest.mark.asyncio
async def test_sin_sesion_sigue_siendo_401_y_no_403(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "oidc")
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as api:
        respuesta = await api.get(RUTA)
    assert respuesta.status_code == 401, respuesta.text


# ¤arbitro
def _url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or os.environ.get("ARNES_BASE") != "postgresql_local":
        pytest.skip("Persistencia BIB-118 no acreditada: falta PostgreSQL local (ARNES_BASE=postgresql_local)")
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


# ¤arbitro
@pytest_asyncio.fixture
async def mundo():
    engine = create_async_engine(_url(), echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            ids = {nombre: "bib118-" + uuid4().hex for nombre in ("sin", "doble", "otra")}
            for usuario in ids.values():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,'Sintético')"),
                                       {"id": usuario, "e": usuario + "@correo.invalid"})
            for usuario, capacidad in ((ids["doble"], "editor"), (ids["doble"], "revisor_tecnico"),
                                       (ids["otra"], "publicador"), (ids["otra"], "revisor_juridico")):
                await conexion.execute(text(
                    "WITH o AS (INSERT INTO users(id,email,nombre) SELECT 'otorgante-'||g, 'otorgante-'||g||'@correo.invalid', 'Otorgante sintético' FROM md5(random()::text) g RETURNING id) "
                    "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                    "SELECT :u,:c,o.id,'Fixture sintética rollback' FROM o"), {"u": usuario, "c": capacidad})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield conexion, sesion, ids
        finally:
            await transaccion.rollback()
    await engine.dispose()


# ¤arbitro
async def _pedir(sesion: AsyncSession, actor: str) -> httpx.Response:
    async def sesion_de_prueba():
        yield sesion
    app.dependency_overrides[get_session] = sesion_de_prueba
    app.dependency_overrides[get_usuario_autenticado] = lambda: actor
    try:
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as api:
            return await api.get(RUTA)
    finally:
        app.dependency_overrides.pop(get_session, None)
        app.dependency_overrides.pop(get_usuario_autenticado, None)


# ¤arbitro
@pytest.mark.asyncio
async def test_sin_capacidades_responde_200_y_lista_vacia(mundo):
    _, sesion, ids = mundo
    respuesta = await _pedir(sesion, ids["sin"])
    assert respuesta.status_code == 200 and respuesta.json() == {"capacidades": []}


# ¤arbitro
@pytest.mark.asyncio
async def test_con_dos_capacidades_devuelve_solo_esas_dos(mundo):
    _, sesion, ids = mundo
    respuesta = await _pedir(sesion, ids["doble"])
    assert respuesta.status_code == 200 and respuesta.json() == {"capacidades": ["editor", "revisor_tecnico"]}


# ¤arbitro
@pytest.mark.asyncio
async def test_nunca_devuelve_capacidades_de_otra_persona(mundo):
    """Defensa en profundidad: con un rol que omite la RLS, el filtro del servicio basta por sí solo."""
    conexion, _, ids = mundo
    await conexion.execute(text("RESET ROLE"))
    if not (await conexion.execute(text(
            "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user"))).scalar():
        pytest.skip("El rol de pruebas no omite la RLS; la defensa en profundidad no es observable aquí")
    async with AsyncSession(bind=conexion, expire_on_commit=False, join_transaction_mode="create_savepoint") as libre:
        for actor, esperadas in ((ids["sin"], []), (ids["doble"], ["editor", "revisor_tecnico"])):
            respuesta = await _pedir(libre, actor)
            assert respuesta.json()["capacidades"] == esperadas
