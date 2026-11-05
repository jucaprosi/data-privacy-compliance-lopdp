# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-307: aceptación de extremo a extremo de Biblioteca con tres perfiles ficticios.

Recorre empresa → tratamiento → requisito → brecha → acción → documento → revisión → evidencia →
verificación → cierre con los servicios reales y los IDs que devuelve la base; nada se fabrica salvo las filas
semilla de cada organización (usuarios, empresa, tratamiento RAT y hoja de ruta), insertadas en una transacción
que se revierte. La persistencia y la RLS se acreditan solo con el arnés local (ARNES_BASE=postgresql_local) o una
rama propia (BIB307_RAMA_PROPIA=1); sin ellas las pruebas de base se omiten y no se acreditan.

Mutación decisiva (BIB-307.md): en ``features/biblioteca/services/documentos_consulta.py``, ``obtener_documento``,
cambiar ``WHERE id=:id AND tenant_id=:t`` por ``WHERE id=:id`` (pedir el documento de otra empresa cambiando su
ID). Falla ``test_db_cero_accesos_cruzados_entre_las_tres_empresas`` en su tramo sin RLS. Restaurar y repetir.
"""
import os
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
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
from features.biblioteca import biblioteca_service as bib
from features.roadmap import roadmap_service as roadmap

PRODUCCION, COMPARTIDA = "ep-late-hall-b50bpbk5", "ep-soft-darkness-b5z454vp"
HASH = "c" * 64
FICHA = {"nombre": "Política de protección de datos", "objetivo": "Aceptación BIB-307", "fuentes": "LOPDP art. 37",
         "fecha_revision": "2026-11-01", "instrucciones": "Completar", "dependencias": "Ninguna",
         "restricciones": "Solo pruebas"}
CUERPO = "# Política de {{organizacion.razon_social}}\nEmitida el {{fecha_emision}}\n"

# Tres perfiles ficticios: qué los distingue y qué debe pasar en cada uno.
PERFILES = {
    "microempresa": {"razon": "Servicios Contables Ficticios S.A.S.", "tratamiento": "Nómina y clientes",
                     "control": "P7", "severidad": "media", "sensibles": False},
    "centro_medico": {"razon": "Centro Médico Ficticio Cía. Ltda.", "tratamiento": "Historias clínicas",
                      "control": "P7", "severidad": "alta", "sensibles": True},
    "entidad_publica": {"razon": "GAD Municipal Ficticio", "tratamiento": "Registro de trámites ciudadanos",
                        "control": "P7", "severidad": "alta", "sensibles": False},
}


# Consultas literales (sin nombres interpolados): filas de otra empresa visibles en cada tabla del recorrido.
AJENOS_POR_TABLA = {
    "biblioteca_documentos": "SELECT count(*) FROM biblioteca_documentos WHERE tenant_id::text <> :t",
    "biblioteca_revisiones_documento": "SELECT count(*) FROM biblioteca_revisiones_documento WHERE tenant_id::text <> :t",
    "biblioteca_revision_acciones": "SELECT count(*) FROM biblioteca_revision_acciones WHERE tenant_id::text <> :t",
    "biblioteca_evidencias": "SELECT count(*) FROM biblioteca_evidencias WHERE tenant_id::text <> :t",
    "biblioteca_verificaciones": "SELECT count(*) FROM biblioteca_verificaciones WHERE tenant_id::text <> :t",
    "hallazgos": "SELECT count(*) FROM hallazgos WHERE tenant_id::text <> :t",
    "roadmap_tasks": "SELECT count(*) FROM roadmap_tasks WHERE tenant_id::text <> :t",
}


# --------------------------------------------------------------------------------------- contrato estático

def test_perfiles_y_compuertas_del_recorrido_existen():
    assert set(PERFILES) == {"microempresa", "centro_medico", "entidad_publica"}
    for nombre in ("crear_documento", "cambiar_documento", "enviar_a_revision", "aprobar_revision", "delegar_autoridad",
                   "abrir_nueva_revision", "crear_enlace", "registrar_evidencia", "registrar_verificacion",
                   "obtener_documento", "VerificadorEvidencia"):
        assert nombre in bib.__all__, nombre
    for nombre in ("registrar_hallazgo", "crear_tareas_desde_hallazgos", "update_task_status", "cerrar_hallazgo",
                   "obtener_accion_para_enlace", "reabrir_accion_no_conforme"):
        assert hasattr(roadmap, nombre), nombre


# ------------------------------------------------------------------------------------------ persistencia

def _url_de_pruebas() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or not (os.environ.get("ARNES_BASE") == "postgresql_local" or os.environ.get("BIB307_RAMA_PROPIA") == "1"):
        pytest.skip("Persistencia/RLS no acreditadas: falta el arnés local o rama propia (BIB307_RAMA_PROPIA=1)")
    if COMPARTIDA in url.lower():
        pytest.fail("La rama test compartida no es una rama propia; no se abrió conexión", pytrace=False)
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


@dataclass
class Empresa:
    perfil: str
    id: str
    usuarios: dict[str, str]
    tratamiento_id: str
    roadmap_id: str
    ola_id: str
    traza: dict[str, str] = field(default_factory=dict)


@dataclass
class Mundo:
    conexion: object
    sesion: AsyncSession
    plantilla_id: str
    empresas: dict[str, Empresa]


async def _semilla_global(conexion) -> dict[str, str]:
    editorial = {rol: "bib307-" + rol + "-" + uuid4().hex[:8] for rol in ("editor", "tecnico", "juridico", "publicador")}
    for rol, usuario in editorial.items():
        await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,:n)"),
                               {"id": usuario, "e": usuario + "@example.test", "n": rol})
    for rol, capacidad in (("editor", "editor"), ("tecnico", "revisor_tecnico"),
                           ("juridico", "revisor_juridico"), ("publicador", "publicador")):
        await conexion.execute(text("INSERT INTO biblioteca_capacidades(usuario_id,capacidad,concedida_por,motivo) "
                                    "VALUES (:id,:cap,:id,'Fixture BIB-307 rollback')"),
                               {"id": editorial[rol], "cap": capacidad})
    return editorial


async def _semilla_empresa(conexion, perfil: str) -> Empresa:
    datos = PERFILES[perfil]
    tid = f"bib307-{perfil}-" + uuid4().hex[:12]
    await conexion.execute(text(
        "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:id, :n, :r, :ruc)"),
        {"id": tid, "n": datos["razon"], "r": datos["razon"], "ruc": str(uuid4().int)[:13]})
    usuarios = {}
    # redactor y responsable de evidencia; asignador de la revisión; aprobador con autoridad; revisor de evidencia.
    for rol, rol_tenant in (("redactor", "implementador"), ("asignador", "coordinador"),
                            ("aprobador", "dpo"), ("revisor", "coordinador")):
        usuario = f"bib307-{perfil}-{rol}-" + uuid4().hex[:8]
        await conexion.execute(text("INSERT INTO users(id,email,nombre) VALUES (:id,:e,:n)"),
                               {"id": usuario, "e": usuario + "@example.test", "n": rol})
        await conexion.execute(text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:id,:u,:t,:r)"),
                               {"id": str(uuid4()), "u": usuario, "t": tid, "r": rol_tenant})
        usuarios[rol] = usuario
    tratamiento = "bib307-rat-" + uuid4().hex
    await conexion.execute(text(
        "INSERT INTO rat_actividades (id, tenant_id, codigo, nombre, area_responsable, finalidad, base_legal, "
        "medio_soporte, pais_transferencia, plazo_conservacion, nivel_riesgo, observaciones_dpo, origen, "
        "categorias_titulares, categorias_datos, encargados, destinatarios, medidas_seguridad, datos_sensibles, "
        "transferencia_internacional, requiere_eipd, es_gran_escala, decisiones_automatizadas, "
        "volumen_titulares_estimado, volumen_titulares_12_meses, version) VALUES (:id, :t, 'A-1', :n, '', "
        "'', 'CONSENTIMIENTO', '', '', '', '', '', 'manual', '[]', '[]', '[]', '[]', '[]', :s, false, false, "
        "false, false, 0, 0, 1)"), {"id": tratamiento, "t": tid, "n": datos["tratamiento"], "s": datos["sensibles"]})
    hoja, ola = str(uuid4()), str(uuid4())
    await conexion.execute(text("INSERT INTO roadmaps(id, tenant_id, variables_json) VALUES (:r, :t, '{}')"),
                           {"r": hoja, "t": tid})
    await conexion.execute(text("INSERT INTO roadmap_waves(id, roadmap_id, tenant_id, name) VALUES (:w, :r, :t, 'Ola 1')"),
                           {"w": ola, "r": hoja, "t": tid})
    return Empresa(perfil, tid, usuarios, tratamiento, hoja, ola)


async def _publicar_plantilla(sesion, editorial) -> str:
    version = await bib.crear_version_md(sesion, editorial["editor"], "B307-" + uuid4().hex[:10].upper(), "0.1.0", CUERPO)
    version = await bib.editar(sesion, editorial["editor"], version["id"], bib.EditarFicha(
        ficha=bib.Ficha(**FICHA), generacion=version["generacion"]))
    for rol, tipo in (("tecnico", "tecnica"), ("juridico", "juridica")):
        await bib.revisar(sesion, editorial[rol], version["id"], bib.Dictamen(
            tipo=tipo, aprobado=True, comentario="Dictamen sintético BIB-307", generacion=version["generacion"]))
    publicada = await bib.publicar(sesion, editorial["publicador"], version["id"], bib.Transicion(
        generacion=version["generacion"], motivo="Publicación sintética BIB-307"))
    return publicada["id"]


@pytest_asyncio.fixture
async def mundo():
    engine = create_async_engine(_url_de_pruebas(), echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            for tabla in ("biblioteca_documentos", "biblioteca_revisiones_documento", "biblioteca_revision_acciones",
                          "biblioteca_verificaciones", "hallazgos", "rat_actividades"):
                if not (await conexion.execute(text("SELECT to_regclass(:t)"), {"t": "public." + tabla})).scalar():
                    pytest.fail(f"Falta la tabla {tabla}: migrar solo la base local o rama propia", pytrace=False)
            editorial = await _semilla_global(conexion)
            empresas = {perfil: await _semilla_empresa(conexion, perfil) for perfil in PERFILES}
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            anterior = roadmap.verificador_cierre_registrado()
            roadmap.registrar_verificador_cierre(bib.VerificadorEvidencia())
            try:
                async with AsyncSession(bind=conexion, expire_on_commit=False,
                                        join_transaction_mode="create_savepoint") as sesion:
                    plantilla = await _publicar_plantilla(sesion, editorial)
                    yield Mundo(conexion, sesion, plantilla, empresas)
            finally:
                roadmap.registrar_verificador_cierre(anterior)
        except DBAPIError:
            pytest.fail("Fallo DB BIB-307 (detalles de conexión omitidos); comprobar migración y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()


async def _estado_tarea(m: Mundo, e: Empresa) -> str:
    await m.sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": e.id})
    return (await m.sesion.execute(text("SELECT status FROM roadmap_tasks WHERE id=:k"),
                                   {"k": e.traza["accion"]})).scalar()


async def _recorrido(m: Mundo, e: Empresa) -> Empresa:
    """Empresa → tratamiento → requisito → brecha → acción → documento → revisión → evidencia → cierre."""
    s, u, datos = m.sesion, e.usuarios, PERFILES[e.perfil]
    # Brecha registrada desde el tratamiento, sobre un requisito (control) concreto.
    brecha, creada = await roadmap.registrar_hallazgo(
        s, e.id, u["asignador"], "rat", e.tratamiento_id, datos["severidad"],
        f"Falta política documentada para «{datos['tratamiento']}»", control_ref=datos["control"], dimension="D01")
    assert creada
    conversion = await roadmap.crear_tareas_desde_hallazgos(s, e.id, u["asignador"], e.roadmap_id, e.ola_id, [brecha])
    assert len(conversion.tareas) == 1
    accion = conversion.tareas[0]["tarea_id"]
    e.traza.update(tratamiento=e.tratamiento_id, requisito=datos["control"], brecha=brecha, accion=accion)

    # Documento desde la plantilla publicada, completado y vinculado a la acción.
    doc = await bib.crear_documento(s, e.id, u["redactor"], bib.CrearDocumento(
        plantilla_id=m.plantilla_id, tarea_hoja_ruta_id=accion))
    assert doc.estado == "borrador" and doc.variables_faltantes
    doc = await bib.cambiar_documento(s, e.id, u["redactor"], doc.id, bib.CambiarDocumento(
        contenido_markdown=f"# Política de {datos['razon']}\nEmitida el 2026-11-04\n", revision=doc.revision))
    assert doc.variables_faltantes == []
    e.traza["documento"] = doc.id

    # Revisión de cuatro ojos: redactor ≠ asignador ≠ aprobador, con autoridad vigente.
    await bib.delegar_autoridad(s, e.id, u["asignador"], bib.DelegarAutoridad(
        usuario_id=u["aprobador"], criterio="Delegación sintética BIB-307",
        vigente_desde=datetime.now(timezone.utc) - timedelta(minutes=5)))
    revision = await bib.enviar_a_revision(s, e.id, u["asignador"], doc.id, bib.EnviarRevision(revisor_id=u["aprobador"]))
    aprobada = await bib.aprobar_revision(s, e.id, u["aprobador"], revision.id, bib.AprobarRevision(
        criterio="Contenido conforme al requisito"))
    assert aprobada.estado == "aprobada"
    doc = await bib.obtener_documento(s, e.id, u["redactor"], doc.id)
    assert doc.estado == "aprobado" and doc.aprobado_por == u["aprobador"]
    e.traza.update(revision=aprobada.id, sha256_aprobado=doc.sha256, revision_documento=str(doc.revision))
    enlace = await bib.crear_enlace(s, e.id, u["asignador"], doc.id, bib.CrearEnlace(
        accion_id=accion, revision=doc.revision), roadmap.obtener_accion_para_enlace)
    assert enlace.accion_id == accion and enlace.requisito == datos["control"] and enlace.hallazgo_id == brecha

    # Un documento aprobado no cierra la acción por sí solo.
    with pytest.raises(ErrorNegocio) as error:
        await roadmap.update_task_status(s, e.id, u["revisor"], accion, roadmap.TaskStatus.completada)
    assert error.value.code == "RM_CIERRE_SIN_EVIDENCIA" and await _estado_tarea(m, e) == "pendiente"

    # Evidencia y verificación conforme por otra persona; recién entonces se cierra.
    evidencia = await bib.registrar_evidencia(s, e.id, u["redactor"], accion, bib.RegistrarEvidencia(
        titulo="Política aprobada y difundida", version="1.0", sha256=HASH, clasificacion="interna",
        permisos=["coordinador"], fecha="2026-11-03"), roadmap.obtener_accion_para_enlace)
    verificacion = await bib.registrar_verificacion(s, e.id, u["revisor"], accion, bib.RegistrarVerificacion(
        evidencia_id=evidencia.id, criterio="La política cubre el tratamiento y está difundida",
        evidencia_legible=True, resultado="conforme", fecha=date.today()),
        roadmap.obtener_accion_para_enlace, roadmap.reabrir_accion_no_conforme)
    assert verificacion.veredicto == "conforme"
    cierre = await roadmap.update_task_status(s, e.id, u["revisor"], accion, roadmap.TaskStatus.completada)
    assert cierre["status"] == "completada"
    assert await roadmap.cerrar_hallazgo(s, e.id, u["revisor"], brecha) is True
    e.traza.update(evidencia=evidencia.id, verificacion=verificacion.verificaciones[-1].id, cierre="completada")
    return e


@pytest.mark.asyncio
@pytest.mark.parametrize("perfil", list(PERFILES))
async def test_db_recorrido_completo_por_perfil_con_ids_reales(mundo, perfil):
    e = await _recorrido(mundo, mundo.empresas[perfil])
    # La traza conserva los IDs que devolvió la base y se puede releer desde ella.
    await mundo.sesion.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": e.id})
    fila = (await mundo.sesion.execute(text(
        "SELECT t.hallazgo_id, t.control_ref, h.origen_ref, h.estado, d.tarea_hoja_ruta_id "
        "FROM roadmap_tasks t JOIN hallazgos h ON h.id=t.hallazgo_id "
        "JOIN biblioteca_documentos d ON d.tarea_hoja_ruta_id=t.id WHERE t.id=:a"), {"a": e.traza["accion"]})).one()
    assert tuple(fila) == (e.traza["brecha"], e.traza["requisito"], e.traza["tratamiento"], "cerrado", e.traza["accion"])
    assert set(e.traza) >= {"tratamiento", "requisito", "brecha", "accion", "documento", "revision", "evidencia",
                            "verificacion", "cierre"}


@pytest.mark.asyncio
async def test_db_aprobado_no_cambia_sin_nueva_revision(mundo):
    e = await _recorrido(mundo, mundo.empresas["centro_medico"])
    s, u, doc_id = mundo.sesion, e.usuarios, e.traza["documento"]
    with pytest.raises(ErrorNegocio) as error:
        await bib.cambiar_documento(s, e.id, u["redactor"], doc_id, bib.CambiarDocumento(
            contenido_markdown="Texto cambiado sin revisión", revision=int(e.traza["revision_documento"])))
    assert error.value.code == "BIB_DOCUMENTO_NO_EDITABLE"
    with pytest.raises(DBAPIError):  # la base también lo impide si alguien salta el servicio
        async with s.begin_nested():
            await s.execute(text("UPDATE biblioteca_documentos SET contenido_markdown='x' WHERE id=:d"), {"d": doc_id})
    intacto = await bib.obtener_documento(s, e.id, u["redactor"], doc_id)
    assert (intacto.estado, intacto.sha256) == ("aprobado", e.traza["sha256_aprobado"])
    # Cambiar exige abrir una revisión nueva: vuelve a borrador y la aprobada queda en su dictamen.
    nueva = await bib.abrir_nueva_revision(s, e.id, u["redactor"], doc_id)
    reabierto = await bib.obtener_documento(s, e.id, u["redactor"], doc_id)
    assert reabierto.estado == "borrador" and reabierto.revision == nueva > int(e.traza["revision_documento"])
    dictamen = await bib.obtener_revision(s, e.id, e.traza["revision"])
    assert (dictamen.estado, dictamen.sha256) == ("aprobada", e.traza["sha256_aprobado"])


@pytest.mark.asyncio
async def test_db_cero_accesos_cruzados_entre_las_tres_empresas(mundo):
    trazas = [await _recorrido(mundo, e) for e in mundo.empresas.values()]
    s = mundo.sesion
    for propia in trazas:
        for ajena in (t for t in trazas if t is not propia):
            u = propia.usuarios
            with pytest.raises(ErrorNegocio) as error:
                await bib.obtener_documento(s, propia.id, u["redactor"], ajena.traza["documento"])
            assert error.value.status_code == 404
            with pytest.raises(ErrorNegocio):
                await bib.crear_enlace(s, propia.id, u["asignador"], propia.traza["documento"], bib.CrearEnlace(
                    accion_id=ajena.traza["accion"], revision=1), roadmap.obtener_accion_para_enlace)
            with pytest.raises(ErrorNegocio) as error:
                await bib.registrar_evidencia(s, propia.id, u["redactor"], ajena.traza["accion"], bib.RegistrarEvidencia(
                    titulo="Intento cruzado", version="1", sha256=HASH, clasificacion="interna",
                    permisos=["coordinador"], fecha="2026-11-03"), roadmap.obtener_accion_para_enlace)
            assert error.value.code == "BIB_VERIF_ACCION_AJENA"
        # Por RLS, cada empresa solo ve sus filas en todas las tablas del recorrido.
        await s.execute(text("SELECT set_config('app.current_tenant_id', :t, true)"), {"t": propia.id})
        for tabla, consulta in AJENOS_POR_TABLA.items():
            assert (await s.execute(text(consulta), {"t": propia.id})).scalar() == 0, tabla
    # Defensa en profundidad: con un rol que omite la RLS, el servicio sigue filtrando por empresa él solo.
    await mundo.conexion.execute(text("RESET ROLE"))
    if not (await mundo.conexion.execute(text(
            "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname=current_user"))).scalar():
        pytest.skip("El rol de pruebas no omite la RLS; la defensa en profundidad no es observable aquí")
    async with AsyncSession(bind=mundo.conexion, expire_on_commit=False, join_transaction_mode="create_savepoint") as libre:
        a, b = trazas[0], trazas[1]
        with pytest.raises(ErrorNegocio) as error:
            await bib.obtener_documento(libre, a.id, a.usuarios["redactor"], b.traza["documento"])
        assert error.value.status_code == 404
    await mundo.conexion.execute(text("SET LOCAL ROLE lopdp_app"))


# ---- API: la empresa sale de la sesión del servidor; cambiar el ID en la URL no da acceso

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
async def test_api_documento_y_expediente_de_otra_empresa_no_se_ven(api, mundo):
    a = await _recorrido(mundo, mundo.empresas["microempresa"])
    b = await _recorrido(mundo, mundo.empresas["entidad_publica"])
    propio = {"x-test-tenant": a.id, "x-test-user": a.usuarios["redactor"], "x-test-role": "implementador"}
    assert (await api.get(f"/api/v1/biblioteca/documentos/{a.traza['documento']}", headers=propio)).status_code == 200
    ajeno = await api.get(f"/api/v1/biblioteca/documentos/{b.traza['documento']}", headers=propio)
    assert ajeno.status_code == 404
    expediente = await api.get(f"/api/v1/biblioteca/verificaciones/acciones/{b.traza['accion']}", headers=propio)
    assert expediente.status_code == 422 and expediente.json()["code"] == "BIB_VERIF_ACCION_AJENA"
