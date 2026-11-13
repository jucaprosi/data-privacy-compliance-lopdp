# ¤roadmap ¤rbac-tenant ¤arbitro
"""RM-25a: primera validación de la evidencia por el Coordinador, contra PostgreSQL 16 local.

Sin TEST_DATABASE_URL se omite. Nunca contra producción. Todo SQL es texto literal con parámetros enlazados.

Mutaciones ejecutadas (cada una dejó en rojo la prueba que se nombra y se restauró):
- `roadmaps_validacion.primera_validacion`: `require_role("coordinador")` por `require_role("coordinador", "dpo", "implementador")`
  -> test_un_dpo_o_un_implementador_no_pueden_registrar_la_primera_validacion.
- `registrar_primera_validacion`: quitar la comprobación `verificar_cuatro_ojos` -> test_quien_subio_la_evidencia_no_puede_validarla_primero
  (la restricción de la base también lo frena, pero con otro código: la prueba exige el 409 de cuatro ojos).
- `registrar_primera_validacion`: quitar `if actual[2] is not None` -> test_la_primera_validacion_se_registra_una_sola_vez.
- `evidencia_engine.validate_evidence`: `validado_rol = NULL` en lugar de `:rol` -> test_la_validacion_final_guarda_el_rol_de_quien_valida.
- Migración: quitar `ck_evidence_nivel_acreditado` -> test_nivel_acreditado_solo_admite_de_0_a_4.
"""
import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

pytestmark = pytest.mark.asyncio

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")


def _async_url() -> str:
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    assert "ep-late-hall" not in _TEST_URL, "Se requiere una base de pruebas (nunca producción)"
    return _TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:10]}"


def _h(user: str, tenant: str, rol: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": rol}


@pytest_asyncio.fixture
async def escenario(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    from app_core.db.session import fijar_contexto_rls, get_session
    from main import app

    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    ta, tb = _id("rm25a-a"), _id("rm25a-b")
    u = {
        "coord_sube": _id("u-cs"), "coord": _id("u-co"), "dpo": _id("u-dp"), "impl": _id("u-im"),
        "resp": _id("u-re"), "coord_b": _id("u-cb"),
    }
    roles = {"coord_sube": ("coordinador", ta), "coord": ("coordinador", ta), "dpo": ("dpo", ta),
             "impl": ("implementador", ta), "resp": ("responsable_area", ta), "coord_b": ("coordinador", tb)}
    tarea, tarea_b = _id("tk"), _id("tk-b")
    ev = {"pendiente": _id("ev-p"), "resuelta": _id("ev-r"), "otro_tenant": _id("ev-b"), "subida_por_resp": _id("ev-s")}

    async with factory() as s:
        for t in (ta, tb):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:i, :n, :r, :ruc)"
            ), {"i": t, "n": f"Org {t}", "r": f"Org {t} SA", "ruc": f"RUC{t[-12:]}"})
        for clave, uid in u.items():
            rol, tenant = roles[clave]
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, :n)"),
                            {"i": uid, "e": f"{uid}@rm25a.invalid", "n": uid})
            await fijar_contexto_rls(s, tenant, uid)
            await s.execute(text(
                "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"
            ), {"i": _id("r"), "u": uid, "t": tenant, "r": rol})
        for t, tk in ((ta, tarea), (tb, tarea_b)):
            rm, wv = _id("rm"), _id("wv")
            await fijar_contexto_rls(s, t)
            await s.execute(text(
                "INSERT INTO roadmaps (id, tenant_id, status, variables_json) VALUES (:i, :t, 'active', '{}')"
            ), {"i": rm, "t": t})
            await s.execute(text(
                "INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name, sort_order) VALUES (:i, :rm, :t, 'Ola', 1)"
            ), {"i": wv, "rm": rm, "t": t})
            await s.execute(text(
                "INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, title, description, priority, status) "
                "VALUES (:i, :w, :t, 'P1', 'D01', 'Tarea', 'Desc', 'alta', 'pendiente')"
            ), {"i": tk, "w": wv, "t": t})

        async def evidencia(eid, tenant, task, subida_por, estado="pending"):
            await fijar_contexto_rls(s, tenant)
            await s.execute(text(
                "INSERT INTO task_evidence (id, task_id, tenant_id, r2_key, mime_type, file_size, uploaded_by, validation_status) "
                "VALUES (:i, :tk, :t, :k, 'application/pdf', 100, :u, :e)"
            ), {"i": eid, "tk": task, "t": tenant, "k": f"{tenant}/{task}/{eid}.pdf", "u": subida_por, "e": estado})

        await evidencia(ev["pendiente"], ta, tarea, u["coord_sube"])
        await evidencia(ev["resuelta"], ta, tarea, u["coord_sube"], "approved")
        await evidencia(ev["subida_por_resp"], ta, tarea, u["resp"])
        await evidencia(ev["otro_tenant"], tb, tarea_b, u["coord_b"])
        await s.commit()

    async def sesion():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    anteriores = dict(app.dependency_overrides)
    app.dependency_overrides[get_session] = sesion
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as cliente:
            yield {"c": cliente, "factory": factory, "ta": ta, "tb": tb, "u": u, "tarea": tarea,
                   "tarea_b": tarea_b, "ev": ev, "roles": roles}
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(anteriores)
        async with factory() as s:
            try:
                for t in (ta, tb):
                    await fijar_contexto_rls(s, t)
                    for sentencia in (
                        "DELETE FROM task_audit_log WHERE tenant_id = :t",
                        "DELETE FROM task_evidence WHERE tenant_id = :t",
                        "DELETE FROM roadmap_tasks WHERE tenant_id = :t",
                        "DELETE FROM roadmap_waves WHERE tenant_id = :t",
                        "DELETE FROM roadmaps WHERE tenant_id = :t",
                        "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                    ):
                        await s.execute(text(sentencia), {"t": t})
                    await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
                await s.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": list(u.values())})
                await s.commit()
            except Exception:
                await s.rollback()
        await engine.dispose()


def _como(e, clave):
    rol, tenant = e["roles"][clave]
    return _h(e["u"][clave], tenant, rol)


def _ruta(e, evidencia="pendiente", tarea=None):
    return f"/api/v1/roadmaps/tasks/{tarea or e['tarea']}/evidence/{e['ev'][evidencia]}/primera-validacion"


async def _fila(e, evidencia="pendiente", tenant=None):
    from app_core.db.session import fijar_contexto_rls

    async with e["factory"]() as s:
        await fijar_contexto_rls(s, tenant or e["ta"])
        return (await s.execute(
            text("SELECT * FROM task_evidence WHERE id = :i"), {"i": e["ev"][evidencia]}
        )).mappings().first()


async def test_el_coordinador_registra_la_primera_validacion(escenario):
    e = escenario
    r = await e["c"].post(_ruta(e), headers=_como(e, "coord"))
    assert r.status_code == 200, r.text
    fila = await _fila(e)
    assert fila["primera_validacion_por"] == e["u"]["coord"]
    assert fila["primera_validacion_rol"] == "coordinador"
    assert fila["primera_validacion_en"] is not None
    # No se añade estado nuevo ni se resuelve la evidencia: sigue pendiente para la validación final.
    assert fila["validation_status"] == "pending" and fila["validated_by"] is None


async def test_quien_subio_la_evidencia_no_puede_validarla_primero(escenario):
    e = escenario
    r = await e["c"].post(_ruta(e), headers=_como(e, "coord_sube"))
    assert r.status_code == 409, r.text
    assert (await _fila(e))["primera_validacion_por"] is None


@pytest.mark.parametrize("clave", ["dpo", "impl", "resp"])
async def test_un_dpo_o_un_implementador_no_pueden_registrar_la_primera_validacion(escenario, clave):
    e = escenario
    r = await e["c"].post(_ruta(e), headers=_como(e, clave))
    assert r.status_code == 403, r.text
    assert (await _fila(e))["primera_validacion_por"] is None


async def test_la_primera_validacion_se_registra_una_sola_vez(escenario):
    e = escenario
    assert (await e["c"].post(_ruta(e), headers=_como(e, "coord"))).status_code == 200
    r = await e["c"].post(_ruta(e), headers=_como(e, "coord"))
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "RM_PRIMERA_VALIDACION_YA_REGISTRADA"


async def test_una_evidencia_ya_resuelta_no_admite_primera_validacion(escenario):
    e = escenario
    r = await e["c"].post(_ruta(e, "resuelta"), headers=_como(e, "coord"))
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "RM_EVIDENCIA_NO_PENDIENTE"


async def test_la_evidencia_de_otra_organizacion_o_de_otra_tarea_no_existe(escenario):
    e = escenario
    ajena = await e["c"].post(_ruta(e, "otro_tenant", e["tarea_b"]), headers=_como(e, "coord"))
    assert ajena.status_code == 404, ajena.text
    otra_tarea = await e["c"].post(_ruta(e, tarea=e["tarea_b"]), headers=_como(e, "coord"))
    assert otra_tarea.status_code == 404, otra_tarea.text
    # Aserción positiva: la ruta sí funciona con la tarea correcta.
    assert (await e["c"].post(_ruta(e), headers=_como(e, "coord"))).status_code == 200


async def test_la_validacion_final_guarda_el_rol_de_quien_valida(escenario):
    """El motor acepta `rol` opcional; el PATCH actual aún no lo pasa (lo conecta RM-25b): queda NULL."""
    from features.roadmap import roadmap_service

    e = escenario
    async with e["factory"]() as s:
        valor = await roadmap_service.validate_evidence(
            s, e["ta"], e["u"]["dpo"], e["ev"]["pendiente"], "approved", "conforme", rol="dpo"
        )
        await s.commit()
    assert valor is not None
    fila = await _fila(e)
    assert fila["validated_by"] == e["u"]["dpo"] and fila["validado_rol"] == "dpo"
    # Sin `rol` (PATCH viejo): la validación sigue funcionando y la columna queda nula.
    r = await e["c"].patch(
        f"/api/v1/roadmaps/tasks/{e['tarea']}/evidence/{e['ev']['subida_por_resp']}",
        headers=_como(e, "dpo"), json={"validation_status": "approved", "notes": "ok"},
    )
    assert r.status_code == 200, r.text
    viejo = await _fila(e, "subida_por_resp")
    assert viejo["validated_by"] == e["u"]["dpo"] and viejo["validado_rol"] is None


async def test_nivel_acreditado_solo_admite_de_0_a_4(escenario):
    e = escenario
    from app_core.db.session import fijar_contexto_rls

    for valor, debe_pasar in ((0, True), (4, True), (5, False), (-1, False)):
        async with e["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, e["ta"], e["u"]["dpo"])
            sentencia = text("UPDATE task_evidence SET nivel_acreditado = :n WHERE id = :i")
            parametros = {"n": valor, "i": e["ev"]["pendiente"]}
            if debe_pasar:
                await s.execute(sentencia, parametros)
            else:
                with pytest.raises(DBAPIError) as info:
                    await s.execute(sentencia, parametros)
                assert info.value.orig.sqlstate == "23514"
            await s.rollback()


async def test_la_base_rechaza_una_primera_validacion_de_quien_subio_o_incompleta(escenario):
    e = escenario
    from app_core.db.session import fijar_contexto_rls

    casos = [
        ("UPDATE task_evidence SET primera_validacion_por = :u, primera_validacion_en = now(), "
         "primera_validacion_rol = 'coordinador' WHERE id = :i", e["u"]["coord_sube"]),
        ("UPDATE task_evidence SET primera_validacion_por = :u WHERE id = :i", e["u"]["coord"]),
    ]
    for sentencia, quien in casos:
        async with e["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, e["ta"], e["u"]["dpo"])
            with pytest.raises(DBAPIError) as info:
                await s.execute(text(sentencia), {"u": quien, "i": e["ev"]["pendiente"]})
            assert info.value.orig.sqlstate == "23514"
            await s.rollback()
