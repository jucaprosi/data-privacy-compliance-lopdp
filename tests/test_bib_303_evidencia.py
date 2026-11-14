# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-303: evidencias y verificación del cierre. La persistencia/RLS se acredita solo con el
arnés local (ARNES_BASE=postgresql_local) o con una URL local; una URL remota no la habilita y sin ella se omite.

Mutación decisiva: en ``features/biblioteca/services/verificacion.py``, ``VerificadorEvidencia.evidencia_conforme``,
cambiar ``return veredicto == "conforme"`` por ``return True`` (aceptar cierre sin evidencia conforme).
Fallan ``test_verificador_bloquea_cierre_sin_verificacion_conforme`` y
``test_db_cierre_bloqueado_hasta_verificacion_conforme_y_no_conforme_reabre``.
"""
import importlib.util
import os
from urllib.parse import urlparse
from datetime import date, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import httpx
import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from tests._alembic_salas import cabeza_de_sala
from fastapi import Request
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from api.errores import ErrorNegocio
from api.rbac import get_context
from app_core.db.session import get_session
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.services import verificacion
from features.roadmap import roadmap_service as roadmap

cierre = roadmap
TaskStatus = roadmap.TaskStatus

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = ROOT / "alembic/versions/20261114_biblioteca_verificaciones.py"
PRODUCCION, COMPARTIDA = "ep-late-hall-b50bpbk5", "ep-soft-darkness-b5z454vp"
HASH = "b" * 64


def _evidencia(**extra) -> dict:
    datos = {"titulo": "Acta de capacitación", "version": "1.0", "sha256": HASH, "clasificacion": "interna",
             "permisos": ["coordinador"], "fecha": "2026-11-01"}
    return {**datos, **extra}


def _verificacion(evidencia_id: str, **extra) -> bib.RegistrarVerificacion:
    datos = {"evidencia_id": evidencia_id, "criterio": "El acta cubre al 100 % del personal objetivo",
             "evidencia_legible": True, "resultado": "conforme", "fecha": date.today()}
    return bib.RegistrarVerificacion(**{**datos, **extra})


# ----------------------------------------------------------------------------------- contrato estático

def test_contratos_compuertas_rutas_y_errores():
    from api.routers import biblioteca_verificaciones as router
    importlib.reload(router)  # otro archivo puede haber retirado el verificador al terminar
    assert router.AUTO_REGISTRO is True
    assert {(m, r.path) for r in router.router.routes for m in r.methods} == {
        ("GET", "/biblioteca/verificaciones/acciones/{accion_id}"),
        ("POST", "/biblioteca/verificaciones/acciones/{accion_id}/evidencias"),
        ("POST", "/biblioteca/verificaciones/acciones/{accion_id}/verificaciones"),
    }
    for nombre in ("RegistrarEvidencia", "RegistrarVerificacion", "ExpedienteVerificacion", "VerificadorEvidencia",
                   "obtener_expediente", "registrar_evidencia", "registrar_verificacion"):
        assert nombre in bib.__all__ and hasattr(bib, nombre)
    assert "reabrir_accion_no_conforme" in roadmap.__all__
    assert isinstance(cierre.verificador_cierre_registrado(), verificacion.VerificadorEvidencia)
    assert isinstance(cierre.verificador_cierre_registrado(), roadmap.VerificadorDeCierre)
    for codigo, estado in (("BIB_VERIF_ACCION_AJENA", 422), ("BIB_EVIDENCIA_NO_ENCONTRADA", 404),
                           ("BIB_EVIDENCIA_PERMISOS_INVALIDOS", 422), ("BIB_EVIDENCIA_REVISION_INCOMPLETA", 422),
                           ("BIB_VERIF_EVIDENCIA_ILEGIBLE", 422), ("BIB_VERIF_EFICACIA_PENDIENTE", 422),
                           ("BIB_VERIF_REVISOR_AUTOR", 409), ("BIB_VERIF_FECHA_FUTURA", 422)):
        assert CATALOGO_ERRORES[codigo].status_code == estado


def test_entradas_exigen_hash_clasificacion_permisos_y_rechazan_identidad():
    bib.RegistrarEvidencia(**_evidencia())
    for malo in ({"sha256": "abc"}, {"clasificacion": "secreta"}, {"permisos": []}, {"tenant_id": "otra"},
                 {"creado_por": "yo"}):
        with pytest.raises(ValidationError):
            bib.RegistrarEvidencia(**_evidencia(**malo))
    with pytest.raises(ValidationError):
        _verificacion("e", revisor="yo")


def test_migracion_solo_anexar_rls_forzada_y_una_cabeza():
    spec = importlib.util.spec_from_file_location("bib303_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    cfg = Config(str(ROOT / "alembic.ini")); cfg.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(cfg)
    assert cabeza_de_sala("biblioteca", guion) and guion.get_revision(migracion.revision) is not None
    assert guion.get_revision(migracion.down_revision) is not None
    sql: list[str] = []
    migracion.op = SimpleNamespace(execute=sql.append)
    migracion.upgrade()
    texto = "\n".join(sql)
    for tabla in ("biblioteca_evidencias", "biblioteca_verificaciones"):
        assert f"ALTER TABLE {tabla} FORCE ROW LEVEL SECURITY" in texto
    assert texto.count("WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true))") == 2
    assert "GRANT SELECT,INSERT ON biblioteca_evidencias, biblioteca_verificaciones TO lopdp_app" in texto
    assert "UPDATE" not in texto.split("REVOKE ALL")[1] and "DELETE" not in texto.split("REVOKE ALL")[1]
    assert "ck_bib_verif_conforme_legible" in texto and "ck_bib_verif_conforme_eficaz" in texto
    assert "NEW.tenant_id" in texto and "ON DELETE RESTRICT" in texto


def test_limite_adpa_y_tamano():
    codigo = (ROOT / "features/biblioteca/services/verificacion.py").read_text(encoding="utf-8")
    assert "features.roadmap" not in codigo and "UPDATE roadmap_tasks" not in codigo
    assert "UPDATE biblioteca_verificaciones" not in codigo and "DELETE FROM biblioteca_" not in codigo
    for relativa in ("features/biblioteca/services/verificacion.py", "features/roadmap/roadmap_service.py",
                     "api/routers/biblioteca_verificaciones.py", "features/biblioteca/biblioteca_service.py"):
        assert len((ROOT / relativa).read_text(encoding="utf-8").splitlines()) <= 500


# ------------------------------------------------------------------------------------ reglas puras

def test_conforme_exige_evidencia_legible_eficacia_y_fecha_no_futura():
    verificacion.validar_verificacion(_verificacion("e"))
    verificacion.validar_verificacion(_verificacion("e", evidencia_legible=False, resultado="no_conforme"))
    casos = ((dict(evidencia_legible=False), "BIB_VERIF_EVIDENCIA_ILEGIBLE"),
             (dict(eficacia_requerida=True), "BIB_VERIF_EFICACIA_PENDIENTE"),
             (dict(eficacia_requerida=True, eficacia_conforme=False), "BIB_VERIF_EFICACIA_PENDIENTE"),
             (dict(fecha=date.today() + timedelta(days=1)), "BIB_VERIF_FECHA_FUTURA"))
    for extra, codigo in casos:
        with pytest.raises(ErrorNegocio) as error:
            verificacion.validar_verificacion(_verificacion("e", **extra))
        assert error.value.code == codigo
    verificacion.validar_verificacion(_verificacion("e", eficacia_requerida=True, eficacia_conforme=True))


def test_veredicto_usa_la_ultima_verificacion_y_un_hash_no_basta():
    assert verificacion.calcular_veredicto(False, None) == "sin_requisito"
    assert verificacion.calcular_veredicto(True, None) == "pendiente"
    assert verificacion.calcular_veredicto(True, "no_conforme") == "no_conforme"
    assert verificacion.calcular_veredicto(True, "conforme") == "conforme"


@pytest.mark.asyncio
@pytest.mark.parametrize("veredicto, esperado", [
    ("pendiente", False), ("no_conforme", False), ("conforme", True), ("sin_requisito", None)])
async def test_verificador_bloquea_cierre_sin_verificacion_conforme(monkeypatch, veredicto, esperado):
    monkeypatch.setattr(verificacion, "contexto", AsyncMock())
    monkeypatch.setattr(verificacion, "veredicto_de_accion", AsyncMock(return_value=veredicto))
    v = verificacion.VerificadorEvidencia()
    await v.preparar(object(), "tenant-a", "u", "tarea-1")
    assert v.evidencia_conforme("tenant-a", "tarea-1") is esperado
    # Un veredicto preparado para otra acción u organización no se reutiliza.
    assert v.evidencia_conforme("tenant-b", "tarea-1") is None
    assert v.evidencia_conforme("tenant-a", "tarea-2") is None


@pytest.mark.asyncio
async def test_compuerta_roadmap_prepara_el_verificador_antes_de_cerrar(monkeypatch):
    llamadas = []

    class Falso:
        async def preparar(self, session, tenant_id, actor, tarea_id):
            llamadas.append(("preparar", tenant_id, tarea_id))

        def evidencia_conforme(self, tenant_id, tarea_id):
            llamadas.append(("consultar", tenant_id, tarea_id))
            return False

    anterior = cierre.verificador_cierre_registrado()
    cierre.registrar_verificador_cierre(Falso())
    try:
        with pytest.raises(ErrorNegocio) as error:
            await roadmap.update_task_status(SimpleNamespace(execute=AsyncMock()), "t", "u", "k", TaskStatus.completada)
        assert error.value.code == "RM_CIERRE_SIN_EVIDENCIA"
        assert llamadas == [("preparar", "t", "k"), ("consultar", "t", "k")]
    finally:
        cierre.registrar_verificador_cierre(anterior)


@pytest.mark.asyncio
async def test_revisor_no_puede_ser_quien_registro_la_evidencia(monkeypatch):
    monkeypatch.setattr(verificacion, "contexto", AsyncMock())
    session = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(scalar=lambda: "autor")))
    reabrir = AsyncMock()
    with pytest.raises(ErrorNegocio) as error:
        await verificacion.registrar_verificacion(session, "t", "autor", "k", _verificacion("e"),
                                                  AsyncMock(return_value={"id": "k"}), reabrir)
    assert error.value.code == "BIB_VERIF_REVISOR_AUTOR" and session.execute.await_count == 1
    reabrir.assert_not_awaited()


# --------------------------------------------------------------------------- persistencia (arnés local)

def _url_de_pruebas() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or not (os.environ.get("ARNES_BASE") == "postgresql_local" or (urlparse(url).hostname or "") in ("127.0.0.1", "localhost", "::1")):
        pytest.skip("Persistencia pendiente: falta base local (arnés PostgreSQL 16 en 127.0.0.1 o ARNES_BASE=postgresql_local); una URL remota no habilita pruebas con base")
    if COMPARTIDA in url.lower():
        pytest.fail("La rama test compartida no es una rama propia; no se abrió conexión", pytrace=False)
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


class Mundo:
    def __init__(self, conexion, sesion, ids, ta, tb, tareas):
        self.conexion, self.sesion, self.ids, self.ta, self.tb, self.tareas = conexion, sesion, ids, ta, tb, tareas


@pytest_asyncio.fixture
async def mundo():
    engine = create_async_engine(_url_de_pruebas(), echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text("SELECT to_regclass('public.biblioteca_verificaciones')"))).scalar():
                pytest.fail("Aplicar la migración de BIB-303 solo en la base local o rama propia", pytrace=False)
            ids = {rol: "bib303-" + uuid4().hex for rol in ("autor_a", "revisor_a", "autor_b")}
            ta, tb = "bib303-org-" + uuid4().hex, "bib303-org-" + uuid4().hex
            for rol, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,:n)"),
                                       {"id": usuario, "e": usuario + "@example.test", "n": rol})
            tareas = {}
            for tid in (ta, tb):
                await conexion.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:id, 'Org sintética', 'Org sintética S.A.', :ruc)"), {"id": tid, "ruc": str(uuid4().int)[:13]})
                hoja, ola, tarea = (str(uuid4()) for _ in range(3))
                await conexion.execute(text("INSERT INTO roadmaps(id, tenant_id, variables_json) VALUES (:r, :t, '{}')"),
                                       {"r": hoja, "t": tid})
                await conexion.execute(text(
                    "INSERT INTO roadmap_waves(id, roadmap_id, tenant_id, name) VALUES (:w, :r, :t, 'Ola')"),
                    {"w": ola, "r": hoja, "t": tid})
                await conexion.execute(text(
                    "INSERT INTO roadmap_tasks(id, wave_id, tenant_id, control_ref, dimension, title, priority) "
                    "VALUES (:k, :w, :t, 'P7', 'D01', 'Capacitar al personal', 'alta')"), {"k": tarea, "w": ola, "t": tid})
                tareas[tid] = tarea
            for usuario, tid, rol in ((ids["autor_a"], ta, "implementador"), (ids["revisor_a"], ta, "coordinador"),
                                      (ids["autor_b"], tb, "implementador")):
                await conexion.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                                            "VALUES (:id, :u, :t, :r)"), {"id": str(uuid4()), "u": usuario, "t": tid, "r": rol})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            anterior = cierre.verificador_cierre_registrado()
            cierre.registrar_verificador_cierre(bib.VerificadorEvidencia())
            try:
                async with AsyncSession(bind=conexion, expire_on_commit=False,
                                        join_transaction_mode="create_savepoint") as sesion:
                    yield Mundo(conexion, sesion, ids, ta, tb, tareas)
            finally:
                cierre.registrar_verificador_cierre(anterior)
        except DBAPIError:
            pytest.fail("Fallo DB BIB-303 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


async def _registrar(m: Mundo, tenant: str, actor: str, **extra) -> bib.Evidencia:
    return await bib.registrar_evidencia(m.sesion, tenant, actor, m.tareas[tenant],
                                         bib.RegistrarEvidencia(**_evidencia(**extra)), roadmap.obtener_accion_para_enlace)


async def _estado(m: Mundo, tenant: str) -> str:
    await m.sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
    return (await m.sesion.execute(text("SELECT status FROM roadmap_tasks WHERE id=:k"), {"k": m.tareas[tenant]})).scalar()


@pytest.mark.asyncio
async def test_db_evidencia_guarda_version_hash_clasificacion_permisos_fecha_y_accion(mundo):
    ev = await _registrar(mundo, mundo.ta, mundo.ids["autor_a"], permisos=["dpo", "coordinador", "dpo"])
    assert (ev.version, ev.sha256, ev.clasificacion, ev.fecha) == ("1.0", HASH, "interna", date(2026, 11, 1))
    assert ev.permisos == ["coordinador", "dpo"] and ev.accion_id == mundo.tareas[mundo.ta] and ev.control_ref == "P7"
    expediente = await bib.obtener_expediente(mundo.sesion, mundo.ta, mundo.ids["autor_a"], mundo.tareas[mundo.ta],
                                              roadmap.obtener_accion_para_enlace)
    assert expediente.veredicto == "pendiente" and [e.id for e in expediente.evidencias] == [ev.id]


@pytest.mark.asyncio
async def test_db_cierre_bloqueado_hasta_verificacion_conforme_y_no_conforme_reabre(mundo):
    ta, tarea, autor, revisor = mundo.ta, mundo.tareas[mundo.ta], mundo.ids["autor_a"], mundo.ids["revisor_a"]
    ev = await _registrar(mundo, ta, autor)
    with pytest.raises(ErrorNegocio) as error:  # tener evidencia con hash no basta para cerrar
        await roadmap.update_task_status(mundo.sesion, ta, revisor, tarea, TaskStatus.completada)
    assert error.value.code == "RM_CIERRE_SIN_EVIDENCIA" and await _estado(mundo, ta) == "pendiente"

    async def registrar(**extra):
        return await bib.registrar_verificacion(mundo.sesion, ta, revisor, tarea, _verificacion(ev.id, **extra),
                                                roadmap.obtener_accion_para_enlace, roadmap.reabrir_accion_no_conforme)

    await registrar(resultado="no_conforme", evidencia_legible=False, observaciones="Acta ilegible")
    with pytest.raises(ErrorNegocio):
        await roadmap.update_task_status(mundo.sesion, ta, revisor, tarea, TaskStatus.completada)
    conforme = await registrar()
    assert conforme.veredicto == "conforme"
    assert (await roadmap.update_task_status(mundo.sesion, ta, revisor, tarea, TaskStatus.completada))["status"] == "completada"
    # Revisión posterior no conforme: conserva el expediente y reabre la acción.
    final = await registrar(resultado="no_conforme", observaciones="La eficacia no se sostiene")
    assert [v.resultado for v in final.verificaciones] == ["no_conforme", "conforme", "no_conforme"]
    assert final.veredicto == "no_conforme" and await _estado(mundo, ta) == "en_progreso"


@pytest.mark.asyncio
async def test_db_sin_requisito_documental_el_cierre_sigue_como_siempre(mundo):
    tb = mundo.tb
    fila = await roadmap.update_task_status(mundo.sesion, tb, mundo.ids["autor_b"], mundo.tareas[tb], TaskStatus.completada)
    assert fila["status"] == "completada"


@pytest.mark.asyncio
async def test_db_referencias_y_lecturas_de_otra_organizacion_se_rechazan(mundo):
    ev_b = await _registrar(mundo, mundo.tb, mundo.ids["autor_b"])
    with pytest.raises(ErrorNegocio) as error:
        await bib.registrar_evidencia(mundo.sesion, mundo.ta, mundo.ids["autor_a"], mundo.tareas[mundo.tb],
                                      bib.RegistrarEvidencia(**_evidencia()), roadmap.obtener_accion_para_enlace)
    assert error.value.code == "BIB_VERIF_ACCION_AJENA"
    with pytest.raises(ErrorNegocio) as error:
        await bib.registrar_verificacion(mundo.sesion, mundo.ta, mundo.ids["revisor_a"], mundo.tareas[mundo.ta],
                                         _verificacion(ev_b.id), roadmap.obtener_accion_para_enlace,
                                         roadmap.reabrir_accion_no_conforme)
    assert error.value.code == "BIB_EVIDENCIA_NO_ENCONTRADA"
    await mundo.sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": mundo.ta})
    assert (await mundo.sesion.execute(text("SELECT count(*) FROM biblioteca_evidencias"))).scalar() == 0
    with pytest.raises(DBAPIError):  # WITH CHECK impide escribir filas de B estando en A
        async with mundo.sesion.begin_nested():
            await mundo.sesion.execute(text(
                "INSERT INTO biblioteca_evidencias(id,tenant_id,accion_id,titulo,version,sha256,clasificacion,"
                "permisos,fecha,creado_por) VALUES (:id,:t,:a,'x','1',:h,'interna',ARRAY['dpo'],now(),:u)"),
                {"id": str(uuid4()), "t": mundo.tb, "a": mundo.tareas[mundo.tb], "h": HASH, "u": mundo.ids["autor_b"]})


@pytest.mark.asyncio
async def test_db_expediente_inmutable_para_la_aplicacion(mundo):
    ev = await _registrar(mundo, mundo.ta, mundo.ids["autor_a"])
    await bib.registrar_verificacion(mundo.sesion, mundo.ta, mundo.ids["revisor_a"], mundo.tareas[mundo.ta],
                                     _verificacion(ev.id), roadmap.obtener_accion_para_enlace,
                                     roadmap.reabrir_accion_no_conforme)
    for sentencia in ("UPDATE biblioteca_verificaciones SET resultado='no_conforme'",
                      "DELETE FROM biblioteca_verificaciones", "UPDATE biblioteca_evidencias SET sha256=sha256",
                      "DELETE FROM biblioteca_evidencias"):
        with pytest.raises(DBAPIError, match="permission denied"):
            async with mundo.sesion.begin_nested():
                await mundo.sesion.execute(text(sentencia))
    await mundo.conexion.execute(text("RESET ROLE"))
    with pytest.raises(DBAPIError, match="ck_bib_verif_conforme_legible"):
        async with mundo.conexion.begin_nested():
            await mundo.conexion.execute(text(
                "INSERT INTO biblioteca_verificaciones(id,tenant_id,accion_id,evidencia_id,criterio,evidencia_legible,"
                "resultado,revisor,fecha) VALUES (:id,:t,:a,:e,'criterio largo',false,'conforme',:u,now())"),
                {"id": str(uuid4()), "t": mundo.ta, "a": mundo.tareas[mundo.ta], "e": ev.id, "u": mundo.ids["revisor_a"]})
    await mundo.conexion.execute(text("SET LOCAL ROLE lopdp_app"))


# ---- API: la organización sale de la sesión y los roles se aplican en servidor

@pytest_asyncio.fixture
async def api(mundo, monkeypatch):
    from main import app

    async def sesion():
        yield mundo.sesion

    async def contexto(request: Request):
        return {"user_id": request.headers["x-test-user"], "tenant_id": request.headers["x-test-tenant"],
                "role": request.headers["x-test-role"]}

    monkeypatch.setitem(app.dependency_overrides, get_session, sesion)
    monkeypatch.setitem(app.dependency_overrides, get_context, contexto)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as cliente:
        yield cliente


@pytest.mark.asyncio
async def test_api_recorrido_y_roles(api, mundo):
    base = f"/api/v1/biblioteca/verificaciones/acciones/{mundo.tareas[mundo.ta]}"
    autor = {"x-test-tenant": mundo.ta, "x-test-user": mundo.ids["autor_a"], "x-test-role": "implementador"}
    revisor = {"x-test-tenant": mundo.ta, "x-test-user": mundo.ids["revisor_a"], "x-test-role": "coordinador"}
    creada = await api.post(f"{base}/evidencias", headers=autor, json=_evidencia())
    assert creada.status_code == 201
    cuerpo = {"evidencia_id": creada.json()["id"], "criterio": "Cubre el 100 % del personal",
              "evidencia_legible": True, "resultado": "conforme", "fecha": date.today().isoformat()}
    assert (await api.post(f"{base}/verificaciones", headers=autor, json=cuerpo)).status_code == 403
    ilegible = await api.post(f"{base}/verificaciones", headers=revisor, json={**cuerpo, "evidencia_legible": False})
    assert ilegible.status_code == 422 and ilegible.json()["code"] == "BIB_VERIF_EVIDENCIA_ILEGIBLE"
    ok = await api.post(f"{base}/verificaciones", headers=revisor, json=cuerpo)
    assert ok.status_code == 201 and ok.json()["veredicto"] == "conforme"
    ajena = {"x-test-tenant": mundo.tb, "x-test-user": mundo.ids["autor_b"], "x-test-role": "implementador"}
    respuesta = await api.get(base, headers=ajena)
    assert respuesta.status_code == 422 and respuesta.json()["code"] == "BIB_VERIF_ACCION_AJENA"
