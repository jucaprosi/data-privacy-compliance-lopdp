# ¤adpa ¤rbac-tenant
# ¤¤qa-engineer
"""Árbitro BIB-204: motor determinista de aplicabilidad de plantillas y recomendaciones explicables.

Verifica:
1. Triestado determinista: Aplica / No aplica / Información insuficiente con fuentes, hechos y versiones.
2. Invariante: Dato desconocido NUNCA se convierte en "No aplica" (prueba de mutación).
3. Modificación humana conserva resultado original, motivo, evidencia, autor y fecha.
4. Exclusión de obligación confirmada exige revisión jurídica (403 con BIB_EXCLUSION_EXIGE_JURIDICO).
5. Migración de una sola cabeza con RLS forzado y permisos mínimos.
6. Router expuesto con AUTO_REGISTRO = True y RBAC por tenant.
"""
import importlib.util
import os
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from alembic.config import Config
from alembic.script import ScriptDirectory
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from api.errores import ErrorNegocio, error_negocio_handler
from api.rbac import get_context, require_role
from api.routers import biblioteca_aplicabilidad
from app_core.db.session import get_session
from app_core.errors import CATALOGO_ERRORES
from features.biblioteca import biblioteca_service as bib
from features.biblioteca.domain.reglas import (
    HechosOrganizacion,
    ResultadoAplicabilidad,
    evaluar_ap01_datos_personales,
    evaluar_ap02_trabajadores_100,
    evaluar_ap03_gran_escala,
    evaluar_ap04_interes_legitimo,
    evaluar_ap05_datos_sensibles,
    evaluar_ap06_alto_riesgo_eipd,
    evaluar_ap07_biometria,
    evaluar_ap08_encargados,
    evaluar_ap09_transferencias,
    evaluar_ap10_sector_publico,
    evaluar_ap11_consentimiento,
    evaluar_ap13_ia,
)
from features.biblioteca.services.aplicabilidad import (
    FuentesAplicabilidad,
    _determinar_reglas_plantilla,
    evaluar_aplicabilidad_organizacion,
    extraer_hechos,
    registrar_modificacion_aplicabilidad,
)

ROOT = Path(__file__).resolve().parents[1]
MIGRACION = next((ROOT / "alembic/versions").glob("*_biblioteca_reglas.py"), None)


# ----------------------------------------------------------------------------- 1. Invariante y Triestado

def test_codigos_error_registrados_en_catalogo():
    """Verifica que los códigos de BIB-204 están en el catálogo común de errores."""
    for codigo in ("BIB_EXCLUSION_EXIGE_JURIDICO", "BIB_MODIFICACION_INVALIDA", "BIB_REGLA_NO_ENCONTRADA"):
        assert codigo in CATALOGO_ERRORES
        assert CATALOGO_ERRORES[codigo].status_code in (403, 404, 422)


def test_dato_desconocido_mantiene_informacion_insuficiente_prueba_de_mutacion():
    """Invariante hard: un dato desconocido o ausente NUNCA se convierte en 'No aplica'."""
    hechos_vacio = HechosOrganizacion(
        tenant_id="test-vacio",
        tamano=None,
        num_trabajadores=None,
        sector=None,
        rat_cargado=False,
        actividades_rat=None,
        mtge_cargado=False,
        tiene_gran_escala=None,
    )

    evaluaciones = [
        evaluar_ap01_datos_personales(hechos_vacio),
        evaluar_ap02_trabajadores_100(hechos_vacio),
        evaluar_ap03_gran_escala(hechos_vacio),
        evaluar_ap04_interes_legitimo(hechos_vacio),
        evaluar_ap05_datos_sensibles(hechos_vacio),
        evaluar_ap06_alto_riesgo_eipd(hechos_vacio),
        evaluar_ap07_biometria(hechos_vacio),
        evaluar_ap08_encargados(hechos_vacio),
        evaluar_ap09_transferencias(hechos_vacio),
        evaluar_ap10_sector_publico(hechos_vacio),
        evaluar_ap11_consentimiento(hechos_vacio),
        evaluar_ap13_ia(hechos_vacio),
    ]

    for ev in evaluaciones:
        assert ev.resultado == ResultadoAplicabilidad.INFORMACION_INSUFICIENTE, (
            f"Fallo de invariante en regla {ev.regla_id}: devolvió {ev.resultado} en vez de 'Información insuficiente'"
        )
        assert len(ev.hechos_faltantes) > 0, f"Regla {ev.regla_id} no reportó hechos faltantes"
        assert ev.fuente_normativa != "", f"Regla {ev.regla_id} sin fuente normativa"
        assert ev.version_regla != "", f"Regla {ev.regla_id} sin versión de regla"

    # También en plantilla concreta RAT-01 con datos desconocidos
    res_rat, es_ob, reglas_rat, motivo = _determinar_reglas_plantilla("RAT-01", hechos_vacio)
    assert res_rat == ResultadoAplicabilidad.INFORMACION_INSUFICIENTE
    assert not es_ob


def test_rat_01_evaluacion_determinista():
    """RAT-01 aplica como obligación legal si trabajadores >= 100 o gran escala; si no, No aplica."""
    # Caso 1: Trabajadores >= 100
    hechos_100 = HechosOrganizacion(
        tenant_id="t1",
        num_trabajadores=120,
        rat_cargado=True,
        actividades_rat=[],
        mtge_cargado=True,
        tiene_gran_escala=False,
    )
    res, es_ob, reglas, _ = _determinar_reglas_plantilla("RAT-01", hechos_100)
    assert res == ResultadoAplicabilidad.APLICA
    assert es_ob is True

    # Caso 2: Gran escala
    hechos_escala = HechosOrganizacion(
        tenant_id="t2",
        tamano="micro",
        num_trabajadores=5,
        rat_cargado=True,
        actividades_rat=[{"es_gran_escala": True}],
        mtge_cargado=True,
        tiene_gran_escala=True,
        total_gran_escala=1,
    )
    res2, es_ob2, _, _ = _determinar_reglas_plantilla("RAT-01", hechos_escala)
    assert res2 == ResultadoAplicabilidad.APLICA
    assert es_ob2 is True

    # Caso 3: Microempresa sin gran escala conocida y comprobada
    hechos_micro = HechosOrganizacion(
        tenant_id="t3",
        tamano="micro",
        num_trabajadores=8,
        rat_cargado=True,
        actividades_rat=[{"nombre": "Facturacion", "es_gran_escala": False}],
        mtge_cargado=True,
        tiene_gran_escala=False,
        total_gran_escala=0,
    )
    res3, es_ob3, _, _ = _determinar_reglas_plantilla("RAT-01", hechos_micro)
    assert res3 == ResultadoAplicabilidad.NO_APLICA
    assert es_ob3 is False


def test_lia_01_interes_legitimo():
    """LIA-01 aplica exclusivamente cuando existen tratamientos fundados en interés legítimo."""
    hechos_con_lia = HechosOrganizacion(
        tenant_id="t",
        rat_cargado=True,
        actividades_rat=[{"nombre": "Marketing directo", "base_legal": "INTERES_LEGITIMO"}],
    )
    res, _, reglas, _ = _determinar_reglas_plantilla("LIA-01", hechos_con_lia)
    assert res == ResultadoAplicabilidad.APLICA

    hechos_sin_lia = HechosOrganizacion(
        tenant_id="t",
        rat_cargado=True,
        actividades_rat=[{"nombre": "Nómina", "base_legal": "CUMPLIMIENTO_CONTRATO"}],
    )
    res2, _, _, _ = _determinar_reglas_plantilla("LIA-01", hechos_sin_lia)
    assert res2 == ResultadoAplicabilidad.NO_APLICA


def test_var_bio_y_eipd_01_biometria():
    """VAR-BIO y EIPD-01 activan cuando se detecta biometría."""
    hechos_bio = HechosOrganizacion(
        tenant_id="t",
        rat_cargado=True,
        actividades_rat=[{"nombre": "Control de acceso", "categorias_datos": ["huella dactilar"]}],
    )
    res_bio, _, _, _ = _determinar_reglas_plantilla("VAR-BIO", hechos_bio)
    assert res_bio == ResultadoAplicabilidad.APLICA

    res_eipd, _, _, _ = _determinar_reglas_plantilla("EIPD-01", hechos_bio)
    assert res_eipd == ResultadoAplicabilidad.APLICA


# ----------------------------------------------------------------------------- 2. Perfiles Sintéticos

def test_perfil_pf01_microempresa_servicios():
    """PF-01: Microempresa privada 8 trabajadores, sin biometría, nube extranjera, encargados nómina."""
    hechos = HechosOrganizacion(
        tenant_id="pf-01",
        tamano="micro",
        num_trabajadores=8,
        sector="privado",
        rat_cargado=True,
        actividades_rat=[
            {"nombre": "Clientes", "encargados": ["Nube AWS"], "transferencia_internacional": True},
            {"nombre": "Nómina", "encargados": ["Contador externo"], "transferencia_internacional": False},
        ],
        mtge_cargado=True,
        tiene_gran_escala=False,
    )
    # RAT no aplica como obligación legal (puede adoptarse voluntariamente)
    res_rat, _, _, _ = _determinar_reglas_plantilla("RAT-01", hechos)
    assert res_rat == ResultadoAplicabilidad.NO_APLICA

    # Biometría no aplica
    res_bio, _, _, _ = _determinar_reglas_plantilla("VAR-BIO", hechos)
    assert res_bio == ResultadoAplicabilidad.NO_APLICA

    # Encargados aplica (CON-01, PRV-01)
    res_con, _, _, _ = _determinar_reglas_plantilla("CON-01", hechos)
    assert res_con == ResultadoAplicabilidad.APLICA

    # Transferencias internacionales aplica (TRA-01)
    res_tra, _, _, _ = _determinar_reglas_plantilla("TRA-01", hechos)
    assert res_tra == ResultadoAplicabilidad.APLICA


def test_perfil_pf03_entidad_publica_municipal():
    """PF-03: Entidad pública municipal con 180 trabajadores y proyecto biométrico."""
    hechos = HechosOrganizacion(
        tenant_id="pf-03",
        num_trabajadores=180,
        sector="publico",
        rat_cargado=True,
        actividades_rat=[
            {"nombre": "Trámites ciudadanos", "categorias_datos": ["identificación", "huella facial"]},
        ],
        mtge_cargado=True,
        tiene_gran_escala=False,
    )
    # RAT aplica por Art. 38 (>=100 trabajadores)
    res_rat, es_ob, _, _ = _determinar_reglas_plantilla("RAT-01", hechos)
    assert res_rat == ResultadoAplicabilidad.APLICA
    assert es_ob is True

    # GOB-01 aplica por sector público
    res_gob, _, _, _ = _determinar_reglas_plantilla("GOB-01", hechos)
    assert res_gob == ResultadoAplicabilidad.APLICA

    # Biometría aplica
    res_bio, _, _, _ = _determinar_reglas_plantilla("VAR-BIO", hechos)
    assert res_bio == ResultadoAplicabilidad.APLICA


# ----------------------------------------------------------------------------- 3. Modificación Humana

@pytest.mark.asyncio
async def test_exclusion_obligacion_confirmada_exige_revision_juridica():
    """Criterio 3: una obligación confirmada exige revisión jurídica para su exclusión."""
    fuentes = FuentesAplicabilidad(
        obtener_organizacion=AsyncMock(return_value={"tamano": "mediana"}),
        listar_actividades=AsyncMock(return_value=[]),
        obtener_gran_escala=AsyncMock(return_value=(False, 0)),
    )
    session = AsyncMock()

    # Intentar excluir RAT-01 sin rol jurídico ni revisor
    with pytest.raises(ErrorNegocio) as exc_info:
        await registrar_modificacion_aplicabilidad(
            session=session,
            tenant_id="tenant-test",
            actor_id="user-consultor",
            plantilla_codigo="RAT-01",
            resultado_modificado=ResultadoAplicabilidad.NO_APLICA,
            motivo="No deseamos llevar RAT en esta empresa",
            evidencia="Decisión de gerencia",
            es_juridico=False,
            revisor_juridico_id=None,
            fuentes=fuentes,
        )
    assert exc_info.value.code == "BIB_EXCLUSION_EXIGE_JURIDICO"
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_modificacion_requiere_motivo_y_evidencia():
    """Una modificación sin motivo o evidencia se rechaza con 422."""
    session = AsyncMock()
    with pytest.raises(ErrorNegocio) as exc:
        await registrar_modificacion_aplicabilidad(
            session=session,
            tenant_id="t",
            actor_id="u",
            plantilla_codigo="INV-01",
            resultado_modificado=ResultadoAplicabilidad.NO_APLICA,
            motivo="",
            evidencia="Doc",
        )
    assert exc.value.code == "BIB_MODIFICACION_INVALIDA"


@pytest.mark.asyncio
async def test_modificacion_humana_exitosa_conserva_datos():
    """Modificación exitosa persiste y conserva resultado_original, autor, fecha y evidencia."""
    fuentes = FuentesAplicabilidad(
        obtener_organizacion=AsyncMock(return_value={"tamano": "micro"}),
        listar_actividades=AsyncMock(return_value=[{"nombre": "Ventas"}]),
        obtener_gran_escala=AsyncMock(return_value=(False, 0)),
    )
    session = AsyncMock()

    mod = await registrar_modificacion_aplicabilidad(
        session=session,
        tenant_id="tenant-test",
        actor_id="user-juridico",
        plantilla_codigo="LIA-01",
        resultado_modificado=ResultadoAplicabilidad.APLICA,
        motivo="Se proyecta implementar campaña bajo interés legítimo el próximo mes",
        evidencia="Plan comercial Q4",
        es_juridico=True,
        revisor_juridico_id="user-juridico",
        fuentes=fuentes,
    )

    assert mod.resultado_original == ResultadoAplicabilidad.NO_APLICA
    assert mod.resultado_modificado == ResultadoAplicabilidad.APLICA
    assert mod.autor_id == "user-juridico"
    assert mod.revisor_juridico_id == "user-juridico"
    assert "Plan comercial" in mod.evidencia
    assert session.commit.called


# ----------------------------------------------------------------------------- 4. Migración Alembic

def test_migracion_una_cabeza_rls_forzada_y_permisos_minimos():
    """Verifica la migración de BIB-204 conforme a las reglas ADPA."""
    assert MIGRACION is not None, "No se encontró el archivo de migración *_biblioteca_reglas.py"
    spec = importlib.util.spec_from_file_location("bib204_migracion", MIGRACION)
    migracion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migracion)

    # Revisión <= 32 caracteres
    assert len(migracion.revision) <= 32

    configuracion = Config(str(ROOT / "alembic.ini"))
    configuracion.set_main_option("script_location", str(ROOT / "alembic"))
    guion = ScriptDirectory.from_config(configuracion)

    # Una sola cabeza en Alembic
    cabezas = guion.get_heads()
    assert len(cabezas) == 1
    assert migracion.revision in {r.revision for r in guion.iterate_revisions(cabezas[0], "base")}
    assert guion.get_revision(migracion.down_revision) is not None

    # Simular upgrade para verificar SQL de seguridad
    sql = []
    migracion.op = SimpleNamespace(execute=sql.append)
    migracion.upgrade()
    texto = "\n".join(sql)

    assert "ENABLE ROW LEVEL SECURITY" in texto
    assert "FORCE ROW LEVEL SECURITY" in texto
    assert "USING (tenant_id = current_setting" in texto
    assert "WITH CHECK (tenant_id = current_setting" in texto
    assert "GRANT SELECT, INSERT ON biblioteca_aplicabilidad_modificaciones TO lopdp_app" in texto
    assert "GRANT UPDATE" in texto


# ----------------------------------------------------------------------------- 5. Router y API

@pytest.fixture
def cliente(monkeypatch):
    """Cliente de pruebas con dependencias RBAC y sesión aisladas en memoria."""
    app = FastAPI()
    app.add_exception_handler(ErrorNegocio, error_negocio_handler)
    app.include_router(biblioteca_aplicabilidad.router, prefix="/api/v1")
    monkeypatch.setitem(app.dependency_overrides, get_session, lambda: AsyncMock())
    return app, TestClient(app)


def test_router_auto_registro_y_endpoints(cliente, monkeypatch):
    """Verifica que el router declara AUTO_REGISTRO = True y expone los endpoints correctos."""
    assert biblioteca_aplicabilidad.AUTO_REGISTRO is True
    _, http = cliente

    # Mock de evaluación para pruebas de endpoints
    async def mock_evaluar(session, tenant_id, *args, **kwargs):
        return [
            bib.EvaluacionPlantilla(
                codigo="RAT-01",
                nombre="Registro de actividades",
                resultado=ResultadoAplicabilidad.APLICA,
                resultado_calculado=ResultadoAplicabilidad.APLICA,
                tipo="registro",
                familia="Tratamientos",
                formato="XLSX",
                naturaleza="Obligación condicional",
                es_obligacion=True,
                fuentes_normativas=["N02", "N12"],
                version_regla="1.0",
                motivo_recomendacion="Obligación por trabajadores",
                hechos_relevantes={"num_trabajadores": 120},
                hechos_faltantes=[],
                reglas_evaluadas=[
                    bib.ReglaEvaluada(
                        regla_id="AP-02",
                        nombre="Trabajadores",
                        resultado=ResultadoAplicabilidad.APLICA,
                        explicacion=">= 100",
                        fuente_normativa="N02",
                        version_regla="1.0",
                        hechos_analizados={"num_trabajadores": 120},
                    )
                ],
            )
        ]

    monkeypatch.setattr(bib, "evaluar_aplicabilidad_organizacion", mock_evaluar)

    # Simular rechazo de exclusión sin revisión jurídica en servicio
    async def mock_modificar(**kwargs):
        if not kwargs.get("es_juridico") and not kwargs.get("revisor_juridico_id"):
            raise ErrorNegocio("BIB_EXCLUSION_EXIGE_JURIDICO", "Exige revisión jurídica")
        return bib.ModificacionHumana(
            resultado_original=ResultadoAplicabilidad.APLICA,
            resultado_modificado=kwargs["resultado_modificado"],
            motivo=kwargs["motivo"],
            evidencia=kwargs["evidencia"],
            autor_id=kwargs["actor_id"],
            fecha=datetime.now(timezone.utc),
            es_obligacion_confirmada=True,
            revisor_juridico_id=kwargs.get("revisor_juridico_id"),
        )

    monkeypatch.setattr(bib, "registrar_modificacion_aplicabilidad", mock_modificar)

    headers = {"X-Tenant-ID": "tenant-test", "X-Role": "admin_organizacion", "X-User-ID": "u-1"}

    # GET /api/v1/biblioteca/aplicabilidad
    r1 = http.get("/api/v1/biblioteca/aplicabilidad", headers=headers)
    assert r1.status_code == 200
    datos = r1.json()
    assert len(datos) == 1
    assert datos[0]["codigo"] == "RAT-01"
    assert datos[0]["resultado"] == "Aplica"
    assert datos[0]["reglas_evaluadas"][0]["regla_id"] == "AP-02"

    # GET /api/v1/biblioteca/recomendados
    r2 = http.get("/api/v1/biblioteca/recomendados", headers=headers)
    assert r2.status_code == 200
    assert len(r2.json()) == 1

    # POST modificar obligación confirmada sin ser DPO da 403
    payload = {
        "resultado_modificado": "No aplica",
        "motivo": "No aplica",
        "evidencia": "Acta",
    }
    r3 = http.post("/api/v1/biblioteca/aplicabilidad/RAT-01/modificar", json=payload, headers=headers)
    assert r3.status_code == 403
    assert r3.json().get("code") == "BIB_EXCLUSION_EXIGE_JURIDICO" or r3.json().get("detail") == "Exige revisión jurídica"

    # POST modificar con rol DPO pasa exitosamente
    headers_dpo = {"X-Tenant-ID": "tenant-test", "X-Role": "dpo", "X-User-ID": "u-dpo"}
    r4 = http.post("/api/v1/biblioteca/aplicabilidad/RAT-01/modificar", json=payload, headers=headers_dpo)
    assert r4.status_code == 200
    assert r4.json()["resultado_modificado"] == "No aplica"


# ----------------------------------------------------------------------------- 6. Persistencia (Base Propia)

@pytest_asyncio.fixture
async def db_bib():
    """Conexión real para persistencia; solo corre con TEST_DATABASE_URL propia."""
    url = os.environ.get("TEST_DATABASE_URL", "")
    if "ep-late-hall-b50bpbk5" in url.lower():
        pytest.fail("Host de producción prohibido; no se abrió conexión", pytrace=False)
    local = "@127.0.0.1" in url or "@localhost" in url
    if not url or not (local or os.environ.get("BIB204_RAMA_PROPIA") == "1"):
        pytest.skip("Persistencia pendiente: falta base propia (arnés local o BIB204_RAMA_PROPIA=1)")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    engine = create_async_engine(url, echo=False, hide_parameters=True)
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        yield session
        await trans.rollback()
    await engine.dispose()
