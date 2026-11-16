# -*- coding: utf-8 -*-
# ¤demo ¤adpa ¤seguridad-tenant
"""DEMO-03f: copia y siembra de la plantilla «Cooperativa Demo» en la sala videovigilancia.

Las pruebas con base corren contra PostgreSQL real (`db_engine`: arnés local o evydentia-pruebas),
dentro de una transacción que se deshace al final: no dejan filas.

Mutaciones documentadas (cada una hace fallar la prueba indicada):
  - copiar sin filtrar por tenant del origen -> test_copia_solo_lo_de_la_plantilla;
  - no traducir creado_por con mapa_ids -> test_el_destino_tiene_las_mismas_filas_con_otro_tenant;
  - insertar sin ON CONFLICT o con ids aleatorios -> test_clonar_dos_veces_no_duplica;
  - hacer commit dentro del motor -> test_no_hace_commit_y_restaura_el_contexto y test_el_motor_no_hace_commit_ni_importa_otra_sala;
  - escribir con el contexto del origen -> test_rls_el_destino_no_ve_la_plantilla;
  - copiar clips o grabaciones de bóveda -> test_no_copia_clips_solo_inventario;
  - sembrar con id no determinista o codec inválido -> test_dos_siembras_dejan_el_mismo_estado.
"""
from __future__ import annotations

import hashlib
import inspect
import json
import os
import re
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

if not os.environ.get("DATABASE_URL"):
    os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL") or "postgresql+psycopg://u:c@localhost/pruebas"

from app_core.pasillo import videovigilancia as pasillo
from features.demo.domain.plantilla import PLANTILLA_TENANT_ID
from features.videovigilancia import videovigilancia_service as compuerta
from features.videovigilancia.services import clon_plantilla_engine as motor

RAIZ = Path(__file__).resolve().parents[1]
MOTOR = RAIZ / "features" / "videovigilancia" / "services" / "clon_plantilla_engine.py"
BLOQUE = {
    "camaras": [
        {"clave": "cam-recepcion", "nombre_ubicacion": "Recepción (ficticia)", "codec": "H265_PLUS"},
        {"clave": "cam-archivo", "nombre_ubicacion": "Archivo (ficticio)", "codec": "H265"},
    ]
}


def _id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:10]}"


async def _contexto(session: AsyncSession, tenant: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})


async def _tenant(session: AsyncSession, tid: str) -> str:
    await session.execute(
        text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:i, :n, :n, :r)"),
        {"i": tid, "n": f"Prueba {tid}", "r": f"R{uuid.uuid4().hex[:12]}"},
    )
    return tid


async def _usuario(session: AsyncSession, tid: str, rol: str) -> str:
    uid = _id("u")
    await session.execute(
        text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Persona ficticia')"),
        {"i": uid, "e": f"{uid}@prueba.invalid"},
    )
    await _contexto(session, tid)
    await session.execute(
        text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
        {"i": _id("r"), "u": uid, "t": tid, "r": rol},
    )
    return uid


async def _camara(session: AsyncSession, tid: str, autor: str, ubicacion: str, codec: str = "H265") -> str:
    cid = str(uuid.uuid4())
    await _contexto(session, tid)
    await session.execute(
        text(
            "INSERT INTO cctv_camaras_inventario (id, tenant_id, nombre_ubicacion, codec, "
            "modo_grabacion, audio_ambiental_activo, mascara_privacidad_activa, plazo_retencion_dias, "
            "estado_conformidad, creado_por) VALUES (:i, :t, :u, :c, 'EVENTO_MOVIMIENTO', false, true, 15, 'CONFORME', :a)"
        ),
        {"i": cid, "t": tid, "u": ubicacion, "c": codec, "a": autor},
    )
    return cid


@pytest_asyncio.fixture
async def mundo(db_engine):
    """Plantilla con dos cámaras, tenant ajeno con una y destino con persona administradora."""
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        plantilla = await _tenant(s, _id("t-plantilla"))
        destino = await _tenant(s, _id("t-destino"))
        ajeno = await _tenant(s, _id("t-ajeno"))
        autor_p = await _usuario(s, plantilla, "admin_organizacion")
        autor_d = await _usuario(s, destino, "admin_organizacion")
        autor_a = await _usuario(s, ajeno, "admin_organizacion")
        camaras = [
            await _camara(s, plantilla, autor_p, "Recepción (ficticia)", "H265_PLUS"),
            await _camara(s, plantilla, autor_p, "Archivo (ficticio)", "H265"),
        ]
        cam_ajena = await _camara(s, ajeno, autor_a, "Cámara ajena de otra organización")
        yield {
            "s": s,
            "plantilla": plantilla,
            "destino": destino,
            "ajeno": ajeno,
            "camaras": camaras,
            "cam_ajena": cam_ajena,
            "mapa": {autor_p: autor_d},
        }
        await s.rollback()


async def _filas_camaras(s: AsyncSession, tid: str) -> list[tuple]:
    await _contexto(s, tid)
    return [
        tuple(f)
        for f in (
            await s.execute(
                text(
                    "SELECT nombre_ubicacion, codec, modo_grabacion, audio_ambiental_activo, "
                    "mascara_privacidad_activa, plazo_retencion_dias, estado_conformidad, creado_por "
                    "FROM cctv_camaras_inventario WHERE tenant_id=:t ORDER BY nombre_ubicacion"
                ),
                {"t": tid},
            )
        ).all()
    ]


# --- Pruebas con base de datos (se omiten limpiamente si db_engine no está configurada) ---


@pytest.mark.asyncio
async def test_el_destino_tiene_las_mismas_filas_con_otro_tenant(mundo):
    s, m = mundo["s"], mundo
    antes = await _filas_camaras(s, m["plantilla"])
    ampliado = await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])

    despues = await _filas_camaras(s, m["destino"])
    assert len(despues) == 2
    assert [f[:7] for f in despues] == [f[:7] for f in antes]
    assert {f[7] for f in despues} == set(m["mapa"].values())
    assert set(m["mapa"].items()) <= set(ampliado.items())
    assert set(m["camaras"]) <= set(ampliado)
    assert not set(m["camaras"]) & set(ampliado.values())


@pytest.mark.asyncio
async def test_la_plantilla_queda_intacta_y_nada_apunta_a_ella(mundo):
    s, m = mundo["s"], mundo
    antes = await _filas_camaras(s, m["plantilla"])
    await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    assert await _filas_camaras(s, m["plantilla"]) == antes
    await _contexto(s, m["destino"])
    ids_destino = [
        str(r[0])
        for r in (await s.execute(text("SELECT id FROM cctv_camaras_inventario WHERE tenant_id=:t"), {"t": m["destino"]})).all()
    ]
    assert ids_destino and not set(ids_destino) & set(m["camaras"])


@pytest.mark.asyncio
async def test_copia_solo_lo_de_la_plantilla(mundo):
    s, m = mundo["s"], mundo
    ampliado = await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    assert m["cam_ajena"] not in ampliado
    assert all("otra organización" not in f[0] for f in await _filas_camaras(s, m["destino"]))


@pytest.mark.asyncio
async def test_clonar_dos_veces_no_duplica(mundo):
    s, m = mundo["s"], mundo
    uno = await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    estado = await _filas_camaras(s, m["destino"])
    dos = await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    assert uno == dos
    assert await _filas_camaras(s, m["destino"]) == estado


@pytest.mark.asyncio
async def test_no_hace_commit_y_restaura_el_contexto(mundo):
    s, m = mundo["s"], mundo
    s.commit = AsyncMock(side_effect=AssertionError("el clon no confirma la transacción"))
    await _contexto(s, m["destino"])
    await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    s.commit.assert_not_called()
    actual = (await s.execute(text("SELECT current_setting('app.current_tenant_id', true)"))).scalar()
    assert actual == m["destino"]


@pytest.mark.asyncio
async def test_rls_el_destino_no_ve_la_plantilla(mundo):
    s, m = mundo["s"], mundo
    await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    await s.execute(text("SET LOCAL ROLE lopdp_app"))
    await _contexto(s, m["destino"])
    vistos = {r[0] for r in (await s.execute(text("SELECT tenant_id FROM cctv_camaras_inventario"))).all()}
    assert vistos == {m["destino"]}
    await s.execute(text("RESET ROLE"))


@pytest.mark.asyncio
async def test_no_copia_clips_solo_inventario(mundo):
    s, m = mundo["s"], mundo
    await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    await _contexto(s, m["destino"])
    # Verificar que el destino no tiene clips ni referencias a grabaciones
    existe_clips = (
        await s.execute(
            text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'cctv_clips_boveda')"
            )
        )
    ).scalar()
    if existe_clips:
        clips = (await s.execute(text("SELECT count(*) FROM cctv_clips_boveda WHERE tenant_id=:t"), {"t": m["destino"]})).scalar()
        assert clips == 0


@pytest.mark.asyncio
async def test_clonar_en_si_mismo_o_sin_traducir_al_autor_falla(mundo):
    s, m = mundo["s"], mundo
    with pytest.raises(ValueError):
        await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["plantilla"], m["mapa"])
    with pytest.raises(ValueError):
        await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], {})


@pytest.mark.asyncio
async def test_dos_siembras_dejan_el_mismo_estado(db_engine):
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        tid = await _tenant(s, _id("t-siembra"))
        await _usuario(s, tid, "admin_organizacion")
        await pasillo.sembrar_en_plantilla(s, tid, BLOQUE)
        filas1 = await _filas_camaras(s, tid)
        assert len(filas1) == 2
        await pasillo.sembrar_en_plantilla(s, tid, BLOQUE)
        filas2 = await _filas_camaras(s, tid)
        assert filas1 == filas2
        await s.rollback()


@pytest.mark.asyncio
async def test_siembra_lee_el_bloque_del_json_y_sin_administrador_falla(db_engine):
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        tid = await _tenant(s, _id("t-json"))
        with pytest.raises(ValueError):
            await compuerta.sembrar_en_plantilla(s, tid, BLOQUE)
        await _usuario(s, tid, "admin_organizacion")
        await compuerta.sembrar_en_plantilla(s, tid)  # lee cooperativa_demo.json
        filas = await _filas_camaras(s, tid)
        assert len(filas) == 2
        nombres = [f[0] for f in filas]
        assert "Recepción (ficticia)" in nombres
        assert "Archivo (ficticio)" in nombres
        await s.rollback()


@pytest.mark.asyncio
async def test_lo_sembrado_se_clona_igual(db_engine):
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        plantilla, destino = await _tenant(s, _id("t-p")), await _tenant(s, _id("t-d"))
        autor_p = await _usuario(s, plantilla, "admin_organizacion")
        autor_d = await _usuario(s, destino, "admin_organizacion")
        await compuerta.sembrar_en_plantilla(s, plantilla, BLOQUE)
        await pasillo.clonar_desde_plantilla(s, plantilla, destino, {autor_p: autor_d})
        origen_f, clon_f = await _filas_camaras(s, plantilla), await _filas_camaras(s, destino)
        assert len(clon_f) == 2
        assert [f[:7] for f in clon_f] == [f[:7] for f in origen_f]
        assert {f[7] for f in clon_f} == {autor_d}
        await s.rollback()


# --- Pruebas estáticas y unitarias sin base de datos ---


def test_el_motor_no_hace_commit_ni_importa_otra_sala():
    codigo = MOTOR.read_text(encoding="utf-8")
    assert not re.search(r"\.commit\(|\.rollback\(", codigo)
    importados = set(re.findall(r"^\s*(?:from|import)\s+([\w.]+)", codigo, re.M))
    ajenos = {
        i
        for i in importados
        if i.startswith(("features.", "app_core.")) and not i.startswith("features.videovigilancia")
    }
    assert not ajenos, ajenos
    assert PLANTILLA_TENANT_ID not in codigo


def test_pasillo_y_compuerta_exponen_las_dos_funciones_con_la_firma_del_contrato():
    for modulo in (pasillo, compuerta):
        firma = inspect.signature(modulo.clonar_desde_plantilla)
        assert list(firma.parameters) == ["session", "origen", "destino", "mapa_ids"]
        assert list(inspect.signature(modulo.sembrar_en_plantilla).parameters)[:2] == ["session", "plantilla_id"]
    assert {"clonar_desde_plantilla", "sembrar_en_plantilla"} <= set(compuerta.__all__)


def test_entrada_engine_encuentra_clonador_en_pasillo():
    from features.demo.services.entrada_engine import _clonador

    clonador = _clonador("videovigilancia")
    assert clonador is not None
    assert clonador is pasillo.clonar_desde_plantilla


def test_derivacion_de_ids_es_estable_y_usa_uuid5():
    from uuid import NAMESPACE_URL, uuid5

    id_dest = motor._id_destino("dest-1", "orig-cam-1")
    esperado = str(uuid5(NAMESPACE_URL, "videovigilancia-demo/dest-1/orig-cam-1"))
    assert id_dest == esperado

    id_plant = motor._id_plantilla("plantilla-x", "cam-recepcion")
    esperado_plant = str(uuid5(NAMESPACE_URL, "videovigilancia-demo/plantilla-x/cam-recepcion"))
    assert id_plant == esperado_plant


def test_bloque_cooperativa_demo_contiene_camaras_conformes():
    ruta_json = RAIZ / "data" / "demo" / "cooperativa_demo.json"
    datos = json.loads(ruta_json.read_text(encoding="utf-8"))
    cctv = datos.get("salas", {}).get("videovigilancia", {})
    camaras = cctv.get("camaras", [])
    assert len(camaras) == 2
    claves = {c["clave"] for c in camaras}
    assert claves == {"cam-recepcion", "cam-archivo"}
    for cam in camaras:
        assert "(fictici" in cam["nombre_ubicacion"]
        assert cam["codec"] in ("H265", "H265_PLUS")


@pytest.mark.asyncio
async def test_clonar_validaciones_memoria():
    session = AsyncMock()
    # Origen igual a destino
    with pytest.raises(ValueError, match="El tenant destino no puede ser el de la plantilla"):
        await compuerta.clonar_desde_plantilla(session, "tenant-a", "tenant-a", {})
