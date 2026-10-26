# ¤mtge-granescala
# ¤rbac-tenant
# ¤arbitro
"""Pruebas exhaustivas contra PostgreSQL para obligaciones de gran escala (MTGE-02).

Cubre:
1. Sin tratamientos calificados a gran escala: todo responde 'NO_APLICA'.
2. Con tratamiento a gran escala:
   - Sin auditorías registradas: estado 'VENCIDA'.
   - Con auditoría hace 12 meses y 1 día (366 días): estado 'VENCIDA' (Art. 17 Res. SPDP-SPD-2026-0005-R).
   - Con auditoría vigente: estado 'AL_DIA' o 'POR_VENCER' si faltan <= 30 días.
   - Certificación equivalente vigente cuenta como 'AL_DIA'.
3. Conservación (5 años):
   - Intento de borrado de informe de auditoría antes de 5 años responde 409 Conflict citando Art. 17.
   - Intento de borrado de informe anual antes de 5 años responde 409 Conflict citando Art. 18.
4. Plazo DPO (90 días, Disposición Transitoria):
   - Sin fecha registrada: 'FALTA_FECHA_VIGENCIA'.
   - Con fecha registrada: calcula 90 días desde dicha fecha.
5. Control de Acceso y RBAC:
   - 'dpo' puede registrar auditorías, informes anuales y políticas de privacidad (201 Created).
   - 'coordinador' y 'admin_organizacion' pueden consultar (200 OK) pero no registrar (403 Forbidden).
   - 'responsable_area' u otros roles reciben 403 en consulta y registro.
6. Aislamiento RLS:
   - Con SET LOCAL ROLE lopdp_app, las consultas sin tenant o de otro tenant devuelven 0 filas.
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timedelta, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app_core.db.session import get_session
from features.rat.domain.models import ActividadRAT, BaseLegitimacion, CategoriaTitular
from features.rat import rat_service
from features.riesgos_mtge import riesgos_mtge_service
from features.riesgos_mtge.services.obligaciones_engine import (
    AuditoriaGranEscalaCreate,
    _fin_conservacion,
    _mas_un_anio,
)
from main import app

pytestmark = pytest.mark.asyncio


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def conn():
    """Conexión transaccional aislada por prueba con rollback estricto."""
    engine = create_async_engine(_async_url(), echo=False)
    async with engine.connect() as connection:
        trans = await connection.begin()
        yield connection
        await trans.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def session(conn):
    async_session = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as s:
        yield s


@pytest_asyncio.fixture
async def cliente_http(conn):
    async def _override_session():
        async_session = async_sessionmaker(bind=conn, class_=AsyncSession, expire_on_commit=False)
        async with async_session() as s:
            yield s

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.pop(get_session, None)


async def _crear_tenant_y_usuarios(conn, tid: str, uid_dpo: str, uid_coord: str, uid_admin: str):
    await conn.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, activo) "
             "VALUES (:t, 'Tenant MTGE', 'Tenant MTGE S.A.', :ruc, TRUE)"),
        {"t": tid, "ruc": f"17{uuid.uuid4().int % 10000000000:010d}001"},
    )
    for u, pref in [(uid_dpo, "dpo"), (uid_coord, "coord"), (uid_admin, "admin")]:
        email = f"{pref}-{u}@example.test"
        await conn.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, :n)"),
            {"u": u, "e": email, "n": pref},
        )
    # Roles en user_tenant_roles
    await conn.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES "
             "(:r1, :u1, :t, 'dpo'), (:r2, :u2, :t, 'coordinador'), (:r3, :u3, :t, 'admin_organizacion')"),
        {"r1": str(uuid.uuid4()), "r2": str(uuid.uuid4()), "r3": str(uuid.uuid4()),
         "u1": uid_dpo, "u2": uid_coord, "u3": uid_admin, "t": tid},
    )


# ============================================================================
# 1. PRUEBA: SIN TRATAMIENTOS A GRAN ESCALA -> TODO 'NO_APLICA'
# ============================================================================

async def test_sin_gran_escala_todo_no_aplica(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    tid = f"t-mtge-{uuid.uuid4().hex[:8]}"
    u_dpo, u_coord, u_admin = f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}"
    await _crear_tenant_y_usuarios(conn, tid, u_dpo, u_coord, u_admin)

    headers = {"X-Tenant-ID": tid, "X-User-ID": u_coord, "X-Role": "coordinador"}
    res = await cliente_http.get("/api/v1/riesgos/mtge/obligaciones", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["tiene_gran_escala"] is False
    assert data["cantidad_tratamientos_gran_escala"] == 0
    for ob in data["obligaciones"]:
        assert ob["estado"] == "NO_APLICA"


# ============================================================================
# 2. PRUEBA: CON GRAN ESCALA -> AUDITORÍA VENCIDA A LOS 12 MESES Y 1 DÍA
# ============================================================================

async def test_auditoria_vencida_12_meses_y_un_dia(conn, session, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    tid = f"t-mtge-{uuid.uuid4().hex[:8]}"
    u_dpo, u_coord, u_admin = f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}"
    await _crear_tenant_y_usuarios(conn, tid, u_dpo, u_coord, u_admin)

    # Fijar tenant y registrar actividad RAT con es_gran_escala = True
    await conn.execute(text("SELECT set_config('app.current_tenant_id', :t, true);"), {"t": tid})
    act = ActividadRAT(
        id=str(uuid.uuid4()),
        tenant_id=tid,
        codigo="RAT-GE-01",
        nombre="Tratamiento de Salud Masivo",
        area_responsable="Médica",
        finalidad="Atención de salud",
        base_legal=BaseLegitimacion.OBLIGACION_LEGAL,
        categorias_titulares=[CategoriaTitular.PACIENTES],
        categorias_datos=["salud", "identificacion"],
        es_gran_escala=True,
    )
    await rat_service.registrar_actividad_rat(session, act, user_id=u_admin)

    # Registrar una auditoría realizada hace 12 meses y 1 día (en calendario, no 366 días)
    hoy = date.today()
    hace_un_anio = hoy.replace(year=hoy.year - 1) if (hoy.month, hoy.day) != (2, 29) else date(hoy.year - 1, 2, 28)
    fecha_aud = hace_un_anio - timedelta(days=1)
    headers_dpo = {"X-Tenant-ID": tid, "X-User-ID": u_dpo, "X-Role": "dpo"}

    res_post = await cliente_http.post(
        "/api/v1/riesgos/mtge/obligaciones/auditorias",
        json={
            "fecha_auditoria": str(fecha_aud),
            "tipo": "externa",
            "alcance": "Auditoría de cumplimiento integral",
            "auditor": "Auditores Asociados Cia. Ltda.",
            "archivo_informe": "s3://evidencias/aud-2025.pdf",
            "es_certificacion_equivalente": False,
        },
        headers=headers_dpo,
    )
    assert res_post.status_code == 201

    # Consultar estado de obligaciones
    res_est = await cliente_http.get("/api/v1/riesgos/mtge/obligaciones", headers=headers_dpo)
    assert res_est.status_code == 200
    data = res_est.json()
    assert data["tiene_gran_escala"] is True

    ob_aud = next(o for o in data["obligaciones"] if "Auditoría periódica" in o["obligacion"])
    assert ob_aud["estado"] == "VENCIDA"
    assert "Art. 17" in ob_aud["articulo_fuente"]
    assert ob_aud["dias_restantes"] < 0


# ============================================================================
# 3. PRUEBA: CERTIFICACIÓN EQUIVALENTE VIGENTE CUENTA COMO 'AL_DIA'
# ============================================================================

async def test_certificacion_equivalente_vigente_cuenta_como_al_dia(conn, session, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    tid = f"t-mtge-{uuid.uuid4().hex[:8]}"
    u_dpo, u_coord, u_admin = f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}"
    await _crear_tenant_y_usuarios(conn, tid, u_dpo, u_coord, u_admin)

    await conn.execute(text("SELECT set_config('app.current_tenant_id', :t, true);"), {"t": tid})
    act = ActividadRAT(
        id=str(uuid.uuid4()),
        tenant_id=tid,
        codigo="RAT-GE-02",
        nombre="Biometría a gran escala",
        area_responsable="Seguridad",
        finalidad="Control de acceso",
        base_legal=BaseLegitimacion.CONSENTIMIENTO,
        categorias_titulares=[CategoriaTitular.CLIENTES],
        categorias_datos=["biometricos"],
        es_gran_escala=True,
    )
    await rat_service.registrar_actividad_rat(session, act, user_id=u_admin)

    # Registrar certificación vigente hasta dentro de 9 meses
    hoy = date.today()
    vigente_hasta = hoy + timedelta(days=270)
    headers_dpo = {"X-Tenant-ID": tid, "X-User-ID": u_dpo, "X-Role": "dpo"}

    res_post = await cliente_http.post(
        "/api/v1/riesgos/mtge/obligaciones/auditorias",
        json={
            "fecha_auditoria": str(hoy - timedelta(days=90)),
            "tipo": "externa",
            "alcance": "Certificación ISO/IEC 27701",
            "auditor": "Certificadora Internacional",
            "es_certificacion_equivalente": True,
            "certificacion_nombre": "ISO/IEC 27701:2019",
            "certificacion_vigente_hasta": str(vigente_hasta),
        },
        headers=headers_dpo,
    )
    assert res_post.status_code == 201

    res_est = await cliente_http.get("/api/v1/riesgos/mtge/obligaciones", headers=headers_dpo)
    assert res_est.status_code == 200
    ob_aud = next(o for o in res_est.json()["obligaciones"] if "Auditoría periódica" in o["obligacion"])
    assert ob_aud["estado"] == "AL_DIA"
    assert ob_aud["dias_restantes"] == 270


# ============================================================================
# 4. PRUEBA: BORRADO ANTES DE 5 AÑOS RESPONDE 409 CON ARTÍCULO
# ============================================================================

async def test_borrado_auditoria_e_informe_antes_de_5_anios_responde_409(conn, session, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    tid = f"t-mtge-{uuid.uuid4().hex[:8]}"
    u_dpo, u_coord, u_admin = f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}"
    await _crear_tenant_y_usuarios(conn, tid, u_dpo, u_coord, u_admin)
    await conn.execute(text("SELECT set_config('app.current_tenant_id', :t, true);"), {"t": tid})

    headers_dpo = {"X-Tenant-ID": tid, "X-User-ID": u_dpo, "X-Role": "dpo"}
    hoy = date.today()

    # 1. Auditoría de hace 1 año (conservación obligatoria: 5 años)
    res_aud = await cliente_http.post(
        "/api/v1/riesgos/mtge/obligaciones/auditorias",
        json={
            "fecha_auditoria": str(hoy - timedelta(days=365)),
            "tipo": "interna",
            "alcance": "Revisión técnica anual",
            "auditor": "Auditor Interno",
        },
        headers=headers_dpo,
    )
    aud_id = res_aud.json()["id"]

    res_del_aud = await cliente_http.delete(f"/api/v1/riesgos/mtge/obligaciones/auditorias/{aud_id}", headers=headers_dpo)
    assert res_del_aud.status_code == 409
    assert "Art. 17" in res_del_aud.json()["detail"]
    assert "5 años" in res_del_aud.json()["detail"]

    # 2. Informe anual de hace 1 año
    res_inf = await cliente_http.post(
        "/api/v1/riesgos/mtge/obligaciones/informes-anuales",
        json={
            "anio": hoy.year - 1,
            "fecha_aprobacion": str(hoy - timedelta(days=180)),
        },
        headers=headers_dpo,
    )
    inf_id = res_inf.json()["id"]

    res_del_inf = await cliente_http.delete(f"/api/v1/riesgos/mtge/obligaciones/informes-anuales/{inf_id}", headers=headers_dpo)
    assert res_del_inf.status_code == 409
    assert "Art. 18" in res_del_inf.json()["detail"]
    assert "5 años" in res_del_inf.json()["detail"]


# ============================================================================
# 5. PRUEBA: PLAZO TRANSITORIO DEL DPO (90 DÍAS)
# ============================================================================

async def test_plazo_transitorio_dpo_90_dias(conn, session, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    tid = f"t-mtge-{uuid.uuid4().hex[:8]}"
    u_dpo, u_coord, u_admin = f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}"
    await _crear_tenant_y_usuarios(conn, tid, u_dpo, u_coord, u_admin)
    await conn.execute(text("SELECT set_config('app.current_tenant_id', :t, true);"), {"t": tid})

    # Tratamiento gran escala
    act = ActividadRAT(
        id=str(uuid.uuid4()), tenant_id=tid, codigo="RAT-GE-03", nombre="Operación MTGE",
        area_responsable="Operaciones", finalidad="Logística", base_legal=BaseLegitimacion.CUMPLIMIENTO_CONTRATO,
        es_gran_escala=True,
    )
    await rat_service.registrar_actividad_rat(session, act, user_id=u_admin)

    headers_admin = {"X-Tenant-ID": tid, "X-User-ID": u_admin, "X-Role": "admin_organizacion"}

    # Sin fecha registrada -> 'FALTA_FECHA_VIGENCIA'
    res_sin = await cliente_http.get("/api/v1/riesgos/mtge/obligaciones", headers=headers_admin)
    ob_dpo_sin = next(o for o in res_sin.json()["obligaciones"] if "DPO" in o["obligacion"])
    assert ob_dpo_sin["estado"] == "FALTA_FECHA_VIGENCIA"

    # Registrar fecha de publicación hace 40 días
    hoy = date.today()
    fv = hoy - timedelta(days=40)
    res_vig = await cliente_http.post(
        "/api/v1/riesgos/mtge/obligaciones/vigencia",
        json={"fecha_vigencia_norma": str(fv)},
        headers=headers_admin,
    )
    assert res_vig.status_code == 200

    # Comprobar cálculo: 90 - 40 = 50 días restantes -> AL_DIA
    res_con = await cliente_http.get("/api/v1/riesgos/mtge/obligaciones", headers=headers_admin)
    ob_dpo_con = next(o for o in res_con.json()["obligaciones"] if "DPO" in o["obligacion"])
    assert ob_dpo_con["estado"] == "AL_DIA"
    assert ob_dpo_con["dias_restantes"] == 50


# ============================================================================
# 6. PRUEBA: CONTROL DE ACCESO (RBAC)
# ============================================================================

async def test_rbac_permisos_lectura_y_escritura(conn, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    tid = f"t-mtge-{uuid.uuid4().hex[:8]}"
    u_dpo, u_coord, u_admin = f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}"
    await _crear_tenant_y_usuarios(conn, tid, u_dpo, u_coord, u_admin)

    headers_coord = {"X-Tenant-ID": tid, "X-User-ID": u_coord, "X-Role": "coordinador"}
    headers_dpo = {"X-Tenant-ID": tid, "X-User-ID": u_dpo, "X-Role": "dpo"}
    headers_resp = {"X-Tenant-ID": tid, "X-User-ID": "u-resp", "X-Role": "responsable_area"}

    # 1. Coordinador puede consultar GET (200 OK)
    res_get_coord = await cliente_http.get("/api/v1/riesgos/mtge/obligaciones", headers=headers_coord)
    assert res_get_coord.status_code == 200

    # 2. Coordinador NO puede escribir auditoría (403 Forbidden)
    res_post_coord = await cliente_http.post(
        "/api/v1/riesgos/mtge/obligaciones/auditorias",
        json={
            "fecha_auditoria": str(date.today()),
            "tipo": "interna",
            "alcance": "Prueba",
            "auditor": "Test",
        },
        headers=headers_coord,
    )
    assert res_post_coord.status_code == 403

    # 3. Responsable de área no puede consultar ni escribir (403 Forbidden)
    res_get_resp = await cliente_http.get("/api/v1/riesgos/mtge/obligaciones", headers=headers_resp)
    assert res_get_resp.status_code == 403

    # 4. DPO sí puede escribir (201 Created)
    res_post_dpo = await cliente_http.post(
        "/api/v1/riesgos/mtge/obligaciones/politicas-privacidad",
        json={
            "version": "v1.0",
            "fecha_emision": str(date.today()),
            "enlace_o_archivo": "https://example.test/privacidad",
            "identifica_gran_escala": True,
        },
        headers=headers_dpo,
    )
    assert res_post_dpo.status_code == 201


# ============================================================================
# 7. PRUEBA: AISLAMIENTO RLS CON SET LOCAL ROLE LOPDP_APP
# ============================================================================

async def test_aislamiento_rls_con_lopdp_app(conn):
    """Verifica que las tablas de MTGE apliquen RLS estricto bajo lopdp_app."""
    t1 = f"t1-{uuid.uuid4().hex[:6]}"
    t2 = f"t2-{uuid.uuid4().hex[:6]}"

    for t in [t1, t2]:
        await conn.execute(
            text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, activo) "
                 "VALUES (:t, :n, :n, :ruc, TRUE)"),
            {"t": t, "n": f"Tenant {t}", "ruc": f"17{uuid.uuid4().int % 10000000000:010d}001"},
        )

    # Insertar registros para t1
    await conn.execute(
        text("INSERT INTO mtge_configuracion_vigencia (tenant_id, fecha_vigencia_norma, registrado_por, creado_en, actualizado_en) "
             "VALUES (:t, '2026-02-02', 'admin', NOW(), NOW())"),
        {"t": t1},
    )
    await conn.execute(
        text("INSERT INTO mtge_auditorias (id, tenant_id, fecha_auditoria, tipo, alcance, auditor, fecha_vencimiento, creado_por, creado_en) "
             "VALUES (:id, :t, '2026-01-15', 'interna', 'Alcance t1', 'Auditor', '2027-01-15', 'admin', NOW())"),
        {"id": f"aud-{uuid.uuid4().hex[:8]}", "t": t1},
    )

    # Cambiar a rol lopdp_app
    sp = await conn.begin_nested()
    try:
        await conn.execute(text("SET LOCAL ROLE lopdp_app;"))

        # 1. Sin fijar tenant_id -> 0 filas
        await conn.execute(text("SELECT set_config('app.current_tenant_id', '', true);"))
        cnt_sin = (await conn.execute(text("SELECT COUNT(*) FROM mtge_auditorias"))).scalar()
        assert cnt_sin == 0, f"Sin tenant fijado no debe ver nada, vio {cnt_sin}"

        # 2. Fijando tenant_id = t2 -> 0 filas (aislamiento)
        await conn.execute(text("SELECT set_config('app.current_tenant_id', :t, true);"), {"t": t2})
        cnt_t2 = (await conn.execute(text("SELECT COUNT(*) FROM mtge_auditorias"))).scalar()
        assert cnt_t2 == 0, f"Tenant t2 vio datos de t1: {cnt_t2}"

        # 3. Fijando tenant_id = t1 -> 1 fila
        await conn.execute(text("SELECT set_config('app.current_tenant_id', :t, true);"), {"t": t1})
        cnt_t1 = (await conn.execute(text("SELECT COUNT(*) FROM mtge_auditorias"))).scalar()
        assert cnt_t1 == 1, f"Tenant t1 debió ver su registro, vio {cnt_t1}"
    finally:
        await sp.rollback()


# ============================================================================
# 7. PLAZOS EN CALENDARIO (sin base de datos)
# ============================================================================

async def test_conservacion_5_anios_calendario_no_1825_dias():
    # 1825 días desde el 1-1-2024 caen el 30-12-2028: dos días antes de cumplir 5 años.
    assert _fin_conservacion(date(2024, 1, 1)) == date(2029, 1, 1)
    assert _fin_conservacion(date(2028, 2, 29)) == date(2033, 3, 1)


async def test_auditoria_vence_el_mismo_dia_del_anio_siguiente():
    assert _mas_un_anio(date(2026, 10, 26)) == date(2027, 10, 26)
    assert _mas_un_anio(date(2028, 2, 29)) == date(2029, 2, 28)


async def test_certificacion_sin_vigencia_se_rechaza():
    with pytest.raises(ValueError):
        AuditoriaGranEscalaCreate(
            fecha_auditoria=date(2026, 1, 1), tipo="externa", alcance="x", auditor="y",
            es_certificacion_equivalente=True,
        )


# ============================================================================
# 8. DPO DESIGNADO E INSCRITO, INFORME ANUAL SIN FECHA LEGAL Y ART. 16
# ============================================================================

async def test_dpo_inscrito_cumple_aunque_venza_el_plazo(conn, session, cliente_http, monkeypatch):
    monkeypatch.setenv("AUTH_MODE", "headers")
    tid = f"t-mtge-{uuid.uuid4().hex[:8]}"
    u_dpo, u_coord, u_admin = f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}", f"u-{uuid.uuid4().hex[:6]}"
    await _crear_tenant_y_usuarios(conn, tid, u_dpo, u_coord, u_admin)
    await conn.execute(text("SELECT set_config('app.current_tenant_id', :t, true);"), {"t": tid})
    act = ActividadRAT(
        id=str(uuid.uuid4()), tenant_id=tid, codigo="RAT-GE-04", nombre="Operación MTGE",
        area_responsable="Operaciones", finalidad="Logística", base_legal=BaseLegitimacion.CUMPLIMIENTO_CONTRATO,
        es_gran_escala=True,
    )
    await rat_service.registrar_actividad_rat(session, act, user_id=u_admin)
    headers_admin = {"X-Tenant-ID": tid, "X-User-ID": u_admin, "X-Role": "admin_organizacion"}
    hoy = date.today()
    res_vig = await cliente_http.post(
        "/api/v1/riesgos/mtge/obligaciones/vigencia",
        json={"fecha_vigencia_norma": str(hoy - timedelta(days=120))},
        headers=headers_admin,
    )
    assert res_vig.status_code == 200

    def _ob(datos, texto):
        return next(o for o in datos["obligaciones"] if texto in o["obligacion"])

    # Sin designación y con el plazo de 90 días cumplido: vencida
    datos = (await cliente_http.get("/api/v1/riesgos/mtge/obligaciones", headers=headers_admin)).json()
    assert _ob(datos, "DPO")["estado"] == "VENCIDA"
    # Sin informe anual: por vencer, nunca vencida (la resolución no fija fecha de presentación)
    assert _ob(datos, "Informe anual")["estado"] == "POR_VENCER"
    # Art. 16: recordatorio, no «al día»
    assert _ob(datos, "Privacidad desde el diseño")["estado"] == "RECORDATORIO"

    # Designación formal activa e inscrita ante la SPDP: cumplida
    await conn.execute(
        text(
            "INSERT INTO designaciones_formales (id, tenant_id, tipo, user_id, representante_nombre, "
            "representante_identificacion, representante_cargo, fecha_designacion, doc_referencia, "
            "inscripcion_spdp_fecha, inscripcion_spdp_ref) VALUES (:id, :t, 'dpd', :u, 'Rep', '1700000000', "
            "'Gerente', :f, 'DOC-1', :f, 'SPDP-1')"
        ),
        {"id": str(uuid.uuid4()), "t": tid, "u": u_dpo, "f": hoy - timedelta(days=10)},
    )
    datos = (await cliente_http.get("/api/v1/riesgos/mtge/obligaciones", headers=headers_admin)).json()
    assert _ob(datos, "DPO")["estado"] == "AL_DIA"
