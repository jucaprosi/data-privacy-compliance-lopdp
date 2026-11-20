# ¤roadmap ¤rbac-tenant ¤arbitro
"""RM-25b: la validación final de la evidencia exige la primera, un rol dpo o auditor y tres personas distintas.

Contra PostgreSQL 16 local con `lopdp_app` y RLS. Sin TEST_DATABASE_URL se omite. Nunca contra producción.
Todo SQL es texto literal con parámetros enlazados.

Mutaciones documentadas (cada una deja en rojo la prueba que se nombra):
- `evidencia_engine.validate_evidence`: quitar `if rol not in ROLES_VALIDACION_FINAL` -> test_coordinador_no_aprueba.
- `evidencia_engine.validate_evidence`: quitar `if current[1] is None` -> test_final_exige_primera.
- `roadmaps.validate_evidence`: devolver `implementador` a `require_role` -> test_implementador_no_valida.
- Migración: quitar `ck_evidence_aprobada_con_primera` -> test_check_aprobada_con_primera.
- Migración: que `SQL_MARCA` promueva (rellene la primera validación) -> test_migracion_marca_sin_promover.
- `tareas_validadas_engine`: quitar la condición de rol -> test_diag12_solo_doble_validacion (tests/test_diag12_estados.py).
"""
import importlib.util
import os
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from conftest import exigir_base_de_pruebas

pytestmark = pytest.mark.asyncio

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
_MIGRACION = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "rm25b_evidencia_exigir.py"


def _async_url() -> str:
    if not _TEST_URL:
        pytest.skip("TEST_DATABASE_URL no configurada")
    exigir_base_de_pruebas()
    return _TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1)


def _id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:10]}"


def _h(user: str, tenant: str, rol: str) -> dict[str, str]:
    return {"X-User-ID": user, "X-Tenant-ID": tenant, "X-Role": rol}


def _migracion():
    spec = importlib.util.spec_from_file_location("rm25b_evidencia_exigir", _MIGRACION)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


# Evidencias del escenario: (quién la sube, quién hizo la primera validación o None).
_EVIDENCIAS = {
    "sin_primera": ("resp", None),
    "con_primera": ("resp", "coord"),
    "para_auditor": ("resp", "coord"),
    "primera_de_quien_cambio_de_rol": ("resp", "antes_coord"),
    "subida_por_dpo": ("dpo_sube", "coord"),
}


@pytest_asyncio.fixture
async def escenario(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    from app_core.db.session import fijar_contexto_rls, get_session
    from main import app

    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    ta, tb = _id("rm25b-a"), _id("rm25b-b")
    roles = {
        "resp": ("responsable_area", ta), "coord": ("coordinador", ta), "dpo": ("dpo", ta),
        "auditor": ("auditor", ta), "impl": ("implementador", ta),
        # Hizo la primera validación como coordinador y hoy es DPO: sigue sin poder hacer la final.
        "antes_coord": ("dpo", ta),
        "dpo_sube": ("dpo", ta),
        "dpo_b": ("dpo", tb),
    }
    u = {clave: _id(f"u-{clave[:6]}") for clave in roles}
    tarea, tarea_b = _id("tk"), _id("tk-b")
    ev = {clave: _id("ev") for clave in _EVIDENCIAS}
    ev["otro_tenant"] = _id("ev-b")

    async with factory() as s:
        for t in (ta, tb):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:i, :n, :r, :ruc)"
            ), {"i": t, "n": f"Org {t}", "r": f"Org {t} SA", "ruc": f"RUC{t[-12:]}"})
        for clave, uid in u.items():
            rol, tenant = roles[clave]
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, :n)"),
                            {"i": uid, "e": f"{uid}@rm25b.invalid", "n": uid})
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

        async def evidencia(eid, tenant, task, sube, primera):
            await fijar_contexto_rls(s, tenant)
            await s.execute(text(
                "INSERT INTO task_evidence (id, task_id, tenant_id, clave_objeto, mime_type, file_size, uploaded_by, "
                "validation_status, primera_validacion_por, primera_validacion_en, primera_validacion_rol) "
                "VALUES (:i, :tk, :t, :k, 'application/pdf', 100, :u, 'pending', :p, "
                "CASE WHEN CAST(:p AS varchar) IS NOT NULL THEN now() END, "
                "CASE WHEN CAST(:p AS varchar) IS NOT NULL THEN 'coordinador' END)"
            ), {"i": eid, "tk": task, "t": tenant, "k": f"{tenant}/{task}/{eid}.pdf", "u": sube, "p": primera})

        for clave, (sube, primera) in _EVIDENCIAS.items():
            await evidencia(ev[clave], ta, tarea, u[sube], u[primera] if primera else None)
        await evidencia(ev["otro_tenant"], tb, tarea_b, u["dpo_b"], None)
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


def _ruta(e, evidencia):
    return f"/api/v1/roadmaps/tasks/{e['tarea']}/evidence/{e['ev'][evidencia]}"


async def _resolver(e, evidencia, clave, estado="approved"):
    return await e["c"].patch(
        _ruta(e, evidencia), headers=_como(e, clave), json={"validation_status": estado, "notes": "nota"}
    )


async def _fila(e, evidencia, tenant=None):
    from app_core.db.session import fijar_contexto_rls

    async with e["factory"]() as s:
        await fijar_contexto_rls(s, tenant or e["ta"])
        return (await s.execute(
            text("SELECT * FROM task_evidence WHERE id = :i"), {"i": e["ev"][evidencia]}
        )).mappings().first()


async def test_final_exige_primera(escenario):
    e = escenario
    r = await _resolver(e, "sin_primera", "dpo")
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "PRIMERA_VALIDACION_PENDIENTE"
    assert (await _fila(e, "sin_primera"))["validation_status"] == "pending"
    # Con la primera validación registrada, el DPO sí hace la final y queda guardado su rol.
    r = await _resolver(e, "con_primera", "dpo")
    assert r.status_code == 200, r.text
    fila = await _fila(e, "con_primera")
    assert (fila["validation_status"], fila["validated_by"], fila["validado_rol"]) == ("approved", e["u"]["dpo"], "dpo")


async def test_el_auditor_hace_la_validacion_final(escenario):
    e = escenario
    r = await _resolver(e, "para_auditor", "auditor")
    assert r.status_code == 200, r.text
    fila = await _fila(e, "para_auditor")
    assert (fila["validation_status"], fila["validado_rol"]) == ("approved", "auditor")


@pytest.mark.parametrize("estado", ["approved", "rejected"])
async def test_implementador_no_valida(escenario, estado):
    e = escenario
    r = await _resolver(e, "con_primera", "impl", estado)
    assert r.status_code == 403, r.text
    assert r.json().get("code") != "ROL_SIN_VALIDACION_FINAL"  # es el 403 de la dependencia de roles
    assert (await _fila(e, "con_primera"))["validation_status"] == "pending"


@pytest.mark.parametrize("evidencia", ["sin_primera", "con_primera"])
async def test_coordinador_no_aprueba(escenario, evidencia):
    """El 403 del rol va antes que los dos 409: sin primera validación y con la primera hecha por él mismo."""
    e = escenario
    r = await _resolver(e, evidencia, "coord")
    assert r.status_code == 403, r.text
    assert r.json()["code"] == "ROL_SIN_VALIDACION_FINAL"
    assert (await _fila(e, evidencia))["validation_status"] == "pending"


@pytest.mark.parametrize("evidencia", ["sin_primera", "con_primera"])
async def test_el_coordinador_si_rechaza_en_cualquiera_de_los_dos_pasos(escenario, evidencia):
    e = escenario
    r = await _resolver(e, evidencia, "coord", "rejected")
    assert r.status_code == 200, r.text
    fila = await _fila(e, evidencia)
    assert (fila["validation_status"], fila["validated_by"], fila["validado_rol"]) == (
        "rejected", e["u"]["coord"], "coordinador")


async def test_tres_personas_distintas(escenario):
    e = escenario
    # Quien hizo la primera validación (entonces coordinador, hoy DPO) no hace la final.
    r = await _resolver(e, "primera_de_quien_cambio_de_rol", "antes_coord")
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "VALIDADOR_REPETIDO"
    # Quien subió la evidencia tampoco, aunque sea DPO y la primera validación exista.
    r = await _resolver(e, "subida_por_dpo", "dpo_sube")
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "VALIDADOR_REPETIDO"
    for evidencia in ("primera_de_quien_cambio_de_rol", "subida_por_dpo"):
        assert (await _fila(e, evidencia))["validation_status"] == "pending"
    # Una tercera persona con rol dpo sí.
    assert (await _resolver(e, "primera_de_quien_cambio_de_rol", "dpo")).status_code == 200


async def test_check_aprobada_con_primera(escenario):
    e = escenario
    from app_core.db.session import fijar_contexto_rls

    insertar = (
        "INSERT INTO task_evidence (id, task_id, tenant_id, clave_objeto, uploaded_by, validation_status, "
        "validated_by, requiere_revalidacion) VALUES (:i, :tk, :t, 'simulada/clave', :u, 'approved', :v, :m)"
    )
    nueva = {"i": _id("ev-n"), "tk": e["tarea"], "t": e["ta"], "u": e["u"]["resp"], "v": e["u"]["dpo"]}
    casos = [
        # (sentencia, parámetros, la base la acepta)
        ("UPDATE task_evidence SET validation_status = 'approved', validated_by = :v WHERE id = :i",
         {"i": e["ev"]["sin_primera"], "v": e["u"]["dpo"]}, False),
        (insertar, {**nueva, "m": False}, False),
        # Con la marca (la aprobada anterior a esta ficha) o con primera validación, sí.
        (insertar, {**nueva, "m": True}, True),
        ("UPDATE task_evidence SET validation_status = 'approved', validated_by = :v WHERE id = :i",
         {"i": e["ev"]["con_primera"], "v": e["u"]["dpo"]}, True),
        # ck_evidence_validadores_distintos: la final no la hace quien hizo la primera.
        ("UPDATE task_evidence SET validation_status = 'approved', validated_by = :v WHERE id = :i",
         {"i": e["ev"]["con_primera"], "v": e["u"]["coord"]}, False),
        # El rechazo de quien hizo la primera validación sigue pasando.
        ("UPDATE task_evidence SET validation_status = 'rejected', validated_by = :v WHERE id = :i",
         {"i": e["ev"]["con_primera"], "v": e["u"]["coord"]}, True),
    ]
    for sentencia, parametros, pasa in casos:
        async with e["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, e["ta"], e["u"]["dpo"])
            if pasa:
                assert (await s.execute(text(sentencia), parametros)).rowcount == 1
            else:
                with pytest.raises(DBAPIError) as info:
                    await s.execute(text(sentencia), parametros)
                assert info.value.orig.sqlstate == "23514", sentencia
            await s.rollback()


async def test_migracion_marca_sin_promover(escenario, capsys):
    """Recrea el estado anterior a la migración dentro de una transacción que se deshace al final."""
    e = escenario
    from app_core.db.session import fijar_contexto_rls

    migracion = _migracion()
    historicas = ("sin_primera", "subida_por_dpo")  # la segunda sí tiene primera validación: no se marca
    async with e["factory"]() as s:
        await fijar_contexto_rls(s, e["ta"])
        for sentencia in (
            "ALTER TABLE task_evidence DROP CONSTRAINT ck_evidence_validadores_distintos",
            "ALTER TABLE task_evidence DROP CONSTRAINT ck_evidence_aprobada_con_primera",
        ):
            await s.execute(text(sentencia))
        await s.execute(
            text("UPDATE task_evidence SET validation_status = 'approved', validated_by = :v WHERE id = ANY(:ids)"),
            {"v": e["u"]["dpo"], "ids": [e["ev"][k] for k in historicas]},
        )
        consulta = text("SELECT * FROM task_evidence WHERE tenant_id = :t ORDER BY id")
        antes = {f["id"]: dict(f) for f in (await s.execute(consulta, {"t": e["ta"]})).mappings().all()}
        esperado = (await s.execute(text(migracion.SQL_RECUENTO))).scalar_one()
        assert esperado >= 1

        recuento = await s.run_sync(lambda sesion: migracion.marcar_sin_promover(sesion.connection()))
        for sentencia in migracion.SQL_RESTRICCIONES:  # las filas históricas quedan cubiertas por la marca
            await s.execute(text(sentencia))

        despues = {f["id"]: dict(f) for f in (await s.execute(consulta, {"t": e["ta"]})).mappings().all()}
        await s.rollback()

    assert recuento == esperado
    assert f"quedan por revalidar: {esperado}" in capsys.readouterr().out
    marcada, con_primera = e["ev"]["sin_primera"], e["ev"]["subida_por_dpo"]
    assert despues[marcada]["requiere_revalidacion"] is True
    assert despues[con_primera]["requiere_revalidacion"] is False
    # Sin promover: salvo la marca, ninguna fila cambia (ni su estado ni su primera validación).
    for eid, fila in antes.items():
        assert {**despues[eid], "requiere_revalidacion": False} == fila
    assert despues[marcada]["validation_status"] == "approved"
    assert despues[marcada]["primera_validacion_por"] is None
    # La transacción se deshizo: las restricciones siguen en la base.
    assert (await _fila(e, "sin_primera"))["validation_status"] == "pending"


async def test_la_validacion_final_quita_la_marca(escenario):
    """Una aprobada anterior (marcada) deja de requerir revalidación cuando pasa por los dos pasos."""
    e = escenario
    from app_core.db.session import fijar_contexto_rls

    async with e["factory"]() as s:
        await fijar_contexto_rls(s, e["ta"])
        await s.execute(text("UPDATE task_evidence SET requiere_revalidacion = true WHERE id = :i"),
                        {"i": e["ev"]["con_primera"]})
        await s.commit()
    assert (await _resolver(e, "con_primera", "dpo")).status_code == 200
    assert (await _fila(e, "con_primera"))["requiere_revalidacion"] is False


async def test_rls_evidencia_exigir(escenario):
    e = escenario
    from app_core.db.session import fijar_contexto_rls

    async with e["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, e["tb"], e["u"]["dpo_b"])
        ajenas = (await s.execute(
            text("SELECT count(*) FROM task_evidence WHERE tenant_id = :t OR id = ANY(:ids)"),
            {"t": e["ta"], "ids": [e["ev"][k] for k in _EVIDENCIAS]},
        )).scalar_one()
        propias = (await s.execute(text("SELECT count(*) FROM task_evidence WHERE NOT requiere_revalidacion"))).scalar_one()
        await s.rollback()
    assert ajenas == 0 and propias == 1  # aserción positiva: B ve la suya, con la columna nueva
    # Por la API, el DPO de B no resuelve una evidencia de A.
    r = await e["c"].patch(_ruta(e, "con_primera"), headers=_como(e, "dpo_b"),
                           json={"validation_status": "approved", "notes": ""})
    assert r.status_code == 404, r.text
    assert (await _fila(e, "con_primera"))["validation_status"] == "pending"
