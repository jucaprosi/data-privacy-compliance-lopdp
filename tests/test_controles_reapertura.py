# ¤controles-periodicos ¤evidencias-vigencia ¤hallazgos ¤rbac-tenant ¤arbitro
"""CAPA-03: la evidencia vencida reabre el control periódico y produce un hallazgo.

Contrato: governance/tareas/CAPA-03.md. Las pruebas puras corren sin base; el resto recorre un
PostgreSQL 16 local en contenedor (nunca producción), con la reapertura ejecutada como `lopdp_app`
para que RLS se evalúe como en la aplicación; sin TEST_DATABASE_URL se omiten.

Prueba de mutación ejecutada el 2026-11-13 contra el contenedor local capa03-pg16:
- En features/auditoria_capa/services/reapertura_engine.py se sustituyó la lectura de la vigencia por la
  compuerta de `evidencias` por una fecha guardada en `auditoria_capa` (la `proxima_verificacion` del
  control como si fuera el vencimiento de la evidencia). pytest tests/test_controles_reapertura.py
  devolvió 1: fallaron test_evidencia_vencida_reabre_y_un_hallazgo, test_evidencia_nueva_devuelve_a_vigente
  y test_renovar_el_documento_restablece (el control con fecha futura no se reabría).
- Se restauró el motor; sin la mutación las pruebas pasan.
"""
import hashlib
import os
import uuid
from datetime import date, timedelta
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if _TEST_URL:
    os.environ["DATABASE_URL"] = _TEST_URL
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from features.auditoria_capa.domain.control_periodico import hoy_guayaquil  # noqa: E402
from features.auditoria_capa.services.reapertura_engine import (  # noqa: E402
    clave_evidencia_vencida,
    evidencia_vencida,
)

RAIZ = Path(__file__).resolve().parents[1]
CONTROLES = "/api/v1/auditoria-capa/controles"
HALLAZGOS = "/api/v1/roadmaps/hallazgos"


# --- Pruebas puras --------------------------------------------------------------------------------


def test_vencida_solo_si_hay_documento_y_paso_la_fecha():
    hoy = date(2026, 11, 13)
    h = "a" * 64
    assert evidencia_vencida({h: date(2026, 11, 12)}, h, hoy) == date(2026, 11, 12)
    assert evidencia_vencida({h: hoy}, h, hoy) is None, "el día del vencimiento sigue vigente (EVI-02)"
    assert evidencia_vencida({h: None}, h, hoy) is None
    assert evidencia_vencida({}, h, hoy) is None
    assert evidencia_vencida({h: date(2020, 1, 1)}, None, hoy) is None


def test_clave_cabe_en_origen_ref():
    from features.roadmap.roadmap_service import ORIGEN_REF_MAX

    clave = clave_evidencia_vencida(str(uuid.uuid4()), "f" * 64, date(2026, 11, 12))
    assert len(clave) <= ORIGEN_REF_MAX and clave.endswith(":2026-11-12")


def test_auditoria_capa_no_guarda_vigencias():
    """Fuente única: la sala no lee tablas de evidencias ni guarda un vencimiento propio."""
    infractores = [
        p.relative_to(RAIZ).as_posix()
        for p in (RAIZ / "features" / "auditoria_capa").rglob("*.py")
        if any(t in p.read_text(encoding="utf-8-sig") for t in ("evidencias_atributos", "vence_en", "features.evidencias"))
    ]
    assert not infractores, f"auditoria_capa lee vigencias por su cuenta: {infractores}"


# --- Recorrido contra PostgreSQL ------------------------------------------------------------------


def _h(usuario: tuple[str, str, str]) -> dict[str, str]:
    uid, tenant, rol = usuario
    return {"X-User-ID": uid, "X-Tenant-ID": tenant, "X-Role": rol}


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una base de pruebas (nunca producción)"
    monkeypatch.setenv("AUTH_MODE", "headers")
    from app_core.db.session import fijar_contexto_rls, get_session
    from features.evidencias import evidencias_service
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = (f"capa03-{x}-{sufijo}" for x in "ab")
    usuarios = {
        "dpo": (f"capa03-dpo-{sufijo}", a, "dpo"),
        "impl": (f"capa03-impl-{sufijo}", a, "implementador"),
        "resp": (f"capa03-resp-{sufijo}", a, "responsable_area"),
        "impl_b": (f"capa03-implb-{sufijo}", b, "implementador"),
    }
    async with factory() as s:
        for tenant in (a, b):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, tamano) "
                "VALUES (:t, :t, :t, :t, 'mediana')"
            ), {"t": tenant})
        for uid, tenant, rol in usuarios.values():
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :u)"),
                            {"u": uid, "e": f"{uid}@example.test"})
            await fijar_contexto_rls(s, tenant, uid)
            await s.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"
            ), {"i": str(uuid.uuid4()), "u": uid, "t": tenant, "r": rol})
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
    evidencias_service.reiniciar_repositorio_evidencias()
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "factory": factory, "a": a, "b": b, "u": usuarios}
    finally:
        app.dependency_overrides.clear()
        evidencias_service.reiniciar_repositorio_evidencias()
        async with factory() as s:
            for t in (a, b):
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM verificaciones_control WHERE tenant_id = :t",
                    "DELETE FROM controles_periodicos WHERE tenant_id = :t",
                    "DELETE FROM hallazgos WHERE tenant_id = :t",
                    "DELETE FROM evidencias_atributos WHERE tenant_id = :t",
                    "DELETE FROM evidencias_documentos WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
            for uid, _, _ in usuarios.values():
                await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
            for t in (a, b):
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.commit()
        await engine.dispose()


async def _documento(ctx, contenido: bytes, vence_en, tenant_clave: str = "a") -> str:
    """Documento registrado en la sala Evidencias, con su vencimiento (EVI-01/EVI-02) y su huella en el registro."""
    from app_core.db.session import fijar_contexto_rls
    from features.evidencias import evidencias_service

    tenant = ctx[tenant_clave]
    huella = hashlib.sha256(contenido).hexdigest()
    documento_id = str(uuid.uuid4())
    dpo = ctx["u"]["dpo"][0]
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, tenant, dpo)
        await s.execute(text(
            "INSERT INTO evidencias_documentos (id, tenant_id, codigo, nombre_archivo, tipo_mime, tamano_bytes, "
            "sha256, normativa, clave_almacen, subido_por, retencion_dias) VALUES (:id, :t, :c, 'acta.pdf', "
            "'application/pdf', :n, :h, 'LOPDP', :k, :u, 365)"
        ), {"id": documento_id, "t": tenant, "c": f"EVD-{uuid.uuid4().hex[:8]}", "n": len(contenido), "h": huella,
            "k": f"capa03/{documento_id}", "u": dpo})
        await s.execute(text(
            "INSERT INTO evidencias_atributos (documento_id, tenant_id, vence_en, actualizado_por) "
            "VALUES (:d, :t, :v, :u)"
        ), {"d": documento_id, "t": tenant, "v": vence_en, "u": dpo})
        await s.commit()
    evidencias_service.registrar_evidencia_deduplicada(evidencias_service.EvidenciaRegistro(
        tenant_id=tenant, codigo=f"EVD-2026-{uuid.uuid4().hex[:4]}", nombre_archivo="acta.pdf", sha256_hash=huella,
    ))
    return huella


async def _vencer_documento(ctx, huella: str, vence_en) -> None:
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, ctx["a"])
        await s.execute(text(
            "UPDATE evidencias_atributos SET vence_en = :v WHERE tenant_id = :t AND documento_id IN "
            "(SELECT id FROM evidencias_documentos WHERE tenant_id = :t AND sha256 = :h)"
        ), {"v": vence_en, "t": ctx["a"], "h": huella})
        await s.commit()


async def _control(ctx, huella, proxima: date, usuario: str = "impl") -> dict:
    u = ctx["u"][usuario]
    r = await ctx["client"].post(CONTROLES, headers=_h(u), json={
        "nombre": "Revisión de accesos", "frecuencia": "anual", "control_ref": "P12",
        "responsable_user_id": u[0], "proxima_verificacion": proxima.isoformat(),
    })
    assert r.status_code == 201, r.text
    control = r.json()
    if huella is not None:
        await _verificar(ctx, control["id"], huella, usuario)
    return control


async def _verificar(ctx, control_id: str, huella: str, usuario: str = "impl") -> None:
    r = await ctx["client"].post(
        f"{CONTROLES}/{control_id}/verificaciones", headers=_h(ctx["u"][usuario]), json={"evidencia_sha256": huella}
    )
    assert r.status_code == 201, r.text


async def _reabrir(ctx, tenant_clave: str = "a", usuario: str = "impl") -> dict:
    """La reapertura por el pasillo de la sala, como la vería la aplicación (rol lopdp_app, RLS forzada)."""
    from app_core.pasillo import auditoria_capa

    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        resultado = await auditoria_capa.reabrir_controles_por_evidencia_vencida(
            s, ctx[tenant_clave], ctx["u"][usuario][0]
        )
        await s.commit()
    return resultado


async def _estado(ctx, usuario: str = "impl") -> list[dict]:
    r = await ctx["client"].get(CONTROLES, headers=_h(ctx["u"][usuario]))
    assert r.status_code == 200, r.text
    return r.json()["controles"]


async def _hallazgos(ctx, usuario: str = "impl") -> list[dict]:
    r = await ctx["client"].get(f"{HALLAZGOS}?origen=control_periodico", headers=_h(ctx["u"][usuario]))
    assert r.status_code == 200, r.text
    return r.json()["hallazgos"]


def _futuro(dias: int = 200) -> date:
    return hoy_guayaquil() + timedelta(days=dias)


@pytest.mark.asyncio
async def test_evidencia_vencida_reabre_y_un_hallazgo(ctx):
    huella = await _documento(ctx, b"acta vigente hoy", _futuro(30))
    control = await _control(ctx, huella, _futuro())
    assert await _reabrir(ctx) == {"reabiertos": 0, "hallazgos_creados": 0, "restablecidos": 0}

    ayer = hoy_guayaquil() - timedelta(days=1)
    await _vencer_documento(ctx, huella, ayer)
    assert await _reabrir(ctx) == {"reabiertos": 1, "hallazgos_creados": 1, "restablecidos": 0}
    assert await _reabrir(ctx) == {"reabiertos": 0, "hallazgos_creados": 0, "restablecidos": 0}

    hallazgos = await _hallazgos(ctx)
    assert len(hallazgos) == 1, "exactamente un hallazgo"
    h = hallazgos[0]
    assert h["origen_ref"] == clave_evidencia_vencida(control["id"], huella, ayer)
    assert h["estado"] == "abierto" and h["control_ref"] == "P12" and h["severidad"] == "alta"
    [c] = await _estado(ctx)
    assert c["estado"] == "vencido" and c["hallazgo_vigente_id"] == h["id"]


@pytest.mark.asyncio
async def test_evidencia_nueva_devuelve_a_vigente(ctx):
    vieja = await _documento(ctx, b"acta vieja", _futuro(30))
    control = await _control(ctx, vieja, _futuro())
    await _vencer_documento(ctx, vieja, hoy_guayaquil() - timedelta(days=3))
    assert (await _reabrir(ctx))["reabiertos"] == 1

    nueva = await _documento(ctx, b"acta nueva", _futuro(90))
    await _verificar(ctx, control["id"], nueva)
    [c] = await _estado(ctx)
    assert c["estado"] == "vigente" and c["hallazgo_vigente_id"] is None
    assert [h["estado"] for h in await _hallazgos(ctx)] == ["cerrado"]
    assert await _reabrir(ctx) == {"reabiertos": 0, "hallazgos_creados": 0, "restablecidos": 0}


@pytest.mark.asyncio
async def test_renovar_el_documento_restablece(ctx):
    huella = await _documento(ctx, b"acta renovable", _futuro(30))
    await _control(ctx, huella, _futuro())
    await _vencer_documento(ctx, huella, hoy_guayaquil() - timedelta(days=1))
    await _reabrir(ctx)

    await _vencer_documento(ctx, huella, _futuro(365))
    assert await _reabrir(ctx) == {"reabiertos": 0, "hallazgos_creados": 0, "restablecidos": 1}
    [c] = await _estado(ctx)
    assert c["estado"] == "vigente" and c["hallazgo_vigente_id"] is None
    assert [h["estado"] for h in await _hallazgos(ctx)] == ["cerrado"]


@pytest.mark.asyncio
async def test_sin_vigencia_conocida_no_reabre(ctx):
    await _control(ctx, None, _futuro())
    from features.evidencias import evidencias_service

    solo_registro = hashlib.sha256(b"sin documento").hexdigest()
    evidencias_service.registrar_evidencia_deduplicada(evidencias_service.EvidenciaRegistro(
        tenant_id=ctx["a"], codigo="EVD-2026-sd01", nombre_archivo="x.pdf", sha256_hash=solo_registro,
    ))
    await _control(ctx, solo_registro, _futuro())
    sin_vencimiento = await _documento(ctx, b"acta sin vencimiento", None)
    await _control(ctx, sin_vencimiento, _futuro())
    assert await _reabrir(ctx) == {"reabiertos": 0, "hallazgos_creados": 0, "restablecidos": 0}
    assert await _hallazgos(ctx) == []


@pytest.mark.asyncio
async def test_vencido_por_fecha_no_se_restablece_por_evidencia(ctx):
    huella = await _documento(ctx, b"acta de control atrasado", _futuro(30))
    control = await _control(ctx, huella, _futuro())
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:  # simula que su fecha periódica pasó y CAPA-02 lo venció
        await fijar_contexto_rls(s, ctx["a"])
        await s.execute(text(
            "UPDATE controles_periodicos SET estado = 'vencido', proxima_verificacion = :d WHERE id = :id"
        ), {"d": hoy_guayaquil() - timedelta(days=2), "id": control["id"]})
        await s.commit()
    assert await _reabrir(ctx) == {"reabiertos": 0, "hallazgos_creados": 0, "restablecidos": 0}
    assert (await _estado(ctx))[0]["estado"] == "vencido"


@pytest.mark.asyncio
async def test_otra_organizacion_no_se_toca(ctx):
    huella = await _documento(ctx, b"acta de a", _futuro(30))
    await _control(ctx, huella, _futuro())
    await _vencer_documento(ctx, huella, hoy_guayaquil() - timedelta(days=1))
    assert await _reabrir(ctx, "b", "impl_b") == {"reabiertos": 0, "hallazgos_creados": 0, "restablecidos": 0}
    assert (await _estado(ctx))[0]["estado"] == "vigente"
