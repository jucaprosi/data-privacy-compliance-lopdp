# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-102: catálogo de plantillas (`GET /biblioteca/plantillas?fuente=&tipo=&ola=`).

Reglas puras y cableado de la ruta sin base de datos. La persistencia (RLS, publicadas, filtros y la
diferencia entre vacío y falta de acceso) corre contra una base local: el contenedor PostgreSQL 16 del arnés (127.0.0.1) o ARNES_BASE=postgresql_local; una URL remota no habilita la prueba; producción se rechaza. Sin base local se omite y no se acredita. Datos sintéticos en una transacción
que se revierte.

Mutación decisiva: en `catalogo.descargable`, aceptar `en_revision` (o quitar `v.estado='publicada'` de
la consulta) hace fallar `test_solo_la_version_publicada_es_descargable` y
`test_db_solo_publicadas_aunque_el_usuario_edite`.
"""
import os
from urllib.parse import urlparse
from uuid import uuid4
import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from api.errores import ErrorNegocio, error_negocio_handler
from api.rbac import get_usuario_autenticado
from api.routers import biblioteca_catalogo
from app_core.db.session import get_tenant_session
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib

FICHA = {"nombre": "Plantilla sintética", "objetivo": "Probar", "fuentes": "Fuente de prueba",
         "fecha_revision": "2026-10-28", "instrucciones": "Revisar", "dependencias": "Ninguna",
         "restricciones": "Solo pruebas"}


# --------------------------------------------------------------------------- reglas puras

# ¤adpa
@pytest.mark.parametrize("estado", ["en_revision", "sustituida", "retirada"])
def test_solo_la_version_publicada_es_descargable(estado):
    assert bib.descargable(estado, "DOCX") is False
    assert bib.descargable(estado, "XLSX") is False
    assert bib.descargable("publicada", "DOCX") is True
    assert bib.descargable("publicada", "XLSX") is True


# ¤adpa
def test_plantilla_markdown_o_sin_formato_no_es_descargable():
    assert bib.descargable("publicada", "MD") is False
    assert bib.descargable("publicada", None) is False


# ¤adpa
def test_codigos_de_error_registrados_en_la_sala():
    assert CATALOGO_ERRORES["BIB_SIN_ACCESO"].status_code == 403
    assert CATALOGO_ERRORES["BIB_FILTRO_INVALIDO"].status_code == 422


# ¤adpa
@pytest.mark.asyncio
@pytest.mark.parametrize("filtros", [{"fuente": "otra"}, {"tipo": "folleto"}, {"ola": 0}, {"ola": -1}])
async def test_filtro_invalido_se_rechaza_antes_de_consultar(filtros):
    class SinConsulta:
        async def execute(self, *_a, **_k):
            raise AssertionError("no debía consultar con un filtro inválido")

    with pytest.raises(ErrorNegocio) as exc:
        await bib.listar_catalogo(SinConsulta(), "usuario", **filtros)
    assert exc.value.code == "BIB_FILTRO_INVALIDO" and exc.value.status_code == 422


# ¤adpa
@pytest.fixture
def cliente(monkeypatch):
    """Ruta real con la sesión y la identidad sustituidas; los overrides se restauran al terminar."""
    app = FastAPI()
    app.add_exception_handler(ErrorNegocio, error_negocio_handler)
    app.include_router(biblioteca_catalogo.router, prefix="/api/v1")
    monkeypatch.setitem(app.dependency_overrides, get_tenant_session, lambda: object())
    monkeypatch.setitem(app.dependency_overrides, get_usuario_autenticado, lambda: "usuario-bib102")
    return app, TestClient(app)


# ¤adpa
def test_ruta_pasa_los_filtros_y_responde_la_lista(cliente, monkeypatch):
    _, http = cliente
    recibido = {}

    async def falso(_sesion, actor, fuente, tipo, ola):
        recibido.update(actor=actor, fuente=fuente, tipo=tipo, ola=ola)
        return []

    monkeypatch.setattr(bib, "listar_catalogo", falso)
    r = http.get("/api/v1/biblioteca/plantillas", params={"fuente": "smartcidi", "tipo": "politica", "ola": 1})
    assert r.status_code == 200 and r.json() == []
    assert recibido == {"actor": "usuario-bib102", "fuente": "smartcidi", "tipo": "politica", "ola": 1}


# ¤adpa
def test_ruta_traduce_falta_de_acceso_a_403_con_su_codigo(cliente, monkeypatch):
    _, http = cliente

    async def sin_acceso(*_a):
        raise ErrorNegocio("BIB_SIN_ACCESO")

    monkeypatch.setattr(bib, "listar_catalogo", sin_acceso)
    r = http.get("/api/v1/biblioteca/plantillas")
    assert r.status_code == 403 and r.json()["code"] == "BIB_SIN_ACCESO"


# ¤adpa
def test_ruta_rechaza_ola_no_numerica(cliente):
    _, http = cliente
    assert http.get("/api/v1/biblioteca/plantillas", params={"ola": "x"}).status_code == 422


# --------------------------------------------------------------------------- persistencia (base propia)

# ¤adpa
@pytest_asyncio.fixture
async def db_bib():
    url = os.environ.get("TEST_DATABASE_URL", "")
    bajo = url.lower()
    if "ep-late-hall-b50bpbk5" in bajo:
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    local = (os.environ.get("ARNES_BASE") == "postgresql_local" or (urlparse(url).hostname or "") in ("127.0.0.1", "localhost", "::1"))
    if not url or not local:
        pytest.skip("Persistencia pendiente: falta base local (arnés PostgreSQL 16 en 127.0.0.1 o ARNES_BASE=postgresql_local); una URL remota no habilita pruebas con base")
    if "ep-soft-darkness-b5z454vp" in bajo:
        pytest.fail("La rama test compartida no es una rama propia; no se abrió conexión", pytrace=False)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text(
                    "SELECT 1 FROM pg_proc WHERE proname='biblioteca_miembro_activo'"))).scalar():
                pytest.fail("Aplicar la migración de BIB-109 en la base propia antes de este árbitro", pytrace=False)
            ids = {rol: "bib102-test-" + uuid4().hex for rol in
                   ("editor", "tecnico", "juridico", "publicador", "miembro", "ajeno")}
            tenant, otro = "bib102-org-" + uuid4().hex, "bib102-org-" + uuid4().hex
            for rol, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:email,:nombre)"),
                                       {"id": usuario, "email": usuario + "@example.test", "nombre": rol})
            for tid in (tenant, otro):
                await conexion.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:id, 'Org sintética', 'Org sintética S.A.', :ruc)"),
                    {"id": tid, "ruc": str(uuid4().int)[:13]})
            # El editor también es miembro de la organización: ve las versiones en revisión por su capacidad.
            for usuario, tid in ((ids["miembro"], tenant), (ids["editor"], tenant), (ids["ajeno"], otro)):
                await conexion.execute(text(
                    "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'implementador')"),
                    {"id": str(uuid4()), "u": usuario, "t": tid})
            for rol, capacidad in [("editor", "editor"), ("tecnico", "revisor_tecnico"),
                                   ("juridico", "revisor_juridico"), ("publicador", "publicador")]:
                await conexion.execute(text(
                    "WITH o AS (INSERT INTO users(id,email,nombre) SELECT 'otorgante-'||g, 'otorgante-'||g||'@correo.invalid', 'Otorgante sintético' FROM md5(random()::text) g RETURNING id) "
                    "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                    "SELECT :id,:cap,o.id,'Fixture sintética rollback' FROM o"), {"id": ids[rol], "cap": capacidad})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
                yield sesion, ids, tenant
        except DBAPIError:
            pytest.fail("Fallo DB BIB-102 (detalles de conexión omitidos); comprobar migraciones y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


# ¤adpa
async def plantilla(sesion, ids, tipo="politica", ola=1, publicar=True):
    """Plantilla MD sintética con su fila de catálogo; publicada por el flujo editorial o en revisión."""
    codigo = "TEST-" + uuid4().hex[:10].upper()
    await sesion.execute(text("SELECT set_config('app.current_user_id', :id, true)"), {"id": ids["editor"]})
    await sesion.execute(text(
        "INSERT INTO biblioteca_catalogo(codigo,nombre,tipo,naturaleza,formato,disponibilidad,metadatos) "
        "VALUES (:c,:n,:t,'privada','MD','con_archivo',CAST(:m AS jsonb))"),
        {"c": codigo, "n": "Plantilla " + codigo, "t": tipo,
         "m": f'{{"ola": {ola}, "validacion_legal": "pendiente"}}'})
    version = await bib.crear_version_md(sesion, ids["editor"], codigo, "0.1.0", "# Prueba\n")
    if publicar:
        version = await bib.editar(sesion, ids["editor"], version["id"], bib.EditarFicha(
            ficha=bib.Ficha(**FICHA), generacion=version["generacion"]))
        for rol, tipo_revision in [("tecnico", "tecnica"), ("juridico", "juridica")]:
            await bib.revisar(sesion, ids[rol], version["id"], bib.Dictamen(
                tipo=tipo_revision, aprobado=True, comentario="Dictamen sintético", generacion=version["generacion"]))
        version = await bib.publicar(sesion, ids["publicador"], version["id"], bib.Transicion(
            generacion=version["generacion"], motivo="Publicación sintética"))
    return codigo, version


# ¤adpa
def de(lista, codigo):
    return [p for p in lista if p.codigo == codigo]


# ¤adpa
@pytest.mark.asyncio
async def test_db_solo_publicadas_aunque_el_usuario_edite(db_bib):
    sesion, ids, _ = db_bib
    publicada, _ = await plantilla(sesion, ids)
    en_revision, _ = await plantilla(sesion, ids, publicar=False)
    for actor in (ids["miembro"], ids["editor"]):
        lista = await bib.listar_catalogo(sesion, actor)
        assert len(de(lista, publicada)) == 1 and de(lista, en_revision) == []
        assert all(p.estado == "publicada" for p in lista)
    elegida = de(await bib.listar_catalogo(sesion, ids["miembro"]), publicada)[0]
    assert (elegida.fuente, elegida.tipo, elegida.ola, elegida.version, elegida.formato) == \
        ("smartcidi", "politica", 1, "0.1.0", "MD")
    assert elegida.validacion_legal == "pendiente" and elegida.descargable is False


# ¤adpa
@pytest.mark.asyncio
async def test_db_filtros_tipo_y_ola_se_combinan(db_bib):
    sesion, ids, _ = db_bib
    politica1, _ = await plantilla(sesion, ids, tipo="politica", ola=1)
    politica2, _ = await plantilla(sesion, ids, tipo="politica", ola=2)
    aviso1, _ = await plantilla(sesion, ids, tipo="aviso", ola=1)
    todas = {politica1, politica2, aviso1}
    propios = lambda lista: {p.codigo for p in lista} & todas
    miembro = ids["miembro"]
    assert propios(await bib.listar_catalogo(sesion, miembro, tipo="politica")) == {politica1, politica2}
    assert propios(await bib.listar_catalogo(sesion, miembro, ola=1)) == {politica1, aviso1}
    assert propios(await bib.listar_catalogo(sesion, miembro, tipo="politica", ola=1)) == {politica1}
    assert propios(await bib.listar_catalogo(sesion, miembro, fuente="smartcidi", tipo="aviso", ola=2)) == set()


# ¤adpa
@pytest.mark.asyncio
async def test_db_vacio_no_es_falta_de_acceso(db_bib):
    sesion, ids, _ = db_bib
    await plantilla(sesion, ids)
    # Miembro con un filtro sin coincidencias: lista vacía, no error.
    assert await bib.listar_catalogo(sesion, ids["miembro"], ola=999) == []
    # «Mi plantilla» no tiene almacén todavía: vacía para un miembro.
    assert await bib.listar_catalogo(sesion, ids["miembro"], fuente="organizacion") == []
    # Sin membresía en la organización activa: error de acceso, con o sin filtros y en ambas fuentes.
    for filtros in ({}, {"ola": 999}, {"fuente": "organizacion"}):
        with pytest.raises(ErrorNegocio) as exc:
            await bib.listar_catalogo(sesion, ids["ajeno"], **filtros)
        assert exc.value.code == "BIB_SIN_ACCESO" and exc.value.status_code == 403
