# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤gemini-vertex
"""IA-03 e IA-13 R4b: prueba de humo REAL contra Vertex. Opt-in (VERTEX_HUMO=1); la corre el propietario, no el CI.

Generación con `VERTEX_LOCATION=us` y vectores con `VERTEX_LOCATION_EMBEDDING=us-central1`, tras desplegar IA-13.
"""
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
    from features.inferencia.domain.modelos_permitidos import MODELO_GENERACION

    esquema = getattr(importlib.import_module(esquema_ruta[0]), esquema_ruta[1])

    async def consumir(org):
        return None

    svc.inyectar_consumidor_de_prueba(consumir)
    try:
        r = asyncio.run(svc.generar_estructurado(
            "Responde con datos de ejemplo ficticios.", "Genera una muestra del esquema.",
            esquema, modelo=MODELO_GENERACION, org_id="org-humo",
        ))
    finally:
        svc.inyectar_consumidor_de_prueba(None)
    assert isinstance(r, esquema)


def test_humo_vectores():
    from features.inferencia import inferencia_service as svc
    from features.inferencia.domain.modelos_permitidos import MODELO_EMBEDDING

    vectores = asyncio.run(svc.vectorizar(["Ley Orgánica de Protección de Datos Personales"], MODELO_EMBEDDING))
    assert len(vectores) == 1 and vectores[0]
