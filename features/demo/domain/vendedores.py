# -*- coding: utf-8 -*-
# ¤demo
"""Lista de vendedores autorizados (`DEMO_VENDEDORES`, secreto del proyecto demo; DEMO-02)."""
from __future__ import annotations

import re

from app_core.cloud.gcp_runtime import leer_secreto

NOMBRE_SECRETO = "DEMO_VENDEDORES"
_SEPARADORES = re.compile(r"[,;\s]+")


def normalizar(texto: str | None) -> frozenset[str]:
    """Correos en minúsculas y sin espacios, separados por comas, punto y coma o saltos de línea."""
    return frozenset(c for c in _SEPARADORES.split((texto or "").strip().lower()) if c)


def autorizados() -> frozenset[str]:
    """Vendedores vigentes. Sin secreto la lista queda vacía y nadie entra (falla cerrado)."""
    return normalizar(leer_secreto(NOMBRE_SECRETO))


def es_autorizado(correo: str | None) -> bool:
    limpio = (correo or "").strip().lower()
    return bool(limpio) and limpio in autorizados()
