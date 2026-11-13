# ¤¤qa-engineer
# ¤cloud-run-perf
"""GCP-05 · Prueba de carga de lectura contra el entorno de PRUEBAS (nunca producción).

    python scripts/prueba_carga.py --entorno pruebas --url https://<url-de-pruebas> --usuarios 200 --duracion 300

Cada usuario simulado es un hilo que recorre las rutas de lectura en bucle durante `--duracion` segundos.
Escribe p50, p95, p99 y el conteo de respuestas por código. Solo usa la biblioteca estándar.

Reglas (especificación GCP-05):
- R3: rechaza un host de producción antes de enviar ninguna petición, y exige que `GET /api/v1/entorno`
  responda exactamente el entorno pedido en `--entorno`. No lee ningún `.env`.
- R4: la meta es p95 < 800 ms y cero 5xx. El script informa el resultado tal cual: no ajusta la meta.
- El token de un usuario de prueba, si hace falta, se toma de la variable `PRUEBA_CARGA_TOKEN`; nunca de un
  argumento ni de un archivo del repositorio, y jamás se imprime.

Salida: 0 meta cumplida, 1 meta no cumplida, 2 no se pudo correr (destino rechazado o mal configurado).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from collections import Counter
from urllib.parse import urlparse

ENTORNOS = ("pruebas", "local")
HOSTS_PRODUCCION = ("app.evydentia.com",)
HUELLAS_PRODUCCION = ("evydentia-production", "evydentia_prod")
RUTAS_POR_DEFECTO = ("/api/v1/entorno", "/api/v1/health")
META_P95_MS = 800.0
TIEMPO_PETICION = 30.0


# ¤cloud-run-perf
def es_destino_de_produccion(url: str) -> bool:
    """True si la URL apunta al dominio o a un recurso de producción."""
    host = (urlparse(url).hostname or "").lower()
    if host in HOSTS_PRODUCCION or any(host.endswith("." + h) for h in HOSTS_PRODUCCION):
        return True
    return any(h in url.lower() for h in HUELLAS_PRODUCCION)


# ¤cloud-run-perf
def percentil(valores: list[float], p: float) -> float:
    """Percentil por rango más cercano; 0 si no hay datos."""
    if not valores:
        return 0.0
    orden = sorted(valores)
    return orden[max(0, math.ceil(p / 100 * len(orden)) - 1)]


# ¤cloud-run-perf
def resumir(latencias_ms: list[float], codigos: Counter) -> dict:
    cinco_xx = sum(n for c, n in codigos.items() if isinstance(c, int) and c >= 500)
    errores_red = codigos.get("error", 0)
    p95 = percentil(latencias_ms, 95)
    return {
        "peticiones": sum(codigos.values()),
        "p50_ms": round(percentil(latencias_ms, 50), 1),
        "p95_ms": round(p95, 1),
        "p99_ms": round(percentil(latencias_ms, 99), 1),
        "codigos": {str(c): n for c, n in sorted(codigos.items(), key=lambda x: str(x[0]))},
        "5xx": cinco_xx,
        "errores_de_red": errores_red,
        "meta_cumplida": bool(latencias_ms) and p95 < META_P95_MS and cinco_xx == 0 and errores_red == 0,
    }


def _get(url: str, token: str | None) -> tuple[int | str, float, bytes]:
    peticion = urllib.request.Request(url, headers={"Accept": "application/json"})
    if token:
        peticion.add_header("Authorization", f"Bearer {token}")
    inicio = time.perf_counter()
    try:
        with urllib.request.urlopen(peticion, timeout=TIEMPO_PETICION) as respuesta:
            cuerpo = respuesta.read()
            return respuesta.status, (time.perf_counter() - inicio) * 1000, cuerpo
    except urllib.error.HTTPError as error:
        return error.code, (time.perf_counter() - inicio) * 1000, b""
    except Exception:  # noqa: BLE001 — se cuenta como error de red; nunca se imprime el mensaje (puede llevar la URL)
        return "error", (time.perf_counter() - inicio) * 1000, b""


# ¤cloud-run-perf
def entorno_del_destino(base: str, token: str | None) -> str | None:
    codigo, _, cuerpo = _get(base.rstrip("/") + "/api/v1/entorno", token)
    if codigo != 200:
        return None
    try:
        return str(json.loads(cuerpo).get("entorno"))
    except (ValueError, AttributeError):
        return None


# ¤cloud-run-perf
def correr(base: str, usuarios: int, duracion: float, rutas: list[str], token: str | None) -> dict:
    latencias: list[float] = []
    codigos: Counter = Counter()
    cerrojo = threading.Lock()
    fin = time.monotonic() + duracion

    def usuario(indice: int) -> None:
        i = indice
        while time.monotonic() < fin:
            codigo, ms, _ = _get(base.rstrip("/") + rutas[i % len(rutas)], token)
            i += 1
            with cerrojo:
                codigos[codigo] += 1
                if codigo != "error":
                    latencias.append(ms)

    hilos = [threading.Thread(target=usuario, args=(n,), daemon=True) for n in range(usuarios)]
    inicio = time.monotonic()
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()
    informe = resumir(latencias, codigos)
    informe.update({"usuarios": usuarios, "duracion_s": round(time.monotonic() - inicio, 1), "rutas": rutas})
    return informe


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--entorno", required=True, choices=ENTORNOS, help="entorno esperado; debe coincidir con GET /api/v1/entorno")
    ap.add_argument("--url", required=True, help="URL base del entorno de pruebas (o local)")
    ap.add_argument("--usuarios", type=int, default=200)
    ap.add_argument("--duracion", type=float, default=300)
    ap.add_argument("--rutas", default=",".join(RUTAS_POR_DEFECTO), help="rutas de lectura, separadas por comas")
    args = ap.parse_args(argv)

    if es_destino_de_produccion(args.url):
        print("RECHAZADO: el destino es de producción. La prueba de carga solo corre contra pruebas.", file=sys.stderr)
        return 2
    if args.usuarios < 1 or args.duracion <= 0:
        print("RECHAZADO: usuarios y duración deben ser positivos.", file=sys.stderr)
        return 2
    token = os.environ.get("PRUEBA_CARGA_TOKEN") or None
    reportado = entorno_del_destino(args.url, token)
    if reportado != args.entorno:
        print(f"RECHAZADO: GET /api/v1/entorno devolvió {reportado!r}, no {args.entorno!r}.", file=sys.stderr)
        return 2
    rutas = [r if r.startswith("/") else "/" + r for r in args.rutas.split(",") if r.strip()]
    informe = correr(args.url, args.usuarios, args.duracion, rutas, token)
    informe["entorno"] = args.entorno
    print(json.dumps(informe, ensure_ascii=False, indent=2))
    print("META CUMPLIDA" if informe["meta_cumplida"] else "META NO CUMPLIDA (p95 < 800 ms y cero 5xx)")
    return 0 if informe["meta_cumplida"] else 1


if __name__ == "__main__":
    sys.exit(main())
