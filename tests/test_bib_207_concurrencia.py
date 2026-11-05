# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-207: guardado con revisión esperada atómica y trabajos de generación idempotentes.

Reglas puras siempre (comparación, códigos, migración, clave, orden de transacciones del worker). La
persistencia (conflicto entre dos editores, idempotencia, fallo y reintento sin duplicar, vencimiento, RLS e
inmutabilidad de la petición) corre contra la base local del arnés o una rama Neon propia, con la fixture de
BIB-201 (transacción que se revierte).

Mutación decisiva: en `features/biblioteca/services/concurrencia.py:27` (constante `GUARDAR`), quitar
`AND revision=:rev` ignora la revisión esperada: el segundo editor sobrescribe sin conflicto y falla
``test_db_dos_editores_concurrentes_conflicto_comparacion_y_recuperacion`` (no se lanza ErrorConflicto).
Observado el 2026-11-04 contra la base local del arnés con `python3 -m pytest tests/test_bib_207_concurrencia.py -q`:
1 fallo, 14 pasan; restaurado: 15 pasan (6 de base se omiten sin TEST_DATABASE_URL).
"""
import re
from contextlib import asynccontextmanager
from pathlib import Path
import pytest
from alembic.config import Config
from alembic.script import ScriptDirectory
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.workers import generacion_worker
from tests.test_bib_201_formularios import db_bib, fuentes  # noqa: F401
from tests.test_bib_205_generacion import COMPLETO, _borrador

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = ROOT / "alembic/versions/20261117_biblioteca_trabajos.py"
CODIGOS = ("BIB_CONFLICTO_EDICION", "BIB_TRABAJO_NO_ENCONTRADO", "BIB_TRABAJO_CLAVE_REUTILIZADA",
           "BIB_TRABAJO_NO_REINTENTABLE", "BIB_TRABAJO_NO_AUTORIZADO", "BIB_TRABAJO_REVISION_CAMBIADA",
           "BIB_TRABAJO_FALLO_INTERNO")


def pedir(clave="clave-0001", modo="borrador", formato="docx"):
    return bib.PedirTrabajo(clave=clave, modo=modo, formato=formato)


# --------------------------------------------------------------------------- reglas puras

def test_comparar_lista_solo_lo_que_difiere_en_orden_estable():
    d = bib.comparar_contextos({"a": 1, "b": "x", "c": None}, {"a": 1, "b": "y", "d": True})
    assert [(x.clave, x.mio, x.vigente) for x in d] == [("b", "x", "y"), ("d", None, True)]


def test_codigos_registrados_y_conflicto_es_409():
    for codigo in CODIGOS:
        assert codigo in CATALOGO_ERRORES
    assert CATALOGO_ERRORES["BIB_CONFLICTO_EDICION"].status_code == 409


@pytest.mark.parametrize("clave", ["corta", "con espacio 123", "x" * 81, "ñandú-12345"])
def test_clave_de_idempotencia_validada(clave):
    with pytest.raises(ValidationError):
        pedir(clave)


def test_migracion_encadenada_rls_unicidad_y_sin_delete():
    script = ScriptDirectory.from_config(Config(str(ROOT / "alembic.ini")))
    revision = script.get_revision("20261117_bib_trabajos")
    assert revision is not None and len(revision.revision) <= 32
    cuerpo = MIGRACION.read_text(encoding="utf-8")
    assert "FORCE ROW LEVEL SECURITY" in cuerpo and "GRANT SELECT,INSERT,UPDATE ON biblioteca_trabajos TO lopdp_app" in cuerpo
    assert "UNIQUE (tenant_id, borrador_id, revision_borrador, clave)" in cuerpo
    assert "generacion_id varchar(36) UNIQUE" in cuerpo
    assert not re.search(r"GRANT[^;]*DELETE[^;]*biblioteca_trabajos", cuerpo)


@pytest.mark.asyncio
async def test_worker_reclama_y_genera_en_transacciones_separadas(monkeypatch):
    pasos = []

    class Sesion:
        @asynccontextmanager
        async def begin(self):
            pasos.append("begin")
            yield
            pasos.append("commit")

    @asynccontextmanager
    async def fabrica():
        yield Sesion()

    async def reclamar(*_):
        pasos.append("reclamar")
        return True

    async def ejecutar(*_):
        pasos.append("ejecutar")
        return "hecho"

    monkeypatch.setattr(generacion_worker, "reclamar", reclamar)
    monkeypatch.setattr(generacion_worker, "ejecutar", ejecutar)
    assert await generacion_worker.procesar(fabrica, fuentes(), "t", "u", "j") == "hecho"
    assert pasos == ["begin", "reclamar", "commit", "begin", "ejecutar", "commit"]


@pytest.mark.asyncio
async def test_worker_caido_no_propaga(monkeypatch):
    @asynccontextmanager
    async def fabrica():
        raise ConnectionError("base caída")
        yield  # pragma: no cover

    assert await generacion_worker.procesar(fabrica, fuentes(), "t", "u", "j") is None


# --------------------------------------------------------------------------- persistencia (base propia)

async def _generaciones(sesion, borrador_id) -> int:
    return (await sesion.execute(text("SELECT count(*) FROM biblioteca_generaciones WHERE borrador_id=:b"),
                                 {"b": borrador_id})).scalar_one()


async def _procesar(sesion, tenant, actor, trabajo_id, f=None):
    assert await bib.reclamar_trabajo(sesion, tenant, actor, trabajo_id)
    return await bib.ejecutar_trabajo(sesion, f or fuentes(), tenant, actor, trabajo_id)


@pytest.mark.asyncio
async def test_db_dos_editores_concurrentes_conflicto_comparacion_y_recuperacion(db_bib):
    sesion, ids, tenant, _ = db_bib
    b = await _borrador(sesion, ids, tenant, {"contexto.camaras": "si"})
    ana = bib.GuardarBorrador(revision=b.revision, contexto={"contexto.camaras": "si", "contexto.finalidad": "Recepción"})
    beto = bib.GuardarBorrador(revision=b.revision, contexto={"contexto.camaras": "no"})
    hecho = await bib.guardar_con_revision(sesion, tenant, ids["miembro"], b.id, ana)
    assert hecho.revision == b.revision + 1
    with pytest.raises(bib.ErrorConflicto) as e:
        await bib.guardar_con_revision(sesion, tenant, ids["editor"], b.id, beto)
    c = e.value.conflicto
    assert e.value.status_code == 409 and e.value.code == "BIB_CONFLICTO_EDICION"
    assert (c.revision_esperada, c.revision_vigente) == (b.revision, hecho.revision)
    assert c.contexto_vigente == ana.contexto  # lo de Ana sigue intacto
    assert {d.clave for d in c.diferencias} == {"contexto.camaras", "contexto.finalidad"}
    vigente = (await sesion.execute(text("SELECT contexto FROM biblioteca_borradores WHERE id=:id"),
                                    {"id": b.id})).scalar_one()
    assert vigente == ana.contexto
    recuperado = await bib.guardar_con_revision(sesion, tenant, ids["editor"], b.id,
                                                bib.GuardarBorrador(revision=c.revision_vigente, contexto=beto.contexto))
    assert recuperado.revision == hecho.revision + 1


@pytest.mark.asyncio
async def test_db_otra_organizacion_no_guarda_ni_ve_trabajos(db_bib):
    sesion, ids, tenant, otro = db_bib
    b = await _borrador(sesion, ids, tenant, COMPLETO)
    with pytest.raises(ErrorNegocio) as e:
        await bib.guardar_con_revision(sesion, otro, ids["ajeno"], b.id, bib.GuardarBorrador(revision=1))
    assert e.value.code == "BIB_BORRADOR_NO_ENCONTRADO"
    t, _ = await bib.solicitar_trabajo(sesion, tenant, ids["miembro"], b.id, pedir())
    with pytest.raises(ErrorNegocio) as e:
        await bib.obtener_trabajo(sesion, otro, ids["ajeno"], t.id)
    assert e.value.code == "BIB_TRABAJO_NO_ENCONTRADO"
    with pytest.raises(ErrorNegocio) as e:
        await bib.solicitar_trabajo(sesion, otro, ids["ajeno"], b.id, pedir())
    assert e.value.code == "BIB_BORRADOR_NO_ENCONTRADO"


@pytest.mark.asyncio
async def test_db_misma_clave_mismo_trabajo_y_mismo_resultado(db_bib):
    sesion, ids, tenant, _ = db_bib
    b = await _borrador(sesion, ids, tenant, COMPLETO)
    uno, creado = await bib.solicitar_trabajo(sesion, tenant, ids["miembro"], b.id, pedir(modo="revision"))
    otro, repetido = await bib.solicitar_trabajo(sesion, tenant, ids["miembro"], b.id, pedir(modo="revision"))
    assert creado and not repetido and uno.id == otro.id and uno.estado == "pendiente"
    listo = await _procesar(sesion, tenant, ids["miembro"], uno.id)
    assert listo.estado == "listo" and listo.generacion_id and listo.intentos == 1
    again = await bib.ejecutar_trabajo(sesion, fuentes(), tenant, ids["miembro"], uno.id)  # reentrega del worker
    assert not await bib.reclamar_trabajo(sesion, tenant, ids["miembro"], uno.id)
    tercero, _ = await bib.solicitar_trabajo(sesion, tenant, ids["miembro"], b.id, pedir(modo="revision"))
    assert again.generacion_id == tercero.generacion_id == listo.generacion_id
    assert await _generaciones(sesion, b.id) == 1
    with pytest.raises(ErrorNegocio) as e:
        await bib.solicitar_trabajo(sesion, tenant, ids["miembro"], b.id, pedir(modo="revision", formato="xlsx"))
    assert e.value.code == "BIB_TRABAJO_CLAVE_REUTILIZADA"
    assert [t.id for t in await bib.listar_trabajos(sesion, tenant, ids["miembro"], b.id)] == [uno.id]


@pytest.mark.asyncio
async def test_db_fallo_visible_y_reintento_sin_duplicar(db_bib):
    sesion, ids, tenant, _ = db_bib
    b = await _borrador(sesion, ids, tenant, {"contexto.camaras": "si"})
    t, _ = await bib.solicitar_trabajo(sesion, tenant, ids["miembro"], b.id, pedir())
    caido = await _procesar(sesion, tenant, ids["miembro"], t.id, fuentes(falla=True))
    assert caido.estado == "fallido" and caido.error_codigo == "BIB_TRABAJO_FALLO_INTERNO"
    assert "fuente caída" not in (caido.error_detalle or "") and await _generaciones(sesion, b.id) == 0
    with pytest.raises(ErrorNegocio) as e:  # otra persona sin rol supervisor
        await bib.reintentar_trabajo(sesion, tenant, ids["editor"], "implementador", t.id)
    assert e.value.code == "BIB_TRABAJO_NO_AUTORIZADO"
    pendiente = await bib.reintentar_trabajo(sesion, tenant, ids["miembro"], "implementador", t.id)
    assert pendiente.id == t.id and pendiente.estado == "pendiente" and pendiente.error_codigo is None
    with pytest.raises(ErrorNegocio) as e:
        await bib.reintentar_trabajo(sesion, tenant, ids["miembro"], "implementador", t.id)
    assert e.value.code == "BIB_TRABAJO_NO_REINTENTABLE"
    listo = await _procesar(sesion, tenant, ids["miembro"], t.id)
    assert listo.estado == "listo" and listo.intentos == 2 and await _generaciones(sesion, b.id) == 1
    revision, _ = await bib.solicitar_trabajo(sesion, tenant, ids["miembro"], b.id, pedir("clave-0002", "revision"))
    negocio = await _procesar(sesion, tenant, ids["miembro"], revision.id)
    assert negocio.estado == "fallido" and negocio.error_codigo == "BIB_GEN_INCOMPLETA"
    assert "contexto.finalidad" in negocio.error_detalle and await _generaciones(sesion, b.id) == 1
    supervisado = await bib.reintentar_trabajo(sesion, tenant, ids["editor"], "dpo", revision.id)
    assert supervisado.estado == "pendiente"


@pytest.mark.asyncio
async def test_db_intento_vencido_se_recupera_y_revision_cambiada_falla(db_bib):
    sesion, ids, tenant, _ = db_bib
    b = await _borrador(sesion, ids, tenant, COMPLETO)
    t, _ = await bib.solicitar_trabajo(sesion, tenant, ids["miembro"], b.id, pedir())
    assert await bib.reclamar_trabajo(sesion, tenant, ids["miembro"], t.id)
    assert not await bib.reclamar_trabajo(sesion, tenant, ids["miembro"], t.id)  # otro worker lo tiene
    assert not (await bib.obtener_trabajo(sesion, tenant, ids["miembro"], t.id)).vencido
    await sesion.execute(text("UPDATE biblioteca_trabajos SET tomado_en=now() - interval '1 hour' WHERE id=:id"),
                         {"id": t.id})
    assert (await bib.obtener_trabajo(sesion, tenant, ids["miembro"], t.id)).vencido
    assert await bib.reclamar_trabajo(sesion, tenant, ids["miembro"], t.id)
    await bib.guardar_con_revision(sesion, tenant, ids["miembro"], b.id,
                                   bib.GuardarBorrador(revision=b.revision, contexto=COMPLETO))
    final = await bib.ejecutar_trabajo(sesion, fuentes(), tenant, ids["miembro"], t.id)
    assert final.estado == "fallido" and final.error_codigo == "BIB_TRABAJO_REVISION_CAMBIADA" and final.intentos == 2
    assert await _generaciones(sesion, b.id) == 0


@pytest.mark.asyncio
async def test_db_peticion_inmutable_y_sin_borrado(db_bib):
    sesion, ids, tenant, _ = db_bib
    b = await _borrador(sesion, ids, tenant, COMPLETO)
    t, _ = await bib.solicitar_trabajo(sesion, tenant, ids["miembro"], b.id, pedir())
    listo = await _procesar(sesion, tenant, ids["miembro"], t.id)
    for orden in ("UPDATE biblioteca_trabajos SET clave='otra-clave-1' WHERE id=:id",
                  "UPDATE biblioteca_trabajos SET estado='fallido', error_codigo='X', generacion_id=NULL WHERE id=:id",
                  "DELETE FROM biblioteca_trabajos WHERE id=:id"):
        punto = await sesion.begin_nested()
        with pytest.raises(DBAPIError):
            await sesion.execute(text(orden), {"id": listo.id})
        await punto.rollback()
