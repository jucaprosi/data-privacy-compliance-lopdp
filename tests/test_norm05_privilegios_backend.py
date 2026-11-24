# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤vigilancia-spdp ¤inteligencia-normativa ¤seguridad ¤arbitro
"""NORM-05: el backend no adopta el rol del monitoreo.

Conectado como `lopdp_app` (SET SESSION AUTHORIZATION sobre una conexión propia, que sobrevive al commit; `SET ROLE` no sirve: lo valida el
usuario de sesión, y en el CI es el superusuario `lopdp_beta_owner`, que puede adoptar cualquier rol): revisa una
resolución, pero no inserta versiones ni bitácora, no cambia otra columna y no adopta `lopdp_normativa`.
El disparo manual lanza el Job con un envío doble: sin red real. Cada prueba documenta su mutación.
"""
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from features.inteligencia_normativa import inteligencia_normativa_service as svc
from features.inteligencia_normativa.domain.errores import EstadoNoPermitido

pytestmark = pytest.mark.asyncio

NOTA = "Cotejada con el Registro Oficial."
JOB = "evydentia-monitoreo-normativo"


@pytest_asyncio.fixture
async def como_app(db_engine):
    """Fábrica de sesiones cuya conexión es `lopdp_app` durante toda su vida (no solo una transacción)."""
    motor = create_async_engine(db_engine.url, poolclass=NullPool)

    @event.listens_for(motor.sync_engine, "connect")
    def _rol(conexion, _registro):
        cursor = conexion.cursor()
        cursor.execute("SET SESSION AUTHORIZATION lopdp_app")
        cursor.close()

    fabrica = async_sessionmaker(motor, expire_on_commit=False, class_=AsyncSession)
    async with fabrica() as s:
        quien = (await s.execute(text(
            "SELECT session_user, current_user, (SELECT rolsuper FROM pg_roles WHERE rolname = session_user)"))).one()
    assert tuple(quien) == ("lopdp_app", "lopdp_app", False), "la prueba no se conecta de verdad como lopdp_app"
    yield fabrica
    await motor.dispose()


@pytest_asyncio.fixture
async def propietario(db_engine):
    fabrica = async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)
    async with fabrica() as s:
        await s.execute(text("TRUNCATE normativa_versiones, normativa_resoluciones, normativa_monitoreo_logs CASCADE"))
        await s.commit()
    yield fabrica
    async with fabrica() as s:
        await s.execute(text("TRUNCATE normativa_versiones, normativa_resoluciones, normativa_monitoreo_logs CASCADE"))
        await s.execute(text("DELETE FROM operadores_plataforma WHERE id LIKE 'n05-%'"))
        await s.commit()


async def _sembrar(propietario) -> str:
    async with propietario() as s:
        i = (await s.execute(
            text("INSERT INTO normativa_resoluciones (numero_resolucion, anio_emision, titulo, organo_emisor, materia, "
                 "url_fuente, seccion_fuente, archivo_sha256, ruta_original, tamano_bytes, estado) "
                 "VALUES ('N05-1', 2026, 'Título', 'SPDP', 'General', 'https://x.invalid/a.pdf', 'resoluciones', :h, "
                 "'spdp/a.pdf', 10, 'pendiente_revision') RETURNING id::text"), {"h": uuid.uuid4().hex * 2})).scalar_one()
        await s.commit()
    return i


async def _debe_fallar(fabrica, sentencia: str, params: dict | None = None) -> None:
    async with fabrica() as s:
        assert (await s.execute(text("SELECT session_user = 'lopdp_app'"))).scalar_one() is True
        with pytest.raises(DBAPIError):
            await s.execute(text(sentencia), params or {})
        await s.rollback()


# ------------------------------------------------------------ R1 y R2: privilegios

async def test_lopdp_app_revisa_la_resolucion(propietario, como_app):
    """Mutación m1: volver a llamar a `_como_normativa(sesion)` en `registrar_revision` da `permission denied`."""
    from features.inteligencia_normativa.services import revision

    i = await _sembrar(propietario)
    async with como_app() as s:
        r = await revision.registrar_revision(s, i, "vigente", NOTA, "sub-n05")
    assert r.estado == "vigente" and r.nota_revision == NOTA and r.revisada_por == "sub-n05"
    assert r.revisada_en is not None


async def test_la_validacion_de_la_revision_no_cambia(propietario, como_app):
    from features.inteligencia_normativa.services import revision

    i = await _sembrar(propietario)
    async with como_app() as s:
        with pytest.raises(EstadoNoPermitido):
            await revision.registrar_revision(s, i, "inventado", NOTA, "sub-n05")


async def test_lopdp_app_no_inserta_versiones_ni_bitacora(propietario, como_app):
    """Mutación m2 (a): conceder `INSERT` sobre las tablas del monitoreo a `lopdp_app` da rojo."""
    i = await _sembrar(propietario)
    await _debe_fallar(como_app, "INSERT INTO normativa_monitoreo_logs (inicio, origen, estado) "
                                 "VALUES (now(), 'programado', 'fallida')")
    await _debe_fallar(como_app, "INSERT INTO normativa_versiones (resolucion_id, archivo_sha256, ruta_original, "
                                 "tamano_bytes) VALUES (CAST(:i AS uuid), :h, 'spdp/b.pdf', 10)",
                       {"i": i, "h": uuid.uuid4().hex * 2})


async def test_lopdp_app_solo_actualiza_las_cuatro_columnas(propietario, como_app):
    """Mutación m2 (b): conceder `UPDATE` de toda la tabla en la migración permite cambiar `titulo` y da rojo."""
    i = await _sembrar(propietario)
    await _debe_fallar(como_app, "UPDATE normativa_resoluciones SET titulo = 'otro' WHERE id = CAST(:i AS uuid)", {"i": i})
    async with como_app() as s:
        await s.execute(text("UPDATE normativa_resoluciones SET nota_revision = 'x' WHERE id = CAST(:i AS uuid)"), {"i": i})
        await s.rollback()


async def test_lopdp_app_no_adopta_el_rol_del_monitoreo(como_app):
    """Mutación m2 (c): `GRANT lopdp_normativa TO lopdp_app` en la migración da rojo."""
    async with como_app() as s:
        miembro = (await s.execute(text("SELECT pg_has_role('lopdp_app', 'lopdp_normativa', 'MEMBER')"))).scalar_one()
        atributos = tuple((await s.execute(
            text("SELECT rolsuper, rolcreaterole FROM pg_roles WHERE rolname = 'lopdp_app'"))).one())
        puede_set = (await s.execute(text("SELECT pg_has_role('lopdp_app', 'lopdp_normativa', 'SET')"))).scalar_one()
    diagnostico = f"(rolsuper, rolcreaterole)={atributos}; MEMBER={miembro}; SET={puede_set}"
    assert not miembro, f"membresía de lopdp_app en lopdp_normativa que viene de fuera del repositorio: {diagnostico}"
    assert not puede_set, f"lopdp_app puede hacer SET ROLE lopdp_normativa (¿ADMIN por haberlo creado?): {diagnostico}"
    await _debe_fallar(como_app, "SET LOCAL ROLE lopdp_normativa")


# ------------------------------------------------------------ R3: disparo manual por el Job

class Envio:
    def __init__(self):
        self.llamadas: list[str] = []

    async def __call__(self, url: str) -> None:
        self.llamadas.append(url)


@pytest_asyncio.fixture
async def cliente(propietario):
    from app_core.db.session import get_session
    from main import app

    async def _sesion():
        async with propietario() as s:
            yield s

    app.dependency_overrides[get_session] = _sesion
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.pop(get_session, None)
    svc.inyectar_envio_del_trabajo_de_prueba()


@pytest_asyncio.fixture
async def operador(propietario):
    correo = f"op-{uuid.uuid4().hex[:6]}@example.test"
    async with propietario() as s:
        await s.execute(
            text("INSERT INTO operadores_plataforma (id, email, nombre, activo, created_at, updated_at) "
                 "VALUES (:i, :e, 'Operador', TRUE, NOW(), NOW())"), {"i": f"n05-{uuid.uuid4().hex[:8]}", "e": correo})
        await s.commit()
    return {"X-User-Email": correo, "X-User-ID": f"sub-{uuid.uuid4().hex[:6]}"}


@pytest.fixture
def en_la_nube(monkeypatch):
    monkeypatch.setenv("K_SERVICE", "evydentia-backend")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "proyecto-de-prueba")
    monkeypatch.setenv("NORMATIVA_TRABAJO_MONITOREO", JOB)


async def test_el_disparo_manual_lanza_el_job(cliente, operador, en_la_nube, monkeypatch):
    """Mutación m3: volver a `tareas.add_task(svc.disparar_monitoreo, "manual")` da rojo."""
    envio = Envio()
    svc.inyectar_envio_del_trabajo_de_prueba(envio)

    async def no_debe_correr(*a, **k):
        raise AssertionError("el backend no corre el monitoreo")

    monkeypatch.setattr(svc, "disparar_monitoreo", no_debe_correr)
    r = await cliente.post("/api/v1/normativa/monitoreo", headers=operador)
    assert r.status_code == 202 and r.json() == {"estado": "aceptado"}
    assert envio.llamadas == [
        f"https://run.googleapis.com/v2/projects/proyecto-de-prueba/locations/us-central1/jobs/{JOB}:run"]


async def test_sin_nombre_del_job_es_503_y_no_llama(cliente, operador, en_la_nube, monkeypatch):
    """Mutación m4: llamar a `:run` aunque `NORMATIVA_TRABAJO_MONITOREO` esté vacía da rojo."""
    monkeypatch.setenv("NORMATIVA_TRABAJO_MONITOREO", "")
    envio = Envio()
    svc.inyectar_envio_del_trabajo_de_prueba(envio)
    r = await cliente.post("/api/v1/normativa/monitoreo", headers=operador)
    assert r.status_code == 503 and r.json()["detail"] == {"codigo": "NORMATIVA_TRABAJO_NO_DISPONIBLE"}
    assert envio.llamadas == []


async def test_fuera_de_cloud_run_no_llama(cliente, operador, en_la_nube, monkeypatch):
    monkeypatch.delenv("K_SERVICE")
    envio = Envio()
    svc.inyectar_envio_del_trabajo_de_prueba(envio)
    r = await cliente.post("/api/v1/normativa/monitoreo", headers=operador)
    assert r.status_code == 503 and envio.llamadas == []


async def test_un_fallo_del_envio_es_503_sin_detalle(cliente, operador, en_la_nube):
    async def roto(url):
        raise RuntimeError("secreto https://interno.invalid")

    svc.inyectar_envio_del_trabajo_de_prueba(roto)
    r = await cliente.post("/api/v1/normativa/monitoreo", headers=operador)
    assert r.status_code == 503 and "interno" not in r.text
