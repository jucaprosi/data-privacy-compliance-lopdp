# ¤seguridad ¤copiloto-ia
"""Catálogo de políticas de SEC-13 y clasificación de rutas.

Los límites iniciales son parámetros: `LIMITE_<POLITICA>` (en mayúsculas) los cambia sin tocar código,
p. ej. `LIMITE_IA_USUARIO=50`. Un valor no entero o menor que 1 se ignora y se conserva el inicial.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import Mapping, Optional

MINUTO = 60
HORA = 60 * MINUTO
DIA = 24 * HORA


@dataclass(frozen=True)
class Politica:
    nombre: str
    ambito: str  # "ip" | "usuario" | "organizacion"
    limite: int
    ventana_segundos: int
    es_ia: bool = False


_INICIALES = (
    Politica("inicio_sesion", "ip", 10, MINUTO),
    Politica("entorno_publico", "ip", 60, MINUTO),  # SEC-21: GET /api/v1/entorno, pública y sin token
    Politica("ia_usuario", "usuario", 30, HORA, es_ia=True),
    Politica("ia_organizacion", "organizacion", 200, DIA, es_ia=True),
    Politica("url_firmada", "usuario", 120, HORA),
    Politica("api_general", "usuario", 300, MINUTO),
)


def cargar_politicas(entorno: Optional[Mapping[str, str]] = None) -> dict[str, Politica]:
    """Políticas con los ajustes `LIMITE_<POLITICA>` del entorno aplicados."""
    entorno = os.environ if entorno is None else entorno
    politicas: dict[str, Politica] = {}
    for p in _INICIALES:
        valor = (entorno.get(f"LIMITE_{p.nombre.upper()}") or "").strip()
        if valor.isdigit() and int(valor) >= 1:
            p = replace(p, limite=int(valor))
        politicas[p.nombre] = p
    return politicas


POLITICAS = cargar_politicas()

PREFIJO_API = "/api/v1"
RUTAS_LIBRES = frozenset({"/health", "/api/v1/health"})
PREFIJOS_INICIO_SESION = ("/api/v1/auth",)
# SEC-21: rutas públicas sin token; sin usuario verificado, el límite es por IP y no comparte cubeta anónima.
PREFIJOS_PUBLICOS_IP = ("/api/v1/entorno",)
# Copiloto, preanálisis, RAG, asistente y generación de hoja de ruta: toda llamada a un modelo.
PREFIJOS_IA = (
    "/api/v1/ai",
    "/api/v1/ai_copilot",
    "/api/v1/preanalisis",
    "/api/v1/rag",
    "/api/v1/roadmaps/generate",
)
SUFIJOS_URL_FIRMADA = ("/upload-url", "/download-url", "/descargar")
METODOS_IA = frozenset({"POST", "PUT", "PATCH"})


def _bajo(ruta: str, prefijo: str) -> bool:
    return ruta == prefijo or ruta.startswith(prefijo + "/")


def politicas_de_ruta(ruta: str, metodo: str) -> tuple[str, ...]:
    """Nombres de las políticas que se aplican a la petición (vacío si queda fuera)."""
    ruta = ruta.rstrip("/") or "/"
    metodo = metodo.upper()
    if ruta in RUTAS_LIBRES or not _bajo(ruta, PREFIJO_API):
        return ()
    if any(_bajo(ruta, p) for p in PREFIJOS_INICIO_SESION):
        return ("inicio_sesion",)
    if metodo in METODOS_IA and any(_bajo(ruta, p) for p in PREFIJOS_IA):
        return ("ia_usuario", "ia_organizacion")
    if metodo == "POST" and ruta.endswith(SUFIJOS_URL_FIRMADA):
        return ("url_firmada",)
    if any(_bajo(ruta, p) for p in PREFIJOS_PUBLICOS_IP):
        return ("entorno_publico",)
    return ("api_general",)
