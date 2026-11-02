"""Árbitro FIRMA-03 contra TEST_DATABASE_URL (rama Neon de pruebas de la persona, nunca producción).

Persistencia de `firma_sessions` y compuerta async: alta en borrador, cierre como firmado, RLS entre
organizaciones con el rol `lopdp_app`, evento de auditoría, listado por estado y compatibilidad de
los bocetos de FIRMA-01.
"""
# ¤¤backend-developer
# ¤firma-electronica
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import async_sessionmaker

pytestmark = pytest.mark.asyncio

SHA = "a" * 64
SHA_FIRMADO = "b" * 64
CERTIFICADO = {"emisor": "ANF AC Ecuador", "numero_serie": "SERIE-TEST-001", "acreditado_arcotel": True}


@pytest_asyncio.fixture
async def firma_env(db_engine):
    from app_core.db.session import fijar_contexto_rls

    url = os.environ.get("TEST_DATABASE_URL", "")
    assert url and "ep-late-hall-b50bpbk5" not in url, "Se requiere una rama de desarrollo"

    factory = async_sessionmaker(db_engine, expire_on_commit=False)
    ta, tb = str(uuid4()), str(uuid4())
    try:
        async with factory() as s:
            for tenant in (ta, tb):
                await s.execute(
                    text(
                        "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                        "VALUES (:t, :t, :t, :t)"
                    ),
                    {"t": tenant},
                )
            await s.commit()
        yield {"factory": factory, "a": ta, "b": tb}
    finally:
        async with factory() as s:
            for tenant in (ta, tb):
                await fijar_contexto_rls(s, tenant)
                await s.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": tenant})
                await s.execute(
                    text("DELETE FROM firma_sessions WHERE tenant_id = CAST(:t AS uuid)"), {"t": tenant}
                )
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant})
            await s.commit()


@asynccontextmanager
async def _db(env, tenant):
    """Sesión con el rol restringido de la aplicación y el tenant fijado; confirma al salir."""
    from app_core.db.session import fijar_contexto_rls

    async with env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, tenant)
        yield s
        await s.commit()


async def _crear(env, tenant=None, documento_id=None):
    from features.firma_electronica import firma_electronica_service as firma

    tenant = tenant or env["a"]
    async with _db(env, tenant) as s:
        return await firma.crear_sesion_firma(
            s, tenant, documento_id or f"doc-{uuid4().hex[:8]}", "1710034065", "PAdES-B-LTV", "ANF", SHA
        )


async def test_crear_sesion_persiste(firma_env):
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    creada = await _crear(env, documento_id="doc-acta-1")
    assert creada.estado == "borrador"

    async with _db(env, env["a"]) as s:  # sesión nueva: la fila viene de la base
        leida = await firma.obtener_sesion(s, creada.firma_id, env["a"])
    assert leida is not None
    assert leida == creada
    assert (leida.documento_id, leida.firmante_id, leida.formato, leida.proveedor) == (
        "doc-acta-1", "1710034065", "PAdES-B-LTV", "ANF",
    )
    assert leida.sha256_original == SHA and leida.sha256_firmado is None
    assert leida.timestamp_tsa is None and leida.certificado_json is None and leida.metadatos == {}


async def test_marcar_firmado(firma_env):
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    creada = await _crear(env)
    momento = datetime(2026, 11, 3, 15, 30, tzinfo=timezone.utc)
    async with _db(env, env["a"]) as s:
        firmada = await firma.marcar_firmado(s, creada.firma_id, env["a"], SHA_FIRMADO, CERTIFICADO, momento)
    assert firmada.estado == "firmado"

    async with _db(env, env["a"]) as s:
        leida = await firma.obtener_sesion(s, creada.firma_id, env["a"])
    assert leida.estado == "firmado"
    assert leida.sha256_firmado == SHA_FIRMADO
    assert leida.timestamp_tsa == momento
    assert leida.certificado_json == CERTIFICADO
    assert leida.sha256_original == SHA and leida.actualizado_en >= leida.creado_en

    # Una sesión firmada no vuelve a firmarse, y una inexistente se distingue de una ya cerrada.
    async with _db(env, env["a"]) as s:
        with pytest.raises(firma.TransicionFirmaInvalidaError):
            await firma.marcar_firmado(s, creada.firma_id, env["a"], SHA_FIRMADO, CERTIFICADO, momento)
    async with _db(env, env["a"]) as s:
        with pytest.raises(firma.SesionFirmaNoEncontradaError):
            await firma.marcar_firmado(s, uuid4(), env["a"], SHA_FIRMADO, CERTIFICADO, momento)


async def test_rls_aislamiento(firma_env):
    from app_core.db.session import fijar_contexto_rls
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    de_a = await _crear(env, env["a"])

    # Tenant B no ve la sesión de A: ni pidiéndola como suya, ni pidiéndola como de A.
    async with _db(env, env["b"]) as s:
        assert await firma.obtener_sesion(s, de_a.firma_id, env["b"]) is None
        assert await firma.obtener_sesion(s, de_a.firma_id, env["a"]) is None
        assert await firma.listar_sesiones(s, env["a"]) == []
        assert await firma.listar_sesiones(s, env["b"]) == []
    async with _db(env, env["a"]) as s:
        assert [x.firma_id for x in await firma.listar_sesiones(s, env["a"])] == [de_a.firma_id]

    async with env["factory"]() as s:
        estado = (
            await s.execute(
                text("SELECT relrowsecurity, relforcerowsecurity FROM pg_class WHERE oid = 'firma_sessions'::regclass")
            )
        ).one()
        assert estado.relrowsecurity and estado.relforcerowsecurity
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        rol = (await s.execute(text("SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname = current_user"))).one()
        assert not rol.rolbypassrls and not rol.rolsuper
        # Sin tenant fijado no se ve ninguna fila.
        await s.execute(text("SELECT set_config('app.current_tenant_id', '', true)"))
        assert (await s.execute(text("SELECT count(*) FROM firma_sessions"))).scalar_one() == 0

    # WITH CHECK: con el tenant B fijado no se puede insertar una fila de A.
    async with env["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, env["b"])
        with pytest.raises(DBAPIError) as exc:
            await s.execute(
                text(
                    "INSERT INTO firma_sessions (tenant_id, documento_id, firmante_id, estado, formato, "
                    "proveedor, sha256_original) VALUES (CAST(:t AS uuid), 'd', 'f', 'borrador', 'PAdES-BES', 'ANF', :h)"
                ),
                {"t": env["a"], "h": SHA},
            )
        assert exc.value.orig.sqlstate == "42501"

    # Los datos del documento no se reescriben y la sesión no se borra: lo impide la base.
    for sentencia in (
        "UPDATE firma_sessions SET sha256_original = 'x' WHERE firma_id = CAST(:id AS uuid)",
        "DELETE FROM firma_sessions WHERE firma_id = CAST(:id AS uuid)",
    ):
        async with env["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, env["a"])
            with pytest.raises(DBAPIError) as exc:
                await s.execute(text(sentencia), {"id": str(de_a.firma_id)})
            assert exc.value.orig.sqlstate == "42501", sentencia


async def test_audit_event_creado(firma_env):
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    creada = await _crear(env)
    consulta = text(
        "SELECT action, entity_type, payload FROM audit_events WHERE entity_id = :id ORDER BY timestamp, action"
    )
    async with _db(env, env["a"]) as s:
        eventos = (await s.execute(consulta, {"id": str(creada.firma_id)})).all()
    assert len(eventos) == 1
    assert eventos[0].entity_type == "firma_session"
    assert eventos[0].action == "crear_sesion_firma"
    assert eventos[0].payload["sha256_original"] == SHA

    # Al firmar se añade un segundo evento de la misma entidad.
    async with _db(env, env["a"]) as s:
        await firma.marcar_firmado(
            s, creada.firma_id, env["a"], SHA_FIRMADO, CERTIFICADO, datetime.now(timezone.utc)
        )
    async with _db(env, env["a"]) as s:
        eventos = (await s.execute(consulta, {"id": str(creada.firma_id)})).all()
    assert sorted(e.action for e in eventos) == ["crear_sesion_firma", "marcar_firmado"]
    assert {e.entity_type for e in eventos} == {"firma_session"}


async def test_listar_por_estado(firma_env):
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    sesiones = [await _crear(env) for _ in range(3)]
    ahora = datetime.now(timezone.utc)
    async with _db(env, env["a"]) as s:
        for sesion in sesiones[:2]:
            await firma.marcar_firmado(s, sesion.firma_id, env["a"], SHA_FIRMADO, CERTIFICADO, ahora)

    async with _db(env, env["a"]) as s:
        firmadas = await firma.listar_sesiones(s, env["a"], estado="firmado")
        borradores = await firma.listar_sesiones(s, env["a"], estado="borrador")
        todas = await firma.listar_sesiones(s, env["a"])
        limitadas = await firma.listar_sesiones(s, env["a"], limit=1)
        with pytest.raises(ValueError):
            await firma.listar_sesiones(s, env["a"], estado="inventado")
    assert {x.firma_id for x in firmadas} == {sesiones[0].firma_id, sesiones[1].firma_id}
    assert [x.firma_id for x in borradores] == [sesiones[2].firma_id]
    assert len(todas) == 3 and len(limitadas) == 1


async def test_bocetos_compatibles():
    from features.firma_electronica import firma_electronica_service as firma

    doc = firma.DocumentoParaFirma(
        documento_id="doc-1",
        tenant_id="t-1",
        nombre_archivo="acta.pdf",
        mime_type="application/pdf",
        sha256_original=SHA,
        tamano_bytes=1024,
    )
    resultado = firma.boceto_firmar_documento_anf(doc, "1710034065")
    assert isinstance(resultado, firma.ResultadoFirma)
    assert resultado.estado == firma.EstadoFirma.FIRMADO
    for nombre in (
        "boceto_firmar_documento_anf",
        "boceto_iniciar_sesion_pasarela",
        "boceto_verificar_webhook_pasarela",
        "boceto_verificar_firma_anf",
        "boceto_verificar_firma",
        "crear_sesion_firma",
        "obtener_sesion",
        "marcar_firmado",
        "listar_sesiones",
    ):
        assert callable(getattr(firma, nombre)) and nombre in firma.__all__, nombre
