# -*- coding: utf-8 -*-
# ¤demo ¤seguridad-tenant ¤evidencias
"""DEMO-03e: copia y siembra de la sala Evidencias para la demo.

Corren contra PostgreSQL real (`db_engine`: el PG16 del arnés o evydentia-pruebas, nunca producción).
Mutaciones documentadas (cada una hace fallar la prueba indicada):
  - clonar sin traducir ids (copiar `id` o `documento_id` tal cual): falla
    test_ninguna_fila_apunta_a_ids_de_la_plantilla;
  - hacer `commit` dentro de la copia: falla test_la_copia_no_hace_commit;
  - copiar la huella y la clave sin recalcular: falla test_la_huella_se_recalcula_y_no_hay_objeto;
  - no fijar el tenant destino antes de insertar (copia como `lopdp_app`): falla
    test_con_rls_forzada_el_destino_no_ve_la_plantilla.
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

from app_core.pasillo import evidencias as pasillo
from features.evidencias.services.clon_plantilla_engine import PREFIJO_SIN_OBJETO, contenido_ficticio

BLOQUE = json.loads(
    (Path(__file__).resolve().parents[1] / "data" / "demo" / "cooperativa_demo.json").read_text(encoding="utf-8")
)["salas"]["evidencias"]
BORRADOS = (
    "DELETE FROM evidencias_vinculos WHERE tenant_id = :t",
    "DELETE FROM evidencias_documentos WHERE tenant_id = :t",
    "DELETE FROM user_tenant_roles WHERE tenant_id = :t",
)
DOC = ("SELECT id, codigo, sha256, tamano_bytes, clave_almacen, subido_por, normativa, retencion_dias "
       "FROM evidencias_documentos WHERE tenant_id = :t ORDER BY codigo")
VIN = ("SELECT id, documento_id, control_id, vinculado_por FROM evidencias_vinculos "
       "WHERE tenant_id = :t ORDER BY control_id")


def _fabrica(db_engine):
    return async_sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def tenants(db_engine):
    """Plantilla y destino de prueba, cada uno con su administrador. Se limpian al terminar."""
    sufijo = uuid.uuid4().hex[:8]
    plantilla, destino = f"test-pl-{sufijo}", f"test-dd-{sufijo}"
    usuarios = {plantilla: f"u-pl-{sufijo}", destino: f"u-dd-{sufijo}"}
    fabrica = _fabrica(db_engine)
    async with fabrica() as s:
        for tid, uid in usuarios.items():
            await s.execute(text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                                 "VALUES (:id, :n, :r, :ruc)"),
                            {"id": tid, "n": f"Test {tid}", "r": f"Test {tid} SA", "ruc": f"RUC{tid[:20]}"})
            await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:id, :e, :n)"),
                            {"id": uid, "e": f"{uid}@demo.invalid", "n": f"Usuario {uid}"})
            await s.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                                 "VALUES (:id, :u, :t, 'admin_organizacion')"),
                            {"id": f"r-{uid}", "u": uid, "t": tid})
        await s.commit()
    yield plantilla, destino, usuarios
    async with fabrica() as s:
        for tid, uid in usuarios.items():
            for sentencia in BORRADOS:
                await s.execute(text(sentencia), {"t": tid})
            await s.execute(text("DELETE FROM users WHERE id = :u"), {"u": uid})
            await s.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tid})
        await s.commit()


async def _foto(session, tenant_id: str) -> dict:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant_id})
    return {"docs": [tuple(f) for f in (await session.execute(text(DOC), {"t": tenant_id})).all()],
            "vins": [tuple(f) for f in (await session.execute(text(VIN), {"t": tenant_id})).all()]}


def _huella(obj) -> str:
    return hashlib.sha256(repr(obj).encode()).hexdigest()


async def _sembrada(db_engine, plantilla: str, con_vinculo: bool = False) -> None:
    async with _fabrica(db_engine)() as s:
        await pasillo.sembrar_en_plantilla(s, plantilla, BLOQUE)
        await s.commit()
        if con_vinculo:
            await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": plantilla})
            doc = (await s.execute(text(DOC), {"t": plantilla})).first()
            uid = (await s.execute(text("SELECT user_id FROM user_tenant_roles WHERE tenant_id = :t"),
                                   {"t": plantilla})).scalar_one()
            await s.execute(text("INSERT INTO evidencias_vinculos "
                                 "(id, tenant_id, documento_id, control_id, vinculado_por) "
                                 "VALUES (:i, :t, :d, 7, :u) ON CONFLICT DO NOTHING"),
                            {"i": f"v-{plantilla}", "t": plantilla, "d": doc[0], "u": uid})
            await s.commit()


# --- Siembra ---------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_dos_siembras_dejan_el_mismo_estado(db_engine, tenants):
    plantilla, _, _ = tenants
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        uno = await _foto(s, plantilla)
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        dos = await _foto(s, plantilla)
    assert _huella(uno) == _huella(dos)
    assert len(uno["docs"]) == len(BLOQUE["registros"])


@pytest.mark.asyncio
async def test_sembrar_sin_bloque_no_escribe(db_engine, tenants):
    plantilla, _, _ = tenants
    async with _fabrica(db_engine)() as s:
        await pasillo.sembrar_en_plantilla(s, plantilla, {})
        await s.commit()
        assert all(not v for v in (await _foto(s, plantilla)).values())


# --- Copia -----------------------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_el_destino_tiene_las_mismas_filas_con_otro_tenant(db_engine, tenants):
    plantilla, destino, usuarios = tenants
    await _sembrada(db_engine, plantilla, con_vinculo=True)
    async with _fabrica(db_engine)() as s:
        mapa = await pasillo.clonar_desde_plantilla(s, plantilla, destino, {"previo": "x"})
        await s.commit()
        origen, copia = await _foto(s, plantilla), await _foto(s, destino)
    assert mapa["previo"] == "x"
    assert len(copia["docs"]) == len(origen["docs"]) > 0 and len(copia["vins"]) == len(origen["vins"]) == 1
    assert [(d[1], d[6], d[7]) for d in copia["docs"]] == [(d[1], d[6], d[7]) for d in origen["docs"]]
    assert {d[5] for d in copia["docs"]} == {usuarios[destino]}
    assert [v[2] for v in copia["vins"]] == [7] and copia["vins"][0][3] == usuarios[destino]


@pytest.mark.asyncio
async def test_la_plantilla_queda_intacta(db_engine, tenants):
    plantilla, destino, _ = tenants
    await _sembrada(db_engine, plantilla, con_vinculo=True)
    async with _fabrica(db_engine)() as s:
        antes = _huella(await _foto(s, plantilla))
    async with _fabrica(db_engine)() as s:
        await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        await s.commit()
    async with _fabrica(db_engine)() as s:
        assert _huella(await _foto(s, plantilla)) == antes


@pytest.mark.asyncio
async def test_ninguna_fila_apunta_a_ids_de_la_plantilla(db_engine, tenants):
    plantilla, destino, _ = tenants
    await _sembrada(db_engine, plantilla, con_vinculo=True)
    async with _fabrica(db_engine)() as s:
        mapa = await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        await s.commit()
        origen, copia = await _foto(s, plantilla), await _foto(s, destino)
    ids_origen = {f[0] for filas in origen.values() for f in filas}
    ids_copia = {f[0] for filas in copia.values() for f in filas}
    assert not ids_origen & ids_copia
    assert set(mapa) == ids_origen and set(mapa.values()) == ids_copia
    assert {v[1] for v in copia["vins"]} <= {d[0] for d in copia["docs"]}


@pytest.mark.asyncio
async def test_la_huella_se_recalcula_y_no_hay_objeto(db_engine, tenants):
    plantilla, destino, _ = tenants
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        await s.commit()
        origen, copia = await _foto(s, plantilla), await _foto(s, destino)
    for d_o, d_c in zip(origen["docs"], copia["docs"]):
        contenido = contenido_ficticio(destino, d_c[1])
        assert d_c[2] == hashlib.sha256(contenido).hexdigest() and d_c[3] == len(contenido)
        assert d_c[2] != d_o[2]
        assert d_c[4] == f"{PREFIJO_SIN_OBJETO}/{destino}/{d_c[0]}" and plantilla not in d_c[4]


@pytest.mark.asyncio
async def test_clonar_dos_veces_no_duplica(db_engine, tenants):
    plantilla, destino, _ = tenants
    await _sembrada(db_engine, plantilla, con_vinculo=True)
    async with _fabrica(db_engine)() as s:
        uno = await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        dos = await pasillo.clonar_desde_plantilla(s, plantilla, destino, uno)
        await s.commit()
        foto = await _foto(s, destino)
    assert uno == dos
    assert len(foto["docs"]) == len(BLOQUE["registros"]) and len(foto["vins"]) == 1


@pytest.mark.asyncio
async def test_la_copia_no_hace_commit(db_engine, tenants):
    plantilla, destino, _ = tenants
    await _sembrada(db_engine, plantilla)
    async with _fabrica(db_engine)() as s:
        await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        await s.rollback()
    async with _fabrica(db_engine)() as s:
        assert all(not v for v in (await _foto(s, destino)).values())


@pytest.mark.asyncio
async def test_origen_igual_a_destino_se_niega(db_engine, tenants):
    plantilla, _, _ = tenants
    async with _fabrica(db_engine)() as s:
        with pytest.raises(ValueError):
            await pasillo.clonar_desde_plantilla(s, plantilla, plantilla, {})


@pytest.mark.asyncio
async def test_con_rls_forzada_el_destino_no_ve_la_plantilla(db_engine, tenants):
    plantilla, destino, _ = tenants
    await _sembrada(db_engine, plantilla, con_vinculo=True)
    # La copia misma corre con el rol de la aplicación: si no fija bien el tenant en cada paso, la RLS la rechaza.
    async with _fabrica(db_engine)() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await pasillo.clonar_desde_plantilla(s, plantilla, destino, {})
        await s.commit()
    async with _fabrica(db_engine)() as s:
        await s.execute(text("SET LOCAL ROLE lopdp_app"))
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": destino})
        for sentencia in ("SELECT tenant_id FROM evidencias_documentos", "SELECT tenant_id FROM evidencias_vinculos"):
            vistos = {f[0] for f in (await s.execute(text(sentencia))).all()}
            assert vistos == {destino}, (sentencia, vistos)
        await s.rollback()
