# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-305: indicadores verificables. La persistencia/RLS se acredita solo con el arnés local
(ARNES_BASE=postgresql_local) o una rama propia (BIB305_RAMA_PROPIA=1); sin ellas se omite.

Mutación decisiva: en ``features/biblioteca/services/indicadores.py``, ``clasificar_accion``, añadir al
inicio ``if documento_aprobado: return "verificada"`` (contar una aprobación documental como acción
verificada). Fallan ``test_aprobacion_documental_no_verifica_la_accion`` y
``test_db_denominador_y_origen_de_acciones``.
"""
import hashlib
import importlib
import os
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from fastapi import Request
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from api.errores import ErrorNegocio
from api.rbac import get_context
from app_core.db.session import get_session
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.services import indicadores as ind

ROOT = Path(__file__).resolve().parents[1]
PRODUCCION, COMPARTIDA = "ep-late-hall-b50bpbk5", "ep-soft-darkness-b5z454vp"
HASH = "c" * 64
HASH_DOC = hashlib.sha256("# x".encode("utf-8")).hexdigest()
CORTE = datetime(2026, 11, 4, tzinfo=timezone.utc)


def _r(categoria: str, i: int = 0) -> ind.RegistroOrigen:
    return ind.RegistroOrigen(id=f"r{i}", categoria=categoria, estado_origen=None, descripcion="x", origen="o")


# ----------------------------------------------------------------------------------- contrato estático

def test_contratos_compuerta_rutas_y_errores():
    from api.routers import biblioteca_indicadores as router
    importlib.reload(router)
    assert router.AUTO_REGISTRO is True
    assert {(m, r.path) for r in router.router.routes for m in r.methods} == {
        ("GET", "/biblioteca/indicadores"), ("GET", "/biblioteca/indicadores/{clave}/registros")}
    for nombre in ("Indicador", "Indicadores", "RegistroOrigen", "RegistrosIndicador", "calcular_indicadores",
                   "registros_de_indicador"):
        assert nombre in bib.__all__ and hasattr(bib, nombre)
    assert CATALOGO_ERRORES["BIB_INDICADOR_DESCONOCIDO"].status_code == 404
    assert CATALOGO_ERRORES["BIB_INDICADOR_CATEGORIA_INVALIDA"].status_code == 422


def test_limite_adpa_sin_cifra_global_y_tamano():
    codigo = (ROOT / "features/biblioteca/services/indicadores.py").read_text(encoding="utf-8")
    assert "features.roadmap" not in codigo and "UPDATE " not in codigo and "DELETE " not in codigo
    for prohibido in ("puntaje_global", "porcentaje_global", "cumplimiento_total", "score"):
        assert prohibido not in codigo
    assert "f\"SELECT" not in codigo and "f'SELECT" not in codigo
    for relativa in ("features/biblioteca/services/indicadores.py", "api/routers/biblioteca_indicadores.py",
                     "features/biblioteca/biblioteca_service.py"):
        assert len((ROOT / relativa).read_text(encoding="utf-8").splitlines()) <= 500
    assert not hasattr(ind.Indicadores, "model_fields") or "total" not in ind.Indicadores.model_fields


# ------------------------------------------------------------------------------------ reglas puras

def test_aprobacion_documental_no_verifica_la_accion():
    assert ind.clasificar_accion(None, documento_aprobado=True) == "pendiente"
    assert ind.clasificar_accion("no_conforme", documento_aprobado=True) == "no_conforme"
    assert ind.clasificar_accion("conforme", documento_aprobado=False) == "verificada"
    assert ind.clasificar_accion("raro", documento_aprobado=False) == "sin_mapear"


def test_clasificacion_de_documentos_y_decisiones():
    assert [ind.clasificar_documento(e) for e in ("en_revision", "borrador", "aprobado", "vencido", "x", None)] == [
        "pendiente_revision", "borrador", "aprobado", "vencido", "sin_mapear", "sin_mapear"]
    assert [ind.clasificar_decision(d) for d in ("pendiente", "actualizar", "no_aplica", "otra")] == [
        "sin_informacion", "decidida", "decidida", "sin_mapear"]


def test_indicador_con_denominador_exclusiones_sin_mapear_y_etiqueta():
    registros = [_r("verificada", 1), _r("pendiente", 2), _r("pendiente", 3), _r("no_conforme", 4),
                 _r("sin_mapear", 5)]
    i = ind.construir_indicador("acciones", registros, CORTE)
    assert (i.valor_foco, i.denominador, i.sin_mapear) == (1, 4, 1)
    assert i.conteos == {"verificada": 1, "no_conforme": 1, "pendiente": 2, "sin_mapear": 1}
    assert i.avance_implementacion == 25.0 and i.fecha_corte == CORTE
    assert "Avance de implementación" in i.etiqueta_avance and "No es una certificación" in i.etiqueta_avance
    assert [e.cantidad for e in i.exclusiones] == [1, None]
    vacio = ind.construir_indicador("decisiones", [], CORTE)
    assert vacio.denominador == 0 and vacio.avance_implementacion is None


@pytest.mark.asyncio
async def test_tres_indicadores_separados_y_drilldown_coherente(monkeypatch):
    monkeypatch.setattr(ind, "contexto", AsyncMock())
    filas = {"acciones": [_r("verificada", 1), _r("pendiente", 2)],
             "documentos": [_r("pendiente_revision", 3)], "decisiones": [_r("sin_informacion", 4)]}

    async def registros(_s, _t, clave, _hoy):
        return filas[clave]

    monkeypatch.setattr(ind, "_registros", registros)
    resultado = await ind.calcular_indicadores(object(), "t", "u")
    assert [i.clave for i in resultado.indicadores] == ["acciones", "documentos", "decisiones"]
    assert "total" not in resultado.model_dump() and resultado.etiqueta == ind.ETIQUETA_AVANCE
    detalle = await ind.registros_de_indicador(object(), "t", "u", "acciones", "pendiente")
    assert [r.id for r in detalle.registros] == ["r2"]
    for clave, categoria, codigo in (("otra", None, "BIB_INDICADOR_DESCONOCIDO"),
                                     ("acciones", "aprobado", "BIB_INDICADOR_CATEGORIA_INVALIDA")):
        with pytest.raises(ErrorNegocio) as error:
            await ind.registros_de_indicador(object(), "t", "u", clave, categoria)
        assert error.value.code == codigo


# --------------------------------------------------------------------------- persistencia (arnés local)

def _url_de_pruebas() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or not (os.environ.get("ARNES_BASE") == "postgresql_local" or os.environ.get("BIB305_RAMA_PROPIA") == "1"):
        pytest.skip("Persistencia/RLS no acreditadas: falta el arnés local o rama propia (BIB305_RAMA_PROPIA=1)")
    if COMPARTIDA in url.lower():
        pytest.fail("La rama test compartida no es una rama propia; no se abrió conexión", pytrace=False)
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


class Mundo:
    def __init__(self, conexion, sesion, usuario, usuario_b, ta, tb, tareas, docs):
        self.conexion, self.sesion, self.usuario, self.usuario_b = conexion, sesion, usuario, usuario_b
        self.ta, self.tb, self.tareas, self.docs = ta, tb, tareas, docs


async def _x(conexion, sql: str, **p):
    await conexion.execute(text(sql), p)


@pytest_asyncio.fixture
async def mundo():
    engine = create_async_engine(_url_de_pruebas(), echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            usuario, usuario_b, revisor = ("bib305-" + uuid4().hex for _ in range(3))
            for u in (usuario, usuario_b, revisor):
                await _x(conexion, "INSERT INTO users(id,email,nombre) VALUES (:id,:e,'Persona')",
                         id=u, e=u + "@example.test")
            ta, tb = "bib305-org-" + uuid4().hex, "bib305-org-" + uuid4().hex
            tareas, docs = {}, {}
            for tid in (ta, tb):
                await _x(conexion, "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                         "VALUES (:id,'Org sintética','Org sintética S.A.',:ruc)", id=tid, ruc=str(uuid4().int)[:13])
                hoja, ola = str(uuid4()), str(uuid4())
                await _x(conexion, "INSERT INTO roadmaps(id, tenant_id, variables_json) VALUES (:r,:t,'{}')", r=hoja, t=tid)
                await _x(conexion, "INSERT INTO roadmap_waves(id, roadmap_id, tenant_id, name) VALUES (:w,:r,:t,'Ola')",
                         w=ola, r=hoja, t=tid)
                tareas[tid] = [str(uuid4()) for _ in range(3)]
                for k in tareas[tid]:
                    await _x(conexion, "INSERT INTO roadmap_tasks(id, wave_id, tenant_id, control_ref, dimension, title, "
                             "priority) VALUES (:k,:w,:t,'P7','D01','Acción','alta')", k=k, w=ola, t=tid)
                await _x(conexion, "INSERT INTO user_tenant_roles (id,user_id,tenant_id,role) VALUES (:id,:u,:t,'coordinador')",
                         id=str(uuid4()), u=usuario if tid == ta else usuario_b, t=tid)
            hoy = date.today()
            for estado, proxima in (("aprobado", hoy + timedelta(days=90)), ("en_revision", hoy + timedelta(days=90)),
                                    ("borrador", hoy + timedelta(days=90)), ("aprobado", hoy - timedelta(days=1))):
                doc = str(uuid4())
                await _x(conexion, "INSERT INTO biblioteca_documentos(id,tenant_id,codigo,nombre,origen,contenido_markdown,"
                         "estado,aprobado_por,aprobado_en,sha256,fecha_emision,proxima_revision,creado_por) VALUES "
                         "(:id,:t,'DOC',:n,'propio','# x',:e,:ap,:en,:h,:f,:p,:u)", id=doc, t=ta, n=f"Doc {estado}",
                         e=estado, ap=usuario if estado == "aprobado" else None,
                         en=datetime.now(timezone.utc) if estado == "aprobado" else None, h=HASH_DOC, f=hoy, p=proxima, u=usuario)
                await _x(conexion, "INSERT INTO biblioteca_documentos_historial(id,tenant_id,documento_id,revision,accion,"
                         "contenido_markdown,sha256,actor_id) VALUES (:id,:t,:d,1,'creado','# x',:h,:u)",
                         id=str(uuid4()), t=ta, d=doc, h=HASH_DOC, u=usuario)
                docs.setdefault(estado, []).append(doc)
            # Acción 0: solo un documento aprobado enlazado. Acción 1: evidencia + verificación conforme.
            # Acción 2: evidencia + verificación no conforme. La organización B tiene su propia acción verificada.
            k0, k1, k2 = tareas[ta]
            await _x(conexion, "INSERT INTO biblioteca_revision_acciones(id,tenant_id,documento_id,documento_revision,"
                     "accion_id,creado_por) VALUES (:id,:t,:d,1,:a,:u)", id=str(uuid4()), t=ta,
                     d=docs["aprobado"][0], a=k0, u=usuario)
            for tid, k, resultado in ((ta, k1, "conforme"), (ta, k2, "no_conforme"), (tb, tareas[tb][0], "conforme")):
                ev = str(uuid4())
                await _x(conexion, "INSERT INTO biblioteca_evidencias(id,tenant_id,accion_id,titulo,version,sha256,"
                         "clasificacion,permisos,fecha,creado_por) VALUES (:id,:t,:a,'Acta','1',:h,'interna',"
                         "ARRAY['coordinador'],:f,:u)", id=ev, t=tid, a=k, h=HASH, f=hoy, u=usuario)
                await _x(conexion, "INSERT INTO biblioteca_verificaciones(id,tenant_id,accion_id,evidencia_id,criterio,"
                         "evidencia_legible,resultado,revisor,fecha) VALUES (:id,:t,:a,:e,'criterio largo',true,:r,:u,:f)",
                         id=str(uuid4()), t=tid, a=k, e=ev, r=resultado, u=revisor, f=hoy)
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield Mundo(conexion, sesion, usuario, usuario_b, ta, tb, tareas, docs)
        except DBAPIError:
            pytest.fail("Fallo DB BIB-305 (detalles de conexión omitidos); comprobar migraciones y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_db_denominador_y_origen_de_acciones(mundo):
    resultado = await bib.calcular_indicadores(mundo.sesion, mundo.ta, mundo.usuario)
    acciones = resultado.indicadores[0]
    assert acciones.clave == "acciones" and acciones.denominador == 3
    assert (acciones.conteos["verificada"], acciones.conteos["pendiente"], acciones.conteos["no_conforme"]) == (1, 1, 1)
    k0, k1, _ = mundo.tareas[mundo.ta]
    verificadas = await bib.registros_de_indicador(mundo.sesion, mundo.ta, mundo.usuario, "acciones", "verificada")
    assert [r.id for r in verificadas.registros] == [k1]
    pendientes = await bib.registros_de_indicador(mundo.sesion, mundo.ta, mundo.usuario, "acciones", "pendiente")
    assert [r.id for r in pendientes.registros] == [k0]  # solo tiene un documento aprobado: no está verificada


@pytest.mark.asyncio
async def test_db_documentos_pendientes_y_vencidos(mundo):
    documentos = (await bib.calcular_indicadores(mundo.sesion, mundo.ta, mundo.usuario)).indicadores[1]
    assert documentos.valor_foco == 1 and documentos.denominador == 4
    assert documentos.conteos == {"pendiente_revision": 1, "borrador": 1, "aprobado": 1, "vencido": 1, "sin_mapear": 0}
    detalle = await bib.registros_de_indicador(mundo.sesion, mundo.ta, mundo.usuario, "documentos", "pendiente_revision")
    assert [r.id for r in detalle.registros] == mundo.docs["en_revision"]
    decisiones = (await bib.calcular_indicadores(mundo.sesion, mundo.ta, mundo.usuario)).indicadores[2]
    assert decisiones.denominador == 0 and decisiones.avance_implementacion is None


@pytest.mark.asyncio
async def test_db_otra_organizacion_no_se_mezcla(mundo):
    b = await bib.calcular_indicadores(mundo.sesion, mundo.tb, mundo.usuario_b)
    assert b.indicadores[0].denominador == 1 and b.indicadores[1].denominador == 0
    detalle = await bib.registros_de_indicador(mundo.sesion, mundo.tb, mundo.usuario_b, "acciones")
    assert [r.id for r in detalle.registros] == [mundo.tareas[mundo.tb][0]]


# ---- API: la organización sale de la sesión autenticada

@pytest_asyncio.fixture
async def api(mundo, monkeypatch):
    from main import app

    async def sesion():
        yield mundo.sesion

    async def contexto(request: Request):
        return {"user_id": request.headers["x-test-user"], "tenant_id": request.headers["x-test-tenant"],
                "role": "coordinador"}

    monkeypatch.setitem(app.dependency_overrides, get_session, sesion)
    monkeypatch.setitem(app.dependency_overrides, get_context, contexto)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as cliente:
        yield cliente


@pytest.mark.asyncio
async def test_api_indicadores_y_drilldown(api, mundo):
    cab = {"x-test-tenant": mundo.ta, "x-test-user": mundo.usuario}
    r = await api.get("/api/v1/biblioteca/indicadores", headers=cab)
    assert r.status_code == 200
    cuerpo = r.json()
    assert [i["clave"] for i in cuerpo["indicadores"]] == ["acciones", "documentos", "decisiones"]
    assert all(i["fecha_corte"] and "exclusiones" in i and "sin_mapear" in i for i in cuerpo["indicadores"])
    d = await api.get("/api/v1/biblioteca/indicadores/documentos/registros?categoria=vencido", headers=cab)
    assert d.status_code == 200 and [x["id"] for x in d.json()["registros"]] == mundo.docs["aprobado"][1:]
    mala = await api.get("/api/v1/biblioteca/indicadores/nada/registros", headers=cab)
    assert mala.status_code == 404 and mala.json()["code"] == "BIB_INDICADOR_DESCONOCIDO"
