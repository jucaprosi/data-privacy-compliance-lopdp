# ¤roadmap ¤hallazgos ¤rbac-tenant ¤arbitro
"""RM-23: el hallazgo se cierra con sus tareas y los recordatorios de vencimiento no se repiten.

Contrato: governance/especificaciones/RM-23.md (§5 Aceptación). Las pruebas puras corren sin base; el resto
recorre PostgreSQL real en una rama Neon de revisión propia (nunca producción); sin TEST_DATABASE_URL se omiten.

Prueba de mutación ejecutada en la rama Neon efímera test-juan-carlos-rm23 (hija de test-juan-carlos):
- En cierre_hallazgos_engine.py, `_TAREA_CUMPLIDA` se cambió por TRUE: test_cierre_hallazgo devolvió 1.
- En reabrir_por_tareas se quitó la comparación del motivo: test_cierre_por_el_origen_no_se_reabre devolvió 1.
- En recordatorios_engine.py se quitó el filtro de enviados: test_recordatorios_agrupados_idempotentes devolvió 1.
- Se restauraron los motores; sin las mutaciones las pruebas pasan.
"""
import json
import os
import uuid
from datetime import date, timedelta

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

from features.notificaciones import notificaciones_service  # noqa: E402
from features.roadmap.roadmap_service import hoy_guayaquil, tipo_recordatorio  # noqa: E402

EJECUTAR = "/api/v1/roadmaps/recordatorios/ejecutar"


# --- Pruebas puras --------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "dias,esperado",
    [(8, None), (7, "7dias"), (6, None), (1, None), (0, "hoy"), (-1, "vencida"), (-30, "vencida")],
)
def test_tipo_de_recordatorio(dias, esperado):
    hoy = date(2026, 11, 2)
    assert tipo_recordatorio(hoy + timedelta(days=dias), hoy) == esperado


def test_correo_sin_evidencias_y_con_html_escapado():
    destino = notificaciones_service.Destinatario("u", "u@example.test", "Ana", "t")
    tarea = notificaciones_service.TareaAsignadaItem("t1", "<b>Política</b>", "P1", "alta", "2026-11-02")
    asunto, plano, html = notificaciones_service.renderizar_correo_recordatorios(
        destino, [(tarea, "hoy")], "https://app.example.test"
    )
    assert "Vence hoy" in plano and "<b>Política</b>" not in html and "&lt;b&gt;" in html
    assert "evidencia" not in (asunto + plano + html).lower()


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
    from main import app

    engine = create_async_engine(_TEST_URL.replace("postgresql://", "postgresql+psycopg://", 1), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    sufijo = uuid.uuid4().hex[:10]
    a, b = (f"rm23-{x}-{sufijo}" for x in "ab")
    usuarios = {
        "impl": (f"rm23-impl-{sufijo}", a, "implementador"),
        "dpo": (f"rm23-dpo-{sufijo}", a, "dpo"),
        "resp": (f"rm23-resp-{sufijo}", a, "responsable_area"),
        "impl_b": (f"rm23-implb-{sufijo}", b, "implementador"),
    }
    oleadas = {}
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
        for tenant in (a, b):
            await fijar_contexto_rls(s, tenant)
            roadmap, ola = str(uuid.uuid4()), str(uuid.uuid4())
            await s.execute(text(
                "INSERT INTO roadmaps (id, tenant_id, status, variables_json) VALUES (:r, :t, 'active', '{}')"
            ), {"r": roadmap, "t": tenant})
            await s.execute(text(
                "INSERT INTO roadmap_waves (id, roadmap_id, tenant_id, name) VALUES (:w, :r, :t, 'Ola 1')"
            ), {"w": ola, "r": roadmap, "t": tenant})
            oleadas[tenant] = ola
        await s.commit()

    async def session_override():
        async with factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    falso = notificaciones_service.NotificadorFalso()
    app.dependency_overrides[get_session] = session_override
    app.dependency_overrides[notificaciones_service.notificador_configurado] = lambda: falso
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            yield {"client": client, "factory": factory, "a": a, "b": b, "u": usuarios, "oleadas": oleadas, "falso": falso}
    finally:
        app.dependency_overrides.clear()
        async with factory() as s:
            for t in (a, b):
                await fijar_contexto_rls(s, t)
                for sentencia in (
                    "DELETE FROM recordatorios_enviados WHERE tenant_id = :t",
                    "DELETE FROM roadmap_tasks WHERE tenant_id = :t",
                    "DELETE FROM hallazgos WHERE tenant_id = :t",
                    "DELETE FROM audit_events WHERE tenant_id = :t",
                    "DELETE FROM roadmap_waves WHERE tenant_id = :t",
                    "DELETE FROM roadmaps WHERE tenant_id = :t",
                    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
                ):
                    await s.execute(text(sentencia), {"t": t})
            for uid, _, _ in usuarios.values():
                await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
            for t in (a, b):
                await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
            await s.commit()
        await engine.dispose()


async def _tarea(ctx, tenant: str, *, fin: date | None = None, hallazgo: str | None = None, responsable: str = "") -> str:
    from app_core.db.session import fijar_contexto_rls

    tarea = str(uuid.uuid4())
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, tenant)
        await s.execute(text(
            "INSERT INTO roadmap_tasks (id, wave_id, tenant_id, control_ref, dimension, title, priority, end_date, "
            "hallazgo_id) VALUES (:i, :w, :t, 'P1', 'D01', :titulo, 'alta', :fin, :h)"
        ), {"i": tarea, "w": ctx["oleadas"][tenant], "t": tenant, "titulo": f"Tarea {tarea[:6]}", "fin": fin, "h": hallazgo})
        if responsable:
            await s.execute(text(
                "INSERT INTO task_audit_log (id, task_id, tenant_id, action, payload) "
                "VALUES (:i, :task, :t, 'task_assigned', CAST(:p AS JSON))"
            ), {"i": str(uuid.uuid4()), "task": tarea, "t": tenant, "p": json.dumps({"responsable_id": responsable})})
        await s.commit()
    return tarea


async def _hallazgo(ctx, tenant: str, estado: str = "en_tratamiento") -> str:
    from app_core.db.session import fijar_contexto_rls

    hallazgo = str(uuid.uuid4())
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, tenant)
        await s.execute(text(
            "INSERT INTO hallazgos (id, tenant_id, origen, origen_ref, severidad, titulo, estado, creado_por) "
            "VALUES (:i, :t, 'auditoria', :i, 'alta', 'Hallazgo', :e, 'prueba')"
        ), {"i": hallazgo, "t": tenant, "e": estado})
        await s.commit()
    return hallazgo


async def _completar(ctx, tenant: str, tarea: str, *, evidencia: str | None = "approved") -> None:
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, tenant)
        await s.execute(text("UPDATE roadmap_tasks SET status = 'completada' WHERE id = :i"), {"i": tarea})
        if evidencia:
            await s.execute(text(
                "INSERT INTO task_evidence (id, task_id, tenant_id, r2_key, mime_type, file_size, uploaded_by, "
                "validation_status) VALUES (:i, :task, :t, 'k', 'application/pdf', 1, :autor, :v)"
            ), {"i": str(uuid.uuid4()), "task": tarea, "t": tenant, "autor": ctx["u"]["resp"][0], "v": evidencia})
        await s.commit()


async def _reabrir_tarea(ctx, tenant: str, tarea: str) -> None:
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, tenant)
        await s.execute(text("UPDATE roadmap_tasks SET status = 'pendiente' WHERE id = :i"), {"i": tarea})
        await s.commit()


async def _estado(ctx, tenant: str, hallazgo: str) -> str:
    from app_core.db.session import fijar_contexto_rls

    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, tenant)
        return (await s.execute(text("SELECT estado FROM hallazgos WHERE id = :i"), {"i": hallazgo})).scalar_one()


async def _ejecutar(ctx, clave: str = "impl") -> dict:
    r = await ctx["client"].post(EJECUTAR, headers=_h(ctx["u"][clave]))
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.asyncio
async def test_cierre_hallazgo(ctx):
    """El índice ux_roadmap_tasks_hallazgo (RM-21) admite una tarea por hallazgo: el «todas» se recorre con una."""
    a = ctx["a"]
    hallazgo = await _hallazgo(ctx, a)
    tarea = await _tarea(ctx, a, hallazgo=hallazgo)

    assert (await _ejecutar(ctx))["hallazgos_cerrados"] == 0
    assert await _estado(ctx, a, hallazgo) == "en_tratamiento"

    await _completar(ctx, a, tarea)
    assert (await _ejecutar(ctx))["hallazgos_cerrados"] == 1
    assert await _estado(ctx, a, hallazgo) == "cerrado"
    assert (await _ejecutar(ctx))["hallazgos_cerrados"] == 0

    await _reabrir_tarea(ctx, a, tarea)
    await _ejecutar(ctx)
    assert await _estado(ctx, a, hallazgo) == "en_tratamiento"


@pytest.mark.asyncio
@pytest.mark.parametrize("evidencia", [None, "pending", "rejected"])
async def test_sin_evidencia_validada_no_cierra(ctx, evidencia):
    a = ctx["a"]
    hallazgo = await _hallazgo(ctx, a)
    tarea = await _tarea(ctx, a, hallazgo=hallazgo)
    await _completar(ctx, a, tarea, evidencia=evidencia)

    assert (await _ejecutar(ctx))["hallazgos_cerrados"] == 0
    assert await _estado(ctx, a, hallazgo) == "en_tratamiento"


@pytest.mark.asyncio
async def test_cierre_por_el_origen_no_se_reabre(ctx):
    """Un hallazgo cerrado por su origen (CAPA-02, RAT-05) sigue cerrado aunque su tarea quede pendiente."""
    from app_core.db.session import fijar_contexto_rls
    from features.roadmap.roadmap_service import cerrar_hallazgo

    a = ctx["a"]
    hallazgo = await _hallazgo(ctx, a)
    await _tarea(ctx, a, hallazgo=hallazgo)
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, a)
        assert await cerrar_hallazgo(s, a, ctx["u"]["impl"][0], hallazgo)
        await s.commit()

    await _ejecutar(ctx)
    assert await _estado(ctx, a, hallazgo) == "cerrado"


@pytest.mark.asyncio
async def test_recordatorios_agrupados_idempotentes(ctx):
    a = ctx["a"]
    resp = ctx["u"]["resp"][0]
    hoy = hoy_guayaquil()
    tareas = [await _tarea(ctx, a, fin=hoy, responsable=resp) for _ in range(3)]

    assert (await _ejecutar(ctx))["correos"] == 1
    correos = ctx["falso"].correos_enviados
    assert len(correos) == 1 and {t.task_id for t in correos[0].tareas} == set(tareas)
    assert correos[0].destinatario.email == f"{resp}@example.test"

    assert (await _ejecutar(ctx))["correos"] == 0
    assert len(ctx["falso"].correos_enviados) == 1


@pytest.mark.asyncio
async def test_un_correo_con_los_tres_tipos_y_sin_lo_que_no_toca(ctx):
    a = ctx["a"]
    resp = ctx["u"]["resp"][0]
    hoy = hoy_guayaquil()
    esperadas = {
        await _tarea(ctx, a, fin=hoy + timedelta(days=7), responsable=resp),
        await _tarea(ctx, a, fin=hoy, responsable=resp),
        await _tarea(ctx, a, fin=hoy - timedelta(days=1), responsable=resp),
    }
    await _tarea(ctx, a, fin=hoy + timedelta(days=3), responsable=resp)
    await _tarea(ctx, a, fin=hoy, responsable="")
    completada = await _tarea(ctx, a, fin=hoy, responsable=resp)
    await _completar(ctx, a, completada, evidencia=None)

    assert (await _ejecutar(ctx))["correos"] == 1
    assert {t.task_id for t in ctx["falso"].correos_enviados[0].tareas} == esperadas


@pytest.mark.asyncio
async def test_vencida_se_avisa_una_sola_vez(ctx):
    from app_core.db.session import fijar_contexto_rls

    a = ctx["a"]
    tarea = await _tarea(ctx, a, fin=hoy_guayaquil() - timedelta(days=2), responsable=ctx["u"]["resp"][0])
    assert (await _ejecutar(ctx))["correos"] == 1
    # El aviso se dio ayer: hoy no se repite aunque la clave incluya el día.
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, a)
        await s.execute(
            text("UPDATE recordatorios_enviados SET dia = dia - 1 WHERE tarea_id = :i"), {"i": tarea}
        )
        await s.commit()
    assert (await _ejecutar(ctx))["correos"] == 0


@pytest.mark.asyncio
async def test_sin_envio_confirmado_no_se_anota(ctx):
    """Con Resend aún en boceto no sale correo ni se anota, y la siguiente corrida lo reintenta."""
    from app_core.db.session import fijar_contexto_rls
    from main import app

    a = ctx["a"]
    await _tarea(ctx, a, fin=hoy_guayaquil(), responsable=ctx["u"]["resp"][0])
    boceto = notificaciones_service.NotificadorResendBoceto(api_key="", remitente="")
    app.dependency_overrides[notificaciones_service.notificador_configurado] = lambda: boceto
    assert (await _ejecutar(ctx))["correos"] == 0
    async with ctx["factory"]() as s:
        await fijar_contexto_rls(s, a)
        filas = await s.execute(text("SELECT count(*) FROM recordatorios_enviados WHERE tenant_id = :t"), {"t": a})
        assert filas.scalar_one() == 0

    app.dependency_overrides[notificaciones_service.notificador_configurado] = lambda: ctx["falso"]
    assert (await _ejecutar(ctx))["correos"] == 1


@pytest.mark.asyncio
async def test_solo_implementador(ctx):
    r = await ctx["client"].post(EJECUTAR, headers=_h(ctx["u"]["dpo"]))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_corrida_de_b_no_toca_a(ctx):
    a = ctx["a"]
    hallazgo = await _hallazgo(ctx, a)
    tarea = await _tarea(ctx, a, fin=hoy_guayaquil(), hallazgo=hallazgo, responsable=ctx["u"]["resp"][0])
    await _completar(ctx, a, tarea)

    assert await _ejecutar(ctx, "impl_b") == {"correos": 0, "hallazgos_cerrados": 0}
    assert await _estado(ctx, a, hallazgo) == "en_tratamiento"


@pytest.mark.asyncio
async def test_rls_recordatorios(ctx):
    from app_core.db.session import fijar_contexto_rls

    a, b = ctx["a"], ctx["b"]
    await _tarea(ctx, a, fin=hoy_guayaquil(), responsable=ctx["u"]["resp"][0])
    assert (await _ejecutar(ctx))["correos"] == 1

    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, b)
        assert (await s.execute(text("SELECT count(*) FROM recordatorios_enviados"))).scalar_one() == 0
        await s.rollback()
    async with ctx["factory"]() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await fijar_contexto_rls(s, a)
        assert (await s.execute(text("SELECT count(*) FROM recordatorios_enviados"))).scalar_one() == 1
        await s.rollback()
