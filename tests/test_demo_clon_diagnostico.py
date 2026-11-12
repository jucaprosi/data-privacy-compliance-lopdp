# -*- coding: utf-8 -*-
# ¤demo ¤seguridad-tenant ¤diagnostico
"""DEMO-03b: copia y siembra de la sala Diagnóstico para la demo.

Corren contra PostgreSQL real (`db_engine`: el PG16 del arnés o evydentia-pruebas, nunca producción).
Mutaciones documentadas (cada una hace fallar la prueba indicada):
  - clonar sin traducir ids (copiar `id` de asignaciones o resultados tal cual): falla
    test_ninguna_fila_apunta_a_ids_de_la_plantilla (y la clave primaria rechaza la copia);
  - hacer `commit` dentro de la copia: falla test_la_copia_no_hace_commit;
  - escribir en el tenant de origen: falla test_la_plantilla_queda_intacta;
  - ids aleatorios en vez de deterministas: falla test_clonar_dos_veces_no_duplica;
  - copiar la huella del origen sin recalcularla: falla test_la_cadena_del_clon_es_integra_y_propia;
  - no fijar el tenant destino antes de insertar: falla test_con_rls_forzada_el_destino_no_ve_la_plantilla.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.pasillo import diagnostico as pasillo
from features.diagnostico.domain.resultados import DimensionSellada, IndicadoresSellados, ResultadoSellado
from features.diagnostico.services.resultados_engine import (
    _fila_a_resultado,
    calcular_huella,
    primer_resultado_alterado,
    tipo_de_secuencia,
)

BLOQUE = json.loads(
    (Path(__file__).resolve().parents[1] / "data" / "demo" / "cooperativa_demo.json").read_text(encoding="utf-8")
)["salas"]["diagnostico"]
BORRADOS = (
    "DELETE FROM diagnostico_respuestas WHERE tenant_id = :t",
    "DELETE FROM diagnostico_asignaciones WHERE tenant_id = :t",
    "DELETE FROM diagnostico_resultados WHERE tenant_id = :t",
    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
)
VISTOS = (
    "SELECT tenant_id FROM diagnostico_respuestas",
    "SELECT tenant_id FROM diagnostico_asignaciones",
    "SELECT tenant_id FROM diagnostico_resultados",
)


def _fabrica(db_engine):
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def tenants(db_engine):
    """Una «plantilla» y un destino, cada uno con su administrador. Se limpian al terminar."""
    sufijo = uuid.uuid4().hex[:8]
    plantilla, destino = f"test-pl-{sufijo}", f"test-dd-{sufijo}"
    admin_pl, admin_dd = f"admin-pl-{sufijo}", f"admin-dd-{sufijo}"
    fabrica = _fabrica(db_engine)
    async with fabrica() as s:
        for tid, uid in ((plantilla, admin_pl), (destino, admin_dd)):
            await s.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                     "VALUES (:id, :n, :r, :ruc)"),
                {"id": tid, "n": f"Test {tid}", "r": f"Test {tid} SA", "ruc": f"RUC{tid[:20]}"})
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'Persona ficticia')"),
                            {"u": uid, "e": f"{uid}@correo.invalid"})
            await s.execute(
                text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, 'admin_organizacion')"),
                {"i": str(uuid.uuid4()), "u": uid, "t": tid})
        await s.commit()
    yield {"plantilla": plantilla, "destino": destino, "admin_pl": admin_pl, "admin_dd": admin_dd}
    async with fabrica() as s:
        for tid in (plantilla, destino):
            for sentencia in BORRADOS:
                await s.execute(text(sentencia), {"t": tid})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tid})
        await s.execute(text("DELETE FROM users WHERE id IN (:a, :b)"), {"a": admin_pl, "b": admin_dd})
        await s.commit()


async def _foto(session, tenant_id: str) -> dict[str, list]:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id})
    consultas = {
        "respuestas": "SELECT pregunta_id, control, dimension, estado, nivel_asignado, nivel_evidencia, "
                      "criticidad, riesgo_base, respondido_por FROM diagnostico_respuestas "
                      "WHERE tenant_id = :t ORDER BY pregunta_id",
        "asignaciones": "SELECT id, dimension, responsable_user_id, asignado_por FROM diagnostico_asignaciones "
                        "WHERE tenant_id = :t ORDER BY dimension, id",
        "resultados": "SELECT id, secuencia, tipo, sellado_por, huella_anterior, huella FROM diagnostico_resultados "
                      "WHERE tenant_id = :t ORDER BY secuencia",
    }
    return {k: [tuple(f) for f in (await session.execute(text(q), {"t": tenant_id})).all()]
            for k, q in consultas.items()}


def _huella(obj) -> str:
    return hashlib.sha256(repr(obj).encode()).hexdigest()


async def _sembrada(db_engine, plantilla: str) -> None:
    async with _fabrica(db_engine)() as s:
        await pasillo.sembrar_en_plantilla(s, plantilla, BLOQUE)
        await s.commit()


def _sello(tenant: str, usuario: str, secuencia: int, anterior: str) -> ResultadoSellado:
    indicadores = IndicadoresSellados(
        cumplimiento=False, brechas_criticas=2, brechas_altas=3,
        por_dimension=[DimensionSellada("D01", "Gobierno", 3, "Definido", 61.0, 100.0, 1, 1)],
        respaldo_documental=42.5, preguntas_evaluadas=10, preguntas_aplicables=12, cobertura=83.3)
    r = ResultadoSellado(
        id=str(uuid.uuid4()), tenant_id=tenant, secuencia=secuencia, sellado_por=usuario,
        sellado_en=datetime(2026, 11, 9, 12, secuencia, tzinfo=timezone.utc), normativa="LOPDP",
        version_normativa="1", tamano="mediana", perfil={}, respuestas=[], indicadores=indicadores,
        huella_anterior=anterior)
    r.huella = calcular_huella(r.contenido())
    return r


async def _con_sellos_y_asignaciones(db_engine, t: dict, personas_extra: dict[str, str]) -> list[ResultadoSellado]:
    """Siembra los dos sellos de DIAG-11 y dos asignaciones de dominio en la plantilla."""
    sellos, anterior = [], "0" * 64
    for secuencia in (1, 2):
        sello = _sello(t["plantilla"], t["admin_pl"], secuencia, anterior)
        sellos.append(sello)
        anterior = sello.huella
    async with _fabrica(db_engine)() as s:
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t["plantilla"]})
        for sello in sellos:
            c = sello.contenido()
            await s.execute(
                text("INSERT INTO diagnostico_resultados (id, tenant_id, secuencia, sellado_por, sellado_en, normativa, "
                     "version_normativa, tamano, perfil, respuestas, indicadores, huella_anterior, huella, tipo) VALUES "
                     "(:id, :t, :sec, :por, :en, 'LOPDP', '1', 'mediana', CAST(:perfil AS jsonb), "
                     "CAST(:resp AS jsonb), CAST(:ind AS jsonb), :ha, :h, :tipo)"),
                {"id": sello.id, "t": t["plantilla"], "sec": sello.secuencia, "por": t["admin_pl"],
                 "en": sello.sellado_en, "perfil": json.dumps(c["perfil"]), "resp": json.dumps(c["respuestas"]),
                 "ind": json.dumps(c["indicadores"]), "ha": sello.huella_anterior, "h": sello.huella,
                 "tipo": tipo_de_secuencia(sello.secuencia)})
        for dimension, responsable in (("D01", t["admin_pl"]), ("D02", "persona-fuera-del-mapa")):
            await s.execute(
                text("INSERT INTO diagnostico_asignaciones (id, tenant_id, dimension, responsable_user_id, asignado_por) "
                     "VALUES (:i, :t, :d, :r, :a)"),
                {"i": str(uuid.uuid4()), "t": t["plantilla"], "d": dimension, "r": responsable, "a": t["admin_pl"]})
        await s.commit()
    return sellos


# --- Siembra ---------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dos_siembras_dejan_el_mismo_estado(db_engine, tenants):
    plantilla = tenants["plantilla"]
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        uno = await _foto(s, plantilla)
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        dos = await _foto(s, plantilla)
    assert _huella(uno) == _huella(dos)
    assert len(uno["respuestas"]) == BLOQUE["respondidas"] < BLOQUE["total"]
    assert {r[8] for r in uno["respuestas"]} == {tenants["admin_pl"]}
    # La plantilla está «en revisión»: ningún sello gastado de los dos de DIAG-11.
    assert uno["resultados"] == [] and uno["asignaciones"] == []


@pytest.mark.asyncio
async def test_la_siembra_muestra_varios_estados_y_dimensiones(db_engine, tenants):
    await _sembrada(db_engine, tenants["plantilla"])
    async with _fabrica(db_engine)() as s:
        foto = await _foto(s, tenants["plantilla"])
    assert {r[3] for r in foto["respuestas"]} >= {"Conforme", "Parcial", "No Conforme"}
    assert len({r[2] for r in foto["respuestas"]}) > 1
    assert all(1 <= r[7] <= 10 for r in foto["respuestas"])


@pytest.mark.asyncio
async def test_sembrar_sin_bloque_no_escribe(db_engine, tenants):
    async with _fabrica(db_engine)() as s:
        await pasillo.sembrar_en_plantilla(s, tenants["plantilla"], {})
        await s.commit()
        assert all(not v for v in (await _foto(s, tenants["plantilla"])).values())


# --- Copia -----------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_el_destino_tiene_las_mismas_filas_con_otro_tenant(db_engine, tenants):
    t = tenants
    await _sembrada(db_engine, t["plantilla"])
    await _con_sellos_y_asignaciones(db_engine, t, {})
    async with _fabrica(db_engine)() as s:
        mapa = await pasillo.clonar_desde_plantilla(s, t["plantilla"], t["destino"], {"previo": "x", t["admin_pl"]: t["admin_dd"]})
        await s.commit()
        origen, copia = await _foto(s, t["plantilla"]), await _foto(s, t["destino"])
    assert mapa["previo"] == "x"
    for clave in ("respuestas", "asignaciones", "resultados"):
        assert len(copia[clave]) == len(origen[clave]) > 0
    assert [r[:8] for r in copia["respuestas"]] == [r[:8] for r in origen["respuestas"]]
    assert {r[8] for r in copia["respuestas"]} == {t["admin_dd"]}
    assert [(r[1], r[2]) for r in copia["resultados"]] == [(r[1], r[2]) for r in origen["resultados"]] == [(1, "prueba"), (2, "real")]


@pytest.mark.asyncio
async def test_la_plantilla_queda_intacta(db_engine, tenants):
    t = tenants
    await _sembrada(db_engine, t["plantilla"])
    await _con_sellos_y_asignaciones(db_engine, t, {})
    async with _fabrica(db_engine)() as s:
        antes = _huella(await _foto(s, t["plantilla"]))
    # La copia misma corre con el rol de la aplicación: si no fija bien el tenant en cada paso, la RLS la rechaza.
    async with _fabrica(db_engine)() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await pasillo.clonar_desde_plantilla(s, t["plantilla"], t["destino"], {})
        await s.commit()
    async with _fabrica(db_engine)() as s:
        assert _huella(await _foto(s, t["plantilla"])) == antes


@pytest.mark.asyncio
async def test_ninguna_fila_apunta_a_ids_de_la_plantilla(db_engine, tenants):
    t = tenants
    await _sembrada(db_engine, t["plantilla"])
    await _con_sellos_y_asignaciones(db_engine, t, {})
    async with _fabrica(db_engine)() as s:
        mapa = await pasillo.clonar_desde_plantilla(s, t["plantilla"], t["destino"], {})
        await s.commit()
        origen, copia = await _foto(s, t["plantilla"]), await _foto(s, t["destino"])
    ids_origen = {f[0] for k in ("asignaciones", "resultados") for f in origen[k]}
    ids_copia = {f[0] for k in ("asignaciones", "resultados") for f in copia[k]}
    assert ids_origen and not ids_origen & ids_copia
    assert set(mapa) == ids_origen and set(mapa.values()) == ids_copia
    # Las personas de la plantilla no pasan al destino: sin mapa, quedan como el administrador del destino.
    personas_copia = ({r[8] for r in copia["respuestas"]} | {r[3] for r in copia["asignaciones"]}
                      | {r[3] for r in copia["resultados"]})
    assert t["admin_pl"] not in personas_copia and personas_copia == {t["admin_dd"]}
    assert {r[2] for r in copia["asignaciones"]} == {None}


@pytest.mark.asyncio
async def test_las_personas_del_mapa_se_traducen(db_engine, tenants):
    t = tenants
    await _con_sellos_y_asignaciones(db_engine, t, {})
    async with _fabrica(db_engine)() as s:
        await pasillo.clonar_desde_plantilla(s, t["plantilla"], t["destino"], {t["admin_pl"]: t["admin_dd"]})
        await s.commit()
        copia = await _foto(s, t["destino"])
    por_dimension = {r[1]: r for r in copia["asignaciones"]}
    assert por_dimension["D01"][2] == t["admin_dd"]
    assert por_dimension["D02"][2] is None


@pytest.mark.asyncio
async def test_la_cadena_del_clon_es_integra_y_propia(db_engine, tenants):
    t = tenants
    origen_sellos = await _con_sellos_y_asignaciones(db_engine, t, {})
    async with _fabrica(db_engine)() as s:
        await pasillo.clonar_desde_plantilla(s, t["plantilla"], t["destino"], {})
        await s.commit()
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t["destino"]})
        filas = (await s.execute(text(
            "SELECT id, tenant_id, secuencia, sellado_por, sellado_en, normativa, version_normativa, tamano, perfil, "
            "respuestas, indicadores, huella_anterior, huella FROM diagnostico_resultados "
            "WHERE tenant_id = :t ORDER BY secuencia"), {"t": t["destino"]})).mappings().all()
    copias = [_fila_a_resultado(dict(f)) for f in filas]
    assert len(copias) == 2 and primer_resultado_alterado(copias) is None
    assert copias[0].huella != origen_sellos[0].huella and copias[1].huella != origen_sellos[1].huella
    assert copias[1].huella_anterior == copias[0].huella
    assert all(c.tenant_id == t["destino"] for c in copias)


@pytest.mark.asyncio
async def test_clonar_dos_veces_no_duplica(db_engine, tenants):
    t = tenants
    await _sembrada(db_engine, t["plantilla"])
    await _con_sellos_y_asignaciones(db_engine, t, {})
    async with _fabrica(db_engine)() as s:
        uno = await pasillo.clonar_desde_plantilla(s, t["plantilla"], t["destino"], {})
        dos = await pasillo.clonar_desde_plantilla(s, t["plantilla"], t["destino"], uno)
        await s.commit()
        foto = await _foto(s, t["destino"])
    assert uno == dos
    assert len(foto["respuestas"]) == BLOQUE["respondidas"]
    assert len(foto["asignaciones"]) == 2 and len(foto["resultados"]) == 2


@pytest.mark.asyncio
async def test_la_copia_no_hace_commit(db_engine, tenants):
    t = tenants
    await _sembrada(db_engine, t["plantilla"])
    async with _fabrica(db_engine)() as s:
        await pasillo.clonar_desde_plantilla(s, t["plantilla"], t["destino"], {})
        await s.rollback()
    async with _fabrica(db_engine)() as s:
        assert all(not v for v in (await _foto(s, t["destino"])).values())


@pytest.mark.asyncio
async def test_origen_igual_a_destino_se_niega(db_engine, tenants):
    async with _fabrica(db_engine)() as s:
        with pytest.raises(ValueError):
            await pasillo.clonar_desde_plantilla(s, tenants["plantilla"], tenants["plantilla"], {})


@pytest.mark.asyncio
async def test_con_rls_forzada_el_destino_no_ve_la_plantilla(db_engine, tenants):
    t = tenants
    await _sembrada(db_engine, t["plantilla"])
    await _con_sellos_y_asignaciones(db_engine, t, {})
    # La copia misma corre con el rol de la aplicación: si no fija bien el tenant en cada paso, la RLS la rechaza.
    async with _fabrica(db_engine)() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await pasillo.clonar_desde_plantilla(s, t["plantilla"], t["destino"], {})
        await s.commit()
    async with _fabrica(db_engine)() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": t["destino"]})
        for sentencia in VISTOS:
            vistos = {f[0] for f in (await s.execute(text(sentencia))).all()}
            assert vistos == {t["destino"]}, (sentencia, vistos)
        await s.rollback()
