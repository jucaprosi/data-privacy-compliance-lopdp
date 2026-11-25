# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤adpa ¤cita-verificada ¤arbitro
"""BIB-406: la IA propone versiones de plantillas como autora; las aprueba una sola persona.

Dos capas. Las reglas puras y el servicio con una sesión simulada corren sin base. Las pruebas `test_db_*`
abren el PostgreSQL 16 de pruebas (`TEST_DATABASE_URL` y `exigir_base_de_pruebas()`) y ejercen el
disparador; sin base se omiten. Cada mutación m1 a m7 de la especificación §5 tiene su prueba: la
mutación aplicada hace fallar la guardia que la vigila.
"""
import hashlib
import importlib.util
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app_core.errors import ErrorNegocio
from features.biblioteca.domain import propuestas_ia as dominio
from features.biblioteca.domain.propuestas_ia import CambioIA, SalidaPropuestaIA

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = ROOT / "alembic/versions/20261125_bib406_propuestas_ia.py"
CITAS = json.loads((ROOT / "data/biblioteca/pmv/citas.json").read_bytes().decode("utf-8"))


def _migracion():
    especificacion = importlib.util.spec_from_file_location("_bib406", MIGRACION)
    modulo = importlib.util.module_from_spec(especificacion)
    especificacion.loader.exec_module(modulo)
    return modulo


# Citas sintéticas con la forma de citas.json: la resolución RES-X solo la cita BIB-003 (para m1).
URL_RES_X = "https://www.spdp.gob.ec/resolucion-sintetica.pdf"
CITAS_M1 = {
    "estados": {"LOPDP-art-7": "verificada", "RES-X-art-1": "verificada"},
    "fuente_de": {"LOPDP-art-7": "LOPDP-RO459", "RES-X-art-1": "RES-X"},
    "fuentes": {"LOPDP-RO459": CITAS["fuentes"]["LOPDP-RO459"], "RES-X": {"sha256": "0" * 64, "url": URL_RES_X}},
    "plantillas": {"BIB-001": ["LOPDP-art-7"], "BIB-003": ["LOPDP-art-7", "RES-X-art-1"],
                   "BIB-007": ["LOPDP-art-7"]},
}


# --- Guardias: cada una devuelve los fallos de una regla para una implementación dada ---

def guardia_afectadas(afectadas) -> list[str]:
    obtenidas = afectadas(CITAS_M1, URL_RES_X)
    esperadas = ["BIB-003"]
    fallos = []
    if "BIB-003" not in obtenidas:
        fallos.append("BIB-003 no recibe la propuesta")
    if obtenidas != esperadas:
        fallos.append("se propone para plantillas que no citan la resolución")
    return fallos


def guardia_citas(aplicar) -> list[str]:
    cuerpo = "Uno. Dos. Tres."
    verificada = next(k for k, e in CITAS["estados"].items() if e == "verificada")
    cambios = [CambioIA(seccion="1", antes="Uno.", despues="Uno bis.", cita=verificada),
               CambioIA(seccion="2", antes="Dos.", despues="Dos bis.", cita="CITA-QUE-NO-EXISTE")]
    nuevo, aplicados = aplicar(cuerpo, cambios, CITAS)
    fallos = []
    if "Dos bis." in nuevo or any(c["cita"] == "CITA-QUE-NO-EXISTE" for c in aplicados):
        fallos.append("entra un cambio sin cita verificada")
    if "Uno bis." not in nuevo:
        fallos.append("no entra el cambio con cita verificada")
    return fallos


def guardia_disparo(debe) -> list[str]:
    fallos = []
    if debe("vigente", None):
        fallos.append("la primera revisión «vigente» propone")
    if not debe("vigente", "observada"):
        fallos.append("pasar a «vigente» desde «observada» no propone")
    if not (debe("reformada", "vigente") and debe("derogada", None)):
        fallos.append("«reformada» o «derogada» no proponen")
    if debe("observada", "vigente"):
        fallos.append("«observada» propone")
    if any(debe(e, e) for e in ("vigente", "observada", "reformada", "derogada")):
        fallos.append("reconfirmar el mismo estado propone")
    if not (debe("reformada", None) and debe("vigente", "reformada")):
        fallos.append("un cambio a estado distinto no propone")
    return fallos


def guardia_disparador(definicion: str) -> list[str]:
    fallos = []
    if "AND r.tipo='tecnica' AND NOT NEW.autores ? r.revisor_id) < 1 THEN" not in definicion:
        fallos.append("la publicación no pide una sola revisión técnica")
    if "IF OLD.redactada_por='ia' THEN\n                        RAISE EXCEPTION 'BIB_VERSION_IA_NO_EDITABLE'" not in definicion:
        fallos.append("la base deja editar una versión de la IA")
    if "NEW.autores<>'[\"ia\"]'::jsonb" not in definicion:
        fallos.append("el alta de la IA no exige autores = [\"ia\"]")
    if "length(trim(COALESCE(NEW.nota_descarte,'')))=0" not in definicion:
        fallos.append("la base deja descartar sin nota")
    return fallos


# --- Reglas puras ---

def test_r1_solo_las_plantillas_que_citan_la_resolucion():
    assert guardia_afectadas(dominio.plantillas_afectadas) == []


def test_m1_proponer_para_todas_las_plantillas_da_rojo():
    assert "se propone para plantillas que no citan la resolución" in guardia_afectadas(
        lambda citas, url: sorted(citas["plantillas"]))


def test_r2_solo_entran_cambios_con_cita_verificada():
    assert guardia_citas(dominio.aplicar_cambios) == []


def test_m2_aceptar_un_cambio_sin_cita_verificada_da_rojo():
    def acepta_todo(cuerpo, cambios, citas):
        for c in cambios:
            cuerpo = cuerpo.replace(c.antes, c.despues)
        return cuerpo, [c.model_dump() for c in cambios]
    assert "entra un cambio sin cita verificada" in guardia_citas(acepta_todo)


def test_r1_disparo_por_estado():
    assert guardia_disparo(dominio.debe_proponer) == []


def test_m7_proponer_en_la_primera_revision_da_rojo():
    assert "la primera revisión «vigente» propone" in guardia_disparo(
        lambda estado, anterior: estado in ("vigente", "reformada", "derogada"))


def test_m8_proponer_al_reconfirmar_el_mismo_estado_da_rojo():
    assert "reconfirmar el mismo estado propone" in guardia_disparo(
        lambda estado, anterior: estado in ("reformada", "derogada")
        or (estado == "vigente" and anterior is not None))


@pytest.mark.asyncio
async def test_una_sola_propuesta_de_la_ia_en_revision_por_plantilla(servicio):
    def responder(sql, parametros):
        return _Resultado(1 if "redactada_por='ia' AND estado='en_revision'" in sql else None)
    sesion = SesionSimulada(responder)
    resultado = await servicio.proponer(sesion, "persona-1", "BIB-003", "Otra", "org-1")
    assert resultado["resultado"] == "propuesta_en_revision"
    assert not any(s.startswith("INSERT INTO biblioteca_versiones") for s, _ in sesion.sentencias)


@pytest.mark.asyncio
async def test_m10_crear_la_segunda_propuesta_da_rojo(servicio, monkeypatch):
    async def nunca(session, codigo):
        return False
    monkeypatch.setattr(servicio, "hay_propuesta_en_revision", nunca)
    sesion = SesionSimulada(lambda sql, p: _Resultado(1 if "en_revision" in sql else None))
    resultado = await servicio.proponer(sesion, "persona-1", "BIB-003", "Otra", "org-1")
    assert resultado["resultado"] == "creada"  # sin la regla, entra una segunda propuesta: la regla es la que la para


def test_m11_proponer_al_pasar_a_observada_da_rojo():
    assert "«observada» propone" in guardia_disparo(
        lambda estado, anterior: estado != anterior and (estado != "vigente" or anterior is not None))


def test_disparador_parte_de_bib403_con_los_cambios_de_bib406():
    definicion = _migracion().definicion_nueva()
    assert guardia_disparador(definicion) == []
    assert "BIB_REVISION_PENDIENTE" in definicion and "BIB_FICHA_INCOMPLETA" in definicion


def test_m4_exigir_dos_revisiones_da_rojo():
    mutada = _migracion().definicion_nueva().replace(
        "AND r.tipo='tecnica' AND NOT NEW.autores ? r.revisor_id) < 1 THEN",
        "AND r.tipo='tecnica' AND NOT NEW.autores ? r.revisor_id) < 2 THEN")
    assert "la publicación no pide una sola revisión técnica" in guardia_disparador(mutada)


def test_version_siguiente_sube_el_parche_y_el_cuerpo_la_declara():
    assert dominio.version_siguiente("0.2.1") == "0.2.2"
    assert dominio.version_siguiente("1.0") == "1.0.1"
    assert dominio.con_version("---\nversion: 0.2.1\n---\n", "0.2.1", "0.2.2") == "---\nversion: 0.2.2\n---\n"


# --- Servicio con sesión simulada ---

class _Resultado:
    def __init__(self, valor=None, filas=None):
        self._valor, self._filas = valor, filas or []

    def scalar(self):
        return self._valor

    def mappings(self):
        return self

    def first(self):
        return self._filas[0] if self._filas else None

    def all(self):
        return self._filas


class SesionSimulada:
    """Registra cada sentencia; `responder(sql, parametros)` da el resultado."""

    def __init__(self, responder=lambda sql, p: _Resultado()):
        self.sentencias, self._responder = [], responder

    async def execute(self, sentencia, parametros=None):
        sql = str(sentencia)
        self.sentencias.append((sql, parametros or {}))
        return self._responder(sql, parametros or {})

    @asynccontextmanager
    async def begin_nested(self):
        yield

    def insercion(self) -> dict:
        return next(p for s, p in self.sentencias if s.startswith("INSERT INTO biblioteca_versiones"))


PUBLICADA = {"id": "pub-1", "codigo": "BIB-003", "version": "0.2.2", "ficha": {"nombre": "x"},
             "cuerpo_md": "---\nversion: 0.2.2\n---\nTexto de la autora.\n"}


@pytest.fixture
def servicio(monkeypatch):
    from features.biblioteca.services import editorial, propuestas_ia as svc

    async def capacidades(session, actor):
        return ["editor"]

    async def publicada(session, codigo):
        return dict(PUBLICADA, codigo=codigo)

    async def leer(session, identificador):
        return {"id": identificador}

    verificada = "LOPDP-art-7"  # verificada en citas.json y en las citas sintéticas

    async def redactor(valores):
        return SalidaPropuestaIA(cambios=[CambioIA(
            seccion="1", antes="Texto de la autora.", despues="Texto nuevo.", cita=verificada)]), None, "modelo-x"

    monkeypatch.setattr(svc, "capacidades", capacidades)
    monkeypatch.setattr(svc, "_publicada", publicada)
    monkeypatch.setattr(editorial, "leer_version", leer)
    svc.inyectar_redactor_de_prueba(redactor)
    yield svc
    svc.inyectar_redactor_de_prueba(None)
    svc.inyectar_normativa_de_prueba(None)


def guardia_autoria(insercion: dict, actor: str) -> list[str]:
    fallos = []
    autores = json.loads(insercion["autores"])
    if autores != ["ia"]:
        fallos.append("autores no es [\"ia\"]")
    if actor in autores:
        fallos.append("quien disparó figura como autor")
    if insercion["actor"] != actor:
        fallos.append("quien disparó no queda como responsable")
    if not insercion["modelo"] or insercion["origen"] not in ("resolucion", "peticion"):
        fallos.append("no guarda modelo y origen")
    return fallos


@pytest.mark.asyncio
async def test_r3_la_ia_es_la_autora_y_quien_dispara_no(servicio):
    sesion = SesionSimulada()
    resultado = await servicio.proponer(sesion, "persona-1", "BIB-003", "Actualizar la cita", "org-1")
    assert resultado["resultado"] == "creada"
    insercion = sesion.insercion()
    assert guardia_autoria(insercion, "persona-1") == []
    assert "'ia'" in [s for s, _ in sesion.sentencias if s.startswith("INSERT INTO biblioteca_versiones")][0]
    assert insercion["version"] == "0.2.3" and "version: 0.2.3" in insercion["cuerpo"]
    assert insercion["sha"] == hashlib.sha256(insercion["cuerpo"].encode("utf-8")).hexdigest()
    assert insercion["sustituye"] == "pub-1"


def test_m3_escribir_al_solicitante_en_autores_da_rojo():
    insercion = {"autores": json.dumps(["ia", "persona-1"]), "actor": "persona-1", "modelo": "m", "origen": "peticion"}
    assert "quien disparó figura como autor" in guardia_autoria(insercion, "persona-1")


@pytest.mark.asyncio
async def test_r2_sin_cambios_no_se_crea_version(servicio):
    async def nada(valores):
        return SalidaPropuestaIA(cambios=[]), None, "modelo-x"
    servicio.inyectar_redactor_de_prueba(nada)
    sesion = SesionSimulada()
    assert (await servicio.proponer(sesion, "persona-1", "BIB-003", "Nada", "org-1"))["resultado"] == "sin_cambios"
    assert not any(s.startswith("INSERT INTO biblioteca_versiones") for s, _ in sesion.sentencias)


@pytest.mark.asyncio
async def test_r1_limite_de_uso(servicio):
    async def tope(valores):
        raise ErrorNegocio("IA_TOPE_ORGANIZACION", status_code=429)
    servicio.inyectar_redactor_de_prueba(tope)
    assert (await servicio.proponer(SesionSimulada(), "p", "BIB-003", "x", "org-1"))["resultado"] == "limite_de_uso"


@pytest.mark.asyncio
async def test_r1_resolucion_reformada_propone_solo_a_quien_la_cita(servicio, monkeypatch):
    monkeypatch.setattr(servicio, "leer_citas", lambda: CITAS_M1)

    class Resolucion:
        url_fuente, titulo = URL_RES_X, "Resolución sintética"

    async def obtener(id_resolucion):
        return Resolucion()
    servicio.inyectar_normativa_de_prueba(obtener)
    sesion = SesionSimulada()
    resultado = await servicio.proponer_por_resolucion(sesion, "res-1", "reformada", "vigente", "operador-1", org_id="org-1")
    codigos = [p["codigo"] for s, p in sesion.sentencias if s.startswith("INSERT INTO biblioteca_versiones")]
    assert codigos == ["BIB-003"] and resultado["resultado"] == "creada"
    assert all(p["origen"] == "resolucion" and p["resolucion"] == "res-1"
               for s, p in sesion.sentencias if s.startswith("INSERT INTO biblioteca_versiones"))
    primera = SesionSimulada()
    assert (await servicio.proponer_por_resolucion(primera, "res-1", "vigente", None, "op", org_id="o"))["resultado"] == "sin_cambios"
    assert primera.sentencias == []


@pytest.fixture
def editorial_simulada(monkeypatch):
    from features.biblioteca.services import editorial

    async def autorizar(session, actor, requerida=None):
        return ["editor", "revisor_tecnico", "publicador"]
    monkeypatch.setattr(editorial, "autorizar", autorizar)
    return editorial


def _sesion_ia():
    def responder(sql, parametros):
        if sql.startswith("SELECT redactada_por"):
            return _Resultado("ia")
        return _Resultado()
    return SesionSimulada(responder)


async def guardia_no_editable(editorial) -> list[str]:
    from features.biblioteca.domain.editorial import ArchivoMaestro, EditarFicha, Ficha
    ficha = Ficha(nombre="n", objetivo="o", fuentes="f", fecha_revision="2026-11-25", instrucciones="i",
                  dependencias="d", restricciones="r")
    fallos = []
    for nombre, llamada in (
        ("editar", lambda s: editorial.editar(s, "p", "v-ia", EditarFicha(ficha=ficha, generacion=1))),
        ("cargar", lambda s: editorial.cargar(s, "p", "v-ia", ArchivoMaestro(
            nombre="a.docx", contenido_base64="QQ==", generacion=1)))):
        sesion = _sesion_ia()
        try:
            await llamada(sesion)
            fallos.append(f"{nombre} edita una versión de la IA")
        except ErrorNegocio as exc:
            if exc.code != "BIB_VERSION_IA_NO_EDITABLE":
                fallos.append(f"{nombre} da {exc.code}")
        if any(s.startswith("UPDATE") for s, _ in sesion.sentencias):
            fallos.append(f"{nombre} llega a escribir")
    return fallos


@pytest.mark.asyncio
async def test_r5b_la_version_de_la_ia_no_se_edita(editorial_simulada):
    assert await guardia_no_editable(editorial_simulada) == []


@pytest.mark.asyncio
async def test_m6_permitir_la_edicion_y_anadir_al_actor_da_rojo(editorial_simulada, monkeypatch):
    async def sin_control(session, identificador):
        return None

    async def version(session, identificador, generacion=None):
        return {"id": identificador, "estado": "en_revision", "autores": ["ia"], "formato": "DOCX", "generacion": 1}

    monkeypatch.setattr(editorial_simulada, "_exigir_de_personas", sin_control)
    monkeypatch.setattr(editorial_simulada, "_version", version)
    monkeypatch.setattr(editorial_simulada, "validar_archivo", lambda e, f: (b"x", "h"))
    fallos = await guardia_no_editable(editorial_simulada)
    assert "editar edita una versión de la IA" in fallos and "editar llega a escribir" in fallos
    mutada = _migracion().definicion_nueva().replace(
        "IF OLD.redactada_por='ia' THEN\n                        RAISE EXCEPTION 'BIB_VERSION_IA_NO_EDITABLE'",
        "IF false THEN\n                        RAISE EXCEPTION 'BIB_VERSION_IA_NO_EDITABLE'")
    assert "la base deja editar una versión de la IA" in guardia_disparador(mutada)


async def guardia_descarte(descartar) -> list[str]:
    sesion = SesionSimulada()
    try:
        await descartar(sesion, "p", "v-1", "   ", 1)
        return ["se descarta sin nota"]
    except ErrorNegocio as exc:
        return [] if exc.code == "BIB_NOTA_DESCARTE_REQUERIDA" else [f"da {exc.code}"]


@pytest.mark.asyncio
async def test_r5_descartar_exige_nota(editorial_simulada):
    assert await guardia_descarte(editorial_simulada.descartar) == []


@pytest.mark.asyncio
async def test_m5_descartar_sin_nota_da_rojo(editorial_simulada):
    async def sin_nota(session, actor, identificador, nota, generacion):
        return {"id": identificador, "estado": "retirada"}
    assert "se descarta sin nota" in await guardia_descarte(sin_nota)
    mutada = _migracion().definicion_nueva().replace("length(trim(COALESCE(NEW.nota_descarte,'')))=0", "false")
    assert "la base deja descartar sin nota" in guardia_disparador(mutada)


def test_pasillo_y_api_exponen_las_propuestas():
    pasillo = (ROOT / "app_core/pasillo/biblioteca.py").read_bytes().decode("utf-8")
    assert "async def proponer_por_resolucion(" in pasillo
    api = (ROOT / "api/routers/biblioteca_editorial.py").read_bytes().decode("utf-8")
    assert '@router.post("/propuestas", status_code=202' in api
    assert '@router.post("/versiones/{identificador}/descartar"' in api
    modelo = dominio.VersionMaestraIA.model_fields
    for campo in ("redactada_por", "modelo_ia", "origen_ia", "motivo_ia", "cambios_ia", "solicitante_nombre"):
        assert campo in modelo


# --- Base de pruebas: el disparador (se omiten sin TEST_DATABASE_URL) ---

FICHA = {"nombre": "Plantilla sintética", "objetivo": "Probar", "fuentes": "Fuente de prueba",
         "fecha_revision": "2026-11-25", "instrucciones": "Revisar", "dependencias": "Ninguna",
         "restricciones": "Solo pruebas"}


@pytest_asyncio.fixture
async def db_bib():
    from conftest import exigir_base_de_pruebas

    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("Persistencia pendiente: falta TEST_DATABASE_URL")
    exigir_base_de_pruebas()
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            if not (await conexion.execute(text(
                    "SELECT 1 FROM information_schema.columns WHERE table_name='biblioteca_versiones' "
                    "AND column_name='redactada_por'"))).scalar():
                pytest.fail("Aplicar la migración de BIB-406 en la base de pruebas antes de este árbitro", pytrace=False)
            ids = {rol: "bib406-test-" + uuid4().hex for rol in ("editor", "aprobadora", "operador")}
            for rol, usuario in ids.items():
                await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:email,:nombre)"),
                                       {"id": usuario, "email": usuario + "@example.test", "nombre": rol})
            for rol, capacidad in [("editor", "editor"), ("aprobadora", "revisor_tecnico"),
                                   ("aprobadora", "publicador"), ("aprobadora", "editor")]:
                await conexion.execute(text(
                    "WITH o AS (INSERT INTO users(id,email,nombre) SELECT 'otorgante-'||g, "
                    "'otorgante-'||g||'@correo.invalid', 'Otorgante sintético' FROM md5(random()::text) g RETURNING id) "
                    "INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                    "SELECT :id,:cap,o.id,'Fixture sintética rollback' FROM o"), {"id": ids[rol], "cap": capacidad})
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                yield sesion, ids
        except DBAPIError:
            pytest.fail("Fallo DB BIB-406 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


async def _publicada_md(sesion, ids, codigo):
    from features.biblioteca import biblioteca_service as bib
    cuerpo = "---\nversion: 0.1.0\n---\nTexto de la autora.\n"
    version = await bib.crear_version_md(sesion, ids["editor"], codigo, "0.1.0", cuerpo, ficha=FICHA)
    await bib.revisar(sesion, ids["aprobadora"], version["id"], bib.Dictamen(
        tipo="tecnica", aprobado=True, comentario="Dictamen sintético", generacion=version["generacion"]))
    return await bib.publicar(sesion, ids["aprobadora"], version["id"], bib.Transicion(
        generacion=version["generacion"], motivo="Publicación sintética"))


@pytest.fixture
def _validacion_validada(monkeypatch):
    from features.biblioteca.services import editorial
    monkeypatch.setattr(editorial, "validacion_de_texto", lambda *a, **k: "validada")


async def _version_ia(sesion, ids, monkeypatch, actor_rol="aprobadora"):
    from features.biblioteca.services import propuestas_ia as svc
    codigo = "TEST-" + uuid4().hex[:10].upper()
    await _publicada_md(sesion, ids, codigo)
    verificada = next(k for k, e in CITAS["estados"].items() if e == "verificada")

    async def redactor(valores):
        return SalidaPropuestaIA(cambios=[CambioIA(seccion="1", antes="Texto de la autora.",
                                                   despues="Texto nuevo.", cita=verificada)]), None, "modelo-x"
    svc.inyectar_redactor_de_prueba(redactor)
    try:
        resultado = await svc.proponer(sesion, ids[actor_rol], codigo, "Petición sintética", "org-sin-tope")
    finally:
        svc.inyectar_redactor_de_prueba(None)
    return resultado["versiones"][0]


@pytest.mark.asyncio
async def test_db_una_persona_revisa_y_publica_la_version_de_la_ia(db_bib, monkeypatch, _validacion_validada):
    from features.biblioteca import biblioteca_service as bib
    sesion, ids = db_bib
    version = await _version_ia(sesion, ids, monkeypatch)
    assert version["redactada_por"] == "ia" and version["autores"] == ["ia"]
    assert version["responsable_id"] == ids["aprobadora"] and version["estado"] == "en_revision"
    with pytest.raises(DBAPIError):
        async with sesion.begin_nested():
            await sesion.execute(text(
                "INSERT INTO biblioteca_revisiones(id,version_id,generacion,tipo,aprobado,revisor_id,comentario) "
                "VALUES (:id,:v,1,'tecnica',true,'ia','La IA no revisa')"), {"id": str(uuid4()), "v": version["id"]})
    await bib.revisar(sesion, ids["aprobadora"], version["id"], bib.Dictamen(
        tipo="tecnica", aprobado=True, comentario="Revisado", generacion=1))
    publicada = await bib.publicar(sesion, ids["aprobadora"], version["id"], bib.Transicion(
        generacion=1, motivo="Publicación de la propuesta"))
    assert publicada["estado"] == "publicada"


@pytest.mark.asyncio
async def test_db_la_base_rechaza_editar_la_version_de_la_ia(db_bib, monkeypatch, _validacion_validada):
    sesion, ids = db_bib
    version = await _version_ia(sesion, ids, monkeypatch)
    await sesion.execute(text("SELECT set_config('app.current_user_id', :id, true)"), {"id": ids["editor"]})
    with pytest.raises(DBAPIError, match="BIB_VERSION_IA_NO_EDITABLE"):
        async with sesion.begin_nested():
            await sesion.execute(text(
                "UPDATE biblioteca_versiones SET cuerpo_md='otro', sha256=:sha, generacion=generacion+1, "
                "autores=CAST(:autores AS jsonb) WHERE id=:id"),
                {"id": version["id"], "sha": hashlib.sha256(b"otro").hexdigest(),
                 "autores": json.dumps(["ia", ids["editor"]])})


@pytest.mark.asyncio
async def test_db_descartar_con_nota_deja_retirada(db_bib, monkeypatch, _validacion_validada):
    from features.biblioteca import biblioteca_service as bib
    sesion, ids = db_bib
    version = await _version_ia(sesion, ids, monkeypatch)
    with pytest.raises(DBAPIError):
        async with sesion.begin_nested():
            await sesion.execute(text(
                "UPDATE biblioteca_versiones SET estado='retirada', motivo='x', descartada_por=:a, "
                "descartada_en=now() WHERE id=:id"), {"id": version["id"], "a": ids["editor"]})
    retirada = await bib.descartar(sesion, ids["editor"], version["id"], "No procede", 1)
    assert retirada["estado"] == "retirada" and retirada["nota_descarte"] == "No procede"
    assert retirada["descartada_por"] == ids["editor"]
