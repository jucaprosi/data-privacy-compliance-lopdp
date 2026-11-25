# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤demo ¤arbitro ¤plantillas-demo
# ¤¤qa-engineer
"""BIB-404: catálogo ficticio de la demo.

Sin base de datos: archivos ficticios válidos (también R8 y citas verificadas), línea de demostración,
guarda de entorno (R1, m3) y que la siembra pase por el flujo editorial (m1).
Con base (PostgreSQL 16; en el CI): siembra por el flujo (m1), idempotencia (m2) y tenant clonado (m4).

Mutaciones (una a una, con el archivo restaurado):
- m1: insertar la versión directamente como `publicada` -> test_m1_publicada_por_el_flujo_con_personas_distintas
  (y, sin base, test_m1_el_motor_no_inserta_versiones_ni_revisiones).
- m2: quitar la comprobación de huella -> test_m2_otra_version_publicada_con_el_mismo_codigo_es_conflicto.
- m3: quitar la guarda de entorno -> test_m3_fuera_de_la_demo_error_y_ninguna_escritura.
- m4: sembrar sin ficha -> test_m4_un_tenant_ve_las_seis_y_puede_usarlas (la publicación exige la ficha completa).
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from features.biblioteca.domain.plantillas_md import leer_metadatos, separar, validar_plantilla_md
from features.biblioteca.domain.validacion import errores_ida, errores_secciones
from features.biblioteca.services import catalogo_demo_engine as motor
from scripts.verificar_citas_plantillas import ARTEFACTO, citas_de, leer_artefacto

RAIZ = Path(__file__).resolve().parents[1]
CARPETA = RAIZ / "data" / "demo" / "biblioteca_catalogo"
LINEA = "Documento de demostración con contenido ficticio. No es una plantilla validada ni sirve de asesoría jurídica."
ESPERADAS = {"BIB-091": ("politica", 1), "BIB-092": ("aviso", 1), "BIB-093": ("formulario", 2),
             "BIB-094": ("registro", 2), "BIB-095": ("contrato", 3), "BIB-096": ("procedimiento", 3)}


def _textos() -> dict[str, str]:
    return {r.stem: r.read_bytes().decode("utf-8") for r in sorted(CARPETA.glob("BIB-*.md"))}


def test_seis_archivos_con_tipos_y_olas_de_la_especificacion():
    textos = _textos()
    assert set(textos) == set(ESPERADAS)
    for codigo, texto in textos.items():
        meta = leer_metadatos(separar(texto)[0])
        assert (meta["tipo"], int(meta["ola"])) == ESPERADAS[codigo] and "validacion_legal" not in meta


def test_cada_archivo_es_valido_y_empieza_con_la_linea_de_demostracion():
    for codigo, texto in _textos().items():
        assert validar_plantilla_md(texto, codigo) == []
        assert separar(texto)[1].lstrip().startswith(LINEA)


def test_citas_verificadas_y_una_cita_por_seccion():
    estados, _, _ = leer_artefacto(ARTEFACTO.read_bytes().decode("utf-8"))
    verificadas = {c for c, e in estados.items() if e == "verificada"}
    for codigo, texto in _textos().items():
        cabecera, cuerpo = separar(texto)
        meta = leer_metadatos(cabecera)
        claves, sin_norma = citas_de(meta, cuerpo)
        informativas = [i["titulo"] for i in meta.get("secciones_informativas", [])]
        assert sin_norma == [] and errores_ida(claves, estados) == [], codigo
        assert errores_secciones(cuerpo, informativas, verificadas) == [], codigo


def test_catalogo_json_lleva_la_ficha_de_siete_campos_por_codigo():
    fichas = json.loads((CARPETA / "catalogo.json").read_bytes().decode("utf-8"))
    assert set(fichas) == set(ESPERADAS)
    campos = {"nombre", "objetivo", "fuentes", "fecha_revision", "instrucciones", "dependencias", "restricciones"}
    for ficha in fichas.values():
        assert set(ficha) == campos and all(str(v).strip() for v in ficha.values())
        assert "ficticio" in ficha["restricciones"]


class SesionProhibida:
    """Cualquier uso de la sesión falla: la guarda debe cortar antes de escribir."""

    def __getattr__(self, nombre):
        raise AssertionError(f"la siembra tocó la sesión ({nombre})")


@pytest.mark.asyncio
@pytest.mark.parametrize("entorno", ["development", "pruebas", "production"])
async def test_m3_fuera_de_la_demo_error_y_ninguna_escritura(monkeypatch, entorno):
    monkeypatch.setenv("APP_ENV", entorno)
    with pytest.raises(ValueError):
        await motor.sembrar_catalogo_demo(SesionProhibida(), {})


def test_m1_el_motor_no_inserta_versiones_ni_revisiones():
    fuente = (RAIZ / "features" / "biblioteca" / "services" / "catalogo_demo_engine.py").read_bytes().decode("utf-8")
    assert "INSERT INTO biblioteca_versiones" not in fuente and "INSERT INTO biblioteca_revisiones" not in fuente
    assert "cargar_plantilla_md" in fuente and "revisar(" in fuente and "publicar(" in fuente


def test_sembrar_en_plantilla_solo_llama_al_catalogo_en_la_demo():
    fuente = (RAIZ / "features" / "biblioteca" / "services" / "clon_plantilla_engine.py").read_bytes().decode("utf-8")
    assert 'entorno_actual() == "demo"' in fuente and "sembrar_catalogo_demo" in fuente


# --- Con base de datos (PostgreSQL 16 del arnés; corre en el CI) -----------------------------------------

def _id(prefijo: str) -> str:
    return f"{prefijo}-{uuid.uuid4().hex[:10]}"


async def _persona(s: AsyncSession, etiqueta: str) -> str:
    uid = _id("u")
    await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Persona ficticia')"),
                    {"i": uid, "e": f"{etiqueta}-{uid}@cooperativa-demo.invalid"})
    return uid


@pytest_asyncio.fixture
async def demo(db_engine, monkeypatch):
    monkeypatch.setenv("APP_ENV", "demo")
    async with AsyncSession(db_engine, expire_on_commit=False) as s:
        admin = await _persona(s, "admin")
        impl = await _persona(s, "implementacion")
        coord = await _persona(s, "coordinacion")
        mapa = {motor.ADMIN: admin, motor.IMPLEMENTACION: impl, motor.COORDINACION: coord}
        yield {"s": s, "mapa": mapa}
        await s.rollback()


async def _cuentas(s: AsyncSession) -> tuple:
    consultas = (
        "SELECT count(*) FROM biblioteca_versiones WHERE codigo LIKE 'BIB-09%'",
        "SELECT count(*) FROM biblioteca_revisiones r JOIN biblioteca_versiones v ON v.id=r.version_id "
        "WHERE v.codigo LIKE 'BIB-09%'",
        "SELECT count(*) FROM biblioteca_capacidades",
    )
    return tuple([(await s.execute(text(q))).scalar() for q in consultas])


@pytest.mark.asyncio
async def test_m1_publicada_por_el_flujo_con_personas_distintas(demo):
    s = demo["s"]
    await motor.sembrar_catalogo_demo(s, demo["mapa"])
    filas = (await s.execute(text(
        "SELECT v.codigo, v.estado, v.responsable_id, v.autores, c.tipo, (c.metadatos->>'ola')::int AS ola, "
        "(SELECT array_agg(r.revisor_id) FROM biblioteca_revisiones r WHERE r.version_id=v.id AND r.tipo='tecnica' "
        "AND r.aprobado) AS revisores FROM biblioteca_versiones v JOIN biblioteca_catalogo c ON c.codigo=v.codigo "
        "WHERE v.codigo LIKE 'BIB-09%' ORDER BY v.codigo"))).mappings().all()
    assert [f["codigo"] for f in filas] == sorted(ESPERADAS)
    for f in filas:
        assert f["estado"] == "publicada" and (f["tipo"], f["ola"]) == ESPERADAS[f["codigo"]]
        assert f["responsable_id"] == demo["mapa"][motor.IMPLEMENTACION]
        assert f["revisores"] == [demo["mapa"][motor.COORDINACION]]
        assert set(f["autores"]) == {demo["mapa"][motor.IMPLEMENTACION]}


@pytest.mark.asyncio
async def test_m2_la_siembra_repetida_no_cambia_nada(demo):
    s = demo["s"]
    await motor.sembrar_catalogo_demo(s, demo["mapa"])
    antes = await _cuentas(s)
    await motor.sembrar_catalogo_demo(s, demo["mapa"])
    assert await _cuentas(s) == antes


@pytest.mark.asyncio
async def test_m2_otra_version_publicada_con_el_mismo_codigo_es_conflicto(demo, monkeypatch):
    from app_core.errors import ErrorNegocio
    s = demo["s"]
    await motor.sembrar_catalogo_demo(s, demo["mapa"])
    monkeypatch.setattr(motor, "huella", lambda texto: "otra-huella")
    with pytest.raises(ErrorNegocio) as error:
        await motor.sembrar_catalogo_demo(s, demo["mapa"])
    assert "BIB_CONFLICTO_VERSION" in str(error.value)


@pytest.mark.asyncio
async def test_m4_un_tenant_ve_las_seis_y_puede_usarlas(demo):
    from features.biblioteca import biblioteca_service as bib
    from features.biblioteca.domain.documentos import CrearDocumento
    s = demo["s"]
    await motor.sembrar_catalogo_demo(s, demo["mapa"])
    tenant, miembro = _id("t-demo"), _id("u-miembro")
    await s.execute(text(
        "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:i, :n, :n, :r)"),
        {"i": tenant, "n": "Cooperativa Demo (ficticia)", "r": f"R{uuid.uuid4().hex[:12]}"})
    await s.execute(text("INSERT INTO users (id, email, nombre) VALUES (:i, :e, 'Miembro ficticio')"),
                    {"i": miembro, "e": f"{miembro}@cooperativa-demo.invalid"})
    await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
    await s.execute(text(
        "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, 'admin_organizacion')"),
        {"i": _id("r"), "u": miembro, "t": tenant})
    segunda_ola = {p.codigo for p in await bib.listar_catalogo(s, miembro, ola=2)}
    assert {"BIB-093", "BIB-094"} <= segunda_ola
    elegida = [p for p in await bib.listar_catalogo(s, miembro) if p.codigo == "BIB-091"][0]
    documento = await bib.crear_documento(s, tenant, miembro, CrearDocumento(plantilla_id=elegida.id))
    assert documento.plantilla_id == elegida.id
