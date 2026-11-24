# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤vigilancia-spdp ¤inteligencia-normativa ¤seguridad
"""NORM-05 R3: el backend lanza el Job del monitoreo (Cloud Run Jobs API v2) en lugar de correrlo él mismo.

Las credenciales son las predeterminadas del backend; el permiso `run.invoker` sobre este Job lo concede el
propietario. Sin `K_SERVICE` o sin `NORMATIVA_TRABAJO_MONITOREO` no se llama a nada.
"""
from __future__ import annotations

import os
from typing import Awaitable, Callable

from features.inteligencia_normativa.domain.errores import ErrorNormativo

NORMATIVA_TRABAJO_NO_DISPONIBLE = "NORMATIVA_TRABAJO_NO_DISPONIBLE"
REGION = "us-central1"
VARIABLE_TRABAJO = "NORMATIVA_TRABAJO_MONITOREO"
Envio = Callable[[str], Awaitable[None]]


class TrabajoNoDisponible(ErrorNormativo):
    codigo = NORMATIVA_TRABAJO_NO_DISPONIBLE


def _url_de_ejecucion() -> str:
    trabajo = os.environ.get(VARIABLE_TRABAJO, "").strip()
    proyecto = os.environ.get("GOOGLE_CLOUD_PROJECT", "").strip()
    if not os.environ.get("K_SERVICE") or not trabajo or not proyecto:
        raise TrabajoNoDisponible()
    return f"https://run.googleapis.com/v2/projects/{proyecto}/locations/{REGION}/jobs/{trabajo}:run"


async def _enviar_por_defecto(url: str) -> None:
    """POST a la API de Cloud Run con las credenciales por defecto; los clientes se importan al primer uso."""
    import google.auth
    import httpx
    from google.auth.transport.requests import Request

    credenciales, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    credenciales.refresh(Request())
    async with httpx.AsyncClient(timeout=15.0) as cliente:
        respuesta = await cliente.post(url, headers={"Authorization": f"Bearer {credenciales.token}"}, json={})
    respuesta.raise_for_status()


async def lanzar(enviar: Envio | None = None) -> None:
    """Lanza una ejecución del Job. Cualquier fallo se vuelve `TrabajoNoDisponible`, sin detalle."""
    url = _url_de_ejecucion()
    try:
        await (enviar or _enviar_por_defecto)(url)
    except Exception as exc:
        raise TrabajoNoDisponible() from exc
