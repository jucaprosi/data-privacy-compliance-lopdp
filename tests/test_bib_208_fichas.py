# ¤adpa ¤rbac-tenant ¤arbitro
# ¤¤qa-engineer
"""Árbitro BIB-208: cobertura de captura/salida de las ocho fichas iniciales.

Cada ficha pasa caso normal, información incompleta, condición especial y regeneración. PLA-01 se exporta
del plan existente y RAT-01 se ancla en el RAT: ninguna crea registros. La lectura real de las compuertas
de Roadmap y RAT con el rol `lopdp_app` se acredita solo con el arnés local (ARNES_BASE=postgresql_local)
o con una URL local; una URL remota no la habilita y sin ella se omite.

Mutación decisiva (ejecutada): en ``features/biblioteca/plantillas/exportaciones.py``, ``exportar_plan``,
antes de ``origen = [...]``, añadir ``filas = filas + [{**filas[0], "accion_id": str(uuid4())}]`` (crear
otra acción al exportar). Fallan ``test_pla_conserva_ids_y_conteo`` y otras tres pruebas PLA/API por
``BIB_FICHA_INICIAL_EXPORTACION_ALTERADA``; restaurado, pasan.
"""
import importlib
import os
from urllib.parse import urlparse
from datetime import date, timedelta
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
from app_core.db.session import fijar_contexto_rls, get_session
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.plantillas import exportaciones as exp
from features.biblioteca.plantillas.captura import ContextoServidor, EntradaFicha, evaluar_tabla
from features.biblioteca.plantillas.mapas import CODIGOS, POR_SECCIONES, TABULARES, mapa
from features.biblioteca.plantillas.secciones import evaluar_secciones

PRODUCCION, COMPARTIDA = "ep-late-hall-b50bpbk5", "ep-soft-darkness-b5z454vp"
CTX = ContextoServidor(organizacion_id="org-a", actor_id="u-1", fecha=date(2026, 11, 4))
T1, T2 = str(uuid4()), str(uuid4())
TRATAMIENTOS = frozenset({T1, T2})


def _fila_completa(codigo: str, **cambios) -> dict:
    """Fila con todos los campos editables llenos con valores válidos del mapa."""
    fila = {}
    for c in mapa(codigo).campos:
        if c.requisito == "D":
            continue
        if c.valores:
            fila[c.clave] = c.valores[0]
        elif c.tipo == "date":
            fila[c.clave] = "2026-10-30"
        elif c.clave == "tratamiento_ids":
            fila[c.clave] = [T1]
        elif c.clave == "tratamiento_id":
            fila[c.clave] = T1
        elif c.tipo == "reference_list":
            fila[c.clave] = ["ref-1"]
        else:
            fila[c.clave] = f"Valor de {c.clave}"
    fila.update(cambios)
    return fila


def _tabla(codigo: str, filas: list[dict], **extra):
    return evaluar_tabla(mapa(codigo), EntradaFicha(filas=filas, **extra), TRATAMIENTOS)


# ------------------------------------------------------------------------------------- contrato y mapas

def test_ocho_mapas_con_su_modo():
    assert set(CODIGOS) == {"INV-01", "INV-02", "RAT-01", "LEG-01", "PLA-01", "EIPD-00", "AVI-01", "PRO-01"}
    assert all(mapa(c).modo == "tabla" for c in TABULARES)
    assert all(mapa(c).modo == "secciones" for c in POR_SECCIONES)
    for c in TABULARES:
        assert all(f.hoja == "Registro" and f.primera_fila == 6 and f.columna for f in mapa(c).campos)
    for c in POR_SECCIONES:
        assert all(f.seccion for f in mapa(c).campos) and len(mapa(c).secciones) >= 3


def test_compuerta_router_y_errores():
    from api.routers import biblioteca_fichas_iniciales as router
    importlib.reload(router)
    assert router.AUTO_REGISTRO is True
    assert {(m, r.path) for r in router.router.routes for m in r.methods} == {
        ("GET", "/biblioteca/fichas-iniciales"), ("GET", "/biblioteca/fichas-iniciales/{codigo}"),
        ("POST", "/biblioteca/fichas-iniciales/{codigo}/evaluar"),
        ("GET", "/biblioteca/fichas-iniciales/PLA-01/instantanea/{roadmap_id}")}
    for nombre in ("EntradaFicha", "evaluar_ficha_inicial", "instantanea_plan", "listar_fichas_iniciales"):
        assert nombre in bib.__all__ and hasattr(bib, nombre)
    assert CATALOGO_ERRORES["BIB_FICHA_INICIAL_DESCONOCIDA"].status_code == 404
    assert CATALOGO_ERRORES["BIB_FICHA_INICIAL_EXPORTACION_ALTERADA"].status_code == 500


# ------------------------------------------------------------------- tablas: INV-01, INV-02, LEG-01

@pytest.mark.parametrize("codigo", ["INV-01", "INV-02", "LEG-01"])
def test_tabla_normal_incompleta_condicional_y_regeneracion(codigo):
    normal = _tabla(codigo, [_fila_completa(codigo), _fila_completa(codigo)])
    assert normal.aceptada and normal.version == 1 and len(normal.ids) == 2
    assert max(c.fila for c in normal.celdas) == 7, "la salida llega a la última fila real y no más"
    instrucciones = {c.regla for c in mapa(codigo).campos} | {c.etiqueta for c in mapa(codigo).campos}
    assert not any(c.valor in instrucciones for c in normal.celdas), "sin instrucciones ni etiquetas en la salida"

    obligatorio = next(c.clave for c in mapa(codigo).campos if c.requisito == "O" and c.tipo == "string")
    incompleta = _tabla(codigo, [_fila_completa(codigo, **{obligatorio: ""})])
    assert not incompleta.aceptada and [(p.campo, p.fila) for p in incompleta.pendientes] == [(obligatorio, 1)]

    condicional = next(c.clave for c in mapa(codigo).campos if c.requisito == "C")
    assert _tabla(codigo, [_fila_completa(codigo, **{condicional: "No aplica: no hay terceros"})]).aceptada
    sin_motivo = _tabla(codigo, [_fila_completa(codigo, **{condicional: "No aplica"})])
    assert not sin_motivo.aceptada and sin_motivo.pendientes[0].campo == condicional

    id_campo = mapa(codigo).campos[0].clave
    regenerada = _tabla(codigo, [_fila_completa(codigo, **{id_campo: i}) for i in normal.ids], version_anterior=1)
    assert regenerada.version == 2 and regenerada.ids == normal.ids


def test_tabla_rechaza_campo_servidor_desconocido_y_fecha_texto():
    with pytest.raises(ErrorNegocio) as error:
        _tabla("INV-01", [_fila_completa("INV-01", inventario_id="manual-1")])
    assert error.value.code == "BIB_FICHA_INICIAL_CAMPO_SERVIDOR"
    with pytest.raises(ErrorNegocio) as error:
        _tabla("INV-01", [_fila_completa("INV-01", columna_inventada="x")])
    assert error.value.code == "BIB_FICHA_INICIAL_CAMPO_DESCONOCIDO"
    for fecha in ("30/10/2026", "0", "2026-02-30"):
        r = _tabla("INV-01", [_fila_completa("INV-01", fecha_de_revision=fecha)])
        assert not r.aceptada and r.pendientes[0].campo == "fecha_de_revision"


def test_referencias_a_tratamientos_de_otra_organizacion_quedan_pendientes():
    r = _tabla("INV-02", [_fila_completa("INV-02", tratamiento_ids=[T1, "ajeno"])])
    assert not r.aceptada and r.pendientes[0].campo == "tratamiento_ids"
    sin_rat = evaluar_tabla(mapa("INV-01"), EntradaFicha(filas=[_fila_completa("INV-01")]), None)
    assert not sin_rat.aceptada, "sin poder verificar el RAT no se declara aceptada"


def test_pla_no_se_captura():
    with pytest.raises(ErrorNegocio) as error:
        _tabla("PLA-01", [{}])
    assert error.value.code == "BIB_FICHA_INICIAL_SOLO_LECTURA"


# ------------------------------------------------------------------------------------------- RAT-01

ACTIVIDAD = {"id": T1, "nombre": "Nómina", "finalidad": "Pago de remuneraciones", "base_legal": "OBLIGACION_LEGAL",
             "plazo_conservacion": "7 años desde el cese", "categorias_datos": ["IDENTIFICATIVOS", "FINANCIEROS"]}


def _rat(filas, **extra):
    return exp.proponer_rat(mapa("RAT-01"), EntradaFicha(filas=filas, **extra), [ACTIVIDAD])


def test_rat_conserva_tratamiento_y_no_crea_otro():
    fila = _fila_completa("RAT-01", tratamiento_id=T1, finalidades="Otra finalidad propuesta")
    resultado = _rat([fila])
    assert resultado.ficha.ids == [T1] and resultado.escrituras_rat == 0
    assert any(c.clave == "finalidades" and c.valor == "Pago de remuneraciones" for c in resultado.ficha.celdas)
    assert [(p.campo, p.valor_propuesto) for p in resultado.propuestas if p.campo == "finalidades"] == [
        ("finalidades", "Otra finalidad propuesta")]
    nueva = _rat([_fila_completa("RAT-01")])
    assert nueva.ficha.ids == [] and not nueva.ficha.aceptada, "una actividad nueva no se crea por Biblioteca"
    assert nueva.ficha.pendientes[0].campo == "tratamiento_id"


def test_rat_normal_incompleto_condicional_y_regeneracion():
    base = _fila_completa("RAT-01", tratamiento_id=T1)
    assert _rat([base]).ficha.aceptada
    assert not _rat([{**base, "titulares": ""}]).ficha.aceptada
    sin_dpd = _rat([{**base, "dpd_y_contacto_si_existe": "No aplica: la organización no designa DPD"}])
    assert sin_dpd.ficha.aceptada
    assert not any(c.clave == "dpd_y_contacto_si_existe" and c.valor == "" for c in sin_dpd.ficha.celdas)
    regenerada = _rat([base], version_anterior=3)
    assert regenerada.ficha.version == 4 and regenerada.ficha.ids == [T1]


# ------------------------------------------------------------------------------------------- PLA-01

CORTE = date(2026, 11, 4)


def _accion(estado="pendiente", prioridad="alta", fin=CORTE + timedelta(days=10), evidencias=(), **extra):
    return {"id": str(uuid4()), "title": "Actualizar aviso", "status": estado, "priority": prioridad, "end_date": fin,
            "owner": "Coordinación", "control_ref": "P7", "hallazgo_id": "h-1", "deliverable": "Aviso aprobado",
            "evidencias_aprobadas": list(evidencias), **extra}


def test_pla_conserva_ids_y_conteo():
    acciones = [_accion(), _accion(estado="en_progreso"), _accion(estado="completada", evidencias=["e-1"])]
    foto = exp.exportar_plan(mapa("PLA-01"), acciones, CORTE)
    assert foto.ids == [a["id"] for a in acciones] and foto.conteo == 3 and len(foto.filas) == 3
    assert foto.fecha_corte == CORTE and foto.instantanea_id
    assert {c.fila for c in foto.celdas} == {6, 7, 8}
    assert [f["control_de_cierre"] for f in foto.filas] == ["Abierta", "Abierta", "Cierre con evidencia"]
    assert [f["alerta_temporal"] for f in foto.filas] == ["En plazo", "En plazo", "Cerrada"]
    assert not foto.aceptada, "tratamiento y eficacia no están en el plan canónico: pendientes explícitos"
    assert {p.campo for p in foto.pendientes} == {"tratamiento_id", "requiere_eficacia"}


def test_pla_estados_sin_equivalencia_cierre_bloqueado_y_fecha_invalida():
    acciones = [_accion(prioridad="critica"), _accion(estado="bloqueada"), _accion(estado="completada"),
                _accion(fin=None), _accion(fin=CORTE - timedelta(days=1))]
    foto = exp.exportar_plan(mapa("PLA-01"), acciones, CORTE)
    assert foto.filas[0]["prioridad"] == exp.SIN_EQUIVALENCIA and foto.filas[1]["estado_declarado"] == exp.SIN_EQUIVALENCIA
    assert foto.filas[2]["control_de_cierre"] == "Cierre bloqueado"
    assert foto.filas[3]["alerta_temporal"] == "Fecha inválida" and foto.filas[4]["alerta_temporal"] == "Vencida"
    assert {(p.campo, p.fila) for p in foto.pendientes} >= {("prioridad", 1), ("estado_declarado", 2), ("fecha_objetivo", 4)}


def test_pla_regenerar_tras_cambio_emite_otra_instantanea():
    acciones = [_accion()]
    primera = exp.exportar_plan(mapa("PLA-01"), acciones, CORTE)
    segunda = exp.exportar_plan(mapa("PLA-01"), [{**acciones[0], "status": "en_progreso"}], CORTE)
    assert primera.instantanea_id != segunda.instantanea_id and primera.ids == segunda.ids
    assert primera.filas[0]["estado_declarado"] == "Pendiente", "la anterior no cambia"


def test_pla_detecta_exportacion_alterada():
    acciones = [_accion(), _accion()]
    with pytest.raises(ErrorNegocio) as error:
        exp.exportar_plan(mapa("PLA-01"), acciones + [acciones[0]], CORTE)
    assert error.value.code == "BIB_FICHA_INICIAL_EXPORTACION_ALTERADA"


# ------------------------------------------------------------------------------------------- AVI-01

def _valores(codigo: str, **cambios) -> dict:
    v = {k: x for k, x in _fila_completa(codigo).items()}
    v.update(cambios)
    return {k: x for k, x in v.items() if x is not None}


def _finalidad(base="OBLIGACION_LEGAL", n=1):
    return {"purpose_id": f"f{n}", "description": f"Finalidad {n}", "legal_basis_id": base,
            "legal_basis_rationale": "Art. 7", "data_delivery_requirement": "Obligatoria", "delivery_consequences": "x"}


def _avi(finalidades, condiciones=None, **valores):
    base = _valores("AVI-01")
    for clave in ("finalidad_1", "base_1_y_sustento", "obligatoriedad_y_consecuencias_1", "finalidad_2_si_aplica",
                  "base_2_y_sustento", "opcionalidad_y_consecuencias_2"):
        base.pop(clave)
    base.update(valores)
    cond = {"leg_validada": True, "tiene_dpd": True, "recoleccion_indirecta": False}
    cond.update(condiciones or {})
    return evaluar_secciones(mapa("AVI-01"), EntradaFicha(valores={k: v for k, v in base.items() if v is not None},
                                                          colecciones={"purposes": finalidades}, condiciones=cond),
                             CTX, TRATAMIENTOS)


def test_avi_tres_finalidades_sin_tope_de_dos():
    r = _avi([_finalidad(n=1), _finalidad("CONSENTIMIENTO", 2), _finalidad("INTERES_LEGITIMO", 3)])
    assert r.aceptada, r.pendientes
    assert sorted({b.indice for b in r.bloques if b.seccion == "Finalidades repetibles" and b.indice}) == [1, 2, 3]
    assert r.version == 1 and any(b.clave == "elabora" and b.valor == "u-1" for b in r.bloques)


def test_avi_sin_dpd_y_sin_consentimiento_omite_bloques_enteros():
    r = _avi([_finalidad()], {"tiene_dpd": False}, **{c: None for c in ("canal_retiro", "efectos_retiro")})
    assert r.aceptada, r.pendientes
    assert "Delegado de protección de datos" in r.omitidos and "Retiro del consentimiento" in r.omitidos
    assert not any(b.clave in ("nombre_dpd", "correo_dpd", "canal_retiro") for b in r.bloques)


def test_avi_incompleto_leg_no_validada_e_indirecta():
    assert not _avi([]).aceptada
    sin_leg = _avi([_finalidad()], {"leg_validada": False})
    assert not sin_leg.aceptada and sin_leg.pendientes[0].campo == "condiciones.leg_validada"
    indirecta = _avi([_finalidad()], {"recoleccion_indirecta": True}, fuente_y_contexto="")
    assert [p.campo for p in indirecta.pendientes] == ["fuente_y_contexto"]
    regenerada = evaluar_secciones(mapa("AVI-01"), EntradaFicha(version_anterior=2), CTX, TRATAMIENTOS)
    assert regenerada.version == 3 and not regenerada.aceptada


# ------------------------------------------------------------------------------------------ EIPD-00

def _criterio(cid, respuesta, evidencia=("ev-1",)):
    return {"criterion_id": cid, "answer": respuesta, "evidence_ids": list(evidencia),
            "legal_source_version_id": "lopdp-2021", "rationale": "Motivo"}


def _eipd(criterios, version_anterior=None, **valores):
    base = _valores("EIPD-00")
    base.pop("si_no"); base.pop("si_no_desconocido")
    base.update(valores)
    return evaluar_secciones(mapa("EIPD-00"), EntradaFicha(valores=base, colecciones={"criteria": criterios},
                                                           version_anterior=version_anterior), CTX, TRATAMIENTOS)


def test_eipd_disparador_confirmado_sostiene_requiere():
    r = _eipd([_criterio("biometria", "Sí"), _criterio("gran_escala", "No")], resultado_eipd="Requiere EIPD")
    assert r.recomendacion == "Requiere EIPD" and r.aceptada, r.pendientes
    contrario = _eipd([_criterio("biometria", "Sí")], resultado_eipd="No se identifica obligación con la evidencia actual",
                      evento_revision="Cambio de proveedor")
    assert not contrario.aceptada and contrario.pendientes[0].campo == "resultado_eipd"


def test_eipd_desconocido_no_concluye_negativo_y_exige_faltantes():
    r = _eipd([_criterio("gran_escala", "Desconocido", ())], resultado_eipd="Información insuficiente",
              datos_faltantes="", responsable_obtenerlos="")
    assert r.recomendacion == "Información insuficiente"
    assert {p.campo for p in r.pendientes} == {"datos_faltantes", "responsable_obtenerlos"}
    assert not _eipd([_criterio("x", "No", ())], resultado_eipd="Requiere EIPD").aceptada, "respuesta firme sin evidencia"
    assert _eipd([_criterio("x", "No")], version_anterior=1, resultado_eipd="Requiere EIPD").version == 2


# ------------------------------------------------------------------------------------------- PRO-01

FUNCIONES = ("recepción", "búsqueda", "ejecución", "revisión", "aprobación")


def _politica(validada=True):
    p = {"right_code": "acceso", "start_event": "Recepción completa", "legal_source_version_id": "lopdp-art-13",
         "duration": "15", "count_unit": "días", "validated_by": "dpd-1", "validated_at": "2026-10-01"}
    return p if validada else {**p, "validated_at": None}


def _pro(politicas, roles=FUNCIONES, version_anterior=None, **valores):
    base = _valores("PRO-01")
    for clave in ("derecho", "articulo", "evento_inicial", "plazo_unidad_calendario", "motivo_y_fundamento_o_no_aplica",
                  "solicitud_id", "fecha_hora_recepcion", "fecha_limite_validada"):
        base.pop(clave)
    base.update(valores)
    return evaluar_secciones(mapa("PRO-01"), EntradaFicha(
        valores=base, version_anterior=version_anterior, colecciones={
            "right_policies": politicas, "operational_roles": [{"function_code": f, "role_id": "r"} for f in roles]}),
        CTX, TRATAMIENTOS)


def test_pro_sin_solicitudes_recibidas_y_anexo_de_campos():
    r = _pro([_politica()])
    assert r.aceptada, r.pendientes
    assert r.anexo == ["solicitud_id", "fecha_hora_recepcion", "fecha_limite_validada"]
    assert not any(b.clave in r.anexo for b in r.bloques)
    with pytest.raises(ErrorNegocio) as error:
        _pro([_politica()], solicitud_id="SOL-123")
    assert error.value.code == "BIB_FICHA_INICIAL_CASO_INDIVIDUAL"


def test_pro_regla_no_validada_y_rol_faltante_impiden_finalizar():
    r = _pro([_politica(validada=False)], roles=FUNCIONES[:4])
    motivos = [p.motivo for p in r.pendientes]
    assert not r.aceptada and any("Configuración pendiente" in m for m in motivos) and any("aprobación" in m for m in motivos)
    assert _pro([_politica()], version_anterior=1).version == 2


# --------------------------------------------------------------------------- API (sin BD, puertos falsos)

@pytest_asyncio.fixture
async def api(monkeypatch):
    from main import app
    from features.rat import rat_service
    from features.roadmap import roadmap_service

    async def sesion():
        yield None

    async def contexto(request: Request):
        return {"user_id": "u-1", "tenant_id": request.headers["x-test-tenant"], "role": request.headers["x-test-rol"]}

    async def actividades(_s, tenant_id):
        return [ACTIVIDAD] if tenant_id == "org-a" else []

    async def acciones(_s, tenant_id, roadmap_id):
        return [_accion(id="acc-1")] if tenant_id == "org-a" and roadmap_id == "plan-a" else []

    monkeypatch.setattr(rat_service, "actividades_para_biblioteca", actividades)
    monkeypatch.setattr(roadmap_service, "acciones_para_instantanea", acciones)
    monkeypatch.setitem(app.dependency_overrides, get_session, sesion)
    monkeypatch.setitem(app.dependency_overrides, get_context, contexto)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://prueba") as cliente:
        yield cliente


@pytest.mark.asyncio
async def test_api_mapas_evaluacion_e_instantanea_por_tenant(api):
    cab = {"x-test-tenant": "org-a", "x-test-rol": "coordinador"}
    mapas = (await api.get("/api/v1/biblioteca/fichas-iniciales", headers=cab)).json()
    assert [m["codigo"] for m in mapas] == list(CODIGOS)
    assert (await api.get("/api/v1/biblioteca/fichas-iniciales/XYZ-99", headers=cab)).status_code == 404
    fila = _fila_completa("RAT-01", tratamiento_id=T1)
    ok = await api.post("/api/v1/biblioteca/fichas-iniciales/RAT-01/evaluar", headers=cab, json={"filas": [fila]})
    assert ok.status_code == 200 and ok.json()["ficha"]["ids"] == [T1]
    ajena = await api.post("/api/v1/biblioteca/fichas-iniciales/RAT-01/evaluar",
                           headers={**cab, "x-test-tenant": "org-b"}, json={"filas": [fila]})
    assert ajena.json()["ficha"]["aceptada"] is False, "el tenant sale de la sesión, no del ID enviado"
    foto = await api.get("/api/v1/biblioteca/fichas-iniciales/PLA-01/instantanea/plan-a?fecha_corte=2026-11-04", headers=cab)
    assert foto.status_code == 200 and foto.json()["ids"] == ["acc-1"]
    otra = await api.get("/api/v1/biblioteca/fichas-iniciales/PLA-01/instantanea/plan-a",
                         headers={**cab, "x-test-tenant": "org-b"})
    assert otra.json()["conteo"] == 0
    mala = await api.get("/api/v1/biblioteca/fichas-iniciales/PLA-01/instantanea/plan-a?fecha_corte=0", headers=cab)
    assert mala.status_code == 422
    lector = await api.post("/api/v1/biblioteca/fichas-iniciales/INV-01/evaluar",
                            headers={**cab, "x-test-rol": "auditor"}, json={"filas": []})
    assert lector.status_code == 403


# ---------------------------------------------------------- compuertas reales con lopdp_app (arnés local)

def _url_de_pruebas() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if PRODUCCION in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    if not url or not (os.environ.get("ARNES_BASE") == "postgresql_local" or (urlparse(url).hostname or "") in ("127.0.0.1", "localhost", "::1")):
        pytest.skip("Persistencia pendiente: falta base local (arnés PostgreSQL 16 en 127.0.0.1 o ARNES_BASE=postgresql_local); una URL remota no habilita pruebas con base")
    if COMPARTIDA in url.lower():
        pytest.fail("La rama test compartida no es una rama propia; no se abrió conexión", pytrace=False)
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


async def _x(conexion, sql: str, **p):
    await conexion.execute(text(sql), p)


@pytest.mark.asyncio
async def test_db_instantanea_lee_solo_el_plan_del_tenant_sin_escribir():
    from features.roadmap import roadmap_service
    engine = create_async_engine(_url_de_pruebas(), echo=False, hide_parameters=True)
    async with engine.connect() as conexion:
        transaccion = await conexion.begin()
        try:
            planes, tareas = {}, {}
            for _ in range(2):
                tid = "bib208-org-" + uuid4().hex
                await _x(conexion, "INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) "
                         "VALUES (:id,'Org sintética','Org sintética S.A.',:ruc)", id=tid, ruc=str(uuid4().int)[:13])
                hoja, ola = str(uuid4()), str(uuid4())
                await _x(conexion, "INSERT INTO roadmaps(id, tenant_id, variables_json) VALUES (:r,:t,'{}')", r=hoja, t=tid)
                await _x(conexion, "INSERT INTO roadmap_waves(id, roadmap_id, tenant_id, name) VALUES (:w,:r,:t,'Ola')",
                         w=ola, r=hoja, t=tid)
                tareas[tid] = [str(uuid4()) for _ in range(3)]
                for k, (estado, prioridad) in zip(tareas[tid], (("pendiente", "alta"), ("bloqueada", "critica"),
                                                                ("completada", "media"))):
                    await _x(conexion, "INSERT INTO roadmap_tasks(id, wave_id, tenant_id, control_ref, dimension, title, "
                             "priority, status, end_date) VALUES (:k,:w,:t,'P7','D01','Acción',:p,:s,:f)",
                             k=k, w=ola, t=tid, p=prioridad, s=estado, f=date(2026, 12, 1))
                await _x(conexion, "INSERT INTO task_evidence(id, task_id, tenant_id, r2_key, validation_status) "
                         "VALUES (:id,:k,:t,'sintetico/acta.pdf','approved')", id=str(uuid4()), k=tareas[tid][2], t=tid)
                planes[tid] = hoja
            ta, tb = list(planes)
            await conexion.execute(text("SET LOCAL ROLE lopdp_app"))
            async with AsyncSession(bind=conexion, expire_on_commit=False,
                                    join_transaction_mode="create_savepoint") as sesion:
                await fijar_contexto_rls(sesion, ta, "u-1")
                antes = (await sesion.execute(text("SELECT count(*) FROM roadmap_tasks"))).scalar()
                foto = await bib.instantanea_plan(sesion, ta, planes[ta], "2026-11-04",
                                                  roadmap_service.acciones_para_instantanea)
                despues = (await sesion.execute(text("SELECT count(*) FROM roadmap_tasks"))).scalar()
                assert sorted(foto.ids) == sorted(tareas[ta]) and foto.conteo == 3 and antes == despues
                cerrada = next(f for f in foto.filas if f["accion_id"] == tareas[ta][2])
                assert cerrada["control_de_cierre"] == "Cierre con evidencia"
                ajena = await bib.instantanea_plan(sesion, ta, planes[tb], "2026-11-04",
                                                   roadmap_service.acciones_para_instantanea)
                assert ajena.conteo == 0, "el plan de otra organización no se exporta"
        except DBAPIError:
            pytest.fail("Fallo DB BIB-208 (detalles de conexión omitidos); comprobar migraciones y permisos", pytrace=False)
        finally:
            await transaccion.rollback()
    await engine.dispose()
