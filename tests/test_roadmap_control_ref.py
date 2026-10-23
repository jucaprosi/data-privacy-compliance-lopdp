# ¤roadmap
# ¤arbitro
"""RM-17: la generación no falla porque la IA escriba «P01» en lugar de «P1».

Hallazgo de las pruebas en físico (2026-10-23): DeepSeek devolvió control_ref «P01» y «P05»,
por analogía con las dimensiones (D01..D10); el validador solo admitía P1..P73 exactos y los dos
intentos fallaban. El control es el mismo: se normaliza a la forma canónica. Lo que no
pertenece al catálogo se sigue rechazando.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import date, timedelta
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from features.roadmap.roadmap_service import SYSTEM_PROMPT, RoadmapTask

HOY = date.today()


def _tarea(control_ref) -> dict:
    return {
        "id": str(uuid.uuid4()), "control_ref": control_ref, "dimension": "D01", "titulo": "T",
        "descripcion": "D", "responsable": "R", "prioridad": "alta", "esfuerzo_estimado_horas": 4,
        "dependencias": [], "entregable": "E", "evidencia_requerida": ["PDF"], "kpi": "K",
        "fecha_inicio": HOY.isoformat(), "fecha_fin": (HOY + timedelta(days=9)).isoformat(),
    }


@pytest.mark.parametrize("entrada, canonico", [
    ("P1", "P1"), ("P01", "P1"), ("P05", "P5"), ("p7", "P7"), (" P073 ", "P73"), ("P73", "P73"),
])
def test_control_ref_se_normaliza_a_la_forma_canonica(entrada, canonico):
    assert RoadmapTask(**_tarea(entrada)).control_ref == canonico


@pytest.mark.parametrize("entrada", ["P0", "P00", "P74", "P100", "X1", "P", "P1a", "", 5])
def test_control_ref_fuera_del_catalogo_se_rechaza(entrada):
    with pytest.raises(ValidationError):
        RoadmapTask(**_tarea(entrada))


def test_el_prompt_dice_como_se_escriben_controles_y_dimensiones():
    assert "nunca P01" in SYSTEM_PROMPT
    assert "D01" in SYSTEM_PROMPT and "dos dígitos" in SYSTEM_PROMPT


def test_generacion_completa_aunque_la_ia_escriba_ceros_a_la_izquierda():
    """Recorrido real con PostgreSQL: solo se simula la IA; antes del arreglo terminaba en «failed»."""
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("TEST_DATABASE_URL no configurada")
    import asyncio
    from fastapi.testclient import TestClient
    from sqlalchemy import text
    from app_core.db.session import async_session_factory
    from main import app

    t, u = f"rm17-{uuid.uuid4().hex[:8]}", f"rm17-u-{uuid.uuid4().hex[:8]}"

    async def ejecutar(sentencias):
        async with async_session_factory() as s:
            for sql, params in sentencias:
                await s.execute(text(sql), params)
            await s.commit()

    asyncio.run(ejecutar([
        ("INSERT INTO tenants (id, nombre_comercial, razon_social, ruc_identificacion) VALUES (:t, :t, :t, :r)",
         {"t": t, "r": f"RUC{uuid.uuid4().hex[:10]}"}),
        ("INSERT INTO users (id, email, nombre) VALUES (:u, :e, 'Implementador RM-17')", {"u": u, "e": f"{u}@example.test"}),
        ("INSERT INTO user_tenant_roles (id, user_id, tenant_id, role) VALUES (:i, :u, :t, 'implementador')",
         {"i": f"r-{uuid.uuid4().hex[:8]}", "u": u, "t": t}),
    ]))
    documento = {
        "roadmap_id": str(uuid.uuid4()), "tenant_id": t, "resumen_ejecutivo": "RM-17",
        "olas": [{"id": "o1", "nombre": "Ola 1", "plazo": "M1", "objetivo": "x", "tareas": [_tarea("P01"), _tarea("P05")]}],
        "kpis_globales": {"criticos_totales": 0, "altos_totales": 2, "score_objetivo": 80.0, "evidencia_verificada_objetivo": 90.0},
    }
    cuerpo = {"tenant_id": t, "user_id": u, "assessment": {},
              "variables": {"plazo_meses": 6, "presupuesto": 100.0, "moneda": "USD", "equipo": ["DPO"], "dpo": "DPO"}}
    try:
        with patch.dict(os.environ, {"AUTH_MODE": "headers"}), \
             patch("features.roadmap.services.generacion_engine.call_roadmap_llm", return_value=json.dumps(documento)):
            r = TestClient(app).post("/api/v1/roadmaps/generate", json=cuerpo,
                                     headers={"X-User-ID": u, "X-Tenant-ID": t, "X-Role": "implementador"})
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "completed", r.text

        async def controles():
            async with async_session_factory() as s:
                return sorted((await s.execute(text("SELECT control_ref FROM roadmap_tasks WHERE tenant_id = :t"), {"t": t})).scalars())
        assert asyncio.run(controles()) == ["P1", "P5"]
    finally:
        asyncio.run(ejecutar([
            ("DELETE FROM roadmap_tasks WHERE tenant_id = :t", {"t": t}),
            ("DELETE FROM roadmap_waves WHERE tenant_id = :t", {"t": t}),
            ("DELETE FROM roadmaps WHERE tenant_id = :t", {"t": t}),
            ("DELETE FROM user_tenant_roles WHERE tenant_id = :t", {"t": t}),
            ("DELETE FROM users WHERE id = :u", {"u": u}),
            ("DELETE FROM tenants WHERE id = :t", {"t": t}),
        ]))
