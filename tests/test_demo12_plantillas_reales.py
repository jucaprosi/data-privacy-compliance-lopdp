# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤demo ¤adpa ¤arbitro
"""DEMO-12: la demo con las plantillas reales del catálogo (governance/especificaciones/DEMO-12.md).

Las pruebas sin base corren en cualquier máquina. Las que siembran usan PostgreSQL real (`db_engine`: el PG16
del arnés o evydentia-pruebas, nunca producción ni la demo), dentro de una transacción que se deshace.

Mutaciones (cada una hace fallar la prueba indicada):
  - m1: quitar `demo` de `ENTORNOS` -> test_m1_el_cargador_admite_demo y test_demo_con_url_de_pruebas_sale_2_sin_conectar;
  - m2: un contenido inventado en un documento -> test_la_huella_de_cada_documento_es_la_de_su_plantilla_rellenada;
  - m3: dejar un solo estado -> test_m3_el_json_cubre_cuatro_estados_y_dos_origenes y
        test_la_siembra_deja_cuatro_documentos_cuatro_estados_y_dos_origenes;
  - m4: saltarse en silencio un código sin versión publicada -> test_m4_sin_version_publicada_falla_cerrado;
  - m5: quitar la leyenda del pie del DOCX -> test_m5_en_la_demo_el_docx_lleva_la_leyenda_en_el_pie.
"""
from __future__ import annotations

import hashlib
import importlib.util
import inspect
import json
import re
import uuid
import zipfile
from io import BytesIO
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

RAIZ = Path(__file__).resolve().parents[1]
JSON_DEMO = RAIZ / "data" / "demo" / "cooperativa_demo.json"
MOTOR = RAIZ / "features" / "biblioteca" / "services" / "clon_plantilla_engine.py"
LEYENDA = "Demostración · datos ficticios"
ESTADOS = {"borrador", "en_revision", "aprobado", "vencido"}
URL_DEMO = "postgresql://app:clave@/evydentia_demo?host=/cloudsql/evydentia-demo:us-central1:evydentia-demo-db"
URL_PRUEBAS = "postgresql://app:clave@10.0.0.5:5432/evydentia_pruebas"


def _script():
    especificacion = importlib.util.spec_from_file_location("cargar_plantillas_pmv_d12", RAIZ / "scripts" / "cargar_plantillas_pmv.py")
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


def _documentos_json() -> list[dict]:
    return json.loads(JSON_DEMO.read_text(encoding="utf-8"))["salas"]["biblioteca"]["documentos"]


# --- R1 · Carga en la demo ------------------------------------------------------------------------

def test_m1_el_cargador_admite_demo():
    script = _script()
    assert "demo" in script.ENTORNOS
    assert script.entorno_de_url(URL_DEMO) == "demo"
    assert script.entorno_de_url("postgresql://u:p@127.0.0.1:5433/evydentia_demo") == "demo"  # antes que «local»
    assert script.entorno_de_url("postgresql://u:p@evydentia-demo-db/otra") == "demo"
    assert script.entorno_de_url(URL_PRUEBAS) == "pruebas"
    assert script.motivo_entorno(URL_DEMO, "demo", True) is None
    assert script.motivo_entorno(URL_DEMO, "demo", False) is not None


def test_demo_con_url_de_pruebas_sale_2_sin_conectar(monkeypatch, capsys):
    script = _script()
    conectado = []

    async def _no_conectar(*_a, **_k):
        conectado.append(True)

    monkeypatch.setattr(script, "_cargar", _no_conectar)
    for url, confirmar in ((URL_PRUEBAS, True), (URL_DEMO, False)):
        monkeypatch.setenv("BIB109_DATABASE_URL", url)
        argv = ["--cargar", "--actor", "u-1", "--entorno", "demo"] + (["--confirmar-entorno"] if confirmar else [])
        assert script.main(argv) == 2
    assert conectado == []
    salida = capsys.readouterr().out
    assert URL_PRUEBAS not in salida and URL_DEMO not in salida


# --- R2 y R3 en el JSON ---------------------------------------------------------------------------

def test_el_json_nombra_codigos_y_estados_nunca_titulos_ni_contenidos():
    catalogo = {p.stem for p in (RAIZ / "data" / "biblioteca" / "pmv").glob("BIB-*.md")}
    documentos = _documentos_json()
    for doc in documentos:
        assert set(doc) <= {"plantilla", "estado", "origen"}, doc
        assert doc["plantilla"] in catalogo
        assert doc["estado"] in ESTADOS
        assert doc.get("origen", "plantilla") in {"plantilla", "propio"}
    assert len({d["plantilla"] for d in documentos}) == len(documentos)


def test_m3_el_json_cubre_cuatro_estados_y_dos_origenes():
    documentos = _documentos_json()
    assert len(documentos) >= 4
    assert {d["estado"] for d in documentos} == ESTADOS
    assert {d.get("origen", "plantilla") for d in documentos} == {"plantilla", "propio"}


def test_r8_los_ids_salen_del_codigo_de_plantilla_nunca_de_la_posicion():
    fuente = MOTOR.read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def _organizacion_ficticia"):]
    assert '_id_destino(plantilla_id, "DEMO-" + version["codigo"])' in cuerpo
    assert "DEMO-DOC-" not in cuerpo and "enumerate(" not in cuerpo
    assert "documentos._rellenador.rellenar(" in cuerpo and ".commit(" not in cuerpo


# --- R4b · Pie de la demo -------------------------------------------------------------------------

TEXTO = "# Política\n\nTexto **negrita**.\n\n- uno\n\n| A | B |\n|---|---|\n| sí | 2026-01-15 |\n"
# Huellas medidas en origin/main 61797614, antes de DEMO-12 (fuera de la demo la salida no cambia).
DOCX_HOY = {None: "a679ae3aa7994f7d66e352dc71519f51c9dd43588c1675890c36b521b5e4a03c",
            ("x",): "93ba002910e93dad56da520b6d41b433365e0b897b83be88e77aa4cf500de9e5"}
XLSX_HOY = {None: "32dcdbeff34746bc84340edc8ead54235a5a0d91d50a17c69824cb61e49bf33a",
            ("x",): "6f82730e4771e1ceccbbabe6458c2bc3b4e1123960322be4211f67843878b461"}
OPENPYXL_MEDIDO = "3.1.5"


def _instantanea():
    from features.biblioteca.domain.generacion import InstantaneaGeneracion

    cuerpo = ("---\ncodigo: BIB-001\nversion: '1.0'\nnombre: Política\n---\n" + TEXTO)
    return InstantaneaGeneracion(version_id="v-1", plantilla_md=cuerpo, plantilla_sha256=hashlib.sha256(cuerpo.encode()).hexdigest(),
                                 esquema=[], organizacion={"organizacion.ruc": "9999999990099"}, contexto={},
                                 fecha_emision="2026-01-15", procedencia=None)


def _construir(monkeypatch, entorno: str, formato: str) -> bytes:
    from features.biblioteca.domain.generacion import PedirGeneracion
    from features.biblioteca.services.generacion import construir

    monkeypatch.setenv("APP_ENV", entorno)
    return construir(_instantanea(), PedirGeneracion(modo="borrador", formato=formato))[0]


def _partes(archivo: bytes) -> dict[str, str]:
    with zipfile.ZipFile(BytesIO(archivo)) as z:
        return {n: z.read(n).decode("utf-8") for n in z.namelist() if n.endswith((".xml", ".rels"))}


def test_fuera_de_la_demo_los_generadores_dan_los_mismos_bytes_que_hoy():
    import openpyxl
    from features.biblioteca.services.generador_docx import generar_docx
    from features.biblioteca.services.generador_xlsx import generar_xlsx
    from features.biblioteca.services.salida import bloques

    partes = bloques(TEXTO)
    for marca, esperado in DOCX_HOY.items():
        assert hashlib.sha256(generar_docx(partes, list(marca) if marca else None)).hexdigest() == esperado
    if openpyxl.__version__ == OPENPYXL_MEDIDO:  # el XLSX depende de la versión del escritor
        for marca, esperado in XLSX_HOY.items():
            libro = generar_xlsx("BIB-001 · Política", {"organizacion.ruc": "9999"}, partes, date(2026, 1, 15),
                                 list(marca) if marca else None)
            assert hashlib.sha256(libro).hexdigest() == esperado


@pytest.mark.parametrize("entorno", ["production", "pruebas"])
@pytest.mark.parametrize("formato", ["docx", "xlsx"])
def test_fuera_de_la_demo_la_salida_es_identica_a_la_de_development(monkeypatch, formato, entorno):
    """R4b (decisión del Arquitecto, #1059): la leyenda va solo con APP_ENV=demo; `pruebas` incluido, no cambia."""
    fuera = _construir(monkeypatch, entorno, formato)
    assert fuera == _construir(monkeypatch, "development", formato)
    assert LEYENDA not in "".join(_partes(fuera).values())


def test_m5_en_la_demo_el_docx_lleva_la_leyenda_en_el_pie(monkeypatch):
    partes = _partes(_construir(monkeypatch, "demo", "docx"))
    pies = [n for n in partes if re.fullmatch(r"word/footer\d*\.xml", n)]
    assert pies and all(LEYENDA in partes[n] for n in pies)
    assert "<w:footerReference" in partes["word/document.xml"]
    assert LEYENDA not in partes["word/document.xml"]  # solo en el pie, sin otro texto en el cuerpo
    assert "footer" in partes["[Content_Types].xml"] and "footer" in partes["word/_rels/document.xml.rels"]


def test_en_la_demo_cada_hoja_del_xlsx_lleva_la_leyenda_en_el_pie_de_impresion(monkeypatch):
    from openpyxl import load_workbook

    libro = load_workbook(BytesIO(_construir(monkeypatch, "demo", "xlsx")))
    assert len(libro.worksheets) >= 2
    for hoja in libro.worksheets:
        assert hoja.oddFooter.center.text == LEYENDA, hoja.title
    assert all(LEYENDA not in str(c.value) for h in libro.worksheets for f in h.iter_rows() for c in f if c.value)


def test_la_descarga_de_maestros_no_cambia():
    fuente = (RAIZ / "features" / "biblioteca" / "services" / "descarga.py").read_text(encoding="utf-8")
    assert "datos_ficticios" not in fuente and LEYENDA not in fuente


# --- Siembra con base (CI) ------------------------------------------------------------------------

def _id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:10]}"


async def _contexto(s: AsyncSession, tenant: str) -> None:
    await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})


async def _tenant(s: AsyncSession) -> str:
    tid = _id("t-d12")
    await s.execute(text("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                         "VALUES (:i, :n, :n, :r)"), {"i": tid, "n": f"Prueba {tid}", "r": f"R{uuid.uuid4().hex[:12]}"})
    return tid


async def _usuario(s: AsyncSession, tid: str | None = None) -> str:
    uid = _id("u")
    await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Persona ficticia')"),
                    {"i": uid, "e": f"{uid}@prueba.invalid"})
    if tid:
        await _contexto(s, tid)
        await s.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                             "VALUES (:i, :u, :t, 'admin_organizacion')"), {"i": _id("r"), "u": uid, "t": tid})
    return uid


async def _publicada(s: AsyncSession, actor: str, nombre: str) -> dict:
    """Una plantilla MD publicada. Sus disparadores exigen el flujo editorial (BIB-403), que no es el objeto de
    esta prueba: se desactivan solo durante la inserción, dentro de la transacción que se deshace."""
    codigo = f"ZZ-D12-{uuid.uuid4().hex[:8].upper()}"
    cuerpo = f"# {nombre}\n\n{{{{organizacion.razon_social}}}} trata datos según la LOPDP ({codigo}).\n"
    version = {"id": str(uuid.uuid4()), "codigo": codigo, "version": "1.0", "cuerpo_md": cuerpo, "nombre": nombre,
               "metadatos": {}}
    await s.execute(text("INSERT INTO biblioteca_catalogo (codigo, nombre, formato) VALUES (:c, :n, 'MD')"),
                    {"c": codigo, "n": nombre})
    await s.execute(text("ALTER TABLE biblioteca_versiones DISABLE TRIGGER USER"))
    await s.execute(text(
        "INSERT INTO biblioteca_versiones (id, codigo, version, formato, responsable_id, autores, estado, cuerpo_md, sha256) "
        "VALUES (:i, :c, '1.0', 'MD', :a, CAST(:au AS jsonb), 'publicada', :cuerpo, :h)"),
        {"i": version["id"], "c": codigo, "a": actor, "au": json.dumps([actor]), "cuerpo": cuerpo,
         "h": hashlib.sha256(cuerpo.encode()).hexdigest()})
    await s.execute(text("ALTER TABLE biblioteca_versiones ENABLE TRIGGER USER"))
    return version


async def _catalogo_de_cuatro(s: AsyncSession, actor: str) -> tuple[list[dict], dict]:
    nombres = ("Política de prueba", "Aviso de prueba", "Registro de prueba", "Procedimiento de prueba")
    versiones = [await _publicada(s, actor, n) for n in nombres]
    estados = ("borrador", "en_revision", "aprobado", "vencido")
    bloque = {"documentos": [{"plantilla": v["codigo"], "estado": e} for v, e in zip(versiones, estados)]}
    bloque["documentos"][3]["origen"] = "propio"
    return versiones, bloque


def _organizacion(tid: str) -> dict:
    tenant = json.loads(JSON_DEMO.read_text(encoding="utf-8"))["tenant"]
    return {"tenant_id": tid, **{f"organizacion.{k}": tenant[k] for k in ("razon_social", "nombre_comercial", "ruc")}}


async def _esperado(version: dict, tid: str) -> str:
    from features.biblioteca.services import documentos

    resultado = documentos._rellenador.rellenar(version, _organizacion(tid), {})
    contenido, _ = await resultado if inspect.isawaitable(resultado) else resultado
    return contenido


async def _sembrados(s: AsyncSession, tid: str) -> list[dict]:
    await _contexto(s, tid)
    return [dict(f) for f in (await s.execute(text(
        "SELECT id, codigo, nombre, origen, plantilla_id, plantilla_version, contenido_markdown, sha256, estado "
        "FROM biblioteca_documentos WHERE tenant_id=:t ORDER BY codigo"), {"t": tid})).mappings()]


@pytest.mark.asyncio
async def test_la_huella_de_cada_documento_es_la_de_su_plantilla_rellenada(db_engine):
    from app_core.pasillo import biblioteca as pasillo

    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        tid = await _tenant(s)
        autor = await _usuario(s, tid)
        versiones, bloque = await _catalogo_de_cuatro(s, autor)
        await pasillo.sembrar_en_plantilla(s, tid, bloque)
        por_codigo = {d["codigo"]: d for d in await _sembrados(s, tid)}
        for v, entrada in zip(versiones, bloque["documentos"]):
            doc = por_codigo[v["codigo"]]
            contenido = await _esperado(v, tid)
            assert doc["contenido_markdown"] == contenido
            assert doc["sha256"] == hashlib.sha256(contenido.encode("utf-8")).hexdigest()
            assert doc["nombre"] == v["nombre"] and "ficticio" not in doc["nombre"]
            if entrada.get("origen") == "propio":
                assert doc["origen"] == "propio"
            else:
                assert (doc["origen"], doc["plantilla_id"], doc["plantilla_version"]) == ("plantilla", v["id"], "1.0")
        await s.rollback()


@pytest.mark.asyncio
async def test_la_siembra_deja_cuatro_documentos_cuatro_estados_y_dos_origenes(db_engine):
    from features.biblioteca import biblioteca_service as compuerta

    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        tid = await _tenant(s)
        autor = await _usuario(s, tid)
        _, bloque = await _catalogo_de_cuatro(s, autor)
        await compuerta.sembrar_en_plantilla(s, tid, bloque)
        uno = await _sembrados(s, tid)
        await compuerta.sembrar_en_plantilla(s, tid, bloque)  # idempotente
        assert await _sembrados(s, tid) == uno
        assert len(uno) == 4
        assert {d["estado"] for d in uno} == ESTADOS
        assert {d["origen"] for d in uno} == {"plantilla", "propio"}
        historial = (await s.execute(text("SELECT count(*) FROM biblioteca_documentos_historial WHERE tenant_id=:t"),
                                     {"t": tid})).scalar()
        assert historial == 4
        await s.rollback()


@pytest.mark.asyncio
async def test_m4_sin_version_publicada_falla_cerrado(db_engine):
    from features.biblioteca import biblioteca_service as compuerta

    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        tid = await _tenant(s)
        autor = await _usuario(s, tid)
        _, bloque = await _catalogo_de_cuatro(s, autor)
        bloque["documentos"].append({"plantilla": "ZZ-D12-SIN-PUBLICAR", "estado": "borrador"})
        with pytest.raises(ValueError, match="ZZ-D12-SIN-PUBLICAR"):
            await compuerta.sembrar_en_plantilla(s, tid, bloque)
        assert await _sembrados(s, tid) == []
        await s.rollback()


@pytest.mark.asyncio
async def test_r8_con_el_viejo_demo_doc_01_la_siembra_no_reutiliza_su_id(db_engine):
    from features.biblioteca import biblioteca_service as compuerta
    from features.biblioteca.services.clon_plantilla_engine import _id_destino

    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        tid = await _tenant(s)
        autor = await _usuario(s, tid)
        viejo, contenido = _id_destino(tid, "DEMO-DOC-01"), "Documento ficticio de demostración. Sin datos reales.\n"
        await _contexto(s, tid)
        await s.execute(text(
            "INSERT INTO biblioteca_documentos (id, tenant_id, codigo, nombre, origen, contenido_markdown, sha256, "
            "fecha_emision, proxima_revision, creado_por) VALUES (:i, :t, 'DEMO-DOC-01', 'Viejo (borrador ficticio)', "
            "'propio', :c, :h, '2026-01-15', '2027-01-15', :u)"),
            {"i": viejo, "t": tid, "c": contenido, "h": hashlib.sha256(contenido.encode()).hexdigest(), "u": autor})
        versiones, bloque = await _catalogo_de_cuatro(s, autor)
        await compuerta.sembrar_en_plantilla(s, tid, bloque)
        sembrados = await _sembrados(s, tid)
        nuevos = [d for d in sembrados if d["id"] != viejo]
        assert len(nuevos) == 4 and len(sembrados) == 5
        assert {d["id"] for d in nuevos} == {_id_destino(tid, "DEMO-" + v["codigo"]) for v in versiones}
        assert all(not d["codigo"].startswith("DEMO-DOC-") for d in nuevos)
        await s.rollback()
