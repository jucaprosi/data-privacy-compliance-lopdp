# ¤adpa ¤rbac-tenant ¤arbitro
"""Árbitro BIB-103: ficha de plantilla, vista previa demostrativa y «Mi plantilla».

Reglas puras y contrato de la migración sin base de datos. La persistencia (RLS, aislamiento entre
organizaciones, copia versionada) corre contra una base local: el contenedor PostgreSQL 16 del arnés (127.0.0.1) o ARNES_BASE=postgresql_local; una URL remota no habilita la prueba:
sin ella se omite y no se acredita. Datos sintéticos dentro de una transacción que se revierte.
"""
import importlib.util
import os
from urllib.parse import urlparse
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock
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
from api.routers import biblioteca_fichas as router
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.services import ficha as servicio

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = next((ROOT / "alembic/versions").glob("*_biblioteca_mis_plantillas.py"), None)
FICHA = {"nombre": "Plantilla sintética", "objetivo": "Probar", "fuentes": "Fuente de prueba",
         "fecha_revision": "2026-10-28", "instrucciones": "Revisar", "dependencias": "Ninguna",
         "restricciones": "Solo pruebas"}
CUERPO = ("---\ncodigo: BIB-001\nnombre: Política de prueba\ntipo: politica\nola: 1\nsector: general\n"
          "naturaleza: privada\ntamano_empresa: [micro, pequena]\nversion: 0.1.0\nbase_lopdp: \"POR VERIFICAR\"\n"
          "validacion_legal: pendiente\nfecha_corte_normativo: 2026-10-27\nvariables_contexto:\n"
          "  - clave: contexto.canal\n    etiqueta: Canal de solicitudes\n    obligatoria: true\nrevision_meses: 12\n---\n\n"
          "# Política de {{organizacion.razon_social}}\n\nDomicilio: {{organizacion.direccion}}. "
          "Canal: {{contexto.canal}}. Emitida el {{fecha_emision}} ({{documento.version}}).\n\n"
          "{{#si dpo.designado}}DPD: {{dpo.nombre}}.{{#sino}}Sin delegado.{{/si}}\n")


# ----------------------------------------------------------------------------- reglas puras

# ¤adpa
def meta_y_cuerpo():
    from features.biblioteca.domain.plantillas_md import metadatos_de, separar
    return metadatos_de(CUERPO), separar(CUERPO)[1]


# ¤adpa
def test_variables_con_origen_etiqueta_y_orden_de_aparicion():
    meta, cuerpo = meta_y_cuerpo()
    por_clave = {v["clave"]: v for v in servicio.variables_de(meta, cuerpo)}
    assert list(por_clave) == ["organizacion.razon_social", "organizacion.direccion", "contexto.canal",
                               "fecha_emision", "documento.version", "dpo.nombre"]
    assert por_clave["organizacion.direccion"]["origen"] == "organizacion"
    assert por_clave["organizacion.direccion"]["etiqueta"] == "Domicilio principal"
    assert por_clave["contexto.canal"]["origen"] == "persona" and por_clave["contexto.canal"]["etiqueta"] == "Canal de solicitudes"
    assert por_clave["dpo.nombre"]["origen"] == "delegado"
    assert por_clave["fecha_emision"]["origen"] == "al_crear"


# ¤adpa
def test_disponible_solo_si_la_organizacion_ya_tiene_el_dato():
    tiene = frozenset({"organizacion.razon_social"})
    assert servicio.clave_disponible("organizacion.razon_social", "organizacion", tiene) is True
    assert servicio.clave_disponible("organizacion.direccion", "organizacion", tiene) is False
    assert servicio.clave_disponible("dpo.nombre", "delegado", tiene) is False
    assert servicio.clave_disponible("fecha_emision", "al_crear", frozenset()) is True
    # Lo que captura la persona no es un dato de la organización, aunque la clave coincida con un conjunto ajeno.
    assert servicio.clave_disponible("contexto.canal", "persona", frozenset({"contexto.canal"})) is False


# ¤adpa
def test_vista_previa_es_demostrativa_sin_llaves_ni_datos_reales():
    meta, cuerpo = meta_y_cuerpo()
    previa = servicio.vista_previa(cuerpo, meta)
    assert "{{" not in previa and "⟦falta" not in previa
    assert "Empresa Ejemplo S.A." in previa and "Calle Ejemplo 123" in previa
    assert "[ejemplo: Canal de solicitudes]" in previa
    assert "DPD: Delegado de Ejemplo." in previa and "Sin delegado" not in previa
    assert "demostrativa" in servicio.AVISO_VISTA_PREVIA.lower()


# ¤adpa
def test_claves_disponibles_cruza_por_la_compuerta_de_organizacion(monkeypatch):
    llamadas = []

    async def variables(_sesion, tenant):
        llamadas.append(tenant)
        return {"valores": {"organizacion.ruc": "0000000000001", "organizacion.direccion": None,
                            "organizacion.ciudad": ""}, "faltantes": []}

    async def designaciones(_sesion, tenant, tipo):
        llamadas.append((tenant, tipo))
        return [{"revocada_at": "2026-01-01"}]

    monkeypatch.setattr(router.organizacion, "obtener_variables_documentales", variables)
    monkeypatch.setattr(router.organizacion, "listar_designaciones_formales", designaciones)
    import asyncio
    claves = asyncio.run(router.claves_disponibles(None, "org-a"))
    assert claves == {"organizacion.ruc"}, "una designación revocada no cuenta como delegado vigente"
    assert llamadas[0] == "org-a" and llamadas[1][0] == "org-a"
    designaciones_vigente = AsyncMock(return_value=[{"revocada_at": None}])
    monkeypatch.setattr(router.organizacion, "listar_designaciones_formales", designaciones_vigente)
    assert {"dpo.nombre", "dpo.correo", "dpo.fecha_designacion"} <= asyncio.run(router.claves_disponibles(None, "org-a"))


# ¤adpa
def test_rutas_y_roles_que_copian():
    rutas = {(m, r.path) for r in router.router.routes for m in r.methods}
    assert ("GET", "/biblioteca/plantillas/{plantilla_id}") in rutas
    assert ("POST", "/biblioteca/plantillas/{plantilla_id}/copias") in rutas
    assert router.AUTO_REGISTRO is True
    assert "responsable_area" not in router.ROLES_QUE_COPIAN and "dpo" in router.ROLES_QUE_COPIAN


# ¤adpa
@pytest.mark.asyncio
async def test_rol_sin_permiso_no_copia():
    with pytest.raises(Exception) as exc:
        await router.copiar("p", None, {"user_id": "u", "tenant_id": "t", "role": "responsable_area"})
    assert getattr(exc.value, "status_code", None) == 403


# ¤adpa
def test_codigos_de_error_registrados():
    from app_core.errors import CATALOGO_ERRORES
    assert CATALOGO_ERRORES["BIB_PLANTILLA_NO_ENCONTRADA"].status_code == 404
    assert CATALOGO_ERRORES["BIB_COPIA_SOLO_SMARTCIDI"].status_code == 422


# ¤adpa
def test_migracion_una_cabeza_rls_forzada_y_permisos_minimos():
    assert MIGRACION is not None
    spec = importlib.util.spec_from_file_location("bib103_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    configuracion = Config(str(ROOT / "alembic.ini"))
    configuracion.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(configuracion)
    cabezas = [cabeza_de_sala("biblioteca", guion)]
    assert len(cabezas) == 1
    assert migracion.revision in {r.revision for r in guion.iterate_revisions(cabezas[0], "base")}
    assert guion.get_revision(migracion.down_revision) is not None
    sql = []
    migracion.op = SimpleNamespace(execute=sql.append)
    migracion.upgrade()
    texto = "\n".join(sql)
    assert "ENABLE ROW LEVEL SECURITY" in texto and "FORCE ROW LEVEL SECURITY" in texto
    assert "USING (tenant_id = current_setting" in texto and "WITH CHECK (tenant_id = current_setting" in texto
    assert "GRANT SELECT, INSERT ON biblioteca_mis_plantillas TO lopdp_app" in texto
    assert "UPDATE" not in texto.split("GRANT")[1] and "DELETE" not in texto.split("GRANT")[1]


# ----------------------------------------------------------------------------- persistencia (base propia)

# ¤adpa
@pytest_asyncio.fixture
async def db_bib():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if "ep-late-hall-b50bpbk5" in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or not (os.environ.get("ARNES_BASE") == "postgresql_local" or (urlparse(url).hostname or "") in ("127.0.0.1", "localhost", "::1")):
        pytest.skip("Persistencia pendiente: falta base local (arnés PostgreSQL 16 en 127.0.0.1 o ARNES_BASE=postgresql_local); una URL remota no habilita pruebas con base")
    if "ep-soft-darkness-b5z454vp" in url.lower():
        pytest.fail("La rama test compartida no es una base propia; no se abrió conexión", pytrace=False)
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text("SELECT to_regclass('biblioteca_mis_plantillas')"))).scalar():
                pytest.fail("Aplicar la migración de BIB-103 solo en la base propia antes de este árbitro", pytrace=False)
            ids = {rol: "bib103-" + rol + "-" + uuid4().hex for rol in
                   ("editor", "tecnico", "juridico", "publicador", "miembro_a", "miembro_b")}
            org_a, org_b = "bib103-org-" + uuid4().hex, "bib103-org-" + uuid4().hex
            for rol, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:email,:nombre)"),
                                       {"id": usuario, "email": usuario + "@example.test", "nombre": rol})
            for tid, direccion in ((org_a, "Calle Real 1"), (org_b, None)):
                await conexion.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, direccion) "
                    "VALUES (:id, 'Org sintética', 'Org sintética S.A.', :ruc, :direccion)"),
                    {"id": tid, "ruc": str(uuid4().int)[:13], "direccion": direccion})
            for usuario, tid in ((ids["miembro_a"], org_a), (ids["miembro_b"], org_b)):
                await conexion.execute(text(
                    "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'dpo')"),
                    {"id": str(uuid4()), "u": usuario, "t": tid})
            for rol, capacidad in [("editor", "editor"), ("tecnico", "revisor_tecnico"),
                                   ("juridico", "revisor_juridico"), ("publicador", "publicador")]:
                await conexion.execute(text("WITH o AS (INSERT INTO users(id,email,nombre) SELECT 'otorgante-'||g, 'otorgante-'||g||'@correo.invalid', 'Otorgante sintético' FROM md5(random()::text) g RETURNING id) "
                                            "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                                            "SELECT :id,:cap,o.id,'Fixture sintética rollback' FROM o"),
                                       {"id": ids[rol], "cap": capacidad})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield sesion, ids, org_a, org_b
        except DBAPIError:
            pytest.fail("Fallo DB BIB-103 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


# ¤adpa
async def publicar_plantilla(sesion, ids, publicar: bool = True) -> dict:
    codigo = "TEST-" + uuid4().hex[:10].upper()
    version = await bib.crear_version_md(sesion, ids["editor"], codigo, "0.1.0", CUERPO)
    if not publicar:
        return version
    version = await bib.editar(sesion, ids["editor"], version["id"], bib.EditarFicha(
        ficha=bib.Ficha(**FICHA), generacion=version["generacion"]))
    for rol, tipo in [("tecnico", "tecnica"), ("juridico", "juridica")]:
        await bib.revisar(sesion, ids[rol], version["id"], bib.Dictamen(
            tipo=tipo, aprobado=True, comentario="Dictamen sintético", generacion=version["generacion"]))
    return await bib.publicar(sesion, ids["publicador"], version["id"], bib.Transicion(
        generacion=version["generacion"], motivo="Publicación sintética"))


# ¤adpa
def contexto(ids, rol, org):
    return {"user_id": ids[rol], "tenant_id": org, "role": "dpo"}


# ¤adpa
@pytest.mark.asyncio
async def test_db_ficha_publicada_con_variables_y_vista_previa_demostrativa(db_bib):
    sesion, ids, org_a, org_b = db_bib
    plantilla = await publicar_plantilla(sesion, ids)
    en_a = await router.ficha(plantilla["id"], sesion, contexto(ids, "miembro_a", org_a))
    en_b = await router.ficha(plantilla["id"], sesion, contexto(ids, "miembro_b", org_b))
    assert en_a["fuente"] == "smartcidi" and en_a["estado_editorial"] == "publicada" and en_a["acciones"] == {"usar": True, "copiar": True}
    assert en_a["ficha"]["objetivo"] == "Probar" and en_a["validacion_legal"] == "pendiente"
    assert en_a["vista_previa"]["demostrativa"] is True and "{{" not in en_a["vista_previa"]["markdown"]
    # El aislamiento por organización: A tiene domicilio y B no, y la vista previa no cambia con la organización.
    disponible = lambda f, clave: next(v for v in f["variables"] if v["clave"] == clave)["disponible"]  # noqa: E731
    assert disponible(en_a, "organizacion.direccion") is True
    assert disponible(en_b, "organizacion.direccion") is False
    assert disponible(en_b, "organizacion.razon_social") is True
    assert en_a["vista_previa"]["markdown"] == en_b["vista_previa"]["markdown"]
    assert "Calle Real 1" not in en_a["vista_previa"]["markdown"] and "Calle Real 1" not in str(en_b)


# ¤adpa
@pytest.mark.asyncio
async def test_db_version_no_publicada_o_inexistente_responde_no_encontrada(db_bib):
    sesion, ids, org_a, _ = db_bib
    borrador = await publicar_plantilla(sesion, ids, publicar=False)
    for identificador in (borrador["id"], str(uuid4())):
        with pytest.raises(ErrorNegocio) as exc:
            await router.ficha(identificador, sesion, contexto(ids, "miembro_a", org_a))
        assert exc.value.code == "BIB_PLANTILLA_NO_ENCONTRADA"


# ¤adpa
@pytest.mark.asyncio
async def test_db_copia_versionada_sin_cambiar_la_original_y_aislada_por_organizacion(db_bib):
    sesion, ids, org_a, org_b = db_bib
    plantilla = await publicar_plantilla(sesion, ids)
    huella_antes = (await sesion.execute(text(
        "SELECT estado, version, sha256, generacion FROM biblioteca_versiones WHERE id=:id"), {"id": plantilla["id"]})).first()
    copia = await router.copiar(plantilla["id"], sesion, contexto(ids, "miembro_a", org_a))
    assert copia["fuente"] == "organizacion" and copia["origen_plantilla_id"] == plantilla["id"]
    assert copia["origen_version"] == "0.1.0" and copia["version"] == 1 and copia["id"] != plantilla["id"]
    fila = (await sesion.execute(text(
        "SELECT tenant_id, plantilla_id, version, sha256, cuerpo_md, creada_por FROM biblioteca_mis_plantillas "
        "WHERE id=:id"), {"id": copia["id"]})).mappings().one()
    assert (fila["tenant_id"], fila["plantilla_id"], fila["version"]) == (org_a, copia["id"], 1)
    assert fila["cuerpo_md"] == CUERPO and fila["creada_por"] == ids["miembro_a"]
    assert fila["sha256"] == plantilla["sha256"]
    assert (await sesion.execute(text(
        "SELECT estado, version, sha256, generacion FROM biblioteca_versiones WHERE id=:id"), {"id": plantilla["id"]})).first() == huella_antes
    # Ficha de la copia en su organización; la otra organización no la ve ni la copia.
    propia = await router.ficha(copia["id"], sesion, contexto(ids, "miembro_a", org_a))
    assert propia["fuente"] == "organizacion" and propia["estado_editorial"] == "mi_plantilla"
    assert propia["origen_plantilla_id"] == plantilla["id"] and propia["acciones"]["copiar"] is False
    for accion in (router.ficha, router.copiar):
        with pytest.raises(ErrorNegocio) as exc:
            await accion(copia["id"], sesion, contexto(ids, "miembro_b", org_b))
        assert exc.value.code == "BIB_PLANTILLA_NO_ENCONTRADA"
    assert (await sesion.execute(text("SELECT count(*) FROM biblioteca_mis_plantillas"))).scalar() == 0


# ¤adpa
@pytest.mark.asyncio
async def test_db_no_se_copia_una_copia_ni_una_no_publicada(db_bib):
    sesion, ids, org_a, _ = db_bib
    copia = await router.copiar((await publicar_plantilla(sesion, ids))["id"], sesion, contexto(ids, "miembro_a", org_a))
    with pytest.raises(ErrorNegocio) as exc:
        await router.copiar(copia["id"], sesion, contexto(ids, "miembro_a", org_a))
    assert exc.value.code == "BIB_COPIA_SOLO_SMARTCIDI"
    borrador = await publicar_plantilla(sesion, ids, publicar=False)
    with pytest.raises(ErrorNegocio) as exc:
        await router.copiar(borrador["id"], sesion, contexto(ids, "miembro_a", org_a))
    assert exc.value.code == "BIB_PLANTILLA_NO_ENCONTRADA"


# ¤adpa
@pytest.mark.asyncio
async def test_db_rls_forzada_solo_insert_y_otra_organizacion_denegada(db_bib):
    sesion, ids, org_a, org_b = db_bib
    copia = await router.copiar((await publicar_plantilla(sesion, ids))["id"], sesion, contexto(ids, "miembro_a", org_a))
    assert (await sesion.execute(text(
        "SELECT relrowsecurity AND relforcerowsecurity FROM pg_class WHERE relname='biblioteca_mis_plantillas'"))).scalar()
    for sentencia in ("UPDATE biblioteca_mis_plantillas SET nombre='x' WHERE id=:id",
                      "DELETE FROM biblioteca_mis_plantillas WHERE id=:id"):
        with pytest.raises(DBAPIError):
            async with sesion.begin_nested():
                await sesion.execute(text(sentencia), {"id": copia["id"]})
    # WITH CHECK: la sesión de A no puede escribir una copia a nombre de B.
    nuevo = str(uuid4())
    with pytest.raises(DBAPIError):
        async with sesion.begin_nested():
            await sesion.execute(text(
                "INSERT INTO biblioteca_mis_plantillas(id,plantilla_id,version,tenant_id,codigo,nombre,cuerpo_md,sha256,"
                "origen_plantilla_id,origen_version,creada_por) SELECT :n,:n,1,:otro,codigo,nombre,cuerpo_md,sha256,"
                "origen_plantilla_id,origen_version,creada_por FROM biblioteca_mis_plantillas WHERE id=:id"),
                {"n": nuevo, "otro": org_b, "id": copia["id"]})
