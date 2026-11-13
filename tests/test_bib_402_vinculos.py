# ¤adpa ¤rbac-tenant ¤rat ¤hallazgos ¤arbitro
"""Árbitro BIB-402: vínculos documento ↔ tratamiento, control y tarea (governance/especificaciones/BIB-402.md).

Las reglas se prueban con una sesión en memoria que interpreta solo el SQL del motor; la persistencia y la RLS
con `lopdp_app`, contra el PostgreSQL local del arnés (ARNES_BASE=postgresql_local) o con una URL local; una URL remota no la habilita. Nunca producción ni la rama `test` compartida.

Mutación decisiva (R1): añadir en `al_aprobar_documento` un
``UPDATE roadmap_tasks SET status='completada' WHERE id=:t`` por cada tarea vinculada hace fallar
``test_aprobar_adjunta_no_cierra``; retirarlo devuelve el archivo a verde.
"""
import hashlib
import importlib.util
import os
from urllib.parse import urlparse
import re
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from pydantic import ValidationError

from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.services import vinculos_engine as motor

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = ROOT / "alembic/versions/20261103_biblioteca_vinculos.py"
AHORA = datetime(2026, 11, 4, tzinfo=timezone.utc)


# ----------------------------------------------------------------------------- sesión en memoria

class _Resultado:
    def __init__(self, filas=None, escalar=None):
        self._filas, self._escalar = filas or [], escalar

    def scalar(self):
        return self._escalar

    def scalars(self):
        return SimpleNamespace(all=lambda: [next(iter(f.values())) for f in self._filas])

    def mappings(self):
        return SimpleNamespace(all=lambda: list(self._filas), first=lambda: self._filas[0] if self._filas else None)


class SesionMemoria:
    """Interpreta las sentencias del motor sobre `biblioteca_vinculos`, y registra cualquier otra."""

    def __init__(self, documentos: dict[str, dict], tareas: dict[str, str] | None = None):
        self.documentos = documentos
        self.tareas = dict(tareas or {})
        self.vinculos: list[dict] = []
        self.sql: list[str] = []

    async def execute(self, consulta, p=None):
        sql, p = " ".join(str(consulta).split()), p or {}
        self.sql.append(sql)
        if sql.startswith("SELECT 1 FROM biblioteca_documentos"):
            doc = self.documentos.get(p["d"])
            return _Resultado(escalar=1 if doc and doc["tenant_id"] == p["t"] else None)
        if sql.startswith("SELECT sha256 FROM biblioteca_documentos"):
            doc = self.documentos.get(p["d"])
            ok = doc and doc["tenant_id"] == p["t"] and doc["estado"] == "aprobado"
            return _Resultado(escalar=doc["sha256"] if ok else None)
        if sql.startswith("UPDATE roadmap_tasks"):
            estado = re.search(r"status='(\w+)'", sql)
            self.tareas[p.get("t") or p.get("id")] = estado.group(1) if estado else "?"
            return _Resultado()
        propios = [v for v in self.vinculos if v["tenant_id"] == p.get("t")]
        if sql.startswith("SELECT tipo,ref FROM biblioteca_vinculos"):
            return _Resultado([v for v in propios if v["documento_id"] == p["d"]])
        if sql.startswith("SELECT id,documento_id,tipo,ref,estado"):
            filas = sorted((v for v in propios if v["documento_id"] == p["d"]), key=lambda v: (v["tipo"], v["ref"]))
            return _Resultado([{k: v[k] for k in ("id", "documento_id", "tipo", "ref", "estado", "creado_por",
                                                  "creado_en")} for v in filas])
        if sql.startswith("SELECT ref FROM biblioteca_vinculos"):
            return _Resultado([{"ref": v["ref"]} for v in sorted(propios, key=lambda v: v["ref"])
                               if v["documento_id"] == p["d"] and v["tipo"] == "tarea"])
        if sql.startswith("DELETE FROM biblioteca_vinculos"):
            self.vinculos = [v for v in self.vinculos if not (
                v["tenant_id"] == p["t"] and v["documento_id"] == p["d"] and v["tipo"] == p["k"] and v["ref"] == p["r"])]
            return _Resultado()
        if sql.startswith("INSERT INTO biblioteca_vinculos"):
            if not any(v["documento_id"] == p["d"] and v["tipo"] == p["k"] and v["ref"] == p["r"] for v in propios):
                self.vinculos.append({"id": p["id"], "tenant_id": p["t"], "documento_id": p["d"], "tipo": p["k"],
                                      "ref": p["r"], "estado": "vigente", "creado_por": p["u"], "creado_en": AHORA})
            return _Resultado()
        if sql.startswith("UPDATE biblioteca_vinculos SET estado='revisar'"):
            tocados = [v for v in propios if v["tipo"] == "tratamiento" and v["ref"] == p["r"]]
            for v in tocados:
                v["estado"] = "revisar"
            return _Resultado([{"documento_id": v["documento_id"]} for v in tocados])
        if sql.startswith("SELECT v.documento_id"):
            return _Resultado([{"documento_id": v["documento_id"], "codigo": "D", "nombre": "Doc",
                                "estado_documento": self.documentos[v["documento_id"]]["estado"],
                                "estado": v["estado"]} for v in propios
                               if v["tipo"] == "tratamiento" and v["ref"] == p["r"]])
        raise AssertionError(f"SQL inesperado: {sql}")


class Referencias:
    def __init__(self, tratamientos=(), tareas=()):
        self.tratamientos, self.tareas = set(tratamientos), set(tareas)

    async def tratamiento_existe(self, session, tenant_id, ref):
        return ref in self.tratamientos

    async def tarea_existe(self, session, tenant_id, ref):
        return ref in self.tareas


@pytest.fixture(autouse=True)
def _sin_base(monkeypatch):
    monkeypatch.setattr(motor, "contexto", AsyncMock())
    monkeypatch.setattr(motor, "registrar_evento", AsyncMock())


def _doc(tenant="org-a", estado="borrador", sha="a" * 64):
    return {"tenant_id": tenant, "estado": estado, "sha256": sha}


# ----------------------------------------------------------------------------- contratos

def test_contratos_rutas_compuerta_y_error():
    from importlib import import_module
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://usuario:clave@localhost/pruebas")
    router = import_module("api.routers.biblioteca_vinculos")
    assert router.AUTO_REGISTRO is True
    assert {(m, r.path) for r in router.router.routes for m in r.methods} == {
        ("GET", "/biblioteca/documentos/{documento_id}/vinculos"),
        ("PUT", "/biblioteca/documentos/{documento_id}/vinculos"),
        ("GET", "/biblioteca/tratamientos/{tratamiento_id}/documentos"),
    }
    for nombre in ("EntradaVinculos", "VinculosDocumento", "listar_vinculos", "reemplazar_vinculos",
                   "documentos_de_tratamiento", "al_aprobar_documento", "al_cambiar_tratamiento"):
        assert nombre in bib.__all__ and hasattr(bib, nombre)
    assert CATALOGO_ERRORES["VINCULO_REF_INEXISTENTE"].status_code == 422
    with pytest.raises(ValidationError):
        bib.EntradaVinculos(tratamientos=[], tenant_id="otra")  # la organización sale del token


def test_roles_de_escritura_implementador_y_coordinador():
    codigo = (ROOT / "api/routers/biblioteca_vinculos.py").read_text(encoding="utf-8")
    assert 'require_role("implementador", "coordinador")' in codigo
    assert codigo.count("ctx: Gestion") == 1 and codigo.count("ctx: Consulta") == 2


def test_migracion_rls_forzada_grants_minimos_y_revision_existente():
    spec = importlib.util.spec_from_file_location("bib402_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    cfg = Config(str(ROOT / "alembic.ini")); cfg.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(cfg)
    assert len(guion.get_heads()) == 1
    assert guion.get_revision(migracion.revision) is not None
    assert guion.get_revision(migracion.down_revision) is not None
    sql = []
    migracion.op = SimpleNamespace(execute=sql.append)
    migracion.upgrade()
    texto = "\n".join(sql)
    assert "CHECK (tipo IN ('tratamiento','control','tarea'))" in texto
    assert "CHECK (estado IN ('vigente','revisar'))" in texto
    assert "UNIQUE (tenant_id, documento_id, tipo, ref)" in texto
    assert "ENABLE ROW LEVEL SECURITY" in texto and "FORCE ROW LEVEL SECURITY" in texto
    assert "WITH CHECK (tenant_id::text=current_setting('app.current_tenant_id',true))" in texto
    assert "GRANT UPDATE (estado) ON biblioteca_vinculos TO lopdp_app" in texto
    assert "GRANT ALL" not in texto and "GRANT SELECT,INSERT,UPDATE" not in texto


def test_limite_adpa_sin_imports_de_otras_salas():
    for relativa in ("features/biblioteca/services/vinculos_engine.py", "api/routers/biblioteca_vinculos.py"):
        codigo = (ROOT / relativa).read_text(encoding="utf-8")
        assert "features.rat" not in codigo, "RAT solo por app_core/pasillo/rat.py"
        assert len(codigo.splitlines()) <= 500
    motor_codigo = (ROOT / "features/biblioteca/services/vinculos_engine.py").read_text(encoding="utf-8")
    assert "features.roadmap" not in motor_codigo and "app_core.pasillo" not in motor_codigo
    assert "roadmap_tasks" not in motor_codigo and "hallazgos " not in motor_codigo


# ----------------------------------------------------------------------------- reglas

@pytest.mark.asyncio
async def test_vinculo_ref_valida():
    sesion = SesionMemoria({"doc-1": _doc()})
    with pytest.raises(ErrorNegocio) as error:
        await bib.reemplazar_vinculos(sesion, "org-a", "u-1", "doc-1", bib.EntradaVinculos(controles=["P99"]),
                                      Referencias())
    assert error.value.code == "VINCULO_REF_INEXISTENTE"
    assert not any(s.startswith(("INSERT", "DELETE")) for s in sesion.sql), "nada se escribe si falla R3"
    for malo in ("P0", "P01", "P81", "p5", "X1"):
        assert not bib.es_control(malo)
    assert all(bib.es_control(f"P{n}") for n in range(1, 81))


@pytest.mark.asyncio
@pytest.mark.parametrize("entrada", [{"tratamientos": ["rat-ajeno"]}, {"tareas": ["tarea-ajena"]}])
async def test_tratamiento_o_tarea_ajenos_son_422(entrada):
    sesion = SesionMemoria({"doc-1": _doc()})
    with pytest.raises(ErrorNegocio) as error:
        await bib.reemplazar_vinculos(sesion, "org-a", "u-1", "doc-1", bib.EntradaVinculos(**entrada),
                                      Referencias(tratamientos={"rat-1"}, tareas={"t-1"}))
    assert error.value.code == "VINCULO_REF_INEXISTENTE"


@pytest.mark.asyncio
async def test_documento_de_otra_organizacion_es_404():
    sesion = SesionMemoria({"doc-1": _doc(tenant="org-b")})
    with pytest.raises(ErrorNegocio) as error:
        await bib.listar_vinculos(sesion, "org-a", "u-1", "doc-1")
    assert error.value.code == "BIB_DOCUMENTO_NO_ENCONTRADO"


@pytest.mark.asyncio
async def test_put_reemplaza_el_conjunto_y_conserva_estado():
    sesion = SesionMemoria({"doc-1": _doc()})
    refs = Referencias(tratamientos={"rat-1", "rat-2"}, tareas={"t-1"})
    await bib.reemplazar_vinculos(sesion, "org-a", "u-1", "doc-1", bib.EntradaVinculos(
        tratamientos=["rat-1", "rat-1"], controles=["P5"], tareas=["t-1"]), refs)
    await bib.al_cambiar_tratamiento(sesion, "org-a", "u-1", "rat-1", SimpleNamespace(registrar=AsyncMock()))
    resultado = await bib.reemplazar_vinculos(sesion, "org-a", "u-1", "doc-1", bib.EntradaVinculos(
        tratamientos=["rat-1", "rat-2"], controles=[]), refs)
    assert [(v.tipo, v.ref, v.estado) for v in resultado.vinculos] == [
        ("tratamiento", "rat-1", "revisar"), ("tratamiento", "rat-2", "vigente")]


@pytest.mark.asyncio
async def test_aprobar_adjunta_no_cierra(monkeypatch):
    """R1 con el adaptador real del router: evidencia nueva en la tarea y la tarea sigue `pendiente`."""
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://usuario:clave@localhost/pruebas")
    from api.routers import biblioteca_vinculos as rutas
    from features.roadmap import roadmap_service

    sesion = SesionMemoria({"doc-1": _doc()}, tareas={"t-1": "pendiente"})
    await bib.reemplazar_vinculos(sesion, "org-a", "u-1", "doc-1", bib.EntradaVinculos(tareas=["t-1"]),
                                  Referencias(tareas={"t-1"}))
    evidencias = []

    async def registrar(session, tenant_id, user_id, task_id, r2_key, mime_type, file_size, file_hash=None):
        evidencias.append((tenant_id, task_id, file_hash))
        return {"id": "e-1"}

    monkeypatch.setattr(roadmap_service, "register_evidence_upload", registrar)
    assert await bib.al_aprobar_documento(sesion, "org-a", "u-2", "doc-1", rutas.EvidenciasVinculos()) == 0, "sin aprobar no hay evidencia"
    sesion.documentos["doc-1"]["estado"] = "aprobado"
    assert await bib.al_aprobar_documento(sesion, "org-a", "u-2", "doc-1", rutas.EvidenciasVinculos()) == 1
    assert evidencias == [("org-a", "t-1", "a" * 64)]
    assert sesion.tareas == {"t-1": "pendiente"}
    assert not any("roadmap_tasks" in s for s in sesion.sql)


@pytest.mark.asyncio
async def test_baja_tratamiento_marca_documentos(monkeypatch):
    """R2 con el adaptador real del router: 2 documentos «revisar» y 2 hallazgos `rat` de severidad media."""
    os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://usuario:clave@localhost/pruebas")
    from api.routers import biblioteca_vinculos as rutas
    from app_core.pasillo import roadmap as pasillo_roadmap

    sesion = SesionMemoria({"doc-1": _doc(), "doc-2": _doc(), "doc-3": _doc()})
    refs = Referencias(tratamientos={"rat-1", "rat-2"})
    for doc, rat in (("doc-1", "rat-1"), ("doc-2", "rat-1"), ("doc-3", "rat-2")):
        await bib.reemplazar_vinculos(sesion, "org-a", "u-1", doc, bib.EntradaVinculos(tratamientos=[rat]), refs)
    hallazgo = AsyncMock(return_value=("h", True))
    monkeypatch.setattr(pasillo_roadmap, "registrar_hallazgo_rat", hallazgo)
    assert await bib.al_cambiar_tratamiento(sesion, "org-a", "u-1", "rat-1", rutas.HallazgosVinculos()) == ["doc-1", "doc-2"]
    estados = {v["documento_id"]: v["estado"] for v in sesion.vinculos}
    assert estados == {"doc-1": "revisar", "doc-2": "revisar", "doc-3": "vigente"}
    assert hallazgo.await_count == 2
    origenes = sorted(c.args[3] for c in hallazgo.await_args_list)
    assert origenes == ["rat-1:documento:doc-1", "rat-1:documento:doc-2"]
    assert all(c.args[4] == "media" for c in hallazgo.await_args_list)
    vista = await bib.documentos_de_tratamiento(sesion, "org-a", "u-1", "rat-1")
    assert {d.documento_id for d in vista} == {"doc-1", "doc-2"} and all(d.estado == "revisar" for d in vista)


# ----------------------------------------------------------------------------- persistencia y RLS (base propia)

@pytest_asyncio.fixture
async def db_bib402():
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

    url = os.environ.get("TEST_DATABASE_URL", "")
    if "ep-late-hall" in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or not (os.environ.get("ARNES_BASE") == "postgresql_local" or (urlparse(url).hostname or "") in ("127.0.0.1", "localhost", "::1")):
        pytest.skip("Persistencia pendiente: falta base local (arnés PostgreSQL 16 en 127.0.0.1 o ARNES_BASE=postgresql_local); una URL remota no habilita pruebas con base")
    if "ep-soft-darkness" in url.lower():
        pytest.fail("La rama test compartida no es una base propia", pytrace=False)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text("SELECT to_regclass('biblioteca_vinculos')"))).scalar():
                pytest.fail("Aplicar la migración de BIB-402 en la base propia antes de este árbitro", pytrace=False)
            usuario = "bib402-u-" + uuid4().hex
            orgs = ["bib402-org-" + uuid4().hex, "bib402-org-" + uuid4().hex]
            docs = [str(uuid4()), str(uuid4())]
            await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,'BIB-402')"),
                                   {"id": usuario, "e": usuario + "@example.test"})
            for org, doc in zip(orgs, docs):
                await conexion.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:id, 'Org sintética', 'Org sintética S.A.', :ruc)"), {"id": org, "ruc": str(uuid4().int)[:13]})
                await conexion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": org})
                await conexion.execute(text(
                    "INSERT INTO biblioteca_documentos(id,tenant_id,codigo,nombre,origen,contenido_markdown,sha256,"
                    "fecha_emision,proxima_revision,creado_por) VALUES (:id,:t,'X','X','propio','a',:h,now(),now(),:u)"),
                    {"id": doc, "t": org, "h": hashlib.sha256(b"a").hexdigest(), "u": usuario})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield sesion, usuario, orgs, docs
        except DBAPIError:
            pytest.fail("Fallo DB BIB-402 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


@pytest.mark.asyncio
async def test_db_rls_y_permisos_con_lopdp_app(db_bib402, monkeypatch):
    from sqlalchemy import text
    from sqlalchemy.exc import DBAPIError
    from app_core.db.session import fijar_contexto_rls

    sesion, usuario, (org_a, org_b), (doc_a, doc_b) = db_bib402
    monkeypatch.setattr(motor, "contexto", fijar_contexto_rls)
    refs = Referencias(tratamientos={"rat-1"})
    hecho = await bib.reemplazar_vinculos(sesion, org_a, usuario, doc_a, bib.EntradaVinculos(
        tratamientos=["rat-1"], controles=["P7"]), refs)
    assert {(v.tipo, v.ref) for v in hecho.vinculos} == {("tratamiento", "rat-1"), ("control", "P7")}
    assert await bib.al_cambiar_tratamiento(sesion, org_a, usuario, "rat-1",
                                            SimpleNamespace(registrar=AsyncMock())) == [doc_a]
    # Desde B no se ve ni se toca lo de A.
    with pytest.raises(ErrorNegocio):
        await bib.listar_vinculos(sesion, org_b, usuario, doc_a)
    assert await bib.al_cambiar_tratamiento(sesion, org_b, usuario, "rat-1",
                                            SimpleNamespace(registrar=AsyncMock())) == []
    assert (await sesion.execute(text("SELECT count(*) FROM biblioteca_vinculos"))).scalar() == 0
    with pytest.raises(DBAPIError):  # WITH CHECK
        async with sesion.begin_nested():
            await sesion.execute(text(
                "INSERT INTO biblioteca_vinculos(id,tenant_id,documento_id,tipo,ref,creado_por) "
                "VALUES ('x',:t,:d,'control','P1',:u)"), {"t": org_a, "d": doc_a, "u": usuario})
    await fijar_contexto_rls(sesion, org_a, usuario)
    with pytest.raises(DBAPIError):  # UPDATE solo sobre `estado`
        async with sesion.begin_nested():
            await sesion.execute(text("UPDATE biblioteca_vinculos SET ref='P2' WHERE tenant_id=:t"), {"t": org_a})
    final = await bib.listar_vinculos(sesion, org_a, usuario, doc_a)
    assert {(v.ref, v.estado) for v in final.vinculos} == {("rat-1", "revisar"), ("P7", "vigente")}
