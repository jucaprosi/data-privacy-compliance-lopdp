# ¤dpo-informe-anual
# ¤arbitro
"""Árbitro de DPO-02: informe anual del DPO e inscripción ante la SPDP.

Valida:
1. El informe de un año incluye solo las actuaciones de ese año y de esa organización.
2. Solo el rol `dpo` genera el informe (los demás reciben 403) y los demás roles lo consultan.
3. El documento descargable lleva la huella de la cadena de la bitácora en el pie.
4. La inscripción es un historial solo de alta: lopdp_app no edita ni borra (42501) y RLS aísla organizaciones.
5. Solo `admin_organizacion` registra la inscripción; el `dpo` la consulta; el cuerpo no fija la organización.

Las pruebas de dominio puro no tocan la BD; las de integración necesitan TEST_DATABASE_URL
(rama Neon propia) y se omiten sin ella. Datos ficticios.

Prueba de mutación (rama Neon test-dpo02): en `informe_anual_engine.armar_informe` se sustituyó
`del_anio = filtrar_por_anio(cadena, anio)` por `del_anio = cadena` (incluir actuaciones de otro año);
`pytest tests/test_dpo_informe_anual.py` falló en
`test_informe_incluye_solo_el_anio_y_la_organizacion` y en `test_filtrar_por_anio_excluye_otros_anios`.
Restaurada la línea, la prueba vuelve a pasar (ver informe de entrega para los códigos de salida).
"""
from __future__ import annotations

import os
import uuid
from datetime import date, datetime, timezone

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from api.errores import ErrorNegocio
from features.dpo_cockpit.domain.models import DictamenDPO, TipoDictamenDPO
from features.dpo_cockpit.services.informe_anual_engine import (
    filtrar_por_anio,
    renderizar_documento,
    resumir,
    validar_anio,
)
from features.dpo_cockpit.services.inscripcion_engine import normalizar_inscripcion
from main import app

client = TestClient(app)
INFORME = "/api/v1/dpo/informe-anual"
INSCRIPCION = "/api/v1/dpo/inscripcion"
ROLES = ("dpo", "admin_organizacion", "coordinador", "implementador", "responsable_area")


def _dictamen(tipo: TipoDictamenDPO, anio: int, mes: int = 3, tenant: str = "t") -> DictamenDPO:
    return DictamenDPO(
        tenant_id=tenant,
        dpo_id="dpo",
        tipo=tipo,
        asunto=f"Asunto {tipo.value} {anio}",
        referencia_normativa="POR VERIFICAR",
        cuerpo="Cuerpo ficticio",
        fecha_emision=datetime(anio, mes, 10, 12, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------- dominio puro (sin BD)

def test_filtrar_por_anio_excluye_otros_anios():
    ds = [
        _dictamen(TipoDictamenDPO.OPINION_CONSULTIVA, 2025),
        _dictamen(TipoDictamenDPO.OPINION_CONSULTIVA, 2026),
        _dictamen(TipoDictamenDPO.ADVERTENCIA_RIESGO, 2026, mes=12),
    ]
    assert [d.fecha_emision.year for d in filtrar_por_anio(ds, 2026)] == [2026, 2026]
    assert len(filtrar_por_anio(ds, 2025)) == 1
    assert filtrar_por_anio(ds, 2024) == []


def test_resumen_agrupa_consultas_dictamenes_y_escalamientos():
    ds = [
        _dictamen(TipoDictamenDPO.OPINION_CONSULTIVA, 2026),
        _dictamen(TipoDictamenDPO.OPINION_CONSULTIVA, 2026),
        _dictamen(TipoDictamenDPO.ADVERTENCIA_RIESGO, 2026),
        _dictamen(TipoDictamenDPO.ALERTA_RIESGO_GRAVE, 2026),
        _dictamen(TipoDictamenDPO.VALIDACION_EIPD, 2026),
        _dictamen(TipoDictamenDPO.DICTAMEN_TRANSFERENCIA, 2026),
    ]
    ds[2].acuse_recibo_alta_direccion = True
    r = resumir(ds)
    assert r["resumen"] == {
        "total_actuaciones": 6,
        "consultas_atendidas": 2,
        "dictamenes": 2,
        "escalamientos": 2,
        "con_acuse_de_direccion": 1,
        "sin_acuse_de_direccion": 5,
    }
    assert r["actuaciones_por_tipo"]["OPINION_CONSULTIVA"] == 2
    assert set(r["actuaciones_por_tipo"]) == {t.value for t in TipoDictamenDPO}


def test_anio_fuera_de_rango_lanza_error_de_negocio():
    hoy = datetime(2026, 10, 28, tzinfo=timezone.utc)
    assert validar_anio(2026, hoy) == 2026
    for malo in (2019, 2027, 0):
        with pytest.raises(ErrorNegocio) as exc:
            validar_anio(malo, hoy)
        assert exc.value.code == "DPO_INFORME_ANIO_INVALIDO"
        assert exc.value.status_code == 422


def test_documento_lleva_la_huella_en_el_pie_y_marca_la_cadena_alterada():
    base = {
        "tenant_id": "t", "anio": 2026, "generado_at": "2026-10-28T00:00:00+00:00",
        **resumir([]), "actuaciones": [], "inscripcion_spdp": None,
    }
    huella = "ab" * 32
    integra = renderizar_documento({**base, "cadena": {
        "huella": huella, "integra": True, "dictamen_alterado": None, "total_en_cadena": 0}})
    assert f"Huella de la cadena de la bitácora: {huella}" in integra.strip().splitlines()[-2]
    assert "íntegra" in integra
    alterada = renderizar_documento({**base, "cadena": {
        "huella": huella, "integra": False, "dictamen_alterado": "d-9", "total_en_cadena": 3}})
    assert "ALTERADA" in alterada and "d-9" in alterada


def test_inscripcion_exige_fecha_y_tramite_solo_si_esta_inscrito():
    hoy = date(2026, 10, 28)
    assert normalizar_inscripcion(False, date(2026, 1, 1), "X-1", hoy) == (None, None)
    assert normalizar_inscripcion(True, date(2026, 1, 1), "  TR-001 ", hoy) == (date(2026, 1, 1), "TR-001")
    for args in ((True, None, "TR"), (True, date(2026, 1, 1), "  "), (True, date(2026, 11, 1), "TR"),
                 (True, date(2026, 1, 1), "x" * 61)):
        with pytest.raises(ErrorNegocio) as exc:
            normalizar_inscripcion(*args, hoy=hoy)
        assert exc.value.code == "DPO_INSCRIPCION_INVALIDA"


# ---------------------------------------------------------------- integración (rama Neon propia)

def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Sin TEST_DATABASE_URL: la parte de BD de DPO-02 queda no verificada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def factory():
    url = _async_url()
    assert "ep-late-hall" not in url, "Nunca producción"
    engine = create_async_engine(url, pool_pre_ping=True)
    yield async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    await engine.dispose()


async def _como_app(s: AsyncSession, tenant: str, usuario: str = "") -> None:
    from app_core.db.session import fijar_contexto_rls

    await s.execute(text("SET LOCAL ROLE lopdp_app"))
    await fijar_contexto_rls(s, tenant, usuario)


@pytest_asyncio.fixture
async def env(factory):
    from app_core.db.session import fijar_contexto_rls
    from features.dpo_cockpit.services.bitacora_service import registrar_dictamen

    sfx = uuid.uuid4().hex[:8]
    ta, tb = f"dpo2a-{sfx}", f"dpo2b-{sfx}"
    ua = {rol: f"dpo2-ua-{rol[:5]}-{sfx}" for rol in ROLES}
    ub = {"dpo": f"dpo2-ub-dpo-{sfx}", "admin_organizacion": f"dpo2-ub-adm-{sfx}"}
    usuarios = (*ua.values(), *ub.values())

    async with factory() as s:
        for t in (ta, tb):
            await s.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                     "VALUES (:t, :t, :t, :t)"), {"t": t})
        for u in usuarios:
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'DPO-02 prueba')"),
                            {"u": u, "e": f"{u}@example.test"})
        for tenant, mapa in ((ta, ua), (tb, ub)):
            for rol, u in mapa.items():
                await fijar_contexto_rls(s, tenant, u)
                await s.execute(
                    text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
                    {"i": str(uuid.uuid4()), "u": u, "t": tenant, "r": rol})
        await s.commit()

    # Bitácora sembrada en orden cronológico (la cadena exige fechas crecientes).
    plan = [
        (ta, TipoDictamenDPO.OPINION_CONSULTIVA, 2025),
        (ta, TipoDictamenDPO.ADVERTENCIA_RIESGO, 2025),
        (ta, TipoDictamenDPO.OPINION_CONSULTIVA, 2026),
        (ta, TipoDictamenDPO.OPINION_CONSULTIVA, 2026),
        (ta, TipoDictamenDPO.VALIDACION_EIPD, 2026),
        (ta, TipoDictamenDPO.ALERTA_RIESGO_GRAVE, 2026),
        (tb, TipoDictamenDPO.OPINION_CONSULTIVA, 2026),
        (tb, TipoDictamenDPO.OPINION_CONSULTIVA, 2026),
        (tb, TipoDictamenDPO.OPINION_CONSULTIVA, 2026),
    ]
    ultimo_a = None
    async with factory() as s:
        for tenant, tipo, anio in plan:
            await _como_app(s, tenant, ua["dpo"] if tenant == ta else ub["dpo"])
            d = _dictamen(tipo, anio, tenant=tenant)
            d.dpo_id = ua["dpo"] if tenant == ta else ub["dpo"]
            await registrar_dictamen(s, d)
            if tenant == ta:
                ultimo_a = d.sha256_hash
            await s.commit()

    yield {"ta": ta, "tb": tb, "ua": ua, "ub": ub, "huella_a": ultimo_a}

    async with factory() as s:
        for t in (ta, tb):
            await fijar_contexto_rls(s, t)
            for sql in ("DELETE FROM audit_events WHERE tenant_id = :t",
                        "DELETE FROM dpo_inscripciones WHERE tenant_id = :t",
                        "DELETE FROM dpo_dictamenes WHERE tenant_id = :t",
                        "DELETE FROM user_tenant_roles WHERE tenant_id = :t"):
                await s.execute(text(sql), {"t": t})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t})
        for u in usuarios:
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": u})
        await s.commit()


def _cab(tenant: str, usuario: str, rol: str) -> dict[str, str]:
    return {"X-Tenant-ID": tenant, "X-User-ID": usuario, "X-Role": rol}


@pytest.mark.asyncio
async def test_informe_incluye_solo_el_anio_y_la_organizacion(env):
    h = _cab(env["ta"], env["ua"]["dpo"], "dpo")
    r = client.post(INFORME, headers=h, json={"anio": 2026})
    assert r.status_code == 200, r.text
    inf = r.json()
    assert inf["tenant_id"] == env["ta"] and inf["anio"] == 2026
    assert inf["resumen"]["total_actuaciones"] == 4, "2 actuaciones de 2025 y las de la org. B no cuentan"
    assert inf["resumen"]["consultas_atendidas"] == 2
    assert inf["resumen"]["dictamenes"] == 1
    assert inf["resumen"]["escalamientos"] == 1
    assert {a["fecha_emision"][:4] for a in inf["actuaciones"]} == {"2026"}
    assert inf["cadena"]["integra"] is True
    assert inf["cadena"]["huella"] == env["huella_a"], "la huella es la del último eslabón de la cadena de A"
    assert inf["cadena"]["total_en_cadena"] == 6

    r25 = client.get(INFORME, headers=h, params={"anio": 2025}).json()
    assert r25["resumen"]["total_actuaciones"] == 2
    assert r25["resumen"]["escalamientos"] == 1
    # Organización B: sus tres actuaciones, no las de A.
    hb = _cab(env["tb"], env["ub"]["dpo"], "dpo")
    assert client.post(INFORME, headers=hb, json={"anio": 2026}).json()["resumen"]["total_actuaciones"] == 3


@pytest.mark.asyncio
async def test_solo_el_dpo_genera_y_los_demas_roles_consultan(env):
    for rol in ROLES:
        h = _cab(env["ta"], env["ua"][rol], rol)
        generar = client.post(INFORME, headers=h, json={"anio": 2026})
        consultar = client.get(INFORME, headers=h, params={"anio": 2026})
        assert generar.status_code == (200 if rol == "dpo" else 403), rol
        assert consultar.status_code == 200, rol
        assert consultar.json()["resumen"]["total_actuaciones"] == 4, rol
    # Quien no es miembro de A no consulta A aunque la nombre en la cabecera.
    assert client.get(INFORME, headers=_cab(env["ta"], env["ub"]["dpo"], "dpo"), params={"anio": 2026}).status_code == 403


@pytest.mark.asyncio
async def test_anio_invalido_y_organizacion_del_cuerpo_se_ignora(env):
    h = _cab(env["ta"], env["ua"]["dpo"], "dpo")
    r = client.post(INFORME, headers=h, json={"anio": 2999})
    assert r.status_code == 422 and r.json()["code"] == "DPO_INFORME_ANIO_INVALIDO"
    r = client.post(INFORME, headers=h, json={"anio": 2026, "tenant_id": env["tb"]})
    assert r.json()["tenant_id"] == env["ta"] and r.json()["resumen"]["total_actuaciones"] == 4


@pytest.mark.asyncio
async def test_documento_descargable_con_huella_en_el_pie(env):
    h = _cab(env["ta"], env["ua"]["implementador"], "implementador")
    r = client.get(f"{INFORME}/documento", headers=h, params={"anio": 2026})
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"] and "informe-dpo-2026" in r.headers["content-disposition"]
    lineas = r.text.strip().splitlines()
    assert lineas[-2] == f"Huella de la cadena de la bitácora: {env['huella_a']}"
    assert "íntegra" in lineas[-1]
    assert "Consultas atendidas: 2" in r.text


@pytest.mark.asyncio
async def test_inscripcion_historial_solo_de_alta_y_roles(env):
    admin = _cab(env["ta"], env["ua"]["admin_organizacion"], "admin_organizacion")
    dpo = _cab(env["ta"], env["ua"]["dpo"], "dpo")
    assert client.get(INSCRIPCION, headers=dpo).json() == {"tenant_id": env["ta"], "vigente": None, "historial": []}

    # El dpo consulta pero no registra; quien no es dpo/admin/coordinador ni consulta.
    assert client.post(INSCRIPCION, headers=dpo, json={"inscrito": False}).status_code == 403
    impl = _cab(env["ta"], env["ua"]["implementador"], "implementador")
    assert client.get(INSCRIPCION, headers=impl).status_code == 403

    # Inscrito sin trámite se rechaza; "no inscrito" descarta fecha y trámite.
    r = client.post(INSCRIPCION, headers=admin, json={"inscrito": True, "fecha_inscripcion": "2026-02-01"})
    assert r.status_code == 422 and r.json()["code"] == "DPO_INSCRIPCION_INVALIDA"
    primera = client.post(INSCRIPCION, headers=admin, json={"inscrito": False, "numero_tramite": "SOBRA", "tenant_id": env["tb"]})
    assert primera.status_code == 200 and primera.json()["numero_tramite"] is None
    segunda = client.post(INSCRIPCION, headers=admin,
                          json={"inscrito": True, "fecha_inscripcion": "2026-02-01", "numero_tramite": "TR-0001"})
    assert segunda.status_code == 200
    assert segunda.json()["registrado_por"] == env["ua"]["admin_organizacion"], "quien registra sale del token"

    lectura = client.get(INSCRIPCION, headers=dpo).json()
    assert lectura["tenant_id"] == env["ta"]
    assert [i["id"] for i in lectura["historial"]] == [segunda.json()["id"], primera.json()["id"]]
    assert lectura["vigente"]["numero_tramite"] == "TR-0001"
    # La inscripción vigente entra al informe; B no ve la de A.
    inf = client.get(INFORME, headers=dpo, params={"anio": 2026}).json()
    assert inf["inscripcion_spdp"] == {"inscrito": True, "fecha_inscripcion": "2026-02-01", "numero_tramite": "TR-0001"}
    assert client.get(INSCRIPCION, headers=_cab(env["tb"], env["ub"]["dpo"], "dpo")).json()["historial"] == []


@pytest.mark.asyncio
async def test_lopdp_app_no_edita_ni_borra_y_rls_aisla(factory, env):
    admin = _cab(env["ta"], env["ua"]["admin_organizacion"], "admin_organizacion")
    ins = client.post(INSCRIPCION, headers=admin, json={"inscrito": True, "fecha_inscripcion": "2026-02-01",
                                                         "numero_tramite": "TR-0002"}).json()

    async with factory() as s:
        fila = (await s.execute(text("SELECT rolbypassrls, rolsuper FROM pg_roles WHERE rolname = 'lopdp_app'"))).one()
    assert (fila.rolbypassrls, fila.rolsuper) == (False, False)

    for sql in ("UPDATE dpo_inscripciones SET numero_tramite = 'X' WHERE id = :i",
                "DELETE FROM dpo_inscripciones WHERE id = :i"):
        async with factory() as s:
            await _como_app(s, env["ta"])
            with pytest.raises(DBAPIError) as exc:
                await s.execute(text(sql), {"i": ins["id"]})
            assert getattr(exc.value.orig, "sqlstate", None) == "42501", sql

    # RLS: la organización B no ve la fila de A y no puede insertar en nombre de A.
    async with factory() as s:
        await _como_app(s, env["tb"])
        assert (await s.execute(text("SELECT count(*) FROM dpo_inscripciones WHERE id = :i"), {"i": ins["id"]})).scalar_one() == 0
    async with factory() as s:
        await _como_app(s, env["tb"])
        with pytest.raises(DBAPIError) as exc:
            await s.execute(
                text("INSERT INTO dpo_inscripciones (id, tenant_id, inscrito, registrado_por) "
                     "VALUES (:i, :t, false, 'x')"), {"i": str(uuid.uuid4()), "t": env["ta"]})
        assert getattr(exc.value.orig, "sqlstate", None) == "42501"
    async with factory() as s:
        await _como_app(s, env["ta"])
        assert (await s.execute(text("SELECT count(*) FROM dpo_inscripciones WHERE id = :i"), {"i": ins["id"]})).scalar_one() == 1
