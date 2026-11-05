# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-202: reutilización con procedencia por campo, instantánea emitida y aviso de cambios.

Reglas puras y vigilantes siempre. La persistencia corre contra la base local del arnés; contra Neon exige
la rama propia (TEST_DATABASE_URL y BIB202_RAMA_PROPIA=1), nunca la de producción ni la compartida.
Datos sintéticos dentro de una transacción que se revierte.
"""
import ast
import os
from dataclasses import fields
from datetime import date, datetime, timezone
from pathlib import Path
from uuid import uuid4
import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from api.errores import ErrorNegocio
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.domain import procedencia as dom
from features.biblioteca.domain.documentos import huella as huella_texto

ROOT = Path(__file__).resolve().parents[1]
ROUTER = ROOT / "api/routers/biblioteca_fuentes.py"
LEIDO = datetime(2026, 11, 4, 12, 0, tzinfo=timezone.utc)


# ¤adpa
def org(**valores) -> dom.RegistroFuente:
    base = {"organizacion.razon_social": "Org Sintética S.A.", "organizacion.ruc": "1790012345001"}
    return dom.RegistroFuente(fuente="organizacion", fuente_id="t-1", valores={**base, **valores}, leido_en=LEIDO)


# ¤adpa
def rat(version="3", validador=None, finalidad="Nómina") -> dom.RegistroFuente:
    return dom.RegistroFuente(fuente="rat", fuente_id="act-1", revision=version, validador=validador, leido_en=LEIDO,
                              prefijo="rat.A-01.", valores={"finalidad": finalidad, "categorias_datos": ["id", "banco"]})


# --------------------------------------------------------------------------- reglas puras

# ¤adpa
def test_cada_valor_conserva_origen_revision_fecha_y_estado():
    campos = {c.clave: c for c in dom.origenes([org(), rat(validador="dpd-1")])}
    finalidad = campos["rat.A-01.finalidad"]
    assert (finalidad.fuente, finalidad.fuente_id, finalidad.revision, finalidad.validador, finalidad.estado) == \
        ("rat", "act-1", "3", "dpd-1", "validado")
    assert finalidad.fecha == LEIDO.isoformat() and finalidad.limitacion is None
    assert campos["rat.A-01.categorias_datos"].valor == "id; banco"


# ¤adpa
def test_fuente_sin_historial_declara_limitacion_y_no_inventa_version_ni_validador():
    ruc = {c.clave: c for c in dom.origenes([org()])}["organizacion.ruc"]
    assert ruc.revision is None and ruc.validador is None and ruc.estado == "sin_validar"
    assert ruc.limitacion == dom.SIN_HISTORIAL and len(ruc.huella) == 64 and ruc.fecha == LEIDO.isoformat()


# ¤adpa
def test_solo_se_precargan_valores_realmente_existentes():
    claves = {c.clave for c in dom.origenes([org(**{"organizacion.direccion": "", "organizacion.telefono": None})])}
    assert claves == {"organizacion.razon_social", "organizacion.ruc"}


# ¤adpa
def test_huella_determinista_independiente_del_orden_y_sensible_al_valor():
    a, b = dom.origenes([org(), rat()]), dom.origenes([rat(), org()])
    assert dom.huella(a) == dom.huella(list(reversed(b)))
    assert dom.huella(a) != dom.huella(dom.origenes([org(), rat(finalidad="Otra")]))
    assert dom.huella(a) != dom.huella(dom.origenes([org(), rat(version="4")]))


# ¤adpa
def test_comparar_detecta_cambios_altas_y_bajas_sin_tocar_lo_emitido():
    emitida = dom.instantanea(dom.origenes([org(), rat()]))
    ahora = dom.origenes([org(**{"organizacion.ruc": "0999999999001"})])
    cambios = {c.clave: (c.emitido, c.actual) for c in dom.comparar(emitida, ahora)}
    assert cambios["organizacion.ruc"] == ("1790012345001", "0999999999001")
    assert cambios["rat.A-01.finalidad"] == ("Nómina", None)
    assert {c.clave: c.valor for c in emitida.campos}["organizacion.ruc"] == "1790012345001"
    assert dom.comparar(emitida, dom.origenes([org(), rat()])) == []


# ¤adpa
def test_el_puerto_de_fuentes_solo_lee():
    assert [f.name for f in fields(bib.PuertoFuentes)] == ["registros"]


# ¤adpa
def test_router_registrado_lee_por_compuertas_y_no_escribe_en_fuentes():
    arbol = ast.parse(ROUTER.read_text(encoding="utf-8"))
    asignaciones = {n.targets[0].id: n.value for n in arbol.body if isinstance(n, ast.Assign)
                    and isinstance(n.targets[0], ast.Name)}
    assert isinstance(asignaciones["AUTO_REGISTRO"], ast.Constant) and asignaciones["AUTO_REGISTRO"].value is True
    llamadas = {n.func.attr for n in ast.walk(arbol) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name) and n.func.value.id in ("organizacion_service", "rat_service")}
    assert llamadas == {"obtener_variables_documentales", "listar_designaciones_formales", "listar_actividades_rat"}
    importados = {a.name for n in ast.walk(ast.parse((ROOT / "features/biblioteca/services/procedencia.py")
                                                     .read_text(encoding="utf-8")))
                  if isinstance(n, ast.ImportFrom) and not n.module.startswith(("features.biblioteca", "api.", "sqlalchemy",
                                                                                 "collections", "dataclasses", "datetime"))
                  for a in n.names}
    assert importados == set()


# ¤adpa
def test_codigos_de_error_registrados():
    assert CATALOGO_ERRORES["BIB_PROCEDENCIA_SIN_INSTANTANEA"].status_code == 404
    assert CATALOGO_ERRORES["BIB_PROCEDENCIA_CAMPO_DESCONOCIDO"].status_code == 422


# --------------------------------------------------------------------------- persistencia

# ¤adpa
@pytest_asyncio.fixture
async def db():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if "ep-late-hall-b50bpbk5" in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    local = "127.0.0.1" in url or "localhost" in url
    if not url or not (local or os.environ.get("BIB202_RAMA_PROPIA") == "1"):
        pytest.skip("Persistencia pendiente: falta base local del arnés o rama Neon propia (BIB202_RAMA_PROPIA=1)")
    if "ep-soft-darkness-b5z454vp" in url.lower():
        pytest.fail("La rama test compartida no es una rama propia; no se abrió conexión", pytrace=False)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            usuario, ajeno = "bib202-" + uuid4().hex, "bib202-" + uuid4().hex
            tenant, otro = "bib202-org-" + uuid4().hex, "bib202-org-" + uuid4().hex
            for u in (usuario, ajeno):
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,'Sintético')"),
                                       {"id": u, "e": u + "@example.test"})
            for tid, u in ((tenant, usuario), (otro, ajeno)):
                await conexion.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:id, 'Org sintética', 'Org sintética S.A.', :ruc)"), {"id": tid, "ruc": str(uuid4().int)[:13]})
                await conexion.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) "
                                            "VALUES (:id, :u, :t, 'implementador')"), {"id": str(uuid4()), "u": u, "t": tid})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield sesion, conexion, usuario, ajeno, tenant, otro
        except DBAPIError:
            pytest.fail("Fallo DB BIB-202 (detalles de conexión omitidos); comprobar migraciones y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


# ¤adpa
class Fuente:
    """Fuente canónica simulada y mutable; cuenta las lecturas y no ofrece escritura."""

    def __init__(self):
        self.ruc, self.finalidad, self.lecturas = "1790012345001", "Nómina", 0

    async def registros(self, session, tenant_id):
        self.lecturas += 1
        return [dom.RegistroFuente(fuente="organizacion", fuente_id=tenant_id, leido_en=LEIDO,
                                   valores={"organizacion.ruc": self.ruc}), rat(finalidad=self.finalidad)]

    @property
    def puerto(self) -> bib.PuertoFuentes:
        return bib.PuertoFuentes(registros=self.registros)


# ¤adpa
async def documento(sesion, tenant, actor, contenido="RUC 1790012345001") -> str:
    from features.biblioteca.services.documentos_consulta import contexto
    await contexto(sesion, tenant, actor)
    ident = str(uuid4())
    await sesion.execute(text(
        "INSERT INTO biblioteca_documentos(id,tenant_id,codigo,nombre,origen,contenido_markdown,sha256,"
        "fecha_emision,proxima_revision,creado_por) VALUES (:id,:t,'PRO-01','Política','propio',:c,:h,:f,:f,:u)"),
        {"id": ident, "t": tenant, "c": contenido, "h": huella_texto(contenido), "f": date(2026, 11, 4), "u": actor})
    return ident


# ¤adpa
@pytest.mark.asyncio
async def test_db_cambiar_la_fuente_avisa_y_la_instantanea_emitida_conserva_lo_anterior(db):
    sesion, _, usuario, _, tenant, _ = db
    fuente = Fuente()
    doc = await documento(sesion, tenant, usuario)
    emitida = await bib.emitir_instantanea(sesion, fuente.puerto, tenant, usuario, doc)
    assert emitida.revision_documento == 1 and emitida.sha256 == dom.huella(emitida.campos)
    sin_cambios = await bib.cambios_de_fuente(sesion, fuente.puerto, tenant, usuario, doc)
    assert not sin_cambios.cambiado and sin_cambios.cambios == []
    fuente.ruc = "0999999999001"
    aviso = await bib.cambios_de_fuente(sesion, fuente.puerto, tenant, usuario, doc)
    assert aviso.cambiado and [(c.clave, c.emitido, c.actual) for c in aviso.cambios] == [
        ("organizacion.ruc", "1790012345001", "0999999999001")]
    guardada = await bib.instantanea_emitida(sesion, tenant, usuario, doc)
    assert {c.clave: c.valor for c in guardada.campos}["organizacion.ruc"] == "1790012345001"
    assert guardada.sha256 == emitida.sha256 and aviso.emitida.sha256 == emitida.sha256
    assert aviso.actual.sha256 != emitida.sha256


# ¤adpa
@pytest.mark.asyncio
async def test_db_proponer_correccion_no_modifica_el_dato_canonico(db):
    sesion, _, usuario, _, tenant, _ = db
    fuente = Fuente()
    doc = await documento(sesion, tenant, usuario)
    await bib.emitir_instantanea(sesion, fuente.puerto, tenant, usuario, doc)
    propuesta = await bib.proponer_correccion(sesion, fuente.puerto, tenant, usuario, doc, bib.EntradaPropuesta(
        clave="organizacion.ruc", valor_propuesto="1790012345002", motivo="Dígito verificador mal copiado"))
    assert (propuesta.estado, propuesta.valor_canonico, propuesta.fuente) == ("propuesto", "1790012345001", "organizacion")
    assert fuente.ruc == "1790012345001"
    assert not (await bib.cambios_de_fuente(sesion, fuente.puerto, tenant, usuario, doc)).cambiado
    with pytest.raises(ErrorNegocio) as error:
        await bib.proponer_correccion(sesion, fuente.puerto, tenant, usuario, doc, bib.EntradaPropuesta(
            clave="organizacion.inventada", valor_propuesto="x", motivo="Prueba"))
    assert error.value.code == "BIB_PROCEDENCIA_CAMPO_DESCONOCIDO"


# ¤adpa
@pytest.mark.asyncio
async def test_db_editar_el_documento_no_toca_la_fuente_ni_la_instantanea(db):
    sesion, _, usuario, _, tenant, _ = db
    fuente = Fuente()
    doc = await documento(sesion, tenant, usuario)
    emitida = await bib.emitir_instantanea(sesion, fuente.puerto, tenant, usuario, doc)
    await bib.cambiar_documento(sesion, tenant, usuario, doc, bib.CambiarDocumento(
        contenido_markdown="RUC corregido a mano 1790012345002", revision=1))
    assert fuente.ruc == "1790012345001"
    guardada = await bib.instantanea_emitida(sesion, tenant, usuario, doc)
    assert guardada.sha256 == emitida.sha256 and guardada.revision_documento == 1


# ¤adpa
@pytest.mark.asyncio
async def test_db_sin_instantanea_y_otra_organizacion(db):
    sesion, _, usuario, ajeno, tenant, otro = db
    fuente = Fuente()
    doc = await documento(sesion, tenant, usuario)
    with pytest.raises(ErrorNegocio) as error:
        await bib.cambios_de_fuente(sesion, fuente.puerto, tenant, usuario, doc)
    assert error.value.code == "BIB_PROCEDENCIA_SIN_INSTANTANEA"
    await bib.emitir_instantanea(sesion, fuente.puerto, tenant, usuario, doc)
    for llamada in (bib.instantanea_emitida(sesion, otro, ajeno, doc),
                    bib.emitir_instantanea(sesion, fuente.puerto, otro, ajeno, doc)):
        with pytest.raises(ErrorNegocio) as error:
            await llamada
        assert error.value.code == "BIB_DOCUMENTO_NO_ENCONTRADO"


# ¤adpa
@pytest.mark.asyncio
async def test_db_la_instantanea_emitida_no_se_reescribe(db):
    sesion, _, usuario, _, tenant, _ = db
    doc = await documento(sesion, tenant, usuario)
    await bib.emitir_instantanea(sesion, Fuente().puerto, tenant, usuario, doc)
    for sentencia in ("UPDATE biblioteca_eventos_documento SET detalle='{}'::jsonb WHERE documento_id=:d",
                      "DELETE FROM biblioteca_eventos_documento WHERE documento_id=:d"):
        with pytest.raises(DBAPIError):
            async with sesion.begin_nested():
                await sesion.execute(text(sentencia), {"d": doc})
