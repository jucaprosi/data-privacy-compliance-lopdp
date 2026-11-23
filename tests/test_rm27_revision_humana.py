# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤roadmap ¤rbac-tenant ¤arbitro
"""RM-27: revisión humana antes de que la Hoja de Ruta valga, con cuatro ojos.

Contra PostgreSQL 16 local con `lopdp_app` y RLS. Sin TEST_DATABASE_URL se omite. Nunca contra producción.
Todo SQL es texto literal con parámetros enlazados y sin `import yaml`.

Mutaciones documentadas (cada una deja en rojo la prueba que se nombra):
- `roadmap_revision.py` / `revision_engine.py`: permitir activar a un rol distinto de coordinador o DPO -> `test_solo_coordinador_o_dpo_activan`.
- `revision_engine.activar_hoja_ruta`: quitar la guarda `generado_por == user_id` -> `test_quien_genera_no_activa`.
- Migración `rm27_revision_hoja_ruta.py`: quitar `ck_roadmaps_cuatro_ojos` -> `test_check_cuatro_ojos`.
- `informe_estado_engine.generar_informe_estado_con_revision`: emitir PDF de hoja nueva en `generated` -> `test_generated_no_vale`.
- `informe_estado_engine` / `roadmaps_informe`: omitir «sin revisión registrada» en hoja anterior -> `test_hoja_anterior_vale_con_etiqueta`.
- Migración `rm27_revision_hoja_ruta.py`: quitar `ck_roadmaps_con_autor` -> `test_hoja_nueva_exige_autor`.
- `generacion_en_linea.py`: regenerar sin fijar `generado_por` -> `test_regenerar_fija_autor`.
"""
from __future__ import annotations

import asyncio
import importlib.util
import json
import os
import uuid
from io import BytesIO
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pypdf import PdfReader
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from conftest import exigir_base_de_pruebas

pytestmark = pytest.mark.asyncio

_TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
_MIGRACION = Path(__file__).resolve().parent.parent / "alembic" / "versions" / "rm27_revision_hoja_ruta.py"


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
    spec = importlib.util.spec_from_file_location("rm27_revision_hoja_ruta", _MIGRACION)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def _doc_llm_p1() -> str:
    return json.dumps({
        "roadmap_id": "rm-sim",
        "tenant_id": "t-sim",
        "resumen_ejecutivo": "Plan generado para pruebas de revisión.",
        "olas": [
            {
                "id": "ola-1",
                "nombre": "Ola 1",
                "plazo": "Meses 1 a 3",
                "objetivo": "Cerrar brecha inicial",
                "tareas": [
                    {
                        "id": "t-p1",
                        "control_ref": "P1",
                        "dimension": "D01",
                        "titulo": "Designar responsables de protección",
                        "descripcion": "Formalizar gobernanza inicial.",
                        "responsable": "DPO",
                        "prioridad": "critica",
                        "esfuerzo_estimado_horas": 16,
                        "dependencias": [],
                        "entregable": "Acta de designación",
                        "evidencia_requerida": ["Acta firmada"],
                        "kpi": "100% aprobado",
                        "fecha_inicio": "2026-11-20",
                        "fecha_fin": "2026-12-20",
                    }
                ],
            }
        ],
        "kpis_globales": {
            "criticos_totales": 1,
            "altos_totales": 0,
            "score_objetivo": 40.0,
            "evidencia_verificada_objetivo": 100.0,
        },
    })


@pytest_asyncio.fixture
async def escenario(monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    from app_core.db.session import fijar_contexto_rls, get_session
    from main import app

    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    ta, tb = _id("rm27-a"), _id("rm27-b")
    roles = {
        "impl": ("implementador", ta),
        "coord1": ("coordinador", ta),
        "coord2": ("coordinador", ta),
        "dpo": ("dpo", ta),
        "admin": ("admin_organizacion", ta),
        "resp": ("responsable_area", ta),
        "auditor": ("auditor", ta),
        "dpo_b": ("dpo", tb),
    }
    u = {clave: _id(f"u-{clave[:6]}") for clave in roles}
    nombres = {
        "impl": "Ana Implementadora",
        "coord1": "Carlos Coordinador Uno",
        "coord2": "Lucía Coordinadora Dos",
        "dpo": "María DPO",
        "admin": "Roberto Admin",
        "resp": "Sofía Área",
        "auditor": "Diego Auditor",
        "dpo_b": "Elena DPO B",
    }

    rm_nueva_impl = _id("rm-impl")
    rm_nueva_coord = _id("rm-coord")
    rm_anterior = _id("rm-ant")
    rm_b = _id("rm-b")

    async with factory() as s:
        for t in (ta, tb):
            await s.execute(text(
                "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                "VALUES (:i, :n, :r, :ruc)"
            ), {"i": t, "n": f"Org {t}", "r": f"Org {t} SA", "ruc": f"RUC{t[-12:]}"})
        for clave, uid in u.items():
            rol, tenant = roles[clave]
            await s.execute(
                text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, :n)"),
                {"i": uid, "e": f"{uid}@rm27.invalid", "n": nombres[clave]},
            )
            await fijar_contexto_rls(s, tenant, uid)
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
                {"i": _id("utr"), "u": uid, "t": tenant, "r": rol},
            )

        await fijar_contexto_rls(s, ta, u["impl"])
        await s.execute(text(
            "INSERT INTO diagnostico_respuestas (tenant_id, pregunta_id, control, dimension, estado, "
            "nivel_evidencia, criticidad, es_critica, riesgo_base, respondido_por) "
            "VALUES (:t, 1, 'Inventario de datos', 'D01', 'No Conforme', 0, 5, TRUE, 10, :u)"
        ), {"t": ta, "u": u["impl"]})

        # Hoja nueva generada por implementador
        await s.execute(text(
            "INSERT INTO roadmaps (id, tenant_id, status, variables_json, summary, generado_por) "
            "VALUES (:i, :t, 'generated', '{}', 'Hoja nueva de implementador', :u)"
        ), {"i": rm_nueva_impl, "t": ta, "u": u["impl"]})
        # Hoja nueva generada por coordinador 1
        await s.execute(text(
            "INSERT INTO roadmaps (id, tenant_id, status, variables_json, summary, generado_por) "
            "VALUES (:i, :t, 'generated', '{}', 'Hoja nueva de coordinador 1', :u)"
        ), {"i": rm_nueva_coord, "t": ta, "u": u["coord1"]})
        # Hoja anterior (sin generado_por ni revisado_por)
        await s.execute(text(
            "INSERT INTO roadmaps (id, tenant_id, status, variables_json, summary) "
            "VALUES (:i, :t, 'active', '{}', 'Hoja anterior a RM-27')"
        ), {"i": rm_anterior, "t": ta})

        for rid, tid in ((rm_nueva_impl, ta), (rm_anterior, ta)):
            wv = _id("wv")
            await s.execute(
                text("INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name, sort_order) VALUES (:w, :r, :t, 'Ola 1', 1)"),
                {"w": wv, "r": rid, "t": tid},
            )
            await s.execute(text(
                "INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, title, priority, status) "
                "VALUES (:i, :w, :t, 'P1', 'D01', 'Tarea de control P1', 'alta', 'pendiente')"
            ), {"i": _id("tk"), "w": wv, "t": tid})

        # Hoja en tenant B (con columnas nuevas pobladas para RLS)
        await fijar_contexto_rls(s, tb, u["dpo_b"])
        await s.execute(text(
            "INSERT INTO roadmaps (id, tenant_id, status, variables_json, summary, generado_por, revisado_por, revisado_en) "
            "VALUES (:i, :t, 'active', '{}', 'Hoja tenant B', :g, :r, now())"
        ), {"i": rm_b, "t": tb, "g": _id("autor-b"), "r": u["dpo_b"]})
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
            yield {
                "c": cliente,
                "factory": factory,
                "ta": ta,
                "tb": tb,
                "u": u,
                "nombres": nombres,
                "roles": roles,
                "rm_nueva_impl": rm_nueva_impl,
                "rm_nueva_coord": rm_nueva_coord,
                "rm_anterior": rm_anterior,
                "rm_b": rm_b,
            }
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(anteriores)
        async with factory() as s:
            try:
                for t in (ta, tb):
                    await fijar_contexto_rls(s, t)
                    for sentencia in (
                        "DELETE FROM audit_events WHERE tenant_id = :t",
                        "DELETE FROM task_audit_log WHERE tenant_id = :t",
                        "DELETE FROM task_evidence WHERE tenant_id = :t",
                        "DELETE FROM task_dependencies WHERE task_id IN "
                        "(SELECT id FROM roadmap_tasks WHERE tenant_id = :t)",
                        "DELETE FROM roadmap_tasks WHERE tenant_id = :t",
                        "DELETE FROM roadmap_waves WHERE tenant_id = :t",
                        "DELETE FROM roadmaps WHERE tenant_id = :t",
                        "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
                        "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                    ):
                        await s.execute(text(sentencia), {"t": t})
                    await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
                await s.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": list(u.values())})
                await s.commit()
            except Exception:
                await s.rollback()
        await engine.dispose()


def _como(e, clave: str) -> dict[str, str]:
    rol, tenant = e["roles"][clave]
    return _h(e["u"][clave], tenant, rol)


async def _fila_roadmap(e, roadmap_id: str, tenant: str | None = None):
    from app_core.db.session import fijar_contexto_rls

    async with e["factory"]() as s:
        await fijar_contexto_rls(s, tenant or e["ta"])
        return (await s.execute(
            text("SELECT * FROM roadmaps WHERE id = :i"),
            {"i": roadmap_id},
        )).mappings().first()


@pytest.mark.parametrize("rol_clave", ["impl", "admin", "resp", "auditor"])
async def test_solo_coordinador_o_dpo_activan(escenario, rol_clave):
    e = escenario
    r = await e["c"].post(f"/api/v1/roadmaps/{e['rm_nueva_impl']}/activar", headers=_como(e, rol_clave))
    assert r.status_code == 403, r.text
    fila = await _fila_roadmap(e, e["rm_nueva_impl"])
    assert fila["status"] == "generated"
    assert fila["revisado_por"] is None

    # También en el servicio directo: sin rol coordinador/dpo vigente, 403.
    from features.roadmap import roadmap_service
    rol, tenant = e["roles"][rol_clave]
    async with e["factory"]() as s:
        with pytest.raises(Exception) as exc:
            await roadmap_service.activar_hoja_ruta(s, tenant, e["rm_nueva_impl"], e["u"][rol_clave], rol=rol)
        assert getattr(exc.value, "code", None) == 403

    # Coordinador (distinto del autor) o DPO sí activan.
    r_ok = await e["c"].post(f"/api/v1/roadmaps/{e['rm_nueva_impl']}/activar", headers=_como(e, "dpo"))
    assert r_ok.status_code == 200, r_ok.text
    cuerpo = r_ok.json()
    assert cuerpo["status"] == "active"
    assert cuerpo["revisado_por"] == e["u"]["dpo"]
    assert cuerpo["revisado_en"] is not None


async def test_quien_genera_no_activa(escenario):
    e = escenario
    # El autor (coord1) ve puede_activar = False y es_autor = True
    est_autor = await e["c"].get(f"/api/v1/roadmaps/{e['rm_nueva_coord']}/revision", headers=_como(e, "coord1"))
    assert est_autor.status_code == 200, est_autor.text
    assert est_autor.json()["puede_activar"] is False
    assert est_autor.json()["es_autor"] is True

    # Otro coordinador ve puede_activar = True y es_autor = False
    est_otro = await e["c"].get(f"/api/v1/roadmaps/{e['rm_nueva_coord']}/revision", headers=_como(e, "coord2"))
    assert est_otro.status_code == 200, est_otro.text
    assert est_otro.json()["puede_activar"] is True
    assert est_otro.json()["es_autor"] is False

    # Quien generó la hoja recibe 409 REVISION_MISMA_PERSONA
    r_misma = await e["c"].post(f"/api/v1/roadmaps/{e['rm_nueva_coord']}/activar", headers=_como(e, "coord1"))
    assert r_misma.status_code == 409, r_misma.text
    assert r_misma.json()["code"] == "REVISION_MISMA_PERSONA"
    assert (await _fila_roadmap(e, e["rm_nueva_coord"]))["status"] == "generated"

    # Otro coordinador (coord2) o el DPO sí la activan
    r_ok = await e["c"].post(f"/api/v1/roadmaps/{e['rm_nueva_coord']}/activar", headers=_como(e, "coord2"))
    assert r_ok.status_code == 200, r_ok.text
    fila = await _fila_roadmap(e, e["rm_nueva_coord"])
    assert (fila["status"], fila["revisado_por"]) == ("active", e["u"]["coord2"])
    assert fila["revisado_en"] is not None

    # Una vez activa, volver a activarla devuelve 409 HOJA_YA_ACTIVA
    r_repetida = await e["c"].post(f"/api/v1/roadmaps/{e['rm_nueva_coord']}/activar", headers=_como(e, "dpo"))
    assert r_repetida.status_code == 409, r_repetida.text
    assert r_repetida.json()["code"] == "HOJA_YA_ACTIVA"


async def test_check_cuatro_ojos(escenario):
    e = escenario
    from app_core.db.session import fijar_contexto_rls

    casos = [
        ("UPDATE roadmaps SET status = 'active' WHERE id = :r", {"r": e["rm_nueva_coord"]}, False),
        (
            "UPDATE roadmaps SET status = 'active', revisado_por = :u WHERE id = :r",
            {"r": e["rm_nueva_coord"], "u": e["u"]["coord1"]},
            False,
        ),
        (
            "UPDATE roadmaps SET status = 'active', revisado_por = :u, revisado_en = now() WHERE id = :r",
            {"r": e["rm_nueva_coord"], "u": e["u"]["dpo"]},
            True,
        ),
    ]
    for sql_stmt, params, pasa in casos:
        async with e["factory"]() as s:
            await s.execute(text("SET LOCAL ROLE lopdp_app"))
            await fijar_contexto_rls(s, e["ta"], e["u"]["dpo"])
            if pasa:
                assert (await s.execute(text(sql_stmt), params)).rowcount == 1
            else:
                with pytest.raises(DBAPIError) as info:
                    await s.execute(text(sql_stmt), params)
                assert info.value.orig.sqlstate == "23514", sql_stmt
            await s.rollback()


async def test_generated_no_vale(escenario):
    e = escenario
    r = await e["c"].get(f"/api/v1/roadmaps/{e['rm_nueva_impl']}/informe.pdf", headers=_como(e, "dpo"))
    assert r.status_code == 409, r.text
    assert r.json()["code"] == "HOJA_PENDIENTE_DE_REVISION"

    # Al activarse por otra persona, el PDF ya se emite y sin etiqueta de «sin revisión registrada».
    assert (await e["c"].post(f"/api/v1/roadmaps/{e['rm_nueva_impl']}/activar", headers=_como(e, "coord1"))).status_code == 200
    r_ok = await e["c"].get(f"/api/v1/roadmaps/{e['rm_nueva_impl']}/informe.pdf", headers=_como(e, "dpo"))
    assert r_ok.status_code == 200 and r_ok.content.startswith(b"%PDF")
    assert r_ok.headers.get("X-Roadmap-Revision") != "sin revisión registrada"
    texto_pdf = "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(r_ok.content)).pages)
    assert "sin revisión registrada" not in texto_pdf


async def test_hoja_anterior_vale_con_etiqueta(escenario):
    e = escenario
    rev = await e["c"].get(f"/api/v1/roadmaps/{e['rm_anterior']}/revision", headers=_como(e, "impl"))
    assert rev.status_code == 200, rev.text
    cuerpo = rev.json()
    assert cuerpo["etiqueta"] == "sin revisión registrada"
    assert cuerpo["generado_por"] is None
    assert cuerpo["revisado_por"] is None

    r = await e["c"].get(f"/api/v1/roadmaps/{e['rm_anterior']}/informe.pdf", headers=_como(e, "impl"))
    assert r.status_code == 200, r.text
    assert r.content.startswith(b"%PDF")
    assert r.headers.get("X-Roadmap-Revision") == "sin revisión registrada"
    texto_pdf = "\n".join(p.extract_text() or "" for p in PdfReader(BytesIO(r.content)).pages)
    assert "sin revisión registrada" in texto_pdf


async def test_hoja_nueva_exige_autor(escenario):
    e = escenario
    from app_core.db.session import fijar_contexto_rls

    async with e["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, e["ta"], e["u"]["impl"])
        with pytest.raises(DBAPIError) as info:
            await s.execute(
                text("INSERT INTO roadmaps (id, tenant_id, status, variables_json) VALUES (:i, :t, 'generated', '{}')"),
                {"i": _id("rm-sin-autor"), "t": e["ta"]},
            )
        assert info.value.orig.sqlstate == "23514"
        await s.rollback()

    # Una `active` sin autor (semilla o clon de plantilla) y una `draft` sin autor entran; una `generated` con autor entra.
    async with e["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, e["ta"], e["u"]["impl"])
        for status, autor in (("active", None), ("draft", None), ("generated", e["u"]["impl"])):
            res = await s.execute(
                text("INSERT INTO roadmaps (id, tenant_id, status, variables_json, generado_por) "
                     "VALUES (:i, :t, :st, '{}', :a)"),
                {"i": _id("rm-ok"), "t": e["ta"], "st": status, "a": autor},
            )
            assert res.rowcount == 1
        await s.rollback()


async def test_regenerar_fija_autor(escenario):
    e = escenario
    from features.roadmap import roadmap_service

    req = roadmap_service.GenerateRoadmapRequest(
        tenant_id=e["ta"],
        user_id=e["u"]["impl"],
        variables=roadmap_service.PlanningVariables(
            plazo_meses=6,
            presupuesto=2000.0,
            moneda="USD",
            equipo=["DPO"],
            dpo="María DPO",
            idioma="ES",
        ),
    )
    async with e["factory"]() as s:
        res = await roadmap_service.generate_roadmap_inline(
            s,
            e["ta"],
            e["u"]["impl"],
            req,
            llm_caller=lambda _s, _u: _doc_llm_p1(),
            roadmap_id=e["rm_anterior"],
        )
    assert res["status"] == "completed", res
    fila = await _fila_roadmap(e, e["rm_anterior"])
    assert (fila["status"], fila["generado_por"], fila["revisado_por"], fila["revisado_en"]) == (
        "generated",
        e["u"]["impl"],
        None,
        None,
    )

    # Desde este momento cuenta como hoja nueva y el informe exige activación
    r_pdf = await e["c"].get(f"/api/v1/roadmaps/{e['rm_anterior']}/informe.pdf", headers=_como(e, "dpo"))
    assert r_pdf.status_code == 409
    assert r_pdf.json()["code"] == "HOJA_PENDIENTE_DE_REVISION"

    # Regeneración directa sin LLM (registrar_regeneracion_hoja) sobre hoja ya activada limpia revisión y fija nuevo autor
    assert (await e["c"].post(f"/api/v1/roadmaps/{e['rm_anterior']}/activar", headers=_como(e, "dpo"))).status_code == 200
    async with e["factory"]() as s:
        reg = await roadmap_service.registrar_regeneracion_hoja(s, e["ta"], e["rm_anterior"], e["u"]["coord1"])
        await s.commit()
    assert reg["status"] == "generated"
    assert reg["generado_por"] == e["u"]["coord1"]
    assert reg["revisado_por"] is None and reg["revisado_en"] is None


async def test_migracion_sin_backfill(escenario):
    e = escenario
    from app_core.db.session import fijar_contexto_rls

    migracion = _migracion()
    cols_previas = ("id", "tenant_id", "created_at", "updated_at", "status", "variables_json", "summary", "score_objetivo")

    async with e["factory"]() as s:
        await fijar_contexto_rls(s, e["ta"])
        for sentencia in migracion.SQL_DESCENDENTE:
            await s.execute(text(sentencia))

        rm_hist_gen = _id("rm-hist-gen")
        await s.execute(
            text("INSERT INTO roadmaps (id, tenant_id, status, variables_json, summary) "
                 "VALUES (:i, :t, 'generated', '{}', 'Histórica generated sin autor')"),
            {"i": rm_hist_gen, "t": e["ta"]},
        )

        antes = {
            f["id"]: {c: f[c] for c in cols_previas}
            for f in (await s.execute(text("SELECT * FROM roadmaps WHERE tenant_id = :t"), {"t": e["ta"]})).mappings().all()
        }

        for sentencia in migracion.SQL_COLUMNAS:
            await s.execute(text(sentencia))
        for sentencia in migracion.SQL_RESTRICCIONES:
            await s.execute(text(sentencia))

        despues = (await s.execute(text("SELECT * FROM roadmaps WHERE tenant_id = :t"), {"t": e["ta"]})).mappings().all()
        await s.rollback()

    assert {f["id"] for f in despues} == set(antes)
    for fila in despues:
        assert {c: fila[c] for c in cols_previas} == antes[fila["id"]]
        assert fila["generado_por"] is None
        assert fila["revisado_por"] is None
        assert fila["revisado_en"] is None
    assert next(f for f in despues if f["id"] == rm_hist_gen)["status"] == "generated"


async def test_activacion_concurrente(escenario):
    e = escenario
    r1, r2 = await asyncio.gather(
        e["c"].post(f"/api/v1/roadmaps/{e['rm_nueva_impl']}/activar", headers=_como(e, "coord1")),
        e["c"].post(f"/api/v1/roadmaps/{e['rm_nueva_impl']}/activar", headers=_como(e, "dpo")),
    )
    estados = sorted((r1.status_code, r2.status_code))
    assert estados == [200, 409], (r1.status_code, r1.text, r2.status_code, r2.text)
    fallo = r1 if r1.status_code == 409 else r2
    assert fallo.json()["code"] == "HOJA_YA_ACTIVA"


async def test_rls_revision(escenario):
    e = escenario
    from app_core.db.session import fijar_contexto_rls

    async with e["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, e["tb"], e["u"]["dpo_b"])
        ajenas = (await s.execute(
            text("SELECT id, generado_por, revisado_por, revisado_en FROM roadmaps "
                 "WHERE tenant_id = :t OR id = ANY(:ids)"),
            {"t": e["ta"], "ids": [e["rm_nueva_impl"], e["rm_nueva_coord"], e["rm_anterior"]]},
        )).all()
        propias = (await s.execute(
            text("SELECT id, generado_por, revisado_por, revisado_en FROM roadmaps"),
        )).mappings().all()
        await s.rollback()

    assert ajenas == []
    assert [f["id"] for f in propias] == [e["rm_b"]]
    assert propias[0]["revisado_por"] == e["u"]["dpo_b"]

    # Por la API, el usuario de B recibe 404 al consultar o intentar activar una hoja de A.
    r_get = await e["c"].get(f"/api/v1/roadmaps/{e['rm_nueva_impl']}/revision", headers=_como(e, "dpo_b"))
    assert r_get.status_code == 404
    r_post = await e["c"].post(f"/api/v1/roadmaps/{e['rm_nueva_impl']}/activar", headers=_como(e, "dpo_b"))
    assert r_post.status_code == 404
    assert (await _fila_roadmap(e, e["rm_nueva_impl"]))["status"] == "generated"
