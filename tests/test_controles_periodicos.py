# ¤controles-periodicos ¤hallazgos ¤rbac-tenant ¤arbitro
"""CAPA-02: controles periódicos; el vencido produce un hallazgo y verificarlo lo cierra.

Contrato: governance/especificaciones/CAPA-02.md (§5 Aceptación). Las pruebas puras corren sin base; el
resto recorre PostgreSQL real en una rama Neon de revisión propia (nunca producción); sin
TEST_DATABASE_URL se omiten.

Prueba de mutación ejecutada en la rama Neon efímera test-juan-carlos-capa02 (hija de test-juan-carlos):
- En features/auditoria_capa/services/controles_engine.py, dentro de vencer_controles, se añadió un
  INSERT INTO roadmap_tasks junto al hallazgo. pytest -k "sin_tareas or vencimiento_un_hallazgo" devolvió 1:
  fallaron test_sin_tareas_creadas_desde_auditoria_capa y test_vencimiento_un_hallazgo.
- En registrar_verificacion se desactivó la llamada a roadmap_service.cerrar_hallazgo:
  test_verificacion_cierra_ciclo devolvió 1 (el hallazgo seguía abierto).
- Se restauró el motor; sin las mutaciones las pruebas pasan.
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
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
if _TEST_URL:
    os.environ["DATABASE_URL"] = _TEST_URL
else:
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://sin-base:sin-base@localhost:1/sin-base")

from features.auditoria_capa.domain.control_periodico import (  # noqa: E402
    clave_vencimiento,
    hoy_guayaquil,
    siguiente_verificacion,
    sumar_meses,
)

RAIZ = Path(__file__).resolve().parents[1]
CONTROLES = "/api/v1/auditoria-capa/controles"
VENCER = f"{CONTROLES}/vencer"
HALLAZGOS = "/api/v1/roadmaps/hallazgos"


def _verificaciones(control_id: str) -> str:
    return f"{CONTROLES}/{control_id}/verificaciones"


# --- Pruebas puras --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "inicio,frecuencia,esperada",
    [
        (date(2026, 1, 15), "mensual", date(2026, 2, 15)),
        (date(2026, 1, 31), "mensual", date(2026, 2, 28)),
        (date(2024, 1, 31), "mensual", date(2024, 2, 29)),
        (date(2026, 11, 30), "trimestral", date(2027, 2, 28)),
        (date(2026, 8, 31), "semestral", date(2027, 2, 28)),
        (date(2024, 2, 29), "anual", date(2025, 2, 28)),
        (date(2026, 12, 15), "mensual", date(2027, 1, 15)),
    ],
)
def test_siguiente_fecha_mismo_dia_o_ultimo_del_mes(inicio, frecuencia, esperada):
    assert siguiente_verificacion(inicio, frecuencia) == esperada


def test_sumar_meses_cruza_anios():
    assert sumar_meses(date(2026, 10, 30), 36) == date(2029, 10, 30)


def test_clave_de_vencimiento_cabe_en_origen_ref():
    from features.roadmap.roadmap_service import ORIGEN_REF_MAX

    clave = clave_vencimiento(str(uuid.uuid4()), date(2026, 10, 30))
    assert clave.endswith(":2026-10-30") and len(clave) <= ORIGEN_REF_MAX


def test_sin_tareas_creadas_desde_auditoria_capa():
    """R4: la sala `auditoria_capa` no toca `roadmap_tasks`; el plan único lo escribe `roadmap`."""
    infractores = [
        p.relative_to(RAIZ).as_posix()
        for p in (RAIZ / "features" / "auditoria_capa").rglob("*.py")
        if "roadmap_tasks" in p.read_text(encoding="utf-8-sig").lower()
    ]
    assert not infractores, f"auditoria_capa escribe tareas por su cuenta: {infractores}"


# --- Recorrido contra PostgreSQL ------------------------------------------------------------------


def _h(usuario: tuple[str, str, str]) -> dict[str, str]:
    uid, tenant, rol = usuario
    return {"X-User-ID": uid, "X-Tenant-ID": tenant, "X-Role": rol}


@pytest_asyncio.fixture
async def ctx(monkeypatch):
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    # Rama Neon de revisión propia: nunca producción.
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una rama de revisión (nunca producción)"
    monkeypatch.setenv("AUTH_MODE", "headers")
    from app_core.db.session import fijar_contexto_rls, get_session
    from features.evidencias import evidencias_service
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = (f"capa02-{x}-{sufijo}" for x in "ab")
    usuarios = {
        "dpo": (f"capa02-dpo-{sufijo}", a, "dpo"),
        "impl": (f"capa02-impl-{sufijo}", a, "implementador"),
        "coord": (f"capa02-coord-{sufijo}", a, "coordinador"),
        "admin": (f"capa02-admin-{sufijo}", a, "admin_organizacion"),
        "resp": (f"capa02-resp-{sufijo}", a, "responsable_area"),
        "otro": (f"capa02-otro-{sufijo}", a, "responsable_area"),
        "impl_b": (f"capa02-implb-{sufijo}", b, "implementador"),
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
                    "DELETE FROM roadmap_tasks WHERE tenant_id = :t",
                    "DELETE FROM hallazgos WHERE tenant_id = :t",
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


async def _crear(ctx, proxima: date, frecuencia: str = "mensual", responsable: str = "resp", **extra) -> dict:
    r = await ctx["client"].post(
        CONTROLES,
        headers=_h(ctx["u"]["impl"]),
        json={
            "nombre": "Revisión de accesos",
            "frecuencia": frecuencia,
            "responsable_user_id": ctx["u"][responsable][0],
            "proxima_verificacion": proxima.isoformat(),
            **extra,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


async def _hallazgos_del_tenant(ctx) -> list[dict]:
    r = await ctx["client"].get(f"{HALLAZGOS}?origen=control_periodico", headers=_h(ctx["u"]["impl"]))
    assert r.status_code == 200, r.text
    return r.json()["hallazgos"]


async def _eventos(ctx, control_id: str) -> list[str]:
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, ctx["a"])
        filas = await s.execute(
            text("SELECT action FROM audit_events WHERE tenant_id = :t AND entity_id = :id ORDER BY timestamp"),
            {"t": ctx["a"], "id": control_id},
        )
        return [f[0] for f in filas]


@pytest.mark.asyncio
async def test_vencimiento_un_hallazgo(ctx):
    ayer = hoy_guayaquil() - timedelta(days=1)
    control = await _crear(ctx, ayer, control_ref="P12")

    primera = await ctx["client"].post(VENCER, headers=_h(ctx["u"]["impl"]))
    segunda = await ctx["client"].post(VENCER, headers=_h(ctx["u"]["impl"]))
    assert primera.status_code == 200, primera.text
    assert primera.json() == {"vencidos": 1, "hallazgos_creados": 1}
    assert segunda.json() == {"vencidos": 0, "hallazgos_creados": 0}

    hallazgos = await _hallazgos_del_tenant(ctx)
    assert len(hallazgos) == 1
    hallazgo = hallazgos[0]
    assert hallazgo["origen_ref"] == f"{control['id']}:{ayer.isoformat()}"
    assert hallazgo["severidad"] == "alta" and hallazgo["control_ref"] == "P12"
    assert hallazgo["titulo"] == "Control vencido: Revisión de accesos"

    listado = (await ctx["client"].get(CONTROLES, headers=_h(ctx["u"]["impl"]))).json()["controles"]
    assert [c["estado"] for c in listado] == ["vencido"]
    assert listado[0]["hallazgo_vigente_id"] == hallazgo["id"]

    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, ctx["a"])
        tareas = (await s.execute(
            text("SELECT count(*) FROM roadmap_tasks WHERE tenant_id = :t"), {"t": ctx["a"]}
        )).scalar_one()
    assert tareas == 0, "vencer no crea tareas: solo el hallazgo"
    assert await _eventos(ctx, control["id"]) == ["creado", "vencido"]


@pytest.mark.asyncio
async def test_vence_solo_lo_que_paso_de_fecha(ctx):
    hoy = hoy_guayaquil()
    await _crear(ctx, hoy)
    await _crear(ctx, hoy + timedelta(days=3))
    r = await ctx["client"].post(VENCER, headers=_h(ctx["u"]["impl"]))
    assert r.json() == {"vencidos": 0, "hallazgos_creados": 0}


@pytest.mark.asyncio
async def test_verificacion_cierra_ciclo(ctx):
    control = await _crear(ctx, hoy_guayaquil() - timedelta(days=1), frecuencia="trimestral")
    await ctx["client"].post(VENCER, headers=_h(ctx["u"]["impl"]))

    r = await ctx["client"].post(
        _verificaciones(control["id"]), headers=_h(ctx["u"]["resp"]), json={"nota": "Accesos revisados"}
    )
    assert r.status_code == 201, r.text
    cuerpo = r.json()
    assert cuerpo["control"]["estado"] == "vigente"
    assert cuerpo["control"]["hallazgo_vigente_id"] is None
    assert cuerpo["control"]["proxima_verificacion"] == siguiente_verificacion(
        hoy_guayaquil(), "trimestral"
    ).isoformat()
    assert cuerpo["control"]["ultima_verificacion_en"] is not None
    assert cuerpo["verificacion"]["nota"] == "Accesos revisados"

    hallazgos = await _hallazgos_del_tenant(ctx)
    assert [h["estado"] for h in hallazgos] == ["cerrado"]
    assert await _eventos(ctx, control["id"]) == ["creado", "vencido", "verificado"]


@pytest.mark.asyncio
async def test_nuevo_vencimiento_es_otro_hallazgo(ctx):
    """El ciclo se repite: la clave lleva la fecha, así que el vencimiento siguiente no choca con el cerrado."""
    from app_core.db.session import fijar_contexto_rls

    control = await _crear(ctx, hoy_guayaquil() - timedelta(days=1))
    await ctx["client"].post(VENCER, headers=_h(ctx["u"]["impl"]))
    await ctx["client"].post(_verificaciones(control["id"]), headers=_h(ctx["u"]["impl"]), json={})
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, ctx["a"])
        await s.execute(
            text("UPDATE controles_periodicos SET proxima_verificacion = :f WHERE id = :id"),
            {"f": hoy_guayaquil() - timedelta(days=2), "id": control["id"]},
        )
        await s.commit()
    r = await ctx["client"].post(VENCER, headers=_h(ctx["u"]["impl"]))
    assert r.json() == {"vencidos": 1, "hallazgos_creados": 1}
    assert sorted(h["estado"] for h in await _hallazgos_del_tenant(ctx)) == ["abierto", "cerrado"]


@pytest.mark.asyncio
async def test_responsable_y_roles(ctx):
    base = {"nombre": "Control", "frecuencia": "anual", "proxima_verificacion": "2027-01-15"}
    cliente, u = ctx["client"], ctx["u"]

    sin_rol = await cliente.post(CONTROLES, headers=_h(u["impl"]), json={**base, "responsable_user_id": "nadie"})
    assert sin_rol.status_code == 422 and sin_rol.json()["code"] == "RESPONSABLE_SIN_ROL"

    # Un usuario con rol solo en otra organización tampoco es responsable aquí.
    ajeno = await cliente.post(CONTROLES, headers=_h(u["impl"]), json={**base, "responsable_user_id": u["impl_b"][0]})
    assert ajeno.status_code == 422 and ajeno.json()["code"] == "RESPONSABLE_SIN_ROL"

    # El dpo no puede ser responsable (D-2) ni crear.
    dpo_resp = await cliente.post(CONTROLES, headers=_h(u["impl"]), json={**base, "responsable_user_id": u["dpo"][0]})
    assert dpo_resp.status_code == 422 and dpo_resp.json()["code"] == "RESPONSABLE_SIN_ROL"
    dpo_crea = await cliente.post(CONTROLES, headers=_h(u["dpo"]), json={**base, "responsable_user_id": u["resp"][0]})
    assert dpo_crea.status_code == 403

    control = await _crear(ctx, date(2027, 1, 15))
    verificar = _verificaciones(control["id"])
    assert (await cliente.post(verificar, headers=_h(u["dpo"]), json={})).status_code == 403
    ajena = await cliente.post(verificar, headers=_h(u["otro"]), json={})
    assert ajena.status_code == 403 and ajena.json()["code"] == "CONTROL_AJENO"
    assert (await cliente.post(verificar, headers=_h(u["coord"]), json={})).status_code == 403

    # responsable_area ve solo los suyos; el dpo consulta todos.
    assert len((await cliente.get(CONTROLES, headers=_h(u["resp"]))).json()["controles"]) == 1
    assert (await cliente.get(CONTROLES, headers=_h(u["otro"]))).json()["controles"] == []
    assert len((await cliente.get(CONTROLES, headers=_h(u["dpo"]))).json()["controles"]) == 1


@pytest.mark.asyncio
async def test_retirado_no_se_verifica_ni_vence(ctx):
    cliente, u = ctx["client"], ctx["u"]
    control = await _crear(ctx, hoy_guayaquil() - timedelta(days=1))
    retirar = f"{CONTROLES}/{control['id']}/retirar"

    r = await cliente.post(retirar, headers=_h(u["coord"]), json={"motivo": "Proceso eliminado"})
    assert r.status_code == 200 and r.json()["estado"] == "retirado"
    assert (await cliente.post(retirar, headers=_h(u["coord"]), json={"motivo": "Otra vez"})).status_code == 409

    verificado = await cliente.post(_verificaciones(control["id"]), headers=_h(u["impl"]), json={})
    assert verificado.status_code == 409 and verificado.json()["code"] == "CONTROL_RETIRADO"
    assert (await cliente.post(VENCER, headers=_h(u["impl"]))).json() == {"vencidos": 0, "hallazgos_creados": 0}
    assert (await cliente.get(f"{CONTROLES}?estado=retirado", headers=_h(u["impl"]))).json()["controles"]
    assert await _eventos(ctx, control["id"]) == ["creado", "retirado"]


@pytest.mark.asyncio
async def test_evidencia_referenciada(ctx):
    from features.evidencias import evidencias_service

    control = await _crear(ctx, date(2027, 1, 15))
    url = _verificaciones(control["id"])
    u = ctx["u"]

    huella_ajena = hashlib.sha256(b"no existe").hexdigest()
    r = await ctx["client"].post(url, headers=_h(u["impl"]), json={"evidencia_sha256": huella_ajena})
    assert r.status_code == 422 and r.json()["code"] == "EVIDENCIA_NO_ENCONTRADA"
    r = await ctx["client"].post(url, headers=_h(u["impl"]), json={"evidencia_sha256": "no-es-un-hash"})
    assert r.status_code == 422 and r.json()["code"] == "EVIDENCIA_NO_ENCONTRADA"

    contenido = b"acta de revision"
    evidencia = evidencias_service.EvidenciaRegistro(
        tenant_id=ctx["a"],
        codigo=f"EVD-2026-{uuid.uuid4().hex[:4]}",
        nombre_archivo="acta.pdf",
        sha256_hash=hashlib.sha256(contenido).hexdigest(),
    )
    evidencias_service.registrar_evidencia_deduplicada(evidencia)

    # La misma huella en otra organización no cuenta.
    otro = await _crear_en_b(ctx)
    r = await ctx["client"].post(
        _verificaciones(otro), headers=_h(u["impl_b"]), json={"evidencia_sha256": evidencia.sha256_hash}
    )
    assert r.status_code == 422

    r = await ctx["client"].post(url, headers=_h(u["impl"]), json={"evidencia_sha256": evidencia.sha256_hash.upper()})
    assert r.status_code == 201, r.text
    assert r.json()["verificacion"]["evidencia_sha256"] == evidencia.sha256_hash


async def _crear_en_b(ctx) -> str:
    r = await ctx["client"].post(
        CONTROLES,
        headers=_h(ctx["u"]["impl_b"]),
        json={
            "nombre": "Control B",
            "frecuencia": "anual",
            "responsable_user_id": ctx["u"]["impl_b"][0],
            "proxima_verificacion": "2027-01-15",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


async def _como_app(s: AsyncSession, tenant: str) -> None:
    from app_core.db.session import fijar_contexto_rls

    await s.execute(text("SET LOCAL ROLE lopdp_app"))
    await fijar_contexto_rls(s, tenant)


@pytest.mark.asyncio
async def test_rls_controles(ctx):
    control = await _crear(ctx, date(2027, 1, 15))
    await ctx["client"].post(_verificaciones(control["id"]), headers=_h(ctx["u"]["resp"]), json={})

    # Por la API, el id de otra organización es 404.
    r = await ctx["client"].post(_verificaciones(control["id"]), headers=_h(ctx["u"]["impl_b"]), json={})
    assert r.status_code == 404 and r.json()["code"] == "CONTROL_NO_ENCONTRADO"

    async with ctx["factory"]() as s:
        await _como_app(s, ctx["b"])
        for sentencia in ("SELECT count(*) FROM controles_periodicos", "SELECT count(*) FROM verificaciones_control"):
            assert (await s.execute(text(sentencia))).scalar_one() == 0
        await s.rollback()

    async with ctx["factory"]() as s:
        await _como_app(s, ctx["a"])
        assert (await s.execute(text("SELECT count(*) FROM controles_periodicos"))).scalar_one() == 1
        assert (await s.execute(text("SELECT count(*) FROM verificaciones_control"))).scalar_one() == 1
        await s.rollback()

    # verificaciones_control es append-only para la aplicación.
    for sentencia in ("UPDATE verificaciones_control SET nota = 'x'", "DELETE FROM verificaciones_control",
                      "DELETE FROM controles_periodicos"):
        async with ctx["factory"]() as s:
            await _como_app(s, ctx["a"])
            with pytest.raises(DBAPIError):
                await s.execute(text(sentencia))
            await s.rollback()
