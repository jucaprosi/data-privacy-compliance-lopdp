# ¤adpa
# ¤¤developer-architect
"""Árbitro BIB-109: plantillas Markdown del PMV en el catálogo.

Reglas puras y cargador sin escritura siempre. La persistencia (RLS, disparador y carga idempotente) es
opt-in en la rama Neon propia (TEST_DATABASE_URL y BIB109_RAMA_PROPIA=1): sin ella se omite y no se
acredita. Datos sintéticos dentro de una transacción que se revierte; no crea asignaciones reales.
"""
import hashlib
import os
from pathlib import Path
from uuid import uuid4
import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from api.errores import ErrorNegocio
from features.biblioteca import biblioteca_service as bib

ROOT = Path(__file__).resolve().parents[1]
PMV = ROOT / "data/biblioteca/pmv"
CODIGOS = [f"BIB-{n:03d}" for n in range(1, 13)]
MIGRACION = next((ROOT / "alembic/versions").glob("*_biblioteca_plantillas_md.py"), None)
FICHA = {"nombre": "Plantilla sintética", "objetivo": "Probar", "fuentes": "Fuente de prueba",
         "fecha_revision": "2026-10-28", "instrucciones": "Revisar", "dependencias": "Ninguna",
         "restricciones": "Solo pruebas"}


# ¤adpa
def plantilla(cuerpo: str, extra: str = "", contexto: str = "") -> str:
    """Plantilla mínima válida salvo por lo que cada prueba cambie."""
    return (
        "---\ncodigo: BIB-001\nnombre: Prueba\ntipo: politica\nola: 1\nsector: general\nnaturaleza: privada\n"
        "tamano_empresa: [micro, pequena]\nversion: 0.1.0\nbase_lopdp: \"PENDIENTE VALIDACIÓN\"\n"
        "validacion_legal: pendiente\nfecha_corte_normativo: 2026-10-27\n"
        f"variables_contexto:\n{contexto}{extra}revision_meses: 12\n---\n\n{cuerpo}\n"
    )


SI_NO = "  - clave: contexto.camaras\n    etiqueta: ¿Hay cámaras?\n    tipo: si_no\n    obligatoria: true\n"


# ¤adpa
def errores(texto: str) -> list[str]:
    return bib.validar_plantilla_md(texto, "BIB-001")


# --------------------------------------------------------------------------- reglas puras

# ¤adpa
def test_doce_plantillas_del_pmv_aceptadas():
    assert sorted(p.stem for p in PMV.glob("BIB-*.md")) == CODIGOS
    for codigo in CODIGOS:
        texto = (PMV / f"{codigo}.md").read_text(encoding="utf-8")
        assert errores_de(texto, codigo) == [], codigo


# ¤adpa
def errores_de(texto: str, codigo: str) -> list[str]:
    return bib.validar_plantilla_md(texto, codigo)


# ¤adpa
def test_plantilla_minima_valida():
    assert errores(plantilla("Hola {{organizacion.razon_social}}, {{fecha_emision}}.")) == []


# ¤adpa
@pytest.mark.parametrize("cuerpo", ["{{organizacion.color}}", "{{cliente.nombre}}", "{{contexto.no_declarada}}",
                                    "{{Organizacion.ruc}}", "{{organizacion.ruc.extra}}"])
def test_variable_fuera_de_la_convencion_rechazada(cuerpo):
    assert any("variable desconocida" in e for e in errores(plantilla(cuerpo)))


# ¤adpa
def test_dpo_fuera_de_su_bloque_rechazado():
    assert any("fuera de" in e for e in errores(plantilla("Delegado: {{dpo.nombre}}.")))
    assert any("fuera de" in e for e in errores(plantilla(
        "{{#si contexto.camaras}}{{dpo.correo}}{{/si}}", contexto=SI_NO)))


# ¤adpa
def test_dpo_dentro_de_su_bloque_y_alternativa_aceptados():
    cuerpo = "{{#si dpo.designado}}DPD: {{dpo.nombre}} ({{dpo.correo}}).{{#sino}}Sin delegado.{{/si}}"
    assert errores(plantilla(cuerpo)) == []


# ¤adpa
@pytest.mark.parametrize("cuerpo,motivo", [
    ("{{#si dpo.designado}}sin cerrar", "sin cerrar"),
    ("{{#si dpo.designado}}{{#si dpo.designado}}x{{/si}}{{/si}}", "anidado"),
    ("{{/si}}", "sin abrir"),
    ("{{#sino}}", "fuera de bloque"),
    ("{{#si contexto.inventada}}x{{/si}}", "condición no admitida"),
])
def test_bloques_mal_formados_o_condicion_no_declarada(cuerpo, motivo):
    assert any(motivo in e for e in errores(plantilla(cuerpo))), errores(plantilla(cuerpo))


# ¤adpa
def test_condicion_de_contexto_texto_no_es_condicion():
    texto_ctx = "  - clave: contexto.zona\n    etiqueta: Zona\n    obligatoria: true\n"
    assert any("condición no admitida" in e for e in errores(plantilla(
        "{{contexto.zona}} {{#si contexto.zona}}x{{/si}}", contexto=texto_ctx)))


# ¤adpa
@pytest.mark.parametrize("aviso,motivo", [
    ("avisos:\n  - cuando: contexto.otra\n    nivel: alto\n    texto: Aviso\n", "condición no declarada"),
    ("avisos:\n  - cuando: contexto.camaras\n    nivel: grave\n    texto: Aviso\n", "nivel"),
    ("avisos:\n  - cuando: contexto.camaras\n    nivel: info\n", "nivel"),
])
def test_avisos_invalidos(aviso, motivo):
    assert any(motivo in e for e in errores(plantilla("x", extra=aviso, contexto=SI_NO)))


# ¤adpa
def test_aviso_valido_aceptado():
    aviso = "avisos:\n  - cuando: contexto.camaras\n    nivel: alto\n    texto: \"Requiere evaluación\"\n"
    assert errores(plantilla("x", extra=aviso, contexto=SI_NO)) == []


# ¤adpa
@pytest.mark.parametrize("cambio,motivo", [
    (("tipo: politica", "tipo: folleto"), "tipo"),
    (("naturaleza: privada", "naturaleza: mixta"), "naturaleza"),
    (("validacion_legal: pendiente", "validacion_legal: aprobada"), "validacion_legal"),
    (("version: 0.1.0", "version: uno"), "version"),
    (("codigo: BIB-001", "codigo: BIB-002"), "codigo"),
    (("revision_meses: 12\n", ""), "falta metadato revision_meses"),
])
def test_metadatos_invalidos(cambio, motivo):
    texto = plantilla("x").replace(*cambio)
    assert any(motivo in e for e in errores(texto)), errores(texto)


# ¤adpa
@pytest.mark.parametrize("texto", ["sin cabecera", "---\ncodigo: BIB-001\n", "---\n: sin clave\n---\nx"])
def test_cabecera_ilegible_rechazada(texto):
    assert errores(texto)


# ¤adpa
def test_cargador_no_admite_validacion_legal_validada():
    texto = plantilla("x").replace("validacion_legal: pendiente", "validacion_legal: validada")
    assert errores(texto) == []
    with pytest.raises(ErrorNegocio) as exc:
        bib.exigir_plantilla_cargable(texto, "BIB-001")
    assert exc.value.code == "BIB_ARCHIVO_INVALIDO"


# ¤adpa
def test_verificacion_sin_escritura_de_las_doce():
    informe = bib.verificar_plantillas_pmv(ROOT)
    assert informe["errores"] == []
    assert [p["codigo"] for p in informe["plantillas"]] == CODIGOS
    for p in informe["plantillas"]:
        datos = (PMV / f"{p['codigo']}.md").read_bytes()
        declarada = next(l.split(":", 1)[1].strip() for l in datos.decode("utf-8").splitlines()
                         if l.startswith("version:"))
        assert p["sha256"] == hashlib.sha256(datos).hexdigest() and p["version"] == declarada
        assert p["validacion_legal"] == "pendiente"


# ¤adpa
def test_script_verificar_sin_base_de_datos():
    import subprocess
    import sys
    entorno = {k: v for k, v in os.environ.items() if "DATABASE_URL" not in k}
    salida = subprocess.run([sys.executable, str(ROOT / "scripts/cargar_plantillas_pmv.py"), "--verificar"],
                            cwd=ROOT, env=entorno, capture_output=True, text=True, timeout=120)
    assert salida.returncode == 0, salida.stdout + salida.stderr
    assert "12 plantillas" in salida.stdout and "sin escritura" in salida.stdout


# ¤adpa
def test_vista_editorial_admite_versiones_md():
    version = {"id": "v", "codigo": "BIB-001", "version": "0.1.0", "formato": "MD", "ficha": None,
               "responsable_id": "e", "autores": ["e"], "estado": "en_revision", "generacion": 1,
               "nombre_archivo": None, "sha256": "a" * 64, "sustituye_id": None, "creada_en": "2026-10-28T00:00:00Z"}
    assert bib.VersionMaestra.model_validate(version).formato == "MD"
    vista = bib.VistaEditorial.model_validate({"actor_id": "e", "capacidades": ["editor"], "versiones": [version],
                                               "revisiones": []})
    assert vista.versiones[0].formato == "MD"


# ¤adpa
def test_migracion_nueva_unica_cabeza_sin_editar_bib105():
    import importlib.util
    assert MIGRACION is not None, "falta alembic/versions/*_biblioteca_plantillas_md.py"
    spec = importlib.util.spec_from_file_location("bib109_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)
    assert len(migracion.revision) <= 32
    configuracion = Config(str(ROOT / "alembic.ini"))
    configuracion.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(configuracion)
    assert guion.get_heads() == [migracion.revision]
    assert guion.get_revision(migracion.down_revision) is not None
    sql = []

    class Operaciones:
        def execute(self, consulta):
            sql.append(consulta)
    migracion.op = Operaciones()
    migracion.upgrade()
    texto = "\n".join(sql)
    assert "'MD'" in texto and "cuerpo_md" in texto
    assert "estado='publicada'" in texto and "biblioteca_miembro_activo()" in texto
    # Sin privilegios nuevos para la aplicación: solo cambia qué filas puede leer.
    assert "GRANT INSERT" not in texto and "GRANT UPDATE" not in texto


# --------------------------------------------------------------------------- persistencia (rama Neon propia)

# ¤adpa
@pytest_asyncio.fixture
async def db_bib():
    url = os.environ.get("TEST_DATABASE_URL", "")
    if "ep-late-hall-b50bpbk5" in url.lower() or "ep-soft-darkness-b5z454vp" in url.lower():
        pytest.fail("Producción o rama test compartida prohibidas; no se abrió conexión", pytrace=False)
    if not url or os.environ.get("BIB109_RAMA_PROPIA") != "1":
        pytest.skip("Persistencia pendiente: falta rama Neon propia (TEST_DATABASE_URL y BIB109_RAMA_PROPIA=1)")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text(
                    "SELECT 1 FROM information_schema.columns WHERE table_name='biblioteca_versiones' "
                    "AND column_name='cuerpo_md'"))).scalar():
                pytest.fail("Aplicar la migración de BIB-109 solo en la rama propia antes de este árbitro", pytrace=False)
            # Aislamiento: las versiones ya publicadas en la rama no deben interferir con los conteos.
            ids = {rol: "bib109-test-" + uuid4().hex for rol in
                   ("editor", "tecnico", "juridico", "publicador", "miembro", "ajeno")}
            tenant, otro = "bib109-org-" + uuid4().hex, "bib109-org-" + uuid4().hex
            for rol, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:email,:nombre)"),
                    {"id": usuario, "email": usuario + "@example.test", "nombre": rol})
            for tid in (tenant, otro):
                await conexion.execute(text(
                    "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                    "VALUES (:id, 'Org sintética', 'Org sintética S.A.', :ruc)"),
                    {"id": tid, "ruc": str(uuid4().int)[:13]})
            for usuario, tid in ((ids["miembro"], tenant), (ids["ajeno"], otro)):
                await conexion.execute(text(
                    "INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id, :u, :t, 'implementador')"),
                    {"id": str(uuid4()), "u": usuario, "t": tid})
            for rol, capacidad in [("editor", "editor"), ("tecnico", "revisor_tecnico"),
                                   ("juridico", "revisor_juridico"), ("publicador", "publicador")]:
                await conexion.execute(text("INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                    "VALUES (:id,:cap,:id,'Fixture sintética rollback')"), {"id": ids[rol], "cap": capacidad})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield sesion, ids, tenant
        except DBAPIError:
            pytest.fail("Fallo DB BIB-109 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


# ¤adpa
async def aprobar_y_publicar(sesion, ids, version):
    if version["ficha"] is None:
        version = await bib.editar(sesion, ids["editor"], version["id"], bib.EditarFicha(
            ficha=bib.Ficha(**FICHA), generacion=version["generacion"]))
    for rol, tipo in [("tecnico", "tecnica"), ("juridico", "juridica")]:
        await bib.revisar(sesion, ids[rol], version["id"], bib.Dictamen(
            tipo=tipo, aprobado=True, comentario="Dictamen sintético", generacion=version["generacion"]))
    return await bib.publicar(sesion, ids["publicador"], version["id"], bib.Transicion(
        generacion=version["generacion"], motivo="Publicación sintética"))


# ¤adpa
async def version_md(sesion, ids, cuerpo: str | None = "# Prueba\n"):
    codigo = "TEST-" + uuid4().hex[:10].upper()
    return await bib.crear_version_md(sesion, ids["editor"], codigo, "0.1.0", cuerpo)


# ¤adpa
@pytest.mark.asyncio
async def test_db_md_sin_cuerpo_no_se_publica_y_docx_sigue_exigiendo_archivo(db_bib):
    sesion, ids, _ = db_bib
    vacia = await version_md(sesion, ids, cuerpo=None)
    with pytest.raises(ErrorNegocio) as exc:
        await aprobar_y_publicar(sesion, ids, vacia)
    assert exc.value.code == "BIB_PUBLICACION_INCOMPLETA"
    with pytest.raises(DBAPIError):
        async with sesion.begin_nested():
            await sesion.execute(text("UPDATE biblioteca_versiones SET estado='publicada', motivo='salto' WHERE id=:id"),
                                 {"id": vacia["id"]})
    docx = await bib.crear(sesion, ids["editor"], bib.CrearVersion(
        codigo="TEST-" + uuid4().hex[:10].upper(), version="1.0", formato="DOCX", ficha=bib.Ficha(**FICHA)))
    with pytest.raises(ErrorNegocio) as exc:
        await aprobar_y_publicar(sesion, ids, docx)
    assert exc.value.code == "BIB_PUBLICACION_INCOMPLETA"
    # Un cuerpo que no corresponde a su huella tampoco entra, aunque lo intente su propio editor.
    await sesion.execute(text("SELECT set_config('app.current_user_id', :id, true)"), {"id": ids["editor"]})
    with pytest.raises(DBAPIError, match="BIB_INTEGRIDAD_INVALIDA"):
        async with sesion.begin_nested():
            await sesion.execute(text("UPDATE biblioteca_versiones SET cuerpo_md='otro', sha256=:sha, "
                                      "generacion=generacion+1 WHERE id=:id"), {"id": vacia["id"], "sha": "b" * 64})


# ¤adpa
@pytest.mark.asyncio
async def test_db_md_completa_se_publica_por_el_flujo_editorial(db_bib):
    sesion, ids, _ = db_bib
    publicada = await aprobar_y_publicar(sesion, ids, await version_md(sesion, ids))
    assert publicada["estado"] == "publicada" and publicada["formato"] == "MD"
    vista = bib.VistaEditorial.model_validate(await bib.listar(sesion, ids["editor"]))
    assert any(v.id == publicada["id"] and v.formato == "MD" for v in vista.versiones)


# ¤adpa
@pytest.mark.asyncio
async def test_db_miembro_sin_capacidad_lee_solo_publicadas_y_no_escribe(db_bib):
    sesion, ids, tenant = db_bib
    publicada = await aprobar_y_publicar(sesion, ids, await version_md(sesion, ids))
    en_revision = await version_md(sesion, ids)
    await sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": tenant})
    visibles = {v["id"] for v in await bib.listar_publicadas(sesion, ids["miembro"])}
    assert publicada["id"] in visibles and en_revision["id"] not in visibles
    assert (await sesion.execute(text("SELECT count(*) FROM biblioteca_versiones WHERE id=:id"),
                                 {"id": en_revision["id"]})).scalar() == 0
    with pytest.raises(ErrorNegocio) as exc:
        await bib.crear_version_md(sesion, ids["miembro"], "TEST-" + uuid4().hex[:10].upper(), "0.1.0", "# x\n")
    assert exc.value.code == "BIB_SIN_CAPACIDAD"
    # Bajo RLS el miembro no puede modificar (0 filas) ni insertar (rechazo) versiones.
    cambiadas = await sesion.execute(text("UPDATE biblioteca_versiones SET motivo='x' WHERE id=:id"),
                                     {"id": publicada["id"]})
    assert cambiadas.rowcount == 0
    with pytest.raises(DBAPIError):
        async with sesion.begin_nested():
            await sesion.execute(text(
                "INSERT INTO biblioteca_versiones(id,codigo,version,formato,responsable_id,autores) "
                "VALUES (:id,:codigo,'0.1.0','MD',:actor,CAST(:autores AS jsonb))"),
                {"id": str(uuid4()), "codigo": publicada["codigo"], "actor": ids["miembro"],
                 "autores": f'["{ids["miembro"]}"]'})
    # Sin membresía en la organización activa no se ve nada.
    visibles_ajeno = {v["id"] for v in await bib.listar_publicadas(sesion, ids["ajeno"])}
    assert publicada["id"] not in visibles_ajeno


# ¤adpa
@pytest.mark.asyncio
async def test_db_carga_idempotente_en_revision_y_conflicto_por_hash(db_bib):
    sesion, ids, _ = db_bib
    previas = {r[0] for r in (await sesion.execute(text(
        "SELECT codigo FROM biblioteca_versiones WHERE codigo LIKE 'BIB-0%'"))).all()}
    if previas:
        pytest.skip("La rama propia ya tiene plantillas BIB-0XX cargadas; la carga sintética no sería aislada")
    primera = await bib.cargar_plantillas_pmv(sesion, ids["editor"], ROOT)
    assert primera == {"catalogo_creadas": 12, "versiones_creadas": 12}
    segunda = await bib.cargar_plantillas_pmv(sesion, ids["editor"], ROOT)
    assert segunda == {"catalogo_creadas": 0, "versiones_creadas": 0}
    filas = (await sesion.execute(text(
        "SELECT codigo, estado, formato, sha256, cuerpo_md FROM biblioteca_versiones WHERE codigo LIKE 'BIB-0%' "
        "ORDER BY codigo"))).mappings().all()
    assert [f["codigo"] for f in filas] == CODIGOS
    assert {f["estado"] for f in filas} == {"en_revision"} and {f["formato"] for f in filas} == {"MD"}
    for fila in filas:
        assert fila["cuerpo_md"] == (PMV / f"{fila['codigo']}.md").read_text(encoding="utf-8")
    alterada = (PMV / "BIB-001.md").read_text(encoding="utf-8") + "\nCambio no aprobado.\n"
    with pytest.raises(ErrorNegocio) as exc:
        await bib.cargar_plantilla_md(sesion, ids["editor"], alterada, "BIB-001")
    assert exc.value.code == "BIB_CONFLICTO_VERSION"
    with pytest.raises(ErrorNegocio) as exc:
        await bib.cargar_plantillas_pmv(sesion, ids["miembro"], ROOT)
    assert exc.value.code == "BIB_SIN_CAPACIDAD"


# ¤adpa
@pytest.mark.asyncio
async def test_db_plantilla_cargada_no_se_publica_sin_revisiones(db_bib):
    sesion, ids, _ = db_bib
    version = await version_md(sesion, ids)
    version = await bib.editar(sesion, ids["editor"], version["id"], bib.EditarFicha(
        ficha=bib.Ficha(**FICHA), generacion=version["generacion"]))
    with pytest.raises(ErrorNegocio) as exc:
        await bib.publicar(sesion, ids["publicador"], version["id"], bib.Transicion(
            generacion=version["generacion"], motivo="Sin revisiones"))
    assert exc.value.code == "BIB_REVISION_PENDIENTE"
