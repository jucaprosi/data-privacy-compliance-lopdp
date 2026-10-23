# ¤roadmap
# ¤arbitro
"""RM-18: el proxy del frontend espera a la generación síncrona de la hoja de ruta.

Hallazgo de las pruebas en físico (2026-10-23): el proxy de `/api/v1` de Next corta a los 30 s
(«socket hang up») mientras el backend sigue esperando a la IA. El tiempo del proxy debe cubrir el
peor caso del backend: todos los intentos agotando su límite.
"""
from __future__ import annotations

import inspect
import re
from pathlib import Path

from features.roadmap.roadmap_service import DEFAULT_TIMEOUT_SECONDS, generate_roadmap_document

CONFIG = Path(__file__).resolve().parents[1] / "frontend" / "next.config.ts"
MARGEN_MS = 10_000


def _proxy_timeout_ms() -> int:
    texto = CONFIG.read_text(encoding="utf-8")
    m = re.search(r"const PROXY_TIMEOUT_MS = ([\d_]+);", texto)
    assert m, "next.config.ts debe declarar PROXY_TIMEOUT_MS"
    assert "proxyTimeout: PROXY_TIMEOUT_MS" in texto, "PROXY_TIMEOUT_MS debe aplicarse a experimental.proxyTimeout"
    return int(m.group(1).replace("_", ""))


def test_el_proxy_cubre_el_peor_caso_de_la_generacion():
    intentos = inspect.signature(generate_roadmap_document).parameters["max_retries"].default
    peor_caso_ms = int(intentos * DEFAULT_TIMEOUT_SECONDS * 1000)
    assert _proxy_timeout_ms() >= peor_caso_ms + MARGEN_MS
