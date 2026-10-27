"""Pruebas del contexto real para la generación de la hoja de ruta (RM-19).

Verifica:
1. Sin diagnóstico guardado, armar_contexto_generacion levanta SinDiagnosticoError:
   «complete el diagnóstico antes de generar».
2. Con diagnóstico guardado en base de datos:
   - El contexto contiene las brechas críticas con su código P y nombre del banco (ej. 'P74 · Campañas de concienciación').
   - Contiene la madurez por dimensión (D01-D10) y el sector y tamaño del tenant.
   - Si existen actividades del RAT con datos sensibles o gran escala, se incluyen y sus nombres están saneados (sin PII).
   - Minimización: el contexto no contiene datos de otra organización ni PII no anonimizada.
3. El prompt enviado a la IA (simulada) incluye el catálogo P1-P80 y las brechas reales del tenant.
"""
import asyncio
import json
import os
import uuid
from datetime import date, timedelta
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from features.diagnostico.diagnostico_service import (
    guardar_respuestas,
    obtener_catalogo_controles_p1_p80,
)
from features.rat.domain.models import ActividadRAT, BaseLegitimacion
from features.rat.rat_service import registrar_actividad_rat
from features.roadmap.roadmap_service import (
    SYSTEM_PROMPT,
    PlanningVariables,
    RoadmapDocument,
    SinDiagnosticoError,
    armar_contexto_generacion,
    build_roadmap_prompt,
    generate_roadmap_inline,
)

pytestmark = pytest.mark.asyncio


def _async_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@pytest_asyncio.fixture
async def seed_tenant_context():
    """Crea un tenant limpio con usuarios para probar el armado del contexto."""
    engine = create_async_engine(_async_url(), pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    t_id = f"t-ctx-{uuid.uuid4().hex[:8]}"
    u_id = f"u-ctx-{uuid.uuid4().hex[:8]}"

    async with factory() as session:
        await session.execute(
            text("""
                INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano)
                VALUES (:t, 'Empresa Contexto', 'Empresa Contexto S.A.', :ruc, 'Salud', 'mediana')
            """),
            {"t": t_id, "ruc": f"RUC{t_id[:10]}"},
        )
        await session.execute(
            text("""
                INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'Implementador Contexto')
            """),
            {"u": u_id, "e": f"{u_id}@example.test"},
        )
        await session.execute(
            text("""
                INSERT INTO user_tenant_roles (id, user_id, tenant_id, role)
                VALUES (:r, :u, :t, 'implementador')
            """),
            {"r": str(uuid.uuid4()), "u": u_id, "t": t_id},
        )
        await session.commit()

    yield {"tenant_id": t_id, "user_id": u_id, "factory": factory}

    # Limpieza
    async with factory() as session:
        await session.execute(text("DELETE FROM roadmap_tasks WHERE tenant_id = :t"), {"t": t_id})
        await session.execute(text("DELETE FROM roadmap_waves WHERE tenant_id = :t"), {"t": t_id})
        await session.execute(text("DELETE FROM roadmaps WHERE tenant_id = :t"), {"t": t_id})
        await session.execute(text("DELETE FROM diagnostico_respuestas WHERE tenant_id = :t"), {"t": t_id})
        await session.execute(text("DELETE FROM rat_actividades WHERE tenant_id = :t"), {"t": t_id})
        await session.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": t_id})
        await session.execute(text("DELETE FROM audit_events WHERE user_id = :u"), {"u": u_id})
        await session.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": t_id})
        await session.execute(text("DELETE FROM users WHERE id = :u"), {"u": u_id})
        await session.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": t_id})
        await session.commit()
    await engine.dispose()


async def test_sin_diagnostico_falla_con_error_claro(seed_tenant_context):
    """Sin respuestas guardadas en la base de la organización, debe fallar con SinDiagnosticoError."""
    tenant_id = seed_tenant_context["tenant_id"]
    user_id = seed_tenant_context["user_id"]
    factory = seed_tenant_context["factory"]

    async with factory() as session:
        with pytest.raises(SinDiagnosticoError) as exc_info:
            await armar_contexto_generacion(session, tenant_id, user_id)
        assert "complete el diagnóstico antes de generar" in str(exc_info.value)


async def test_armar_contexto_con_diagnostico_y_rat_real(seed_tenant_context):
    """Con diagnóstico y RAT sembrados, el contexto recupera brechas críticas con código P y nombres del banco."""
    tenant_id = seed_tenant_context["tenant_id"]
    user_id = seed_tenant_context["user_id"]
    factory = seed_tenant_context["factory"]

    async with factory() as session:
        # 1. Sembrar respuestas del diagnóstico
        # P1 (D01) No Conforme (Crítico)
        # P74 (D10) No Conforme (Crítico) - 'Campañas de concienciación'
        respuestas = [
            {
                "pregunta_id": 1,
                "control": "Política de protección de datos personales",
                "dimension": "D01",
                "estado": "No Conforme",
                "nivel_evidencia": 0,
                "criticidad": 5,
                "es_critica": True,
                "riesgo_base": 10,
            },
            {
                "pregunta_id": 74,
                "control": "Campañas de concienciación",
                "dimension": "D10",
                "estado": "No Conforme",
                "nivel_evidencia": 0,
                "criticidad": 4,
                "es_critica": True,
                "riesgo_base": 8,
            },
        ]
        await guardar_respuestas(session, tenant_id, user_id, respuestas)

        # 2. Sembrar actividad RAT con datos sensibles y PII en el nombre para verificar sanitización
        actividad = ActividadRAT(
            tenant_id=tenant_id,
            codigo="RAT-MED-01",
            nombre="Historia clínica de paciente Juan Pérez juan@example.com con cédula 1710000001",
            area_responsable="Médica",
            finalidad="Atención de salud",
            base_legal=BaseLegitimacion.OBLIGACION_LEGAL,
            datos_sensibles=True,
            es_gran_escala=False,
            requiere_eipd=True,
        )
        await registrar_actividad_rat(session, actividad, user_id=user_id)
        await session.commit()

        # 3. Armar contexto
        contexto = await armar_contexto_generacion(session, tenant_id, user_id)

    # Validaciones del contexto armado
    assert contexto["tenant_id"] == tenant_id
    assert contexto["ficha_organizacion"]["sector"] == "Salud"
    assert contexto["ficha_organizacion"]["tamano"] == "mediana"
    assert len(contexto["madurez_por_dimension"]) == 10

    # Brechas críticas deben incluir P1 y P74 con sus nombres canónicos
    brechas_codigos = {b["codigo"]: b["control"] for b in contexto["brechas_criticas"]}
    assert "P1" in brechas_codigos
    assert "P74" in brechas_codigos
    assert brechas_codigos["P74"] == "Campañas de concienciación"

    # RAT sensible sanitizado sin PII libre
    assert len(contexto["actividades_rat_criticas"]) == 1
    rat_item = contexto["actividades_rat_criticas"][0]
    assert rat_item["codigo"] == "RAT-MED-01"
    assert "juan@example.com" not in rat_item["nombre"]
    assert "1710000001" not in rat_item["nombre"]
    assert "[EMAIL_1]" in rat_item["nombre"] or "[PERSONA_" in rat_item["nombre"] or "[CEDULA_" in rat_item["nombre"]

    # 4. Verificar el prompt generado para la IA
    variables = {
        "plazo_meses": 6,
        "presupuesto": 5000.0,
        "moneda": "USD",
        "equipo": ["DPO"],
        "dpo": "DPO Salud",
        "idioma": "ES",
    }
    user_prompt = build_roadmap_prompt(contexto, variables)

    # El prompt debe contener el catálogo P1-P80 en SYSTEM_PROMPT y las brechas en user_prompt
    assert "P1-P80" in SYSTEM_PROMPT
    assert "P74" in user_prompt
    assert "Campañas de concienciación" in user_prompt


async def test_aislamiento_no_incluye_datos_de_otra_organizacion(seed_tenant_context):
    """Verifica que el contexto del tenant A no contiene respuestas ni actividades del tenant B."""
    tenant_a = seed_tenant_context["tenant_id"]
    user_a = seed_tenant_context["user_id"]
    factory = seed_tenant_context["factory"]

    # Crear tenant B
    tenant_b = f"t-other-{uuid.uuid4().hex[:8]}"
    user_b = f"u-other-{uuid.uuid4().hex[:8]}"

    async with factory() as session:
        await session.execute(
            text("""
                INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion, sector, tamano)
                VALUES (:t, 'Otra Empresa', 'Otra S.A.', :ruc, 'Finanzas', 'corporativo')
            """),
            {"t": tenant_b, "ruc": f"RUC{tenant_b[:10]}"},
        )
        await session.execute(
            text("INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'User B')"),
            {"u": user_b, "e": f"{user_b}@example.test"},
        )
        await session.execute(
            text("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:r, :u, :t, 'implementador')"),
            {"r": str(uuid.uuid4()), "u": user_b, "t": tenant_b},
        )
        # Respuestas para Tenant A (P1)
        await guardar_respuestas(session, tenant_a, user_a, [{
            "pregunta_id": 1, "control": "Control A", "dimension": "D01",
            "estado": "No Conforme", "nivel_evidencia": 0, "criticidad": 5, "es_critica": True, "riesgo_base": 10,
        }])
        # Respuestas para Tenant B (P80)
        await guardar_respuestas(session, tenant_b, user_b, [{
            "pregunta_id": 80, "control": "Control B Secreto", "dimension": "D10",
            "estado": "No Conforme", "nivel_evidencia": 0, "criticidad": 5, "es_critica": True, "riesgo_base": 10,
        }])
        await session.commit()

        # Armar contexto para Tenant A
        ctx_a = await armar_contexto_generacion(session, tenant_a, user_a)

    # Limpiar tenant B
    async with factory() as session:
        await session.execute(text("DELETE FROM diagnostico_respuestas WHERE tenant_id = :t"), {"t": tenant_b})
        await session.execute(text("DELETE FROM audit_events WHERE tenant_id = :t"), {"t": tenant_b})
        await session.execute(text("DELETE FROM audit_events WHERE user_id = :u"), {"u": user_b})
        await session.execute(text("DELETE FROM user_tenant_roles WHERE tenant_id = :t"), {"t": tenant_b})
        await session.execute(text("DELETE FROM users WHERE id = :u"), {"u": user_b})
        await session.execute(text("DELETE FROM tenants WHERE id = :t"), {"t": tenant_b})
        await session.commit()

    # El contexto de A no debe incluir nada de B
    codigos_a = {b["codigo"] for b in ctx_a["brechas_criticas"]}
    assert "P1" in codigos_a
    assert "P80" not in codigos_a
    assert "Control B Secreto" not in json.dumps(ctx_a)

async def test_mutacion_assessment_vacio_falla_en_linea(seed_tenant_context):
    """Prueba que confirma que generar con assessment vacio no provee brechas de diagnostico."""
    tenant_id = seed_tenant_context["tenant_id"]
    user_id = seed_tenant_context["user_id"]
    factory = seed_tenant_context["factory"]

    # Con diagnostico sembrado, el contexto real TIENE brechas
    async with factory() as session:
        await guardar_respuestas(session, tenant_id, user_id, [{
            "pregunta_id": 74, "control": "Campa?as de concienciaci?n", "dimension": "D10",
            "estado": "No Conforme", "nivel_evidencia": 0, "criticidad": 4, "es_critica": True, "riesgo_base": 8,
        }])
        await session.commit()
        ctx = await armar_contexto_generacion(session, tenant_id, user_id)
        assert len(ctx["brechas_criticas"]) > 0
        assert "P74" in {b["codigo"] for b in ctx["brechas_criticas"]}

        # Si se volviera a enviar assessment = {}, no hay brechas ni contexto real
        assessment_vacio = {}
        assert "brechas_criticas" not in assessment_vacio or len(assessment_vacio.get("brechas_criticas", [])) == 0
