# ¤gemini-vertex
"""IA-03: prueba de humo REAL contra Vertex. Opt-in (VERTEX_HUMO=1); la corre el propietario, no el CI."""
import asyncio
import os

import pytest

pytestmark = pytest.mark.skipif(os.environ.get("VERTEX_HUMO") != "1", reason="humo opt-in: VERTEX_HUMO=1")


@pytest.mark.parametrize("esquema_ruta", [
    ("features.preanalisis.domain.models", "PropuestaModelo"),
    ("features.ai_copilot.domain.models", "PlanMitigacionResponse"),
])
def test_humo_esquema(esquema_ruta):
    import importlib

    from features.inferencia import inferencia_service as svc

    esquema = getattr(importlib.import_module(esquema_ruta[0]), esquema_ruta[1])

    async def consumir(org):
        return None

    svc.inyectar_consumidor_de_prueba(consumir)
    try:
        r = asyncio.run(svc.generar_estructurado(
            "Responde con datos de ejemplo ficticios.", "Genera una muestra del esquema.",
            esquema, modelo="gemini-2.5-flash", org_id="org-humo",
        ))
    finally:
        svc.inyectar_consumidor_de_prueba(None)
    assert isinstance(r, esquema)
