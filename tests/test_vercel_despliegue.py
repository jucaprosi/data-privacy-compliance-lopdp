# ¤arbitro
"""Árbitro estático: Vercel despliega solo lo que el propietario aprueba.

Invariante (decisión del propietario, 2026-10-26): los dos proyectos de Vercel (backend en la
raíz, frontend en ``frontend/``) despliegan solo
- ``main``: el propietario fusiona el PR, es decir, cierra el proceso;
- ``preview/**``: vista previa pedida a propósito, empujando una rama con ese prefijo.

Cualquier otra rama (``feat/*``, ``fix/*``, ``chore/*``) no crea despliegue. Antes, cada push
creaba dos despliegues y el cupo del plan gratuito (100 por día) se agotaba. Con las reglas de
``git.deploymentEnabled``, si una rama coincide con varias y alguna es ``true``, se despliega;
``**`` (y no ``*``) cubre las ramas con barra.
"""
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).parents[1]
REGLAS = {"main": True, "preview/**": True, "**": False}


@pytest.mark.parametrize("archivo", ["vercel.json", "frontend/vercel.json"])
def test_vercel_despliega_solo_main_y_vistas_previas_pedidas(archivo: str) -> None:
    config = json.loads((RAIZ / archivo).read_text(encoding="utf-8"))
    assert config.get("git", {}).get("deploymentEnabled") == REGLAS, (
        f"{archivo}: git.deploymentEnabled debe ser {REGLAS}"
    )
