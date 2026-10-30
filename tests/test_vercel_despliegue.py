# ¤arbitro
"""Árbitro estático: Vercel despliega solo lo que el propietario aprueba.

Invariante (decisiones del propietario, 2026-10-26 y 2026-10-29): los dos proyectos de Vercel
(backend en la raíz, frontend en ``frontend/``) despliegan solo
- ``produccion``: rama de producción en Vercel; quien cierra la ventana nocturna la pone al día
  con ``main`` una sola vez por noche, después de migrar (regla 10 de governance/tareas/README.md);
- ``preview/**``: vista previa pedida a propósito, empujando una rama con ese prefijo.

Cualquier otra rama, también ``main``, no crea despliegue. Antes, cada push creaba dos despliegues
y el cupo del plan gratuito (100 por día) se agotaba; hasta el 2026-10-29 cada fusión a ``main``
creaba dos (28 ese día, con 14 fusiones). Con las reglas de
``git.deploymentEnabled``, si una rama coincide con varias y alguna es ``true``, se despliega;
``**`` (y no ``*``) cubre las ramas con barra.
"""
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).parents[1]
REGLAS = {"produccion": True, "preview/**": True, "**": False}


@pytest.mark.parametrize("archivo", ["vercel.json", "frontend/vercel.json"])
def test_vercel_despliega_solo_main_y_vistas_previas_pedidas(archivo: str) -> None:
    config = json.loads((RAIZ / archivo).read_text(encoding="utf-8"))
    assert config.get("git", {}).get("deploymentEnabled") == REGLAS, (
        f"{archivo}: git.deploymentEnabled debe ser {REGLAS}"
    )
