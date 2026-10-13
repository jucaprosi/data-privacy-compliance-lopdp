# -*- coding: utf-8 -*-
# ¤arbitro
# ¤ci-cd
"""Árbitro exógeno de verificación de despliegue para la Plataforma LOPDP 360.

Comprueba que un despliegue (Production, Preview o local) cumple:
1. GET /api/v1/health responde 200 con status == 'OPERATIONAL' y todos los routers cargados.
2. GET /openapi.json responde 200 y contiene todas las rutas esperadas (incluyendo
   las rutas montadas por cada router activo y las rutas raíz).

Uso:
    python scripts/verificar_despliegue.py <dominio_o_url>

Código de salida:
    0 si todos los chequeos pasan.
    1 si falla cualquier condición o hay error de red/formato (indicando el motivo).
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from typing import Any

# Rutas mínimas que todo despliegue operativo debe exponer en /openapi.json
# Cubre las salas del sistema y endpoints fundamentales.
RUTAS_ESPERADAS_BASE: list[str] = [
    "/",
    "/health",
    "/api/v1/health",
    "/api/v1/diagnostico/dimensiones",
    "/api/v1/diagnostico/evaluar",
    "/api/v1/rat/actividades",
    "/api/v1/riesgos/mtge/evaluar",
    "/api/v1/dpo/dictamenes",
    "/api/v1/capa/tickets",
    "/api/v1/evidencias",
    "/api/v1/rag/consulta",
    "/api/v1/arco/solicitudes",
    "/api/v1/terceros/encargados",
    "/api/v1/ai/diagnosticar",
    "/api/v1/niif18/informe",
    "/api/v1/preanalisis/estado",
    "/api/v1/organizacion/me/roles",
]


def normalizar_url_base(destino: str) -> str:
    """Normaliza un dominio o URL en una URL base con protocolo sin barra final."""
    destino = destino.strip()
    if not destino.startswith(("http://", "https://")):
        destino = f"https://{destino}"
    return destino.rstrip("/")


def peticion_json(url: str, timeout: float = 15.0) -> tuple[int, Any, str]:
    """Realiza una petición GET HTTP/HTTPS y devuelve (status_code, parsed_json, error_msg)."""
    headers = {
        "User-Agent": "LOPDP360-VerificadorDespliegue/1.0",
        "Accept": "application/json",
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.getcode()
            body = response.read().decode("utf-8")
            try:
                data = json.loads(body)
                return status, data, ""
            except json.JSONDecodeError as exc:
                return status, None, f"Respuesta no es JSON válido: {exc}"
    except urllib.error.HTTPError as exc:
        status = exc.code
        body = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(body)
        except Exception:
            data = None
        return status, data, f"HTTP Error {status}: {exc.reason}"
    except Exception as exc:
        return 0, None, f"Error de conexión a {url}: {exc}"


def verificar_health(cuerpo_health: Any, status_http: int) -> tuple[bool, str]:
    """Valida los requisitos de /api/v1/health:

    - HTTP 200
    - status == 'OPERATIONAL'
    - todos los routers cargados (fallidos vacío, total == len(cargados) > 0)
    """
    if status_http != 200:
        return False, f"/api/v1/health respondió código HTTP {status_http} (se esperaba 200)"
    if not isinstance(cuerpo_health, dict):
        return False, "/api/v1/health no devolvió un objeto JSON"

    estado = cuerpo_health.get("status")
    if estado != "OPERATIONAL":
        return False, f"Estado de salud '{estado}' no es 'OPERATIONAL'"

    routers = cuerpo_health.get("routers")
    if not isinstance(routers, dict):
        return False, "Campo 'routers' no presente o no es un diccionario en /api/v1/health"

    fallidos = routers.get("fallidos", [])
    if fallidos:
        nombres_fallidos = [
            f.get("router", str(f)) if isinstance(f, dict) else str(f)
            for f in fallidos
        ]
        return False, f"Existen routers fallidos ({len(fallidos)}): {', '.join(nombres_fallidos)}"

    cargados = routers.get("cargados", [])
    total = routers.get("total")
    if not cargados:
        return False, "No hay ningún router cargado en la plataforma"

    if total is not None and len(cargados) != total:
        return (
            False,
            f"Discrepancia en routers: cargados={len(cargados)} != total={total}",
        )

    return True, "OK"


def verificar_openapi(
    cuerpo_openapi: Any, status_http: int, rutas_esperadas: list[str] | None = None
) -> tuple[bool, str]:
    """Valida los requisitos de /openapi.json:

    - HTTP 200
    - paths contiene todas las rutas_esperadas
    """
    if status_http != 200:
        return False, f"/openapi.json respondió código HTTP {status_http} (se esperaba 200)"
    if not isinstance(cuerpo_openapi, dict):
        return False, "/openapi.json no devolvió un esquema JSON válido"

    paths = cuerpo_openapi.get("paths")
    if not isinstance(paths, dict):
        return False, "Esquema OpenAPI no contiene el campo 'paths' tipo diccionario"

    rutas_a_comprobar = rutas_esperadas if rutas_esperadas is not None else RUTAS_ESPERADAS_BASE
    paths_registrados = set(paths.keys())

    faltantes = [ruta for ruta in rutas_a_comprobar if ruta not in paths_registrados]
    if faltantes:
        return False, f"Faltan rutas esperadas en /openapi.json ({len(faltantes)}): {', '.join(faltantes)}"

    return True, "OK"


def ejecutar_verificacion(
    url_base: str,
    timeout: float = 15.0,
    rutas_esperadas: list[str] | None = None,
    cliente_http=peticion_json,
) -> tuple[bool, list[str]]:
    """Ejecuta la verificación completa contra el host y devuelve (exito, mensajes_motivo)."""
    motivos: list[str] = []
    base = normalizar_url_base(url_base)

    # 1. Verificar /api/v1/health
    url_health = f"{base}/api/v1/health"
    status_health, cuerpo_health, err_health = cliente_http(url_health, timeout=timeout)
    if err_health and status_health == 0:
        motivos.append(f"No se pudo conectar a {url_health}: {err_health}")
    else:
        ok_health, msg_health = verificar_health(cuerpo_health, status_health)
        if not ok_health:
            motivos.append(f"Fallo en /api/v1/health: {msg_health}")

    # 2. Verificar /openapi.json
    url_openapi = f"{base}/openapi.json"
    status_openapi, cuerpo_openapi, err_openapi = cliente_http(url_openapi, timeout=timeout)
    if err_openapi and status_openapi == 0:
        motivos.append(f"No se pudo conectar a {url_openapi}: {err_openapi}")
    else:
        ok_openapi, msg_openapi = verificar_openapi(
            cuerpo_openapi, status_openapi, rutas_esperadas=rutas_esperadas
        )
        if not ok_openapi:
            motivos.append(f"Fallo en /openapi.json: {msg_openapi}")

    if motivos:
        return False, motivos
    return True, ["Despliegue operativo y verificado exitosamente."]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Verifica un despliegue de Plataforma LOPDP 360 (health y openapi)."
    )
    parser.add_argument(
        "dominio",
        help="Dominio o URL base del despliegue a verificar (ej. https://api.lopdp360.com o localhost:5000)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Tiempo máximo de espera para peticiones HTTP en segundos (por defecto 15.0)",
    )
    args = parser.parse_args(argv)

    exito, mensajes = ejecutar_verificacion(args.dominio, timeout=args.timeout)
    for m in mensajes:
        if exito:
            print(f"[VERIFICAR_DESPLIEGUE] OK: {m}")
        else:
            print(f"[VERIFICAR_DESPLIEGUE] ERROR: {m}", file=sys.stderr)

    return 0 if exito else 1


if __name__ == "__main__":
    sys.exit(main())
