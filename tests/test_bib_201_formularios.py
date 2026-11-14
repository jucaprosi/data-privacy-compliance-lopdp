# ¤adpa
# ¤¤qa-engineer
"""Árbitro BIB-201: formulario por versión (rellenado determinista, faltantes, condicionales y borradores).

Reglas puras y vigilantes siempre. La persistencia (RLS, revisión, guardado incompleto) corre contra la base
local del arnés (127.0.0.1 o ARNES_BASE=postgresql_local); una URL remota no la habilita y producción se rechaza. Datos sintéticos dentro de una transacción que se revierte.
"""
import ast
import os
from urllib.parse import urlparse
from datetime import date
from pathlib import Path
from uuid import uuid4
import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from tests._alembic_salas import cabeza_de_sala
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from api.errores import ErrorNegocio
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.domain.plantillas_md import COMUNES
from features.biblioteca.services.rellenado import _meses, datos_del_documento

ROOT = Path(__file__).resolve().parents[1]
PMV = ROOT / "data/biblioteca/pmv"
FICHA = {"nombre": "Plantilla sintética", "objetivo": "Probar", "fuentes": "Fuente de prueba",
         "fecha_revision": "2026-10-28", "instrucciones": "Revisar", "dependencias": "Ninguna",
         "restricciones": "Solo pruebas"}
ORG = {v: f"<{v}>" for v in COMUNES if v.split(".")[0] in ("organizacion", "representante")}
CAMARAS = "  - clave: contexto.camaras\n    etiqueta: ¿Hay cámaras?\n    tipo: si_no\n    obligatoria: true\n"
FINALIDAD = "  - clave: contexto.finalidad\n    etiqueta: Finalidad\n    obligatoria: true\n"


# ¤adpa
def plantilla(cuerpo: str, contexto: str = "", extra: str = "", codigo: str = "BIB-099") -> str:
    return (f"---\ncodigo: {codigo}\nnombre: Prueba\ntipo: politica\nola: 1\nsector: general\nnaturaleza: privada\n"
            "tamano_empresa: [micro, pequena]\nversion: 0.1.0\nbase_lopdp: \"PENDIENTE VALIDACIÓN\"\n"
            "validacion_legal: pendiente\nfecha_corte_normativo: 2026-10-27\n"
            f"variables_contexto:\n{contexto}{extra}revision_meses: 12\n---\n\n{cuerpo}\n")


# ¤adpa
def llenar(texto: str, org=None, contexto=None, dpd=False) -> tuple[str, list[str]]:
    p = bib.leer_plantilla(texto)
    datos = dict(ORG if org is None else org)
    datos.update(datos_del_documento(p, date(2026, 11, 3)))
    datos["dpo.designado"] = dpd
    if dpd:
        datos.update({"dpo.nombre": "Ana DPD", "dpo.correo": "dpd@example.test"})
    return bib.rellenar(p, datos, contexto or {})


# --------------------------------------------------------------------------- reglas puras

# ¤adpa
def test_variables_de_organizacion_y_documento_se_rellenan():
    contenido, faltantes = llenar(plantilla("{{organizacion.razon_social}} · {{documento.codigo}} · {{fecha_emision}}"))
    assert contenido == "<organizacion.razon_social> · BIB-099 · 2026-11-03" and faltantes == []


# ¤adpa
def test_variable_sin_valor_queda_marcada_y_listada():
    contenido, faltantes = llenar(plantilla("{{organizacion.direccion}} y {{organizacion.ruc}}"),
                                  org={"organizacion.ruc": "1790012345001", "organizacion.direccion": ""})
    assert "⟦falta: organizacion.direccion⟧" in contenido and "1790012345001" in contenido
    assert faltantes == ["organizacion.direccion"]


# ¤adpa
def test_proxima_revision_suma_meses_y_respeta_fin_de_mes():
    assert _meses(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert _meses(date(2026, 11, 3), 12) == date(2027, 11, 3)
    assert _meses(date(2026, 12, 15), 2) == date(2027, 2, 15)


# ¤adpa
def test_aprobacion_se_completa_al_aprobar_y_no_bloquea_el_borrador():
    contenido, faltantes = llenar(plantilla("Aprobado por {{documento.aprobado_por}}."))
    assert "⟦pendiente: documento.aprobado_por⟧" in contenido and faltantes == []


# ¤adpa
def test_parte_condicional_del_dpd_en_las_dos_variantes():
    cuerpo = "{{#si dpo.designado}}DPD: {{dpo.nombre}} ({{dpo.correo}}){{#sino}}Sin delegado.{{/si}}"
    con, faltantes_con = llenar(plantilla(cuerpo), dpd=True)
    sin, faltantes_sin = llenar(plantilla(cuerpo), dpd=False)
    assert con == "DPD: Ana DPD (dpd@example.test)" and faltantes_con == []
    assert sin == "Sin delegado." and faltantes_sin == []  # la falta de DPD no bloquea la revisión


# ¤adpa
def test_dpd_designado_sin_nombre_si_cuenta_como_faltante():
    cuerpo = "{{#si dpo.designado}}DPD: {{dpo.nombre}}{{#sino}}Sin delegado.{{/si}}"
    p = bib.leer_plantilla(plantilla(cuerpo))
    _, faltantes = bib.rellenar(p, {"dpo.designado": True, "dpo.nombre": None}, {})
    assert faltantes == ["dpo.nombre"]


# ¤adpa
def test_variables_de_la_rama_que_no_aplica_no_cuentan():
    cuerpo = "{{#si contexto.camaras}}Zonas: {{contexto.finalidad}}{{#sino}}No hay cámaras.{{/si}}"
    texto = plantilla(cuerpo, contexto=CAMARAS + FINALIDAD)
    no, faltantes_no = llenar(texto, contexto={"contexto.camaras": "no"})
    si, faltantes_si = llenar(texto, contexto={"contexto.camaras": "si"})
    assert no == "No hay cámaras." and faltantes_no == []
    assert si.startswith("Zonas: ⟦falta: contexto.finalidad⟧") and faltantes_si == ["contexto.finalidad"]


# ¤adpa
def test_condicion_sin_responder_es_faltante():
    texto = plantilla("{{#si contexto.camaras}}A{{#sino}}B{{/si}}", contexto=CAMARAS)
    contenido, faltantes = llenar(texto)
    assert contenido == "⟦falta: contexto.camaras⟧" and faltantes == ["contexto.camaras"]


# ¤adpa
def test_el_dato_nunca_se_interpreta_como_plantilla_ni_como_codigo():
    peligrosos = ["{{organizacion.ruc}}", "{{#si dpo.designado}}x{{/si}}", "{{__import__('os').system('x')}}",
                  "${7*7} {{7*7}} {% raw %}"]
    for dato in peligrosos:
        contenido, faltantes = llenar(plantilla("Dir: {{organizacion.direccion}}. RUC {{organizacion.ruc}}"),
                                      org={"organizacion.direccion": dato, "organizacion.ruc": "R"})
        assert contenido == f"Dir: {dato}. RUC R" and faltantes == []


# ¤adpa
def test_rellenado_determinista():
    texto = plantilla("{{organizacion.razon_social}} {{organizacion.direccion}}")
    assert llenar(texto, org={"organizacion.razon_social": "A"}) == llenar(texto, org={"organizacion.razon_social": "A"})


# ¤adpa
def test_las_doce_plantillas_se_rellenan_sin_faltantes_con_datos_completos():
    for archivo in sorted(PMV.glob("BIB-*.md")):
        p = bib.leer_plantilla(archivo.read_text(encoding="utf-8"))
        contexto = {c.clave: "si" if c.tipo == "si_no" else "x" for c in p.campos}
        contenido, faltantes = llenar(archivo.read_text(encoding="utf-8"),
                                      org={**ORG, **{v: "t" for v in COMUNES if v.startswith("tratamiento.")}},
                                      contexto=contexto, dpd=True)
        assert faltantes == [] and "⟦falta" not in contenido, archivo.stem
        _, sin_datos = llenar(archivo.read_text(encoding="utf-8"), org={}, contexto={})
        assert sin_datos, archivo.stem  # con una organización vacía siempre hay faltantes


# ¤adpa
def test_avisos_se_activan_con_la_condicion_y_suben_a_alto_sin_dpd():
    p = bib.leer_plantilla((PMV / "BIB-011.md").read_text(encoding="utf-8"))
    assert bib.avisos_activos(p, {"contexto.camaras_acceso_publico": "no"}, con_dpd=True) == []
    assert bib.avisos_activos(p, {}, con_dpd=True) == []
    con = bib.avisos_activos(p, {"contexto.camaras_acceso_publico": "si"}, con_dpd=True)
    sin = bib.avisos_activos(p, {"contexto.camaras_acceso_publico": "si"}, con_dpd=False)
    assert [a.nivel for a in con] == ["alto"] and len(con) == 1
    assert [a.nivel for a in sin] == ["alto"] and sin[0].texto == con[0].texto


# ¤adpa
ACTIVIDAD = {"codigo": "ACT-1", "nombre": "Facturación | clientes", "finalidad": "Cobrar", "base_legal": "CUMPLIMIENTO_CONTRATO",
             "categorias_titulares": ["CLIENTES"], "categorias_datos": ["identificativos", "contacto"],
             "datos_sensibles": False, "transferencia_internacional": False, "decisiones_automatizadas": False,
             "destinatarios": ["Contador"], "plazo_conservacion": "7 años", "medidas_seguridad": ["Cifrado"],
             "encargados": []}


# ¤adpa
def test_ficha_de_actividad_tiene_los_nueve_contenidos_y_marca_lo_que_falta():
    completa = bib.fichas_de_actividades([ACTIVIDAD])
    assert [f"| {n}. " in completa for n in range(1, 10)] == [True] * 9 and "⟦falta" not in completa
    assert "### Actividad: Facturación | clientes" in completa  # el título admite «|»; las celdas lo sustituyen
    incompleta = bib.fichas_de_actividades([{**ACTIVIDAD, "plazo_conservacion": "", "transferencia_internacional": True,
                                             "pais_transferencia": ""}])
    assert "⟦falta: contexto.actividades[ACT-1].plazo_conservacion⟧" in incompleta
    assert "⟦falta: contexto.actividades[ACT-1].pais_transferencia⟧" in incompleta


# ¤adpa
def test_validar_contexto_rechaza_lo_ajeno_y_acepta_incompleto():
    p = bib.leer_plantilla(plantilla("{{contexto.finalidad}}{{#si contexto.camaras}}x{{/si}}", contexto=CAMARAS + FINALIDAD))
    assert bib.validar_contexto(p.campos, {"contexto.finalidad": "  ", "contexto.camaras": "si"}) == {"contexto.camaras": "si"}
    for malo in ({"contexto.otra": "x"}, {"contexto.camaras": "quizá"}, {"contexto.finalidad": 5},
                 {"contexto.finalidad": "x" * 2001}, {"contexto.finalidad": ["a"]}):
        with pytest.raises(ErrorNegocio) as exc:
            bib.validar_contexto(p.campos, malo)
        assert exc.value.code == "BIB_CONTEXTO_INVALIDO"


# ¤adpa
def test_actividades_las_genera_el_servidor_y_no_se_capturan():
    p = bib.leer_plantilla((PMV / "BIB-006.md").read_text(encoding="utf-8"))
    assert {c.clave: c.origen for c in p.campos}["contexto.actividades"] == "rat"
    with pytest.raises(ErrorNegocio):
        bib.validar_contexto(p.campos, {"contexto.actividades": "inventado"})


# ¤adpa
def test_exigir_revisable():
    bib.exigir_revisable([])
    with pytest.raises(ErrorNegocio) as exc:
        bib.exigir_revisable(["organizacion.direccion"])
    assert exc.value.code == "BIB_VARIABLES_FALTANTES" and "organizacion.direccion" in exc.value.detail


# --------------------------------------------------------------------------- vigilantes

# ¤adpa
def test_el_esquema_nunca_ejecuta_codigo():
    prohibidos = {"eval", "exec", "compile", "__import__", "getattr", "setattr", "globals", "locals", "system", "popen"}
    for ruta in ("domain/esquemas.py", "services/rellenado.py", "services/validacion.py", "services/borradores.py"):
        arbol = ast.parse((ROOT / "features/biblioteca" / ruta).read_text(encoding="utf-8"))
        nombres = {n.id for n in ast.walk(arbol) if isinstance(n, ast.Name)}
        atributos = {n.attr for n in ast.walk(arbol) if isinstance(n, ast.Attribute)}
        # `getattr(valor, "value", valor)` solo lee el enum del RAT; el resto es inadmisible.
        assert not (nombres & (prohibidos - {"getattr"})) and not (atributos & {"system", "popen", "eval", "exec"}), ruta
        assert not any(isinstance(n, ast.Import) and n.names[0].name in ("subprocess", "os", "pickle")
                       for n in ast.walk(arbol)), ruta
    # Biblioteca no importa a otras salas: ORG-14, DPD y RAT llegan por FuentesDatos desde el router.
    for ruta in ("domain/esquemas.py", "services/rellenado.py", "services/borradores.py", "services/validacion.py"):
        assert "features.organizacion" not in (ROOT / "features/biblioteca" / ruta).read_text(encoding="utf-8")
        assert "features.rat" not in (ROOT / "features/biblioteca" / ruta).read_text(encoding="utf-8")


# ¤adpa
def test_migracion_encadenada_con_rls_forzado_y_permisos_minimos():
    ruta = next((ROOT / "alembic/versions").glob("*_biblioteca_borradores.py"))
    fuente = ruta.read_text(encoding="utf-8")
    revision = next(n.value.value for n in ast.parse(fuente).body
                    if isinstance(n, ast.Assign) and n.targets[0].id == "revision")
    assert len(revision) <= 32
    configuracion = Config()
    configuracion.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(configuracion)
    assert cabeza_de_sala("biblioteca", guion) or guion.get_revision(revision) is not None
    assert guion.get_revision(revision).down_revision is not None
    for exigido in ("ENABLE ROW LEVEL SECURITY", "FORCE ROW LEVEL SECURITY", "WITH CHECK",
                    "GRANT SELECT, INSERT ON biblioteca_borradores TO lopdp_app",
                    "GRANT UPDATE (contexto, fecha_emision, revision, actualizado_por, actualizado_en)"):
        assert exigido in fuente
    assert not [l for l in fuente.splitlines() if "GRANT" in l and ("DELETE" in l or "ALL" in l)]


# ¤adpa
def test_router_registrado_con_auto_registro_y_roles_de_edicion():
    import api.routers.biblioteca_borradores as router
    assert router.AUTO_REGISTRO is True
    rutas = {(m, r.path) for r in router.router.routes for m in r.methods}
    assert rutas == {("POST", "/biblioteca/borradores"), ("GET", "/biblioteca/borradores/{identificador}"),
                     ("PUT", "/biblioteca/borradores/{identificador}")}
    assert "responsable_area" not in router.EDITORES


# --------------------------------------------------------------------------- persistencia

# ¤adpa
@pytest_asyncio.fixture
async def db_bib():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if "ep-late-hall-b50bpbk5" in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    local = (os.environ.get("ARNES_BASE") == "postgresql_local" or (urlparse(url).hostname or "") in ("127.0.0.1", "localhost", "::1"))
    if not url or not local:
        pytest.skip("Persistencia pendiente: falta base local (arnés PostgreSQL 16 en 127.0.0.1 o ARNES_BASE=postgresql_local); una URL remota no habilita pruebas con base")
    if "ep-soft-darkness-b5z454vp" in url.lower():
        pytest.fail("La rama test compartida no es una rama propia; no se abrió conexión", pytrace=False)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text("SELECT to_regclass('public.biblioteca_borradores')"))).scalar():
                pytest.fail("Aplicar la migración de BIB-201 solo en la base propia antes de este árbitro", pytrace=False)
            ids = {rol: "bib201-" + uuid4().hex for rol in ("editor", "tecnico", "juridico", "publicador", "miembro", "ajeno")}
            tenant, otro = "bib201-org-" + uuid4().hex, "bib201-org-" + uuid4().hex
            for rol, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:email,:nombre)"),
                                       {"id": usuario, "email": usuario + "@example.test", "nombre": rol})
            for tid in (tenant, otro):
                await conexion.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:id, 'Org sintética', 'Org sintética S.A.', :ruc)"), {"id": tid, "ruc": str(uuid4().int)[:13]})
            for usuario, tid in ((ids["miembro"], tenant), (ids["ajeno"], otro)):
                await conexion.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                                            "VALUES (:id, :u, :t, 'implementador')"), {"id": str(uuid4()), "u": usuario, "t": tid})
            for rol, capacidad in [("editor", "editor"), ("tecnico", "revisor_tecnico"),
                                   ("juridico", "revisor_juridico"), ("publicador", "publicador")]:
                await conexion.execute(text("WITH o AS (INSERT INTO users(id,email,nombre) SELECT 'otorgante-'||g, 'otorgante-'||g||'@correo.invalid', 'Otorgante sintético' FROM md5(random()::text) g RETURNING id) "
                                            "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                                            "SELECT :id,:cap,o.id,'Fixture sintética rollback' FROM o"), {"id": ids[rol], "cap": capacidad})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield sesion, ids, tenant, otro
        except DBAPIError:
            pytest.fail("Fallo DB BIB-201 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


# ¤adpa
def fuentes(org=None, dpd=None, actividades=None, falla=False):
    async def organizacion(session, tenant):
        if falla:
            raise ConnectionError("fuente caída")
        return ORG if org is None else org

    async def dpd_vigente(session, tenant):
        return dpd

    async def lista(session, tenant):
        return actividades or []
    return bib.FuentesDatos(organizacion=organizacion, dpd_vigente=dpd_vigente, actividades=lista)


# ¤adpa
async def publicar(sesion, ids, texto: str, codigo: str = "BIB-099") -> str:
    v = await bib.crear_version_md(sesion, ids["editor"], codigo, "0.1.0", texto)
    v = await bib.editar(sesion, ids["editor"], v["id"], bib.EditarFicha(ficha=bib.Ficha(**FICHA), generacion=v["generacion"]))
    for rol, tipo in [("tecnico", "tecnica"), ("juridico", "juridica")]:
        await bib.revisar(sesion, ids[rol], v["id"], bib.Dictamen(tipo=tipo, aprobado=True, comentario="Dictamen sintético",
                                                                    generacion=v["generacion"]))
    return (await bib.publicar(sesion, ids["publicador"], v["id"], bib.Transicion(
        generacion=v["generacion"], motivo="Publicación sintética")))["id"]


CUERPO = ("{{organizacion.razon_social}} {{organizacion.direccion}}\n"
          "{{#si dpo.designado}}DPD {{dpo.nombre}}{{#sino}}Sin delegado.{{/si}}\n"
          "{{#si contexto.camaras}}Zonas: {{contexto.finalidad}}{{#sino}}Sin cámaras.{{/si}}")


# ¤adpa
@pytest.mark.asyncio
async def test_db_guardar_incompleto_muestra_faltantes_y_completo_es_revisable(db_bib):
    sesion, ids, tenant, _ = db_bib
    version = await publicar(sesion, ids, plantilla(CUERPO, contexto=CAMARAS + FINALIDAD))
    f = fuentes(org={**ORG, "organizacion.direccion": ""})
    b = await bib.crear_borrador(sesion, f, tenant, ids["miembro"], bib.EntradaBorrador(version_id=version))
    assert b.revision == 1 and not b.revisable and b.variables_faltantes == ["organizacion.direccion", "contexto.camaras"]
    b = await bib.guardar_borrador(sesion, f, tenant, ids["miembro"], b.id,
                                   bib.GuardarBorrador(revision=1, contexto={"contexto.camaras": "si"}))
    assert b.revision == 2 and b.variables_faltantes == ["organizacion.direccion", "contexto.finalidad"]
    completo = fuentes()
    b = await bib.guardar_borrador(sesion, completo, tenant, ids["miembro"], b.id, bib.GuardarBorrador(
        revision=2, contexto={"contexto.camaras": "no"}))
    assert b.revisable and b.variables_faltantes == [] and "Sin delegado." in b.contenido_markdown  # sin DPD no bloquea
    persistido = await bib.obtener_borrador(sesion, completo, tenant, ids["miembro"], b.id)
    assert persistido.contexto == {"contexto.camaras": "no"} and persistido.revision == 3


# ¤adpa
@pytest.mark.asyncio
async def test_db_revision_desfasada_se_rechaza_y_no_cambia_nada(db_bib):
    sesion, ids, tenant, _ = db_bib
    version = await publicar(sesion, ids, plantilla(CUERPO, contexto=CAMARAS + FINALIDAD))
    f = fuentes()
    b = await bib.crear_borrador(sesion, f, tenant, ids["miembro"], bib.EntradaBorrador(version_id=version))
    await bib.guardar_borrador(sesion, f, tenant, ids["miembro"], b.id,
                               bib.GuardarBorrador(revision=1, contexto={"contexto.camaras": "si"}))
    with pytest.raises(ErrorNegocio) as exc:  # un cliente con la revisión 1 no pisa la 2
        await bib.guardar_borrador(sesion, f, tenant, ids["miembro"], b.id,
                                   bib.GuardarBorrador(revision=1, contexto={"contexto.camaras": "no"}))
    assert exc.value.code == "BIB_REVISION_DESFASADA" and exc.value.status_code == 409
    actual = await bib.obtener_borrador(sesion, f, tenant, ids["miembro"], b.id)
    assert actual.contexto == {"contexto.camaras": "si"} and actual.revision == 2


# ¤adpa
@pytest.mark.asyncio
async def test_db_fallo_de_una_fuente_no_se_anuncia_como_guardado(db_bib):
    sesion, ids, tenant, _ = db_bib
    version = await publicar(sesion, ids, plantilla(CUERPO, contexto=CAMARAS + FINALIDAD))
    b = await bib.crear_borrador(sesion, fuentes(), tenant, ids["miembro"], bib.EntradaBorrador(version_id=version))
    with pytest.raises(ConnectionError):  # la excepción sube: no hay Borrador de respuesta que parezca guardado
        await bib.guardar_borrador(sesion, fuentes(falla=True), tenant, ids["miembro"], b.id,
                                   bib.GuardarBorrador(revision=1, contexto={"contexto.camaras": "si"}))


# ¤adpa
@pytest.mark.asyncio
async def test_db_otra_organizacion_no_ve_ni_guarda_el_borrador(db_bib):
    sesion, ids, tenant, otro = db_bib
    version = await publicar(sesion, ids, plantilla(CUERPO, contexto=CAMARAS + FINALIDAD))
    b = await bib.crear_borrador(sesion, fuentes(), tenant, ids["miembro"], bib.EntradaBorrador(version_id=version))
    for operacion in (bib.obtener_borrador(sesion, fuentes(), otro, ids["ajeno"], b.id),
                      bib.guardar_borrador(sesion, fuentes(), otro, ids["ajeno"], b.id,
                                           bib.GuardarBorrador(revision=1, contexto={}))):
        with pytest.raises(ErrorNegocio) as exc:
            await operacion
        assert exc.value.code == "BIB_BORRADOR_NO_ENCONTRADO"


# ¤adpa
@pytest.mark.asyncio
async def test_db_solo_se_rellena_una_plantilla_publicada(db_bib):
    sesion, ids, tenant, _ = db_bib
    en_revision = (await bib.crear_version_md(sesion, ids["editor"], "BIB-098", "0.1.0", plantilla(CUERPO, CAMARAS + FINALIDAD,
                                                                                                  codigo="BIB-098")))["id"]
    for version in (en_revision, str(uuid4())):
        with pytest.raises(ErrorNegocio) as exc:
            await bib.crear_borrador(sesion, fuentes(), tenant, ids["miembro"], bib.EntradaBorrador(version_id=version))
        assert exc.value.code == "BIB_PLANTILLA_NO_DISPONIBLE"


# ¤adpa
@pytest.mark.asyncio
async def test_db_clave_ajena_al_esquema_se_rechaza_al_guardar(db_bib):
    sesion, ids, tenant, _ = db_bib
    version = await publicar(sesion, ids, plantilla(CUERPO, contexto=CAMARAS + FINALIDAD))
    with pytest.raises(ErrorNegocio) as exc:
        await bib.crear_borrador(sesion, fuentes(), tenant, ids["miembro"], bib.EntradaBorrador(
            version_id=version, contexto={"contexto.inventada": "x"}))
    assert exc.value.code == "BIB_CONTEXTO_INVALIDO"


# ¤adpa
@pytest.mark.asyncio
async def test_db_bib_006_genera_actividades_desde_el_rat_en_solo_lectura(db_bib):
    sesion, ids, tenant, _ = db_bib
    texto = (PMV / "BIB-006.md").read_text(encoding="utf-8")
    version = await publicar(sesion, ids, texto, codigo="BIB-006")
    sin_rat = await bib.crear_borrador(sesion, fuentes(), tenant, ids["miembro"], bib.EntradaBorrador(
        version_id=version, contexto={"contexto.motivo_obligacion": "Voluntario"}))
    assert "contexto.actividades" in sin_rat.variables_faltantes and not sin_rat.revisable
    con_rat = await bib.crear_borrador(sesion, fuentes(actividades=[ACTIVIDAD]), tenant, ids["miembro"],
                                       bib.EntradaBorrador(version_id=version, contexto={"contexto.motivo_obligacion": "Voluntario"}))
    assert "### Actividad: Facturación | clientes" in con_rat.contenido_markdown
    assert "contexto.actividades" not in con_rat.variables_faltantes
    assert not any(k.startswith("contexto.actividades") for k in con_rat.contexto)  # no se guarda: se genera al leer
    incompleto = await bib.obtener_borrador(sesion, fuentes(actividades=[{**ACTIVIDAD, "plazo_conservacion": ""}]),
                                            tenant, ids["miembro"], con_rat.id)
    assert "contexto.actividades[ACT-1].plazo_conservacion" in incompleto.variables_faltantes and not incompleto.revisable


# ¤adpa
@pytest.mark.asyncio
async def test_db_rls_oculta_borradores_sin_contexto_y_la_copia_de_plantilla_es_inmutable(db_bib):
    sesion, ids, tenant, _ = db_bib
    version = await publicar(sesion, ids, plantilla(CUERPO, contexto=CAMARAS + FINALIDAD))
    b = await bib.crear_borrador(sesion, fuentes(), tenant, ids["miembro"], bib.EntradaBorrador(version_id=version))
    with pytest.raises(DBAPIError):  # lopdp_app no puede reescribir la copia de la plantilla ni borrar
        async with sesion.begin_nested():
            await sesion.execute(text("UPDATE biblioteca_borradores SET plantilla_md='x' WHERE id=:i"), {"i": b.id})
    with pytest.raises(DBAPIError):
        async with sesion.begin_nested():
            await sesion.execute(text("DELETE FROM biblioteca_borradores WHERE id=:i"), {"i": b.id})
    await sesion.execute(text("SELECT set_config('app.current_tenant_id', 'otra', true)"))
    assert (await sesion.execute(text("SELECT count(*) FROM biblioteca_borradores"))).scalar() == 0


# ¤adpa
@pytest.mark.asyncio
async def test_db_las_compuertas_reales_entregan_organizacion_dpd_y_rat_de_la_sesion(db_bib):
    """El router conecta ORG-14, las designaciones y el RAT por sus compuertas; aquí contra las tablas reales."""
    import api.routers.biblioteca_borradores as router
    sesion, ids, tenant, otro = db_bib
    await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
    valores = await router.FUENTES.organizacion(sesion, tenant)
    assert valores["organizacion.razon_social"] == "Org sintética S.A." and "representante.nombre" in valores
    assert await router.FUENTES.actividades(sesion, tenant) == []
    assert await router.FUENTES.dpd_vigente(sesion, tenant) is None  # sin designación: variante sin delegado
    await sesion.execute(text(
        "INSERT INTO designaciones_formales(id, tenant_id, tipo, user_id, representante_nombre, "
        "representante_identificacion, representante_cargo, fecha_designacion, doc_referencia) "
        "VALUES (:id, :t, 'dpd', :u, 'Rep', '1', 'Gerente', DATE '2026-10-01', 'Acta 1')"),
        {"id": str(uuid4()), "t": tenant, "u": ids["editor"]})
    dpd = await router.FUENTES.dpd_vigente(sesion, tenant)
    assert dpd["nombre"] == "editor" and dpd["correo"].endswith("@example.test") and dpd["fecha_designacion"] == date(2026, 10, 1)
    assert await router.FUENTES.dpd_vigente(sesion, otro) is None  # la designación es de otra organización
