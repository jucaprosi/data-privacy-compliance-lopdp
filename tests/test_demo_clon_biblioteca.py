# -*- coding: utf-8 -*-
# ¤demo ¤adpa ¤seguridad-tenant
"""DEMO-03d: copia y siembra de la plantilla «Cooperativa Demo» en la sala biblioteca.

Las pruebas con base corren contra PostgreSQL real (`db_engine`: el PG16 del arnés o evydentia-pruebas,
nunca producción), dentro de una transacción que se deshace al final: no dejan filas.

Mutaciones documentadas (cada una hace fallar la prueba indicada):
  - copiar sin filtrar por tenant del origen -> test_copia_solo_lo_de_la_plantilla;
  - no traducir `creado_por` con `mapa_ids` -> test_el_destino_tiene_las_mismas_filas_con_otro_tenant;
  - insertar sin ON CONFLICT o con ids aleatorios -> test_clonar_dos_veces_no_duplica;
  - hacer `commit` dentro del motor -> test_no_hace_commit y test_el_motor_no_hace_commit_ni_importa_otra_sala;
  - escribir con el contexto del origen -> test_rls_el_destino_no_ve_la_plantilla;
  - volver a poner al creador como aprobador -> test_aprobado_sin_aprobador_traducido_falla_sin_dejar_filas;
  - sembrar con fecha o id no deterministas -> test_dos_siembras_dejan_el_mismo_estado.
"""
from __future__ import annotations

import hashlib
import re
import uuid
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app_core.pasillo import biblioteca as pasillo
from features.biblioteca import biblioteca_service as compuerta
from features.biblioteca.domain.documentos import huella
from features.demo.domain.plantilla import PLANTILLA_TENANT_ID

RAIZ = Path(__file__).resolve().parents[1]
MOTOR = RAIZ / "features" / "biblioteca" / "services" / "clon_plantilla_engine.py"
BLOQUE = {"documentos": [{"titulo": "Política ficticia A", "estado": "borrador"},
                         {"titulo": "Procedimiento ficticio B", "estado": "en_revision"}]}


def _id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:10]}"


async def _contexto(session: AsyncSession, tenant: str) -> None:
    await session.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})


async def _tenant(session: AsyncSession, tid: str) -> str:
    await session.execute(text(
        "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:i, :n, :n, :r)"),
        {"i": tid, "n": f"Prueba {tid}", "r": f"R{uuid.uuid4().hex[:12]}"})
    return tid


async def _usuario(session: AsyncSession, tid: str, rol: str) -> str:
    uid = _id("u")
    await session.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Persona ficticia')"),
                          {"i": uid, "e": f"{uid}@prueba.invalid"})
    await _contexto(session, tid)
    await session.execute(text(
        "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, :r)"),
        {"i": _id("r"), "u": uid, "t": tid, "r": rol})
    return uid


async def _documento(session: AsyncSession, tid: str, autor: str, nombre: str) -> str:
    did, contenido = str(uuid.uuid4()), f"# {nombre}\n\nTexto ficticio.\n"
    await _contexto(session, tid)
    await session.execute(text(
        "INSERT INTO biblioteca_documentos(id, tenant_id, codigo, nombre, origen, contenido_markdown, sha256, "
        "fecha_emision, proxima_revision, creado_por) VALUES (:i, :t, :c, :n, 'propio', :m, :h, "
        "'2026-01-15', '2027-01-15', :u)"),
        {"i": did, "t": tid, "c": f"COD-{did[:6]}", "n": nombre, "m": contenido, "h": huella(contenido), "u": autor})
    await session.execute(text(
        "INSERT INTO biblioteca_documentos_historial(id, tenant_id, documento_id, revision, accion, "
        "contenido_markdown, sha256, actor_id) VALUES (:i, :t, :d, 1, 'creado', :m, :h, :u)"),
        {"i": str(uuid.uuid4()), "t": tid, "d": did, "m": contenido, "h": huella(contenido), "u": autor})
    return did


@pytest_asyncio.fixture
async def mundo(db_engine):
    """Plantilla con dos documentos, otro tenant con uno propio y un destino con su persona; todo se deshace."""
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        plantilla = await _tenant(s, _id("t-plantilla"))
        destino = await _tenant(s, _id("t-destino"))
        ajeno = await _tenant(s, _id("t-ajeno"))
        autor_p = await _usuario(s, plantilla, "admin_organizacion")
        autor_d = await _usuario(s, destino, "admin_organizacion")
        autor_a = await _usuario(s, ajeno, "admin_organizacion")
        docs = [await _documento(s, plantilla, autor_p, n) for n in ("Política ficticia", "Registro ficticio")]
        doc_ajeno = await _documento(s, ajeno, autor_a, "Documento de otra organización")
        yield {"s": s, "plantilla": plantilla, "destino": destino, "ajeno": ajeno, "docs": docs,
               "doc_ajeno": doc_ajeno, "mapa": {autor_p: autor_d}}
        await s.rollback()


async def _filas(s: AsyncSession, tid: str) -> list[tuple]:
    await _contexto(s, tid)
    return [tuple(f) for f in (await s.execute(text(
        "SELECT codigo, nombre, contenido_markdown, sha256, estado, revision, creado_por FROM biblioteca_documentos "
        "WHERE tenant_id=:t ORDER BY codigo"), {"t": tid})).all()]


@pytest.mark.asyncio
async def test_el_destino_tiene_las_mismas_filas_con_otro_tenant(mundo):
    s, m = mundo["s"], mundo
    antes = await _filas(s, m["plantilla"])
    ampliado = await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])

    despues = await _filas(s, m["destino"])
    assert [f[:6] for f in despues] == [f[:6] for f in antes]
    assert {f[6] for f in despues} == set(m["mapa"].values())  # el autor es la persona del destino
    await _contexto(s, m["destino"])
    historial = (await s.execute(text(
        "SELECT count(*) FROM biblioteca_documentos_historial WHERE tenant_id=:t"), {"t": m["destino"]})).scalar()
    assert historial == len(m["docs"])
    # el mapa se amplía sin perder lo que ya traía, y traduce cada documento
    assert set(m["mapa"].items()) <= set(ampliado.items())
    assert set(m["docs"]) <= set(ampliado)
    assert not set(m["docs"]) & set(ampliado.values())


@pytest.mark.asyncio
async def test_la_plantilla_queda_intacta_y_nada_apunta_a_ella(mundo):
    s, m = mundo["s"], mundo
    antes = await _filas(s, m["plantilla"])
    await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    assert await _filas(s, m["plantilla"]) == antes
    await _contexto(s, m["destino"])
    ids_destino = [r[0] for r in (await s.execute(text(
        "SELECT id FROM biblioteca_documentos WHERE tenant_id=:t"), {"t": m["destino"]})).all()]
    assert ids_destino and not set(ids_destino) & set(m["docs"])
    huerfanas = (await s.execute(text(
        "SELECT count(*) FROM biblioteca_documentos_historial h WHERE h.tenant_id=:t AND NOT EXISTS ("
        "SELECT 1 FROM biblioteca_documentos d WHERE d.id=h.documento_id AND d.tenant_id=:t)"),
        {"t": m["destino"]})).scalar()
    assert huerfanas == 0


@pytest.mark.asyncio
async def test_copia_solo_lo_de_la_plantilla(mundo):
    s, m = mundo["s"], mundo
    ampliado = await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    assert m["doc_ajeno"] not in ampliado
    assert all("otra organización" not in f[1] for f in await _filas(s, m["destino"]))


@pytest.mark.asyncio
async def test_clonar_dos_veces_no_duplica(mundo):
    s, m = mundo["s"], mundo
    uno = await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    estado = await _filas(s, m["destino"])
    dos = await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    assert uno == dos
    assert await _filas(s, m["destino"]) == estado


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
    vistos = {r[0] for r in (await s.execute(text("SELECT tenant_id FROM biblioteca_documentos"))).all()}
    assert vistos == {m["destino"]}
    vistos_h = {r[0] for r in (await s.execute(text("SELECT tenant_id FROM biblioteca_documentos_historial"))).all()}
    assert vistos_h == {m["destino"]}
    await s.execute(text("RESET ROLE"))


@pytest.mark.asyncio
async def test_clonar_en_si_mismo_o_sin_traducir_al_autor_falla(mundo):
    s, m = mundo["s"], mundo
    with pytest.raises(ValueError):
        await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["plantilla"], m["mapa"])
    with pytest.raises(ValueError):
        await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], {})


@pytest.mark.asyncio
async def test_aprobado_sin_aprobador_traducido_falla_sin_dejar_filas(mundo):
    s, m = mundo["s"], mundo
    await _contexto(s, m["plantilla"])
    aprobador = (await s.execute(text("SELECT creado_por FROM biblioteca_documentos WHERE id=:i"),
                                 {"i": m["docs"][1]})).scalar()
    otro = await _usuario(s, m["plantilla"], "dpo")
    await _contexto(s, m["plantilla"])
    await s.execute(text("UPDATE biblioteca_documentos SET estado='aprobado', aprobado_por=:a, aprobado_en=now() "
                         "WHERE id=:i"), {"a": otro, "i": m["docs"][1]})
    assert aprobador in m["mapa"] and otro not in m["mapa"]
    with pytest.raises(ValueError, match="aprobador"):
        await compuerta.clonar_desde_plantilla(s, m["plantilla"], m["destino"], m["mapa"])
    assert await _filas(s, m["destino"]) == []


async def _estado_siembra(s: AsyncSession, tid: str) -> str:
    await _contexto(s, tid)
    filas = [tuple(f) for f in (await s.execute(text(
        "SELECT id, codigo, nombre, estado, sha256, fecha_emision, proxima_revision, creado_por "
        "FROM biblioteca_documentos WHERE tenant_id=:t ORDER BY codigo"), {"t": tid})).all()]
    hist = [tuple(f) for f in (await s.execute(text(
        "SELECT id, documento_id, revision FROM biblioteca_documentos_historial WHERE tenant_id=:t ORDER BY id"),
        {"t": tid})).all()]
    return hashlib.sha256(repr((filas, hist)).encode()).hexdigest() + f":{len(filas)}:{len(hist)}"


@pytest.mark.asyncio
async def test_dos_siembras_dejan_el_mismo_estado(db_engine):
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        tid = await _tenant(s, _id("t-siembra"))
        await _usuario(s, tid, "admin_organizacion")
        await pasillo.sembrar_en_plantilla(s, tid, BLOQUE)
        uno = await _estado_siembra(s, tid)
        await pasillo.sembrar_en_plantilla(s, tid, BLOQUE)
        assert await _estado_siembra(s, tid) == uno
        assert uno.endswith(":2:2")
        await s.rollback()


@pytest.mark.asyncio
async def test_siembra_lee_el_bloque_del_json_y_sin_administrador_falla(db_engine):
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        tid = await _tenant(s, _id("t-json"))
        with pytest.raises(ValueError):
            await compuerta.sembrar_en_plantilla(s, tid, BLOQUE)
        await _usuario(s, tid, "admin_organizacion")
        await compuerta.sembrar_en_plantilla(s, tid)  # sin datos: lee data/demo/cooperativa_demo.json
        nombres = [f[2] for f in [tuple(r) for r in (await s.execute(text(
            "SELECT codigo, id, nombre FROM biblioteca_documentos WHERE tenant_id=:t"), {"t": tid})).all()]]
        assert nombres == ["Política de protección de datos (borrador ficticio)"]
        await s.rollback()


@pytest.mark.asyncio
async def test_lo_sembrado_se_clona_igual(db_engine):
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        plantilla, destino = await _tenant(s, _id("t-p")), await _tenant(s, _id("t-d"))
        autor_p, autor_d = await _usuario(s, plantilla, "admin_organizacion"), await _usuario(s, destino, "admin_organizacion")
        await compuerta.sembrar_en_plantilla(s, plantilla, BLOQUE)
        await pasillo.clonar_desde_plantilla(s, plantilla, destino, {autor_p: autor_d})
        origen_f, clon_f = await _filas(s, plantilla), await _filas(s, destino)
        assert [f[:6] for f in clon_f] == [f[:6] for f in origen_f] and len(clon_f) == 2
        assert {f[6] for f in clon_f} == {autor_d}
        await s.rollback()


# --- Estáticas -------------------------------------------------------------------------------------

def test_el_motor_no_hace_commit_ni_importa_otra_sala():
    codigo = MOTOR.read_text(encoding="utf-8")
    assert not re.search(r"\.commit\(|\.rollback\(", codigo)
    importados = set(re.findall(r"^\s*(?:from|import)\s+([\w.]+)", codigo, re.M))
    ajenos = {i for i in importados if i.startswith(("features.", "app_core.")) and not i.startswith("features.biblioteca")}
    assert not ajenos, ajenos
    assert PLANTILLA_TENANT_ID not in codigo  # el id de la plantilla llega por parámetro


def test_pasillo_y_compuerta_exponen_las_dos_funciones_con_la_firma_del_contrato():
    import inspect

    for modulo in (pasillo, compuerta):
        firma = inspect.signature(modulo.clonar_desde_plantilla)
        assert list(firma.parameters) == ["session", "origen", "destino", "mapa_ids"]
        assert list(inspect.signature(modulo.sembrar_en_plantilla).parameters)[:2] == ["session", "plantilla_id"]
    assert {"clonar_desde_plantilla", "sembrar_en_plantilla"} <= set(compuerta.__all__)
