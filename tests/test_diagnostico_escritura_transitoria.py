# ¤diagnostico ¤rbac-tenant ¤arbitro
"""DIAG-07a: quién guarda respuestas del diagnóstico durante la transición (expandir).

Recorrido real contra PostgreSQL. Sin TEST_DATABASE_URL las pruebas se omiten. Solo valores generados y
correos `.invalid`. Mutación documentada: quitar `admin_organizacion` de `_escritura` hace fallar la
primera prueba; quitar `dpo`, la segunda.
"""
import os
import uuid

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL")
if not _TEST_URL:
    pytest.skip("TEST_DATABASE_URL no configurada", allow_module_level=True)
os.environ["DATABASE_URL"] = _TEST_URL

from app_core.db.session import fijar_contexto_rls  # noqa: E402

pytestmark = pytest.mark.asyncio
RESPUESTAS = "/api/v1/diagnostico/respuestas"


def _url() -> str:
    return _TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _respuesta(pregunta_id: int) -> dict:
    return {
        "pregunta_id": pregunta_id, "control": "Control del banco", "dimension": "D01", "nivel_asignado": 4,
        "nivel_evidencia": 2, "criticidad": 3, "es_critica": False, "riesgo_base": 5,
    }


@pytest_asyncio.fixture
async def api(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    from httpx import ASGITransport, AsyncClient

    from app_core.db.session import get_session
    from main import app

    engine = create_async_engine(_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    tenant = f"esc-{sufijo}"
    roles = {"dpo": "dpo", "admin": "admin_organizacion", "impl": "implementador", "coord": "coordinador"}
    usuarios = {clave: (f"esc-{clave}-{sufijo}", tenant, rol) for clave, rol in roles.items()}
    async with factory() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
            "VALUES (:t, :t, :t, :t, 'mediana')"
        ), {"t": tenant})
        for uid, t, rol in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.invalid"})
            await s.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"
            ), {"i": str(uuid.uuid4()), "u": uid, "t": t, "r": rol})
        await s.commit()

    async def session_override():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_session] = session_override
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield {"client": client, "u": usuarios}
    app.dependency_overrides.clear()
    async with factory() as s:
        await fijar_contexto_rls(s, tenant)
        for sentencia in (
            "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
            "DELETE FROM audit_events WHERE tenant_id = :t",
            "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
        ):
            await s.execute(text(sentencia), {"t": tenant})
        await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
        await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"esc-%-{sufijo}"})
        await s.commit()
    await engine.dispose()


def _como(api, clave):
    uid, tenant, rol = api["u"][clave]
    return {"X-User-ID": uid, "X-Tenant-ID": tenant, "X-Role": rol}


async def test_el_administrador_guarda(api):
    r = await api["client"].put(RESPUESTAS, headers=_como(api, "admin"), json={"respuestas": [_respuesta(12)]})
    assert r.status_code == 200, r.text


async def test_el_dpo_sigue_guardando(api):
    r = await api["client"].put(RESPUESTAS, headers=_como(api, "dpo"), json={"respuestas": [_respuesta(12)]})
    assert r.status_code == 200, r.text


@pytest.mark.parametrize("clave", ["impl", "coord"])
async def test_implementador_y_coordinador_no_guardan(api, clave):
    r = await api["client"].put(RESPUESTAS, headers=_como(api, clave), json={"respuestas": [_respuesta(12)]})
    assert r.status_code == 403
