# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-107: documentos de cada organización.

Reglas puras, migración y rutas siempre. La persistencia y la RLS con `lopdp_app` corren contra el arnés
local (ARNES_BASE=postgresql_local) o una rama propia con BIB107_RAMA_PROPIA=1; sin ellas se omiten y no se
acreditan. Todo ocurre en una transacción que se revierte, con datos sintéticos.

Mutación decisiva (BIB-107.md): quitar `AND tenant_id=:t` y el `tenant_id=:t` inicial de `listar_documentos`
(features/biblioteca/services/documentos_consulta.py) hace fallar `test_db_el_filtro_del_servicio_aisla_aun_sin_rls`.
Solo esa: las demás siguen verdes porque la RLS forzada ya protege a `lopdp_app`. Por eso aquella prueba corre con un
rol que omite la RLS y demuestra que el servicio filtra por organización él solo.
"""
import os
from datetime import date, timedelta
from pathlib import Path
from uuid import uuid4
import httpx
import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
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
from features.biblioteca.domain import documentos as dominio
from features.biblioteca.services import documentos as servicio
from main import app

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = next((ROOT / "alembic/versions").glob("*_biblioteca_documentos.py"), None)
PRODUCCION, COMPARTIDA = "ep-late-hall-b50bpbk5", "ep-soft-darkness-b5z454vp"
FICHA = {"nombre": "Plantilla sintética", "objetivo": "Probar", "fuentes": "Fuente de prueba",
         "fecha_revision": "2026-10-28", "instrucciones": "Revisar", "dependencias": "Ninguna",
         "restricciones": "Solo pruebas"}
CUERPO = ("# Política de {{organizacion.razon_social}}\nEmitida el {{fecha_emision}}\n"
          "{{#si dpo.designado}}{{dpo.nombre}}{{#sino}}Sin delegado{{/si}}\n")


# ---------------------------------------------------------------------------- reglas puras (sin BD)

# ¤adpa
def test_variables_faltantes_se_leen_del_contenido_y_las_etiquetas_de_bloque_no_cuentan():
    relleno, faltantes = dominio.RellenadoLiteral().rellenar({"cuerpo_md": CUERPO}, {}, {})
    assert faltantes == ["organizacion.razon_social", "fecha_emision", "dpo.nombre"]
    assert "⟦falta: organizacion.razon_social⟧" in relleno and "{{#si dpo.designado}}" in relleno
    assert dominio.faltantes_de(relleno) == faltantes
    assert dominio.faltantes_de("Texto ya completo") == []


# ¤adpa
def test_proxima_revision_suma_meses_sin_desbordar_el_dia():
    assert dominio.sumar_meses(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert dominio.sumar_meses(date(2027, 12, 15), 12) == date(2028, 12, 15)
    assert dominio.sumar_meses(date(2026, 11, 3), 1) == date(2026, 12, 3)
    assert dominio.meses_de_revision({"revision_meses": 6}) == 6
    for invalido in ({}, None, {"revision_meses": 0}, {"revision_meses": True}, {"revision_meses": "12"}):
        assert dominio.meses_de_revision(invalido) == dominio.MESES_REVISION


# ¤adpa
def test_vencido_se_calcula_solo_para_los_aprobados():
    hoy = date(2026, 11, 3)
    assert dominio.estado_efectivo("aprobado", date(2026, 11, 2), hoy) == "vencido"
    assert dominio.estado_efectivo("aprobado", hoy, hoy) == "aprobado"
    assert dominio.estado_efectivo("borrador", date(2020, 1, 1), hoy) == "borrador"


# ¤adpa
def test_el_cuerpo_nunca_nombra_la_organizacion():
    with pytest.raises(ValidationError):
        dominio.CrearDocumento(plantilla_id="x", tenant_id="otra")
    with pytest.raises(ValidationError):
        dominio.CambiarDocumento(contenido_markdown="x", revision=1, tenant_id="otra")
    with pytest.raises(ValidationError):
        dominio.CambiarDocumento(contenido_markdown="x", revision=0)


# ¤adpa
def test_la_compuerta_expone_lo_de_bib_107_y_registra_sus_errores():
    for nombre in ("crear_documento", "cambiar_documento", "listar_documentos", "obtener_documento", "pendientes",
                   "historial_documento", "registrar_rellenador", "Documento", "PuertoRellenado"):
        assert nombre in bib.__all__ and hasattr(bib, nombre)
    for codigo, estado in (("BIB_DOCUMENTO_NO_ENCONTRADO", 404), ("BIB_PLANTILLA_NO_DISPONIBLE", 404),
                           ("BIB_DOCUMENTO_REVISION_DESFASADA", 409), ("BIB_DOCUMENTO_NO_EDITABLE", 409),
                           ("BIB_TAREA_AJENA", 422)):
        assert CATALOGO_ERRORES[codigo].status_code == estado


# ¤adpa
def test_secciones_de_la_ficha_una_vez_y_archivos_dentro_del_tope():
    for relativa in ("features/biblioteca/biblioteca_service.py", "features/biblioteca/domain/errores.py"):
        texto = (ROOT / relativa).read_text(encoding="utf-8")
        assert texto.count("# === BIB-107 ===") == 1 and texto.count("# === fin BIB-107 ===") == 1
    for relativa in ("features/biblioteca/services/documentos.py", "features/biblioteca/services/documentos_consulta.py",
                     "features/biblioteca/domain/documentos.py", "api/routers/biblioteca_documentos.py"):
        assert len((ROOT / relativa).read_text(encoding="utf-8").splitlines()) <= 500


# ¤adpa
def test_rutas_del_contrato_y_pendientes_antes_que_el_id():
    from api.routers import biblioteca_documentos as router
    assert router.AUTO_REGISTRO is True
    rutas = [(sorted(r.methods)[0], r.path) for r in router.router.routes]
    base = "/biblioteca/documentos"
    for esperada in (("POST", base), ("GET", base), ("GET", base + "/pendientes"), ("GET", base + "/{documento_id}"),
                     ("PATCH", base + "/{documento_id}")):
        assert esperada in rutas
    assert rutas.index(("GET", base + "/pendientes")) < rutas.index(("GET", base + "/{documento_id}"))
    publicadas = app.openapi()["paths"]  # main las monta bajo /api/v1 por AUTO_REGISTRO
    assert set(publicadas["/api/v1" + base]) == {"get", "post"}
    assert set(publicadas["/api/v1" + base + "/{documento_id}"]) == {"get", "patch"}
    assert "/api/v1" + base + "/pendientes" in publicadas


# ¤adpa
def test_migracion_una_cabeza_rls_forzada_y_permisos_minimos():
    import importlib.util
    assert MIGRACION is not None, "falta alembic/versions/*_biblioteca_documentos.py"
    spec = importlib.util.spec_from_file_location("bib107_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    configuracion = Config(str(ROOT / "alembic.ini"))
    configuracion.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(configuracion)
    cabezas = guion.get_heads()
    assert len(cabezas) == 1
    assert migracion.revision in {r.revision for r in guion.iterate_revisions(cabezas[0], "base")}
    assert guion.get_revision(migracion.down_revision) is not None
    sql = []

    class Operaciones:
        def execute(self, consulta):
            sql.append(consulta)
    migracion.op = Operaciones()
    migracion.upgrade()
    texto = "\n".join(sql)
    for tabla in ("biblioteca_documentos", "biblioteca_documentos_historial"):
        assert f"ALTER TABLE {tabla} ENABLE ROW LEVEL SECURITY" in texto
        assert f"ALTER TABLE {tabla} FORCE ROW LEVEL SECURITY" in texto
        assert f"CREATE POLICY tenant_isolation_{tabla} ON {tabla}" in texto
    assert texto.count("USING (tenant_id::text = current_setting('app.current_tenant_id', true))") == 2
    assert texto.count("WITH CHECK (tenant_id::text = current_setting('app.current_tenant_id', true))") == 2
    assert "GRANT SELECT, INSERT ON biblioteca_documentos, biblioteca_documentos_historial TO lopdp_app" in texto
    assert "DELETE" not in texto.replace("BEFORE UPDATE OR DELETE", "") and "GRANT ALL" not in texto
    assert "GRANT UPDATE (contenido_markdown, editado, sha256, revision, actualizado_en)" in texto
    assert "estado" not in texto.split("GRANT UPDATE (")[1].split(")")[0]


# --------------------------------------------------------------------------- persistencia (arnés local)

# ¤adpa
def _url_de_pruebas() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or not (os.environ.get("ARNES_BASE") == "postgresql_local" or os.environ.get("BIB107_RAMA_PROPIA") == "1"):
        pytest.skip("Persistencia/RLS no acreditadas: falta el arnés local o rama propia (BIB107_RAMA_PROPIA=1)")
    if COMPARTIDA in url.lower():
        pytest.fail("La rama test compartida no es una rama propia; no se abrió conexión", pytrace=False)
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


class Mundo:
    """Dos organizaciones con un redactor cada una y una plantilla publicada, dentro de una transacción."""
    def __init__(self, conexion, sesion, ids, ta, tb, plantilla_id):
        self.conexion, self.sesion, self.ids, self.ta, self.tb, self.plantilla_id = conexion, sesion, ids, ta, tb, plantilla_id

    async def como_propietario(self, sql: str, **parametros):
        await self.conexion.execute(text("RESET ROLE"))
        try:
            return await self.conexion.execute(text(sql), parametros)
        finally:
            await self.conexion.execute(text("SET LOCAL ROLE lopdp_app"))


# ¤adpa
async def _publicar(sesion, ids):
    version = await bib.crear_version_md(sesion, ids["editor"], "TEST-" + uuid4().hex[:10].upper(), "0.1.0", CUERPO)
    version = await bib.editar(sesion, ids["editor"], version["id"], bib.EditarFicha(
        ficha=bib.Ficha(**FICHA), generacion=version["generacion"]))
    for rol, tipo in (("tecnico", "tecnica"), ("juridico", "juridica")):
        await bib.revisar(sesion, ids[rol], version["id"], bib.Dictamen(
            tipo=tipo, aprobado=True, comentario="Dictamen sintético", generacion=version["generacion"]))
    return await bib.publicar(sesion, ids["publicador"], version["id"], bib.Transicion(
        generacion=version["generacion"], motivo="Publicación sintética"))


# ¤adpa
@pytest_asyncio.fixture
async def mundo():
    engine = create_async_engine(_url_de_pruebas(), echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text("SELECT to_regclass('public.biblioteca_documentos')"))).scalar():
                pytest.fail("Aplicar la migración de BIB-107 solo en la base local o rama propia", pytrace=False)
            ids = {rol: "bib107-" + uuid4().hex for rol in
                   ("editor", "tecnico", "juridico", "publicador", "redactor_a", "redactor_b", "lector_a")}
            ta, tb = "bib107-org-" + uuid4().hex, "bib107-org-" + uuid4().hex
            for rol, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,:n)"),
                                       {"id": usuario, "e": usuario + "@example.test", "n": rol})
            for tid in (ta, tb):
                await conexion.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:id, 'Org sintética', 'Org sintética S.A.', :ruc)"), {"id": tid, "ruc": str(uuid4().int)[:13]})
            for usuario, tid, rol in ((ids["redactor_a"], ta, "implementador"), (ids["redactor_b"], tb, "implementador"),
                                      (ids["lector_a"], ta, "responsable_area")):
                await conexion.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                                            "VALUES (:id, :u, :t, :r)"), {"id": str(uuid4()), "u": usuario, "t": tid, "r": rol})
            for rol, capacidad in (("editor", "editor"), ("tecnico", "revisor_tecnico"),
                                   ("juridico", "revisor_juridico"), ("publicador", "publicador")):
                await conexion.execute(text("INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                                            "VALUES (:id,:cap,:id,'Fixture sintética rollback')"), {"id": ids[rol], "cap": capacidad})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False, join_transaction_mode="create_savepoint") as sesion:
                await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": ta})
                publicada = await _publicar(sesion, ids)
                yield Mundo(conexion, sesion, ids, ta, tb, publicada["id"])
        except DBAPIError:
            pytest.fail("Fallo DB BIB-107 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


# ¤adpa
def _crear(m: Mundo, tenant: str, usuario: str, **extra):
    return bib.crear_documento(m.sesion, tenant, usuario, bib.CrearDocumento(plantilla_id=m.plantilla_id, **extra))


# ¤adpa
@pytest.mark.asyncio
async def test_db_crea_borrador_desde_plantilla_con_historial_y_proxima_revision(mundo):
    emision = date(2026, 1, 31)
    doc = await _crear(mundo, mundo.ta, mundo.ids["redactor_a"], fecha_emision=emision)
    assert (doc.origen, doc.estado, doc.revision, doc.editado) == ("plantilla", "borrador", 1, False)
    assert doc.plantilla_id == mundo.plantilla_id and doc.plantilla_version == "0.1.0"
    assert doc.proxima_revision == date(2027, 1, 31) and doc.fecha_emision == emision
    assert doc.variables_faltantes == ["organizacion.razon_social", "fecha_emision", "dpo.nombre"]
    assert doc.sha256 == dominio.huella(doc.contenido_markdown) and doc.aprobado_por is None
    assert [(e.revision, e.accion) for e in await bib.historial_documento(
        mundo.sesion, mundo.ta, mundo.ids["redactor_a"], doc.id)] == [(1, "creado")]


# ¤adpa
@pytest.mark.asyncio
async def test_db_plantilla_inexistente_o_sin_publicar_no_crea_documento(mundo):
    for falsa in ("no-existe", (await bib.crear_version_md(
            mundo.sesion, mundo.ids["editor"], "TEST-" + uuid4().hex[:10].upper(), "0.1.0", CUERPO))["id"]):
        with pytest.raises(ErrorNegocio) as exc:
            await bib.crear_documento(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], bib.CrearDocumento(plantilla_id=falsa))
        assert exc.value.code == "BIB_PLANTILLA_NO_DISPONIBLE"


# ¤adpa
@pytest.mark.asyncio
async def test_db_edicion_guarda_revision_y_una_revision_desfasada_es_409_sin_perder_nada(mundo):
    actor = mundo.ids["redactor_a"]
    doc = await _crear(mundo, mundo.ta, actor)
    editado = await bib.cambiar_documento(mundo.sesion, mundo.ta, actor, doc.id, bib.CambiarDocumento(
        contenido_markdown="Texto completo sin variables", revision=1))
    assert (editado.revision, editado.editado, editado.variables_faltantes) == (2, True, [])
    assert editado.sha256 == dominio.huella("Texto completo sin variables")
    with pytest.raises(ErrorNegocio) as exc:
        await bib.cambiar_documento(mundo.sesion, mundo.ta, actor, doc.id, bib.CambiarDocumento(
            contenido_markdown="Pisa el cambio ajeno", revision=1))
    assert exc.value.code == "BIB_DOCUMENTO_REVISION_DESFASADA" and exc.value.status_code == 409
    vigente = await bib.obtener_documento(mundo.sesion, mundo.ta, actor, doc.id)
    assert vigente.contenido_markdown == "Texto completo sin variables" and vigente.revision == 2
    historial = await bib.historial_documento(mundo.sesion, mundo.ta, actor, doc.id)
    assert [(e.revision, e.accion) for e in historial] == [(1, "creado"), (2, "editado")]


# ¤adpa
@pytest.mark.asyncio
async def test_db_solo_se_edita_en_borrador(mundo):
    actor = mundo.ids["redactor_a"]
    doc = await _crear(mundo, mundo.ta, actor)
    await mundo.como_propietario("UPDATE biblioteca_documentos SET estado='en_revision' WHERE id=:id", id=doc.id)
    with pytest.raises(ErrorNegocio) as exc:
        await bib.cambiar_documento(mundo.sesion, mundo.ta, actor, doc.id, bib.CambiarDocumento(
            contenido_markdown="x", revision=1))
    assert exc.value.code == "BIB_DOCUMENTO_NO_EDITABLE"


# ¤adpa
@pytest.mark.asyncio
async def test_db_lista_con_filtros_y_pendientes_cuentan_cada_documento_una_vez(mundo):
    actor, hoy = mundo.ids["redactor_a"], date.today()
    docs = [await _crear(mundo, mundo.ta, actor) for _ in range(5)]
    await mundo.como_propietario("UPDATE biblioteca_documentos SET estado='en_revision' WHERE id=:id", id=docs[1].id)
    for doc, estado, dias in ((docs[2], "aprobado", 10), (docs[3], "aprobado", -1), (docs[4], "aprobado", 400)):
        await mundo.como_propietario(
            "UPDATE biblioteca_documentos SET estado=:e, aprobado_por=:u, aprobado_en=now(), proxima_revision=:p WHERE id=:id",
            e=estado, u=mundo.ids["editor"], p=hoy + timedelta(days=dias), id=doc.id)
    p = await bib.pendientes(mundo.sesion, mundo.ta, actor)
    assert (p.borrador, p.en_revision, p.por_vencer, p.vencidos, p.total) == (1, 1, 1, 1, 4)
    todos = await bib.listar_documentos(mundo.sesion, mundo.ta, actor)
    assert len(todos) == 5
    solo = {estado: [d.id for d in await bib.listar_documentos(mundo.sesion, mundo.ta, actor, estado=estado)]
            for estado in ("borrador", "en_revision", "aprobado", "vencido")}
    assert solo == {"borrador": [docs[0].id], "en_revision": [docs[1].id], "aprobado": sorted(
        [docs[2].id, docs[4].id], key=lambda i: [d.id for d in todos].index(i)), "vencido": [docs[3].id]}
    assert len(await bib.listar_documentos(mundo.sesion, mundo.ta, actor, origen="plantilla", autor=actor)) == 5
    assert await bib.listar_documentos(mundo.sesion, mundo.ta, actor, origen="subido") == []
    assert await bib.listar_documentos(mundo.sesion, mundo.ta, actor, codigo="OTRO") == []
    assert await bib.listar_documentos(mundo.sesion, mundo.ta, actor, desde=hoy + timedelta(days=1)) == []
    assert len(await bib.listar_documentos(mundo.sesion, mundo.ta, actor, desde=hoy, hasta=hoy)) == 5


# ¤adpa
@pytest.mark.asyncio
async def test_db_la_tarea_de_la_hoja_de_ruta_debe_ser_de_la_misma_organizacion(mundo):
    tareas = {}
    for tenant in (mundo.ta, mundo.tb):
        roadmap, ola, tarea = (str(uuid4()) for _ in range(3))
        await mundo.como_propietario("INSERT INTO roadmaps(id, tenant_id, variables_json) VALUES (:r, :t, '{}')", r=roadmap, t=tenant)
        await mundo.como_propietario("INSERT INTO roadmap_waves(id, roadmap_id, tenant_id, name) VALUES (:w, :r, :t, 'Ola')",
                                     w=ola, r=roadmap, t=tenant)
        await mundo.como_propietario(
            "INSERT INTO roadmap_tasks(id, wave_id, tenant_id, control_ref, dimension, title, priority) "
            "VALUES (:k, :w, :t, 'P1', 'D01', 'Tarea', 'alta')", k=tarea, w=ola, t=tenant)
        tareas[tenant] = tarea
    actor = mundo.ids["redactor_a"]
    propia = await _crear(mundo, mundo.ta, actor, tarea_hoja_ruta_id=tareas[mundo.ta])
    assert propia.tarea_hoja_ruta_id == tareas[mundo.ta]
    for ajena in (tareas[mundo.tb], "no-existe"):
        with pytest.raises(ErrorNegocio) as exc:
            await _crear(mundo, mundo.ta, actor, tarea_hoja_ruta_id=ajena)
        assert exc.value.code == "BIB_TAREA_AJENA" and exc.value.status_code == 422


# ¤adpa
@pytest.mark.asyncio
async def test_db_rellenador_registrado_por_bib_201_se_usa_sea_sincrono_o_corrutina(mundo, monkeypatch):
    llamadas = []

    class Asincrono:
        async def rellenar(self, plantilla, organizacion, contexto):
            llamadas.append((plantilla["codigo"], organizacion, contexto))
            return "Relleno por BIB-201", []

    class Sincrono:
        def rellenar(self, plantilla, organizacion, contexto):
            return "Relleno síncrono", []

    monkeypatch.setattr(servicio, "_rellenador", servicio._rellenador)  # restaura el original al terminar
    for rellenador, esperado in ((Asincrono(), "Relleno por BIB-201"), (Sincrono(), "Relleno síncrono")):
        bib.registrar_rellenador(rellenador)
        doc = await _crear(mundo, mundo.ta, mundo.ids["redactor_a"], contexto={"finalidad": "x"})
        assert doc.contenido_markdown == esperado and doc.variables_faltantes == []
    assert llamadas[0][1] == {"tenant_id": mundo.ta} and llamadas[0][2] == {"finalidad": "x"}


# ---- aislamiento entre organizaciones y RLS

# ¤adpa
@pytest.mark.asyncio
async def test_db_documento_de_otra_organizacion_responde_404(mundo):
    doc = await _crear(mundo, mundo.ta, mundo.ids["redactor_a"])
    ajeno = mundo.ids["redactor_b"]
    with pytest.raises(ErrorNegocio) as exc:
        await bib.obtener_documento(mundo.sesion, mundo.tb, ajeno, doc.id)
    assert (exc.value.code, exc.value.status_code) == ("BIB_DOCUMENTO_NO_ENCONTRADO", 404)
    with pytest.raises(ErrorNegocio) as exc:
        await bib.cambiar_documento(mundo.sesion, mundo.tb, ajeno, doc.id, bib.CambiarDocumento(contenido_markdown="x", revision=1))
    assert exc.value.status_code == 404
    with pytest.raises(ErrorNegocio):
        await bib.historial_documento(mundo.sesion, mundo.tb, ajeno, doc.id)
    assert await bib.listar_documentos(mundo.sesion, mundo.tb, ajeno) == []
    assert (await bib.pendientes(mundo.sesion, mundo.tb, ajeno)).total == 0
    intacto = await bib.obtener_documento(mundo.sesion, mundo.ta, mundo.ids["redactor_a"], doc.id)
    assert intacto.revision == 1 and intacto.contenido_markdown == doc.contenido_markdown


# ¤adpa
@pytest.mark.asyncio
async def test_db_el_filtro_del_servicio_aisla_aun_sin_rls(mundo):
    """Defensa en profundidad: con un rol que omite la RLS, el servicio debe filtrar por organización él solo."""
    doc = await _crear(mundo, mundo.ta, mundo.ids["redactor_a"])
    await mundo.conexion.execute(text("RESET ROLE"))
    if not (await mundo.conexion.execute(text(
            "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user"))).scalar():
        pytest.skip("El rol de pruebas no omite la RLS; la defensa en profundidad no es observable aquí")
    async with AsyncSession(bind=mundo.conexion, expire_on_commit=False, join_transaction_mode="create_savepoint") as libre:
        with pytest.raises(ErrorNegocio) as exc:
            await bib.obtener_documento(libre, mundo.tb, mundo.ids["redactor_b"], doc.id)
        assert exc.value.status_code == 404
        assert await bib.listar_documentos(libre, mundo.tb, mundo.ids["redactor_b"]) == []
        assert (await bib.pendientes(libre, mundo.tb, mundo.ids["redactor_b"])).total == 0
        with pytest.raises(ErrorNegocio):
            await bib.historial_documento(libre, mundo.tb, mundo.ids["redactor_b"], doc.id)
        assert [d.id for d in await bib.listar_documentos(libre, mundo.ta, mundo.ids["redactor_a"])] == [doc.id]


# ¤adpa
@pytest.mark.asyncio
async def test_db_rls_con_lopdp_app_aisla_lee_y_escribe_por_organizacion(mundo):
    doc = await _crear(mundo, mundo.ta, mundo.ids["redactor_a"])
    sesion = mundo.sesion

    consultas = {"biblioteca_documentos": "SELECT count(*) FROM biblioteca_documentos",
                 "biblioteca_documentos_historial": "SELECT count(*) FROM biblioteca_documentos_historial"}

    async def contar(tabla: str, tenant: str | None) -> int:
        await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant or ""})
        return (await sesion.execute(text(consultas[tabla]))).scalar()

    for tabla in ("biblioteca_documentos", "biblioteca_documentos_historial"):
        assert (await contar(tabla, mundo.ta), await contar(tabla, mundo.tb), await contar(tabla, None)) == (1, 0, 0)
    await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": mundo.tb})
    with pytest.raises(DBAPIError):  # WITH CHECK: no se inserta una fila de la organización A estando en B
        async with sesion.begin_nested():
            await sesion.execute(text(
                "INSERT INTO biblioteca_documentos(id,tenant_id,codigo,nombre,origen,contenido_markdown,sha256,"
                "fecha_emision,proxima_revision,creado_por) VALUES (:id,:t,'X','X','propio','a',:h,now(),now(),:u)"),
                {"id": str(uuid4()), "t": mundo.ta, "h": dominio.huella("a"), "u": mundo.ids["redactor_b"]})
    ajeno = await sesion.execute(text("UPDATE biblioteca_documentos SET revision=revision+1 WHERE id=:id"), {"id": doc.id})
    assert ajeno.rowcount == 0


# ¤adpa
@pytest.mark.asyncio
async def test_db_historial_inmutable_y_permisos_minimos_de_la_aplicacion(mundo):
    actor = mundo.ids["redactor_a"]
    doc = await _crear(mundo, mundo.ta, actor)
    await bib.cambiar_documento(mundo.sesion, mundo.ta, actor, doc.id, bib.CambiarDocumento(contenido_markdown="v2", revision=1))
    privilegios = {(t, p): (await mundo.sesion.execute(text("SELECT has_table_privilege('lopdp_app', :t, :p)"),
                                                       {"t": t, "p": p})).scalar()
                   for t in ("biblioteca_documentos", "biblioteca_documentos_historial")
                   for p in ("SELECT", "INSERT", "UPDATE", "DELETE")}
    assert privilegios == {("biblioteca_documentos", "SELECT"): True, ("biblioteca_documentos", "INSERT"): True,
                           ("biblioteca_documentos", "UPDATE"): False, ("biblioteca_documentos", "DELETE"): False,
                           ("biblioteca_documentos_historial", "SELECT"): True,
                           ("biblioteca_documentos_historial", "INSERT"): True,
                           ("biblioteca_documentos_historial", "UPDATE"): False,
                           ("biblioteca_documentos_historial", "DELETE"): False}
    for sentencia in ("UPDATE biblioteca_documentos_historial SET contenido_markdown='x'",
                      "DELETE FROM biblioteca_documentos_historial", "DELETE FROM biblioteca_documentos",
                      "UPDATE biblioteca_documentos SET estado='aprobado'",
                      "UPDATE biblioteca_documentos SET tenant_id='otra'"):
        with pytest.raises(DBAPIError, match="permission denied"):
            async with mundo.sesion.begin_nested():
                await mundo.sesion.execute(text(sentencia))
    # Ni siquiera el propietario reescribe el historial: lo impide el disparador.
    await mundo.conexion.execute(text("RESET ROLE"))
    for sentencia in ("UPDATE biblioteca_documentos_historial SET contenido_markdown='x'",
                      "DELETE FROM biblioteca_documentos_historial"):
        with pytest.raises(DBAPIError, match="BIB_HISTORIAL_INMUTABLE"):
            async with mundo.conexion.begin_nested():
                await mundo.conexion.execute(text(sentencia))
    await mundo.conexion.execute(text("SET LOCAL ROLE lopdp_app"))
    assert len(await bib.historial_documento(mundo.sesion, mundo.ta, actor, doc.id)) == 2


# ---- API: la organización sale de la sesión, los roles sin redacción solo leen, los errores llevan su código

@pytest_asyncio.fixture
async def api(mundo, monkeypatch):
    async def sesion():
        yield mundo.sesion

    async def contexto(request: Request):
        return {"user_id": request.headers["x-test-user"], "tenant_id": request.headers["x-test-tenant"],
                "role": request.headers["x-test-role"]}

    monkeypatch.setitem(app.dependency_overrides, get_session, sesion)
    monkeypatch.setitem(app.dependency_overrides, get_context, contexto)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as cliente:
        yield cliente


def _cabeceras(tenant: str, usuario: str, rol: str = "implementador") -> dict:
    return {"x-test-tenant": tenant, "x-test-user": usuario, "x-test-role": rol}


# ¤adpa
@pytest.mark.asyncio
async def test_api_recorrido_crear_listar_ver_editar_y_pendientes(api, mundo):
    base, a = "/api/v1/biblioteca/documentos", _cabeceras(mundo.ta, mundo.ids["redactor_a"])
    creado = await api.post(base, headers=a, json={"plantilla_id": mundo.plantilla_id, "fecha_emision": "2026-11-03"})
    assert creado.status_code == 201
    doc = creado.json()
    assert doc["estado"] == "borrador" and doc["origen"] == "plantilla" and doc["revision"] == 1
    assert (await api.get(base, headers=a)).json()[0]["id"] == doc["id"]
    assert (await api.get(f"{base}?estado=aprobado", headers=a)).json() == []
    assert (await api.get(f"{base}/pendientes", headers=a)).json() == {
        "borrador": 1, "en_revision": 0, "por_vencer": 0, "vencidos": 0, "total": 1}
    assert (await api.get(f"{base}/{doc['id']}", headers=a)).json()["contenido_markdown"] == doc["contenido_markdown"]
    editado = await api.patch(f"{base}/{doc['id']}", headers=a, json={"contenido_markdown": "Nuevo", "revision": 1})
    assert editado.status_code == 200 and editado.json()["revision"] == 2 and editado.json()["editado"] is True
    viejo = await api.patch(f"{base}/{doc['id']}", headers=a, json={"contenido_markdown": "Viejo", "revision": 1})
    assert viejo.status_code == 409 and viejo.json()["code"] == "BIB_DOCUMENTO_REVISION_DESFASADA"
    assert [e["accion"] for e in (await api.get(f"{base}/{doc['id']}/historial", headers=a)).json()] == ["creado", "editado"]


# ¤adpa
@pytest.mark.asyncio
async def test_api_documento_ajeno_404_organizacion_en_el_cuerpo_rechazada_y_lector_sin_escritura(api, mundo):
    base, a = "/api/v1/biblioteca/documentos", _cabeceras(mundo.ta, mundo.ids["redactor_a"])
    b = _cabeceras(mundo.tb, mundo.ids["redactor_b"])
    doc = (await api.post(base, headers=a, json={"plantilla_id": mundo.plantilla_id})).json()
    ajeno = await api.get(f"{base}/{doc['id']}", headers=b)
    assert ajeno.status_code == 404 and ajeno.json()["code"] == "BIB_DOCUMENTO_NO_ENCONTRADO" and doc["id"] not in ajeno.text.replace(
        "BIB_DOCUMENTO_NO_ENCONTRADO", "")
    assert (await api.patch(f"{base}/{doc['id']}", headers=b, json={"contenido_markdown": "x", "revision": 1})).status_code == 404
    assert (await api.get(f"{base}/{doc['id']}/historial", headers=b)).status_code == 404
    assert (await api.get(base, headers=b)).json() == []
    # La organización del cuerpo no cuenta: ni se admite el campo ni se usa la de otro.
    intruso = await api.post(base, headers=b, json={"plantilla_id": mundo.plantilla_id, "tenant_id": mundo.ta})
    assert intruso.status_code == 422
    lector = _cabeceras(mundo.ta, mundo.ids["lector_a"], "responsable_area")
    assert (await api.get(f"{base}/{doc['id']}", headers=lector)).status_code == 200
    assert (await api.post(base, headers=lector, json={"plantilla_id": mundo.plantilla_id})).status_code == 403
    assert (await api.patch(f"{base}/{doc['id']}", headers=lector, json={"contenido_markdown": "x", "revision": 1})).status_code == 403
