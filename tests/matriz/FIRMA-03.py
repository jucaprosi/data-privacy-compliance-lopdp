# -*- coding: utf-8 -*-
"""FIRMA-05 · Matriz de aceptación de FIRMA-03: persistencia de `firma_sessions` (10 casos, F03-01..F03-10).

Se ejecuta por ruta (`pytest tests/matriz/FIRMA-03.py -v`) contra TEST_DATABASE_URL, la rama Neon de
pruebas de la persona (nunca producción). Cada caso crea sus propias organizaciones con UUID únicos,
usa el rol restringido `lopdp_app` con el tenant fijado, y limpia lo que crea; no depende del orden.

`tests/test_matriz_permisos.py` carga todos los `tests/matriz/*.py` y exige `FILAS`: esta tarea no
añade endpoints, así que la lista va vacía.

Contrato real de FIRMA-03 (el que fija el engine): la sesión nace en `borrador`; los eventos de
auditoría se llaman `crear_sesion_firma` y `marcar_firmado`; `obtener_sesion` y `marcar_firmado`
reciben `(db, firma_id, tenant_id, ...)`.
"""
# ¤¤qa-engineer
# ¤firma-electronica ¤arbitro
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

FILAS: list[tuple[str, str, str, set[str]]] = []

pytestmark = pytest.mark.asyncio

SHA = "a" * 64
SHA_FIRMADO = "b" * 64
CERTIFICADO = {"emisor": "ANF AC Ecuador", "numero_serie": "SERIE-F05-001", "acreditado_arcotel": True}
MOMENTO_TSA = datetime(2026, 11, 3, 15, 30, tzinfo=timezone.utc)


@pytest_asyncio.fixture
async def firma_env(db_engine):
    """Dos organizaciones UUID nuevas; al terminar borra auditoría, sesiones y organizaciones."""
    from app_core.db.session import fijar_contexto_rls

    url = os.environ.get("TEST_DATABASE_URL", "")
    assert url and "ep-late-hall" not in url, "Se requiere la rama de pruebas de la persona, nunca producción"

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


async def _crear(env, tenant=None, documento_id=None, firmante="1710034065"):
    from features.firma_electronica import firma_electronica_service as firma

    tenant = tenant or env["a"]
    async with _db(env, tenant) as s:
        return await firma.crear_sesion_firma(
            s, tenant, documento_id or f"doc-{uuid4().hex[:8]}", firmante, "PAdES-B-LTV", "ANF", SHA
        )


async def _firmar(env, sesion, tenant=None):
    from features.firma_electronica import firma_electronica_service as firma

    tenant = tenant or env["a"]
    async with _db(env, tenant) as s:
        return await firma.marcar_firmado(s, sesion.firma_id, tenant, SHA_FIRMADO, CERTIFICADO, MOMENTO_TSA)


async def _eventos(env, tenant, entidad_id):
    consulta = text(
        "SELECT action, entity_type, payload FROM audit_events WHERE entity_id = :id ORDER BY action"
    )
    async with _db(env, tenant) as s:
        return (await s.execute(consulta, {"id": str(entidad_id)})).all()


async def test_crear_sesion_persiste(firma_env):
    """F03-01 · crear_sesion_firma → obtener_sesion devuelve la misma fila, en estado borrador."""
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    creada = await _crear(env)
    assert creada.estado == "borrador"
    async with _db(env, env["a"]) as s:  # sesión de BD nueva: la fila viene de la base
        leida = await firma.obtener_sesion(s, creada.firma_id, env["a"])
    assert leida is not None and leida == creada and leida.estado == "borrador"


async def test_crear_sesion_campos_completos(firma_env):
    """F03-02 · Todos los campos obligatorios quedan guardados correctamente."""
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    creada = await _crear(env, documento_id="doc-acta-f02", firmante="1700000001")
    async with _db(env, env["a"]) as s:
        leida = await firma.obtener_sesion(s, creada.firma_id, env["a"])
    assert isinstance(leida.firma_id, UUID) and str(leida.tenant_id) == env["a"]
    assert (leida.documento_id, leida.firmante_id) == ("doc-acta-f02", "1700000001")
    assert (leida.formato, leida.proveedor, leida.sha256_original) == ("PAdES-B-LTV", "ANF", SHA)
    assert leida.sha256_firmado is None and leida.timestamp_tsa is None and leida.certificado_json is None
    assert leida.metadatos == {}
    assert leida.creado_en is not None and leida.actualizado_en is not None


async def test_marcar_firmado_actualiza_estado(firma_env):
    """F03-03 · marcar_firmado → estado firmado, con sha256_firmado y timestamp_tsa persistidos."""
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    creada = await _crear(env)
    firmada = await _firmar(env, creada)
    assert firmada.estado == "firmado"
    async with _db(env, env["a"]) as s:
        leida = await firma.obtener_sesion(s, creada.firma_id, env["a"])
    assert leida.estado == "firmado"
    assert leida.sha256_firmado == SHA_FIRMADO and leida.timestamp_tsa == MOMENTO_TSA
    assert leida.certificado_json == CERTIFICADO and leida.sha256_original == SHA
    # Se cierra una sola vez.
    with pytest.raises(firma.TransicionFirmaInvalidaError):
        await _firmar(env, creada)


async def test_rls_tenant_a_no_ve_tenant_b(firma_env):
    """F03-04 · Sesión de la organización A: la organización B recibe None, la pida como la pida."""
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    de_a = await _crear(env, env["a"])
    async with _db(env, env["b"]) as s:
        assert await firma.obtener_sesion(s, de_a.firma_id, env["b"]) is None
        assert await firma.obtener_sesion(s, de_a.firma_id, env["a"]) is None  # RLS aunque pida el tenant ajeno
    async with _db(env, env["a"]) as s:
        assert (await firma.obtener_sesion(s, de_a.firma_id, env["a"])).firma_id == de_a.firma_id


async def test_rls_listar_solo_propio_tenant(firma_env):
    """F03-05 · 3 sesiones de A y 2 de B → cada organización lista solo las suyas."""
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    de_a = [await _crear(env, env["a"]) for _ in range(3)]
    de_b = [await _crear(env, env["b"]) for _ in range(2)]
    async with _db(env, env["a"]) as s:
        listadas_a = await firma.listar_sesiones(s, env["a"])
        assert await firma.listar_sesiones(s, env["b"]) == []  # RLS: con el contexto de A no hay filas de B
    async with _db(env, env["b"]) as s:
        listadas_b = await firma.listar_sesiones(s, env["b"])
    assert len(listadas_a) == 3 and {x.firma_id for x in listadas_a} == {x.firma_id for x in de_a}
    assert len(listadas_b) == 2 and {x.firma_id for x in listadas_b} == {x.firma_id for x in de_b}


async def test_audit_event_al_crear(firma_env):
    """F03-06 · Crear deja exactamente un evento: entity_type firma_session, action crear_sesion_firma."""
    env = firma_env
    creada = await _crear(env)
    eventos = await _eventos(env, env["a"], creada.firma_id)
    assert len(eventos) == 1
    assert (eventos[0].entity_type, eventos[0].action) == ("firma_session", "crear_sesion_firma")
    assert eventos[0].payload["sha256_original"] == SHA and eventos[0].payload["documento_id"] == creada.documento_id


async def test_audit_event_al_firmar(firma_env):
    """F03-07 · Tras marcar_firmado hay un evento marcar_firmado de la misma entidad."""
    env = firma_env
    creada = await _crear(env)
    await _firmar(env, creada)
    eventos = await _eventos(env, env["a"], creada.firma_id)
    assert sorted(e.action for e in eventos) == ["crear_sesion_firma", "marcar_firmado"]
    firmado = next(e for e in eventos if e.action == "marcar_firmado")
    assert firmado.entity_type == "firma_session" and firmado.payload["sha256_firmado"] == SHA_FIRMADO


async def test_listar_filtro_estado(firma_env):
    """F03-08 · Sesiones firmado, firmado y borrador → listar(estado='firmado') devuelve 2."""
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    sesiones = [await _crear(env) for _ in range(3)]
    for sesion in sesiones[:2]:
        await _firmar(env, sesion)
    async with _db(env, env["a"]) as s:
        firmadas = await firma.listar_sesiones(s, env["a"], estado="firmado")
        borradores = await firma.listar_sesiones(s, env["a"], estado="borrador")
        with pytest.raises(ValueError):
            await firma.listar_sesiones(s, env["a"], estado="inventado")
    assert {x.firma_id for x in firmadas} == {sesiones[0].firma_id, sesiones[1].firma_id}
    assert [x.firma_id for x in borradores] == [sesiones[2].firma_id]


async def test_bocetos_compatibles():
    """F03-09 · Los bocetos de FIRMA-01 siguen devolviendo ResultadoFirma en estado FIRMADO."""
    from features.firma_electronica import firma_electronica_service as firma

    doc = firma.DocumentoParaFirma(
        documento_id="doc-1", tenant_id="t-1", nombre_archivo="acta.pdf", mime_type="application/pdf",
        sha256_original=SHA, tamano_bytes=1024,
    )
    resultado = firma.boceto_firmar_documento_anf(doc, "1710034065")
    assert isinstance(resultado, firma.ResultadoFirma)
    assert resultado.estado == firma.EstadoFirma.FIRMADO
    assert resultado.documento_id == "doc-1" and resultado.sha256_firmado == f"boceto-signed-{SHA}"


async def test_obtener_sesion_inexistente(firma_env):
    """F03-10 · Un UUID aleatorio no existe: obtener_sesion devuelve None (no lanza)."""
    from features.firma_electronica import firma_electronica_service as firma

    env = firma_env
    async with _db(env, env["a"]) as s:
        assert await firma.obtener_sesion(s, uuid4(), env["a"]) is None
