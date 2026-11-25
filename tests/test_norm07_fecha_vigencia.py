# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤monitoreo-job ¤inteligencia-normativa ¤arbitro
"""NORM-07: fecha de entrada en vigencia y disparo de la propuesta de la biblioteca al revisar una resolución.

Conectado como `lopdp_app` (fixtures de NORM-05). La biblioteca es siempre un doble: ninguna prueba propone de verdad.
Cada prueba documenta su mutación: el cambio en el código que la pondría en rojo.
"""
import logging
import uuid
from datetime import date

import pytest
from sqlalchemy import text

from tests.test_norm05_privilegios_backend import como_app, propietario  # noqa: F401 - fixtures de NORM-05

pytestmark = pytest.mark.asyncio

NOTA = "Cotejada con el Registro Oficial."
FECHA = date(2026, 12, 1)

try:  # sin DATABASE_URL (sin PostgreSQL) la sala no se puede importar: las pruebas de base se saltan
    from features.inteligencia_normativa import inteligencia_normativa_service as svc
    from features.inteligencia_normativa.services import revision

    HAY_BASE = True
except RuntimeError:
    HAY_BASE = False

con_base = pytest.mark.skipif(not HAY_BASE, reason="necesita PostgreSQL (DATABASE_URL)")


async def _sembrar(propietario, estado="pendiente_revision", fecha=None) -> str:  # noqa: F811
    async with propietario() as s:
        i = (await s.execute(
            text("INSERT INTO normativa_resoluciones (numero_resolucion, anio_emision, titulo, organo_emisor, materia, "
                 "url_fuente, seccion_fuente, archivo_sha256, ruta_original, tamano_bytes, estado, fecha_vigencia) "
                 "VALUES (:n, 2026, 'Título', 'SPDP', 'General', 'https://x.invalid/a.pdf', 'resoluciones', :h, "
                 "'spdp/a.pdf', 10, :e, :f) RETURNING id::text"),
            {"n": f"N07-{uuid.uuid4().hex[:10]}", "h": uuid.uuid4().hex * 2, "e": estado, "f": fecha})).scalar_one()
        await s.commit()
    return i


class Biblioteca:
    """Doble del pasillo de la biblioteca: anota cada llamada a `proponer_por_resolucion`."""

    def __init__(self, falla=False):
        self.llamadas: list[tuple] = []
        self.falla = falla

    async def __call__(self, session, id_resolucion, estado, estado_anterior, actor):
        self.llamadas.append((id_resolucion, estado, estado_anterior, actor))
        if self.falla:
            raise RuntimeError("la biblioteca no responde")
        return {"resultado": "sin_cambios", "versiones": []}


@pytest.fixture
def biblioteca(monkeypatch, como_app):  # noqa: F811
    from app_core.pasillo import biblioteca as pasillo_biblioteca

    doble = Biblioteca()
    monkeypatch.setattr(pasillo_biblioteca, "proponer_por_resolucion", doble)
    svc.inyectar_dependencias_de_prueba(sesion_factory=como_app)
    svc.inyectar_dependencias_de_impacto_de_prueba(solicitar_cache=lambda corpus: None)
    yield doble
    svc.inyectar_dependencias_de_prueba()
    svc.inyectar_dependencias_de_impacto_de_prueba()


async def _revisar(resolucion, estado, fecha=None, operador="op-n07"):
    return await svc.revisar_estado(resolucion, estado, NOTA, operador, fecha_vigencia=fecha)


# ------------------------------------------------------------ R2 sin base: cuándo proponer

@pytest.mark.parametrize("estado,anterior,propone", [
    ("reformada", "vigente", True), ("derogada", "vigente", True), ("reformada", None, True),
    ("vigente", "observada", True), ("vigente", "reformada", True),
    ("observada", "vigente", False), ("observada", None, False),
    ("vigente", "vigente", False), ("reformada", "reformada", False), ("vigente", None, False),
])
def test_cuando_la_sala_pide_la_propuesta(estado, anterior, propone):
    """Mutación m2: devolver verdadero también con `observada` da rojo."""
    from features.inteligencia_normativa.services import revision as rev

    assert rev.debe_pedir_propuesta(estado, anterior) is propone


@pytest.mark.parametrize("guardado,anterior", [
    ("pendiente_revision", None), ("homologada", None), ("observada", "observada"), ("vigente", "vigente"),
])
def test_el_estado_inicial_cuenta_como_primera_revision(guardado, anterior):
    """Mutación m4: devolver siempre `None` da rojo."""
    from features.inteligencia_normativa.services import revision as rev

    assert rev.estado_anterior_de(guardado) == anterior


# ------------------------------------------------------------ R1 y R3: fecha

@con_base
async def test_la_fecha_se_guarda_con_la_revision_y_el_pasillo_la_devuelve(propietario, como_app, biblioteca):  # noqa: F811
    """Mutación m1: no escribir `fecha_vigencia` en el UPDATE da rojo."""
    from app_core.pasillo import inteligencia_normativa as pasillo

    i = await _sembrar(propietario)
    r = await _revisar(i, "vigente", FECHA)
    assert r.fecha_vigencia == FECHA
    assert await pasillo.fecha_vigencia_de(i) == FECHA


@con_base
async def test_sin_fecha_se_conserva_la_que_hubiera(propietario, como_app, biblioteca):  # noqa: F811
    i = await _sembrar(propietario, fecha=FECHA)
    r = await _revisar(i, "vigente")
    assert r.fecha_vigencia == FECHA


@con_base
async def test_sin_fecha_en_una_resolucion_sin_fecha_queda_nula(propietario, como_app, biblioteca):  # noqa: F811
    from app_core.pasillo import inteligencia_normativa as pasillo

    i = await _sembrar(propietario)
    r = await _revisar(i, "vigente")
    assert r.fecha_vigencia is None and await pasillo.fecha_vigencia_de(i) is None


# ------------------------------------------------------------ R2: disparo

@con_base
async def test_reformada_llama_una_vez_con_el_operador_como_actor(propietario, como_app, biblioteca):  # noqa: F811
    """Mutación m2: llamarla también con `observada` da rojo (en la prueba siguiente)."""
    i = await _sembrar(propietario, estado="vigente")
    await _revisar(i, "reformada", operador="op-77")
    assert biblioteca.llamadas == [(i, "reformada", "vigente", "op-77")]


@con_base
async def test_observada_no_llama(propietario, como_app, biblioteca):  # noqa: F811
    i = await _sembrar(propietario, estado="vigente")
    await _revisar(i, "observada")
    assert biblioteca.llamadas == []


@con_base
async def test_el_estado_anterior_llega_a_la_biblioteca(propietario, como_app, biblioteca):  # noqa: F811
    """Mutación m4: pasar siempre `None` como estado anterior da rojo."""
    i = await _sembrar(propietario, estado="observada")
    await _revisar(i, "vigente")
    assert biblioteca.llamadas[0][2] == "observada"
    j = await _sembrar(propietario)  # primera revisión: nunca se revisó
    await _revisar(j, "reformada")
    assert biblioteca.llamadas[1][2] is None


@con_base
async def test_el_mismo_estado_no_llama_y_vigente_en_la_primera_revision_tampoco(propietario, como_app, biblioteca):  # noqa: F811
    i = await _sembrar(propietario, estado="reformada")
    await _revisar(i, "reformada")
    j = await _sembrar(propietario)
    await _revisar(j, "vigente")
    assert biblioteca.llamadas == []


@con_base
async def test_si_la_propuesta_falla_la_revision_queda_hecha_y_el_fallo_se_registra(  # noqa: F811
        propietario, como_app, biblioteca, caplog):
    biblioteca.falla = True
    i = await _sembrar(propietario, estado="vigente")
    with caplog.at_level(logging.WARNING):
        r = await _revisar(i, "derogada")
    assert r.estado == "derogada" and len(biblioteca.llamadas) == 1
    assert "RuntimeError" in caplog.text and "la biblioteca no responde" not in caplog.text


# ------------------------------------------------------------ API

def test_la_peticion_acepta_una_fecha_iso_opcional_y_rechaza_otra():
    from pydantic import ValidationError

    try:
        from api.routers.inteligencia_normativa import RevisionRequest
    except RuntimeError:
        pytest.skip("necesita PostgreSQL (DATABASE_URL)")

    assert RevisionRequest(estado="vigente", nota=NOTA).fecha_vigencia is None
    assert RevisionRequest(estado="vigente", nota=NOTA, fecha_vigencia="2026-12-01").fecha_vigencia == FECHA
    with pytest.raises(ValidationError):
        RevisionRequest(estado="vigente", nota=NOTA, fecha_vigencia="01/12/2026")
