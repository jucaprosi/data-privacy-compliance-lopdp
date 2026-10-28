# ¤rbac-tenant ¤seguridad ¤arbitro
"""ORG-13: una persona pertenece a varias organizaciones solo como DPO o implementador.

Recorrido real contra PostgreSQL (rama Neon de desarrollo o la rama test del CI, nunca
producción); sin TEST_DATABASE_URL las pruebas se omiten. La regla vive en un disparador de la
base, así que se prueba por la API y también insertando directamente como lopdp_app.

Prueba de mutación ejecutada en la rama Neon rama-org-13:
- Se desactivó el disparador (ALTER TABLE user_tenant_roles DISABLE TRIGGER
  trg_utr_organizaciones_por_persona).
- pytest tests/test_organizaciones_por_persona.py::test_un_rol_no_compartible_impide_estar_en_otra_organizacion[coordinador-dpo]
  devolvió 1 (FAILED: assert 201 == 409).
- Se volvió a activar el disparador; sin la mutación la prueba pasa.
"""
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if not _TEST_URL:
    pytest.skip("TEST_DATABASE_URL no configurada", allow_module_level=True)
os.environ["DATABASE_URL"] = _TEST_URL

from app_core.db.session import fijar_contexto_rls, get_session  # noqa: E402
from main import app  # noqa: E402

ROLES = "/api/v1/organizacion/roles"
MIS_ORGANIZACIONES = "/api/v1/organizacion/mis-organizaciones"
MENSAJE = "ya pertenece a otra organización"


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    # Rama de desarrollo o la rama test del CI, nunca producción.
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una rama de desarrollo o test (nunca producción)"
    monkeypatch.setenv("AUTH_MODE", "headers")
    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    tenants = {clave: f"org13-{clave}-{sufijo}" for clave in ("a", "b", "c")}
    usuarios = {clave: f"org13-{clave}-{sufijo}" for clave in ("admin_a", "admin_b", "admin_c", "persona", "otra")}
    creados: dict[str, list[str]] = {"tenants": [], "operadores": []}
    async with factory() as s:
        for clave, t in tenants.items():
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                "VALUES (:t, :n, :t, :t, 'mediana')"
            ), {"t": t, "n": f"Organización {clave.upper()}"})
        for uid in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.test"})
        for clave in ("a", "b", "c"):
            await _insertar_rol(s, tenants[clave], usuarios[f"admin_{clave}"], "admin_organizacion")
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
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "factory": factory, "t": tenants, "u": usuarios, "creados": creados}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            for t in [*tenants.values(), *creados["tenants"]]:
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM invitaciones_organizacion WHERE tenant_id = :t",
                    "DELETE FROM auditoria_plataforma WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            for operador in creados["operadores"]:
                await s.execute(text("DELETE FROM auditoria_plataforma WHERE actor_id = :o"), {"o": operador})
                await s.execute(text("DELETE FROM operadores_plataforma WHERE id = :o"), {"o": operador})
            await s.execute(text("DELETE FROM users WHERE id LIKE :p"), {"p": f"org13-%-{sufijo}"})
            await s.commit()
        await engine.dispose()


async def _insertar_rol(session, tenant: str, usuario: str, rol: str, caducado: bool = False) -> None:
    """Inserción directa en la base (como dueño): el disparador también la vigila."""
    await fijar_contexto_rls(session, tenant)
    sentencia = (
        "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role, valid_to) "
        "VALUES (:i, :u, :t, :r, now() - interval '1 day')"
        if caducado
        else "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"
    )
    await session.execute(text(sentencia), {"i": str(uuid.uuid4()), "u": usuario, "t": tenant, "r": rol})


def _como_admin(ctx, clave: str) -> dict[str, str]:
    return {"X-User-ID": ctx["u"][f"admin_{clave}"], "X-Tenant-ID": ctx["t"][clave], "X-Role": "admin_organizacion"}


async def _conceder(ctx, clave: str, rol: str, usuario: str = "persona"):
    return await ctx["client"].post(
        ROLES, headers=_como_admin(ctx, clave), json={"user_id": ctx["u"][usuario], "role": rol}
    )


async def _roles_vigentes(ctx, clave: str, usuario: str = "persona") -> list[str]:
    async with ctx["factory"]() as s:
        filas = await s.execute(text(
            "SELECT role FROM user_tenant_roles WHERE tenant_id = :t AND user_id = :u "
            "AND (valid_to IS NULL OR valid_to > now())"
        ), {"t": ctx["t"][clave], "u": ctx["u"][usuario]})
        return [f[0] for f in filas]


@pytest.mark.asyncio
@pytest.mark.parametrize("rol_a, rol_b", [("dpo", "dpo"), ("dpo", "implementador"), ("implementador", "implementador")])
async def test_dpo_e_implementador_se_comparten_entre_organizaciones(ctx, rol_a, rol_b):
    assert (await _conceder(ctx, "a", rol_a)).status_code == 201
    r = await _conceder(ctx, "b", rol_b)
    assert r.status_code == 201, r.text
    assert await _roles_vigentes(ctx, "b") == [rol_b]


@pytest.mark.asyncio
@pytest.mark.parametrize("rol_a, rol_b", [
    ("coordinador", "dpo"),
    ("coordinador", "implementador"),
    ("admin_organizacion", "dpo"),
    ("responsable_area", "implementador"),
    ("dpo", "coordinador"),
    ("implementador", "admin_organizacion"),
    ("dpo", "responsable_area"),
])
async def test_un_rol_no_compartible_impide_estar_en_otra_organizacion(ctx, rol_a, rol_b):
    assert (await _conceder(ctx, "a", rol_a)).status_code == 201
    r = await _conceder(ctx, "b", rol_b)
    assert r.status_code == 409, r.text
    assert MENSAJE in r.json()["detail"]
    assert await _roles_vigentes(ctx, "b") == []


@pytest.mark.asyncio
async def test_un_rol_caducado_no_impide_asignar_en_otra(ctx):
    async with ctx["factory"]() as s:
        await _insertar_rol(s, ctx["t"]["a"], ctx["u"]["persona"], "coordinador", caducado=True)
        await s.commit()
    assert (await _conceder(ctx, "b", "coordinador")).status_code == 201


@pytest.mark.asyncio
async def test_la_regla_se_cumple_aunque_se_inserte_directo_como_lopdp_app(ctx):
    assert (await _conceder(ctx, "a", "dpo")).status_code == 201
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["t"]["b"])
        with pytest.raises(DBAPIError) as error:
            await s.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, 'coordinador')"
            ), {"i": str(uuid.uuid4()), "u": ctx["u"]["persona"], "t": ctx["t"]["b"]})
        assert error.value.orig.sqlstate == "23514"
        assert "ORGANIZACION_EXCLUSIVA" in str(error.value.orig)


@pytest.mark.asyncio
async def test_mis_organizaciones_lista_solo_las_propias_con_roles_vigentes(ctx):
    assert (await _conceder(ctx, "a", "dpo")).status_code == 201
    assert (await _conceder(ctx, "b", "implementador")).status_code == 201
    async with ctx["factory"]() as s:
        await _insertar_rol(s, ctx["t"]["c"], ctx["u"]["persona"], "dpo", caducado=True)
        await s.commit()
    assert (await _conceder(ctx, "c", "coordinador", usuario="otra")).status_code == 201

    # Sin cabecera de organización ni de rol: la identidad basta.
    r = await ctx["client"].get(MIS_ORGANIZACIONES, headers={"X-User-ID": ctx["u"]["persona"]})
    assert r.status_code == 200, r.text
    assert r.json()["organizaciones"] == [
        {"tenant_id": ctx["t"]["a"], "nombre_comercial": "Organización A", "roles": ["dpo"]},
        {"tenant_id": ctx["t"]["b"], "nombre_comercial": "Organización B", "roles": ["implementador"]},
    ]
    otra = (await ctx["client"].get(MIS_ORGANIZACIONES, headers={"X-User-ID": ctx["u"]["otra"]})).json()
    assert otra["organizaciones"] == [
        {"tenant_id": ctx["t"]["c"], "nombre_comercial": "Organización C", "roles": ["coordinador"]},
    ]


@pytest.mark.asyncio
async def test_la_rls_de_las_asignaciones_queda_intacta(ctx):
    assert (await _conceder(ctx, "b", "dpo")).status_code == 201
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, ctx["t"]["a"])
        visibles = (await s.execute(
            text("SELECT count(*) FROM user_tenant_roles WHERE tenant_id = :t"), {"t": ctx["t"]["b"]}
        )).scalar_one()
    assert visibles == 0


@pytest.mark.asyncio
async def test_aceptar_una_invitacion_respeta_la_regla(ctx):
    assert (await _conceder(ctx, "a", "coordinador")).status_code == 201
    operador = f"org13-op-{uuid.uuid4().hex[:8]}"
    correo_operador = f"{operador}@example.test"
    async with ctx["factory"]() as s:
        await s.execute(text(
            "INSERT INTO operadores_plataforma (id, email, nombre, activo, created_at, updated_at) "
            "VALUES (:id, :e, 'Operador ORG-13', TRUE, NOW(), NOW())"
        ), {"id": operador, "e": correo_operador})
        await s.commit()
    ctx["creados"]["operadores"].append(operador)

    correo_persona = f"{ctx['u']['persona']}@example.test"
    alta = await ctx["client"].post(
        "/api/v1/plataforma/organizaciones",
        json={
            "nombre_comercial": "Organización D",
            "razon_social": "Organización D S.A.",
            "ruc_identificacion": f"17{uuid.uuid4().int % 10000000000:010d}001",
            "tamano": "mediana",
            "email_admin_inicial": correo_persona,
        },
        headers={"X-User-Email": correo_operador, "X-User-ID": "sub-operador-org13"},
    )
    assert alta.status_code in (200, 201), alta.text
    ctx["creados"]["tenants"].append(alta.json()["tenant_id"])

    r = await ctx["client"].post(
        "/api/v1/plataforma/invitaciones/aceptar",
        json={"codigo": alta.json()["codigo_invitacion"]},
        headers={"X-User-Email": correo_persona, "X-User-ID": "sub-persona-org13"},
    )
    assert r.status_code == 409, r.text
    assert MENSAJE in r.json()["detail"]
    async with ctx["factory"]() as s:
        estado = (await s.execute(
            text("SELECT estado FROM invitaciones_organizacion WHERE tenant_id = :t"), {"t": alta.json()["tenant_id"]}
        )).scalar_one()
    assert estado == "emitida"
