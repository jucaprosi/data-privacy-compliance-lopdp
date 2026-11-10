# ¤gemini-vertex
"""Cliente Gemini en Vertex AI con credenciales por defecto, sin clave de API. Se crea al primer uso."""
from __future__ import annotations

import os

from features.inferencia.domain.errores import InferenciaNoDisponible

TIMEOUT_MS = 60_000


def configuracion() -> tuple[str, str]:
    """(proyecto, región) del entorno; sin valores implícitos."""
    proyecto = (os.environ.get("GOOGLE_CLOUD_PROJECT") or "").strip()
    region = (os.environ.get("VERTEX_LOCATION") or "").strip()
    if not proyecto or not region:
        raise InferenciaNoDisponible()
    return proyecto, region


def crear_cliente():
    """Crea `genai.Client(vertexai=True, ...)`. Nunca recibe `api_key`."""
    proyecto, region = configuracion()
    from google import genai
    from google.genai import types

    return genai.Client(
        vertexai=True,
        project=proyecto,
        location=region,
        http_options=types.HttpOptions(timeout=TIMEOUT_MS),
    )


async def generar_json(cliente, modelo: str, sistema: str, usuario: str, esquema) -> object:
    """Una llamada estructurada; devuelve la respuesta cruda del SDK."""
    from google.genai import types

    return await cliente.aio.models.generate_content(
        model=modelo,
        contents=usuario,
        config=types.GenerateContentConfig(
            system_instruction=sistema,
            response_mime_type="application/json",
            response_schema=esquema,
            temperature=0,
        ),
    )
