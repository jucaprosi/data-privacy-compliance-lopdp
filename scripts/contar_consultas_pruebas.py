# -*- coding: utf-8 -*-
# ¤ci-cd
# ¤arbitro
"""Corre pytest con plugin_contar_consultas contra PostgreSQL local y escribe la tabla por archivo.

El número de consultas no depende de la región, así que nunca se usa Neon. Sin argumentos mide los 10 archivos más
lentos de governance/operaciones/MEDICION_PRUEBAS_LENTAS.md; `--todos` mide la suite completa, siempre en serie.
El worktree necesita su `.env` propio aunque solo apunte a la base local.

    python scripts/contar_consultas_pruebas.py --salida tabla.md --json filas.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import re
import statistics
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
MEDICION = RAIZ / "governance" / "operaciones" / "MEDICION_PRUEBAS_LENTAS.md"
VIAJES_POR_FILA = ("consultas", "checkouts", "begin", "commit", "rollback")
_FILA_DE_ARCHIVO = re.compile(r"^\| `(test_\w+)` \|", re.M)
_SIN_CONTAR = re.compile(r"psycopg\.connect|psycopg\.AsyncConnection|AsyncConnection\.connect")
_HOSTS_PROHIBIDOS = ("neon", "ep-")


def exigir_base_local(url: str) -> None:
    if any(host in url.lower() for host in _HOSTS_PROHIBIDOS):
        raise SystemExit("[CONSULTAS] Esta medición solo corre contra PostgreSQL local o en contenedor, nunca contra Neon.")


def archivos_de_la_medicion(texto: str) -> list[str]:
    return [f"tests/{nombre}.py" for nombre in _FILA_DE_ARCHIVO.findall(texto)]


def por_archivo(filas: list[dict]) -> list[dict]:
    grupos: dict[str, list[dict]] = {}
    for fila in filas:
        grupos.setdefault(fila["nodeid"].split("::")[0], []).append(fila)
    salida = []
    for archivo, grupo in grupos.items():
        consultas = [fila["consultas"] for fila in grupo]
        total = sum(consultas)
        salida.append({
            "archivo": archivo, "pruebas": len(grupo), "consultas": total, "mediana": statistics.median(consultas),
            "maximo": max(consultas), "pct_fixtures": round(sum(f["consultas_en_fixtures"] for f in grupo) / total * 100) if total else 0,
            "conexiones": sum(fila["conexiones"] for fila in grupo),
            "viajes": sum(fila[campo] for fila in grupo for campo in VIAJES_POR_FILA),
        })
    return sorted(salida, key=lambda fila: -fila["consultas"])


def latencia_implicita_ms(segundos_lejos: float, segundos_cerca: float, viajes: int) -> float | None:
    """Lo que tendría que costar cada viaje para que los viajes solos explicaran la diferencia entre dos regiones."""
    return round((segundos_lejos - segundos_cerca) / viajes * 1000, 1) if viajes else None


def tabla(filas: list[dict]) -> str:
    salida = [
        "| Archivo | Pruebas | Consultas | Mediana por prueba | Máximo | % en fixtures | Conexiones | Viajes sin saludo |",
        "| :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for f in por_archivo(filas):
        salida.append(
            f"| `{Path(f['archivo']).stem}` | {f['pruebas']} | {f['consultas']} | {f['mediana']:g} | {f['maximo']} "
            f"| {f['pct_fixtures']} | {f['conexiones']} | {f['viajes']} |"
        )
    return "\n".join(salida) + "\n"


def archivos_sin_contar(archivos: list[str]) -> list[str]:
    return [a for a in archivos if _SIN_CONTAR.search((RAIZ / a).read_text(encoding="utf-8-sig", errors="replace"))]


def _arnes_local():
    spec = importlib.util.spec_from_file_location("arnes_local", RAIZ / "verificadores" / "arnes_local.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["arnes_local"] = modulo
    spec.loader.exec_module(modulo)
    return modulo


def entorno_local() -> dict[str, str]:
    """Levanta y migra la base local de este worktree con el mismo código del arnés, pero sin -n."""
    arnes = _arnes_local()
    entorno = arnes.entorno_de_pruebas(dict(os.environ))
    entorno.pop("PYTEST_ADDOPTS", None)
    exigir_base_local(entorno["TEST_DATABASE_URL"])
    arnes.preparar_servidor(arnes.carpeta_postgres())
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=RAIZ, env=entorno, check=True)
    return entorno


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("archivos", nargs="*", help="archivos de prueba; por omisión, los de MEDICION_PRUEBAS_LENTAS.md")
    ap.add_argument("--todos", action="store_true", help="mide toda la carpeta tests/")
    ap.add_argument("--salida", type=Path, help="escribe aquí la tabla; sin esto, a la salida estándar")
    ap.add_argument("--json", type=Path, default=Path(tempfile.gettempdir()) / "consultas_por_prueba.json", help="contadores por prueba")
    args = ap.parse_args(argv)

    archivos = ["tests/"] if args.todos else args.archivos or archivos_de_la_medicion(MEDICION.read_text(encoding="utf-8-sig"))
    entorno = entorno_local()
    entorno["PYTHONPATH"] = str(RAIZ / "tests")
    pytest_ = subprocess.run(
        [sys.executable, "-m", "pytest", *archivos, "-q", "-p", "plugin_contar_consultas", "--consultas-json", str(args.json)],
        cwd=RAIZ, env=entorno,
    )
    resultado = tabla(json.loads(args.json.read_text(encoding="utf-8")))
    if not args.todos:
        resultado += f"\nArchivos con psycopg directo, no contado: {archivos_sin_contar(archivos) or 'ninguno'}.\n"
    if args.salida:
        args.salida.write_text(resultado, encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(resultado)
    return pytest_.returncode


if __name__ == "__main__":
    sys.exit(main())
