# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤rbac-tenant ¤arbitro
"""ORG-23: el auditor lee diagnóstico, incidentes y hallazgos de su organización y no escribe en ellos.

Contrato: governance/especificaciones/ORG-23.md §5. Recorrido real contra el PostgreSQL 16 local del arnés
o el del CI; sin TEST_DATABASE_URL las pruebas que abren la base se omiten.

Mutación m1 (documentada en el PR): quitar "auditor" de una de las tres tuplas ROLES_CONSULTA
(api/routers/diagnostico_resultados.py, features/incidentes/domain/models.py o
api/routers/roadmaps_hallazgos.py) deja en rojo test_auditor_lee_las_tres_apis en el GET correspondiente
(403 en lugar de 200) y test_las_tres_tuplas_incluyen_al_auditor.
"""
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from conftest import exigir_base_de_pruebas

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if _TEST_URL:
    os.environ["DATABASE_URL"] = _TEST_URL
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

LECTURAS = (
    "/api/v1/diagnostico/resultados",
    "/api/v1/diagnostico/etapa",
    "/api/v1/incidentes",
    "/api/v1/roadmaps/hallazgos",
)


def _incidente() -> dict:
    return {
        "fecha_deteccion": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        "titulo": "Acceso no autorizado a la base de clientes",
        "descripcion": "Se detectaron consultas masivas desde una cuenta de servicio.",
        "severidad": "Alta",
        "afecta_datos_personales": True,
        "categorias_datos": ["Contacto (Email / Teléfono)"],
        "medidas_inmediatas": "Se revocó la credencial de la cuenta de servicio.",
    }


def test_las_tres_tuplas_incluyen_al_auditor():
    from api.routers import diagnostico_resultados, roadmaps_hallazgos
    from features.incidentes.domain import models as incidentes

    assert "auditor" in diagnostico_resultados.ROLES_CONSULTA
    assert "auditor" in incidentes.ROLES_CONSULTA
    assert "auditor" in roadmaps_hallazgos.ROLES_CONSULTA
    # R2: la lectura no abre la escritura.
    assert "auditor" not in incidentes.ROLES_REGISTRO
    assert "auditor" not in roadmaps_hallazgos.ROLES_GESTION


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    exigir_base_de_pruebas()
    monkeypatch.setenv("AUTH_MODE", "headers")
    from app_core.db.session import fijar_contexto_rls, get_session
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    tenant = f"org23-{sufijo}"
    auditor = f"org23-aud-{sufijo}"
    async with factory() as s:
        await s.execute(text(
            "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
            "VALUES (:t, :t, :t, :t, 'mediana')"
        ), {"t": tenant})
        await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                        {"u": auditor, "e": f"{auditor}@example.test"})
        await fijar_contexto_rls(s, tenant, auditor)
        await s.execute(text(
            "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, 'auditor')"
        ), {"i": str(uuid.uuid4()), "u": auditor, "t": tenant})
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
    cabeceras = {"X-User-ID": auditor, "X-Tenant-ID": tenant, "X-Role": "auditor"}
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "h": cabeceras}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            await fijar_contexto_rls(s, tenant)
            for sentencia in (
                "DELETE FROM incidentes WHERE tenant_id = :t",
                "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
                "DELETE FROM audit_events WHERE tenant_id = :t",
                "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
            ):
                await s.execute(text(sentencia), {"t": tenant})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": auditor})
            await s.commit()
        await engine.dispose()


@pytest.mark.asyncio
@pytest.mark.parametrize("ruta", LECTURAS)
async def test_auditor_lee_las_tres_apis(ctx, ruta):
    r = await ctx["client"].get(ruta, headers=ctx["h"])
    assert r.status_code == 200, r.text


# Identificadores fijos: con uuid4() en la colección, cada trabajador de xdist ve ids de prueba distintos y la
#   corrida en paralelo aborta («Different tests were collected»). El 403 llega antes de buscar el recurso.
_INEXISTENTE = "00000000-0000-4000-8000-000000000023"

ESCRITURAS = (
    ("POST", "/api/v1/diagnostico/resultados", {}),
    ("POST", "/api/v1/incidentes", _incidente()),
    ("POST", f"/api/v1/incidentes/{_INEXISTENTE}/cerrar", {"motivo": "Se contuvo la vulneración y se documentó."}),
    ("POST", f"/api/v1/incidentes/{_INEXISTENTE}/reabrir", {"motivo": "Apareció un acceso nuevo de la misma cuenta."}),
    ("POST", "/api/v1/roadmaps/hallazgos/desde-diagnostico", None),
    ("POST", f"/api/v1/roadmaps/{_INEXISTENTE}/hallazgos/convertir",
     {"hallazgo_ids": [_INEXISTENTE], "wave_id": _INEXISTENTE}),
)


@pytest.mark.asyncio
@pytest.mark.parametrize(("metodo", "ruta", "cuerpo"), ESCRITURAS,
                         ids=("sellar", "registrar", "cerrar", "reabrir", "hallazgos", "convertir"))
async def test_auditor_no_escribe(ctx, metodo, ruta, cuerpo):
    r = await ctx["client"].request(metodo, ruta, headers=ctx["h"], json=cuerpo)
    assert r.status_code == 403, r.text
