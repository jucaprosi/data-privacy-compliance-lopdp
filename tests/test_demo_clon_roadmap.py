# -*- coding: utf-8 -*-
# ¤demo ¤seguridad-tenant
"""DEMO-03c: copia y siembra de la sala Hoja de Ruta para la demo.

Corren contra PostgreSQL real (`db_engine`: el PG16 del arnés o evydentia-pruebas, nunca producción).
Mutaciones documentadas (cada una hace fallar la prueba indicada):
  - clonar sin traducir ids (copiar `id`, `wave_id` o `hallazgo_id` tal cual): falla
    test_ninguna_fila_apunta_a_ids_de_la_plantilla (y la clave primaria rechaza la copia);
  - hacer `commit` dentro de la copia: falla test_la_copia_no_hace_commit;
  - escribir en el tenant de origen: falla test_la_plantilla_queda_intacta;
  - ids aleatorios en vez de deterministas: falla test_clonar_dos_veces_no_duplica;
  - no fijar el tenant destino antes de insertar: falla test_con_rls_forzada_el_destino_no_ve_la_plantilla.
"""
from __future__ import annotations

import hashlib
import json
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app_core.pasillo import roadmap as pasillo

BLOQUE = json.loads(
    (Path(__file__).resolve().parents[1] / "data" / "demo" / "cooperativa_demo.json").read_text(encoding="utf-8")
)["salas"]["roadmap"]
TABLAS = ("task_dependencies", "roadmap_tasks", "roadmap_waves", "roadmaps", "hallazgos")


def _fabrica(db_engine):
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def tenants(db_engine):
    """Dos tenants de prueba: una «plantilla» y un destino. Se limpian al terminar."""
    sufijo = uuid.uuid4().hex[:8]
    plantilla, destino = f"test-pl-{sufijo}", f"test-dd-{sufijo}"
    fabrica = _fabrica(db_engine)
    async with fabrica() as s:
        for tid in (plantilla, destino):
            await s.execute(
                text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                     "VALUES (:id, :n, :r, :ruc)"),
                {"id": tid, "n": f"Test {tid}", "r": f"Test {tid} SA", "ruc": f"RUC{tid[:20]}"})
        await s.commit()
    yield plantilla, destino
    async with fabrica() as s:
        for tid in (plantilla, destino):
            await s.execute(text(
                "DELETE FROM task_dependencies WHERE task_id IN (SELECT id FROM roadmap_tasks WHERE tenant_id = :t)"),
                {"t": tid})
            for tabla in ("roadmap_tasks", "roadmap_waves", "roadmaps", "hallazgos"):
                await s.execute(text(f"DELETE FROM {tabla} WHERE tenant_id = :t"), {"t": tid})  # noqa: S608
            await s.execute(text("DELETE FROM areas WHERE tenant_id = :t"), {"t": tid})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tid})
        await s.commit()


async def _foto(session, tenant_id: str) -> dict[str, list]:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id})
    consultas = {
        "hallazgos": "SELECT id, origen_ref, titulo, estado, control_ref FROM hallazgos WHERE tenant_id = :t ORDER BY origen_ref",
        "roadmaps": "SELECT id, status FROM roadmaps WHERE tenant_id = :t ORDER BY id",
        "olas": "SELECT id, roadmap_id, name FROM roadmap_waves WHERE tenant_id = :t ORDER BY name",
        "tareas": "SELECT id, wave_id, hallazgo_id, title, status, area_id FROM roadmap_tasks WHERE tenant_id = :t ORDER BY title",
    }
    return {k: [tuple(f) for f in (await session.execute(text(q), {"t": tenant_id})).all()]
            for k, q in consultas.items()}


def _huella(obj) -> str:
    return hashlib.sha256(repr(obj).encode()).hexdigest()


async def _sembrada(db_engine, plantilla: str) -> None:
    async with _fabrica(db_engine)() as s:
        await pasillo.sembrar_en_plantilla(s, plantilla, BLOQUE)
        await s.commit()


# --- Siembra ---------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dos_siembras_dejan_el_mismo_estado(db_engine, tenants):
    plantilla, _ = tenants
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        uno = await _foto(s, plantilla)
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        dos = await _foto(s, plantilla)
    assert _huella(uno) == _huella(dos)
    assert len(uno["tareas"]) == len(BLOQUE["hallazgos_y_tareas"]) == len(uno["hallazgos"])
    assert len(uno["roadmaps"]) == len(uno["olas"]) == 1
    assert {t[3] for t in uno["tareas"]} == {e["titulo"] for e in BLOQUE["hallazgos_y_tareas"]}


@pytest.mark.asyncio
async def test_sembrar_sin_bloque_no_escribe(db_engine, tenants):
    plantilla, _ = tenants
    async with _fabrica(db_engine)() as s:
        await pasillo.sembrar_en_plantilla(s, plantilla, {})
        await s.commit()
        assert all(not v for v in (await _foto(s, plantilla)).values())


# --- Copia -----------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_el_destino_tiene_las_mismas_filas_con_otro_tenant(db_engine, tenants):
    plantilla, destino = tenants
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        mapa = await pasillo.clonar_desde_plantilla(s, plantilla, destino, {"previo": "x"})
        await s.commit()
        origen, copia = await _foto(s, plantilla), await _foto(s, destino)
    assert mapa["previo"] == "x"
    for clave in ("hallazgos", "roadmaps", "olas", "tareas"):
        assert len(copia[clave]) == len(origen[clave]) > 0
    assert [(t[3], t[4]) for t in copia["tareas"]] == [(t[3], t[4]) for t in origen["tareas"]]
    assert [(h[1], h[2], h[3]) for h in copia["hallazgos"]] == [(h[1], h[2], h[3]) for h in origen["hallazgos"]]
    async with _fabrica(db_engine)() as s:
        filas = (await s.execute(
            text("SELECT count(*) FROM roadmap_tasks WHERE tenant_id = :t"), {"t": destino})).scalar_one()
    assert filas == len(origen["tareas"])


@pytest.mark.asyncio
async def test_la_plantilla_queda_intacta(db_engine, tenants):
    plantilla, destino = tenants
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        antes = _huella(await _foto(s, plantilla))
    # La copia misma corre con el rol de la aplicación: si no fija bien el tenant en cada paso, la RLS la rechaza.
    async with _fabrica(db_engine)() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        await s.commit()
    async with _fabrica(db_engine)() as s:
        assert _huella(await _foto(s, plantilla)) == antes


@pytest.mark.asyncio
async def test_ninguna_fila_apunta_a_ids_de_la_plantilla(db_engine, tenants):
    plantilla, destino = tenants
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        mapa = await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        await s.commit()
        origen, copia = await _foto(s, plantilla), await _foto(s, destino)
    ids_origen = {f[0] for filas in origen.values() for f in filas}
    ids_copia = {f[0] for filas in copia.values() for f in filas}
    assert not ids_origen & ids_copia
    assert set(mapa) == ids_origen and set(mapa.values()) == ids_copia
    for ola in copia["olas"]:
        assert ola[1] in {r[0] for r in copia["roadmaps"]}
    for tarea in copia["tareas"]:
        assert tarea[1] in {o[0] for o in copia["olas"]}
        assert tarea[2] in {h[0] for h in copia["hallazgos"]}


@pytest.mark.asyncio
async def test_clonar_dos_veces_no_duplica(db_engine, tenants):
    plantilla, destino = tenants
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        uno = await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        dos = await pasillo.clonar_desde_plantilla(s, plantilla, destino, uno)
        await s.commit()
        foto = await _foto(s, destino)
    assert uno == dos
    assert len(foto["tareas"]) == len(BLOQUE["hallazgos_y_tareas"])
    assert len(foto["hallazgos"]) == len(foto["tareas"])


@pytest.mark.asyncio
async def test_la_copia_no_hace_commit(db_engine, tenants):
    plantilla, destino = tenants
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        await s.rollback()
    async with _fabrica(db_engine)() as s:
        assert all(not v for v in (await _foto(s, destino)).values())


@pytest.mark.asyncio
async def test_origen_igual_a_destino_se_niega(db_engine, tenants):
    plantilla, _ = tenants
    async with _fabrica(db_engine)() as s:
        with pytest.raises(ValueError):
            await pasillo.clonar_desde_plantilla(s, plantilla, plantilla, {})


@pytest.mark.asyncio
async def test_dependencias_y_areas_se_traducen(db_engine, tenants):
    plantilla, destino = tenants
    await _sembrada(db_engine, plantilla)
    area_pl, area_dd = f"area-{uuid.uuid4().hex[:8]}", f"area-{uuid.uuid4().hex[:8]}"
    async with _fabrica(db_engine)() as s:
        for tid, aid in ((plantilla, area_pl), (destino, area_dd)):
            await s.execute(text("INSERT INTO areas (id, tenant_id, nombre, codigo, nivel) "
                                 "VALUES (:i, :t, 'Unidad ficticia', 'DEMO-X', 'unidad')"), {"i": aid, "t": tid})
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": plantilla})
        tareas = [f[0] for f in (await s.execute(
            text("SELECT id FROM roadmap_tasks WHERE tenant_id = :t ORDER BY title"), {"t": plantilla})).all()]
        await s.execute(text("UPDATE roadmap_tasks SET area_id = :a WHERE id = :i"), {"a": area_pl, "i": tareas[0]})
        await s.execute(text("UPDATE roadmap_tasks SET area_id = :a WHERE id = :i"), {"a": area_pl, "i": tareas[1]})
        await s.execute(text("INSERT INTO task_dependencies VALUES (:a, :b)"), {"a": tareas[1], "b": tareas[0]})
        await s.commit()
    async with _fabrica(db_engine)() as s:
        # Solo la primera área está en el mapa: la otra no puede quedar apuntando a la plantilla.
        mapa = await pasillo.clonar_desde_plantilla(s, plantilla, destino, {area_pl: area_dd})
        await s.commit()
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": destino})
        areas = (await s.execute(text("SELECT area_id FROM roadmap_tasks WHERE tenant_id = :t"), {"t": destino})).all()
        deps = (await s.execute(text(
            "SELECT task_id, depends_on_task_id FROM task_dependencies WHERE task_id = :a"),
            {"a": mapa[tareas[1]]})).all()
    assert {a[0] for a in areas} == {area_dd, None}
    assert [tuple(d) for d in deps] == [(mapa[tareas[1]], mapa[tareas[0]])]


@pytest.mark.asyncio
async def test_con_rls_forzada_el_destino_no_ve_la_plantilla(db_engine, tenants):
    plantilla, destino = tenants
    await _sembrada(db_engine, plantilla)
    # La copia misma corre con el rol de la aplicación: si no fija bien el tenant en cada paso, la RLS la rechaza.
    async with _fabrica(db_engine)() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        await s.commit()
    async with _fabrica(db_engine)() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": destino})
        for tabla in ("roadmap_tasks", "roadmap_waves", "roadmaps", "hallazgos"):
            tenants_vistos = {f[0] for f in (await s.execute(text(f"SELECT tenant_id FROM {tabla}"))).all()}  # noqa: S608
            assert tenants_vistos == {destino}, (tabla, tenants_vistos)
        await s.rollback()
