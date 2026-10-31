# -*- coding: utf-8 -*-
# ¤arbitro
"""Una corrida de CI a la vez por rama de Neon.

Las corridas que comparten la rama de Neon de una persona se reparten su cómputo: tres a la vez tardaron
casi el triple que una sola (medido el 2026-10-31). Este paso espera, por orden de número de corrida, a que
terminen los arneses de las corridas anteriores de la misma persona. Si la API no responde o se agota el
límite, sigue adelante: esperar nunca puede impedir una verificación.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time

PERSONAS = ("juan-carlos", "aleczandra", "jose")  # misma regla que TEST_DATABASE_URL en el workflow
ARNESES_NEON = ("Arnés por salas", "Arnés completo")
WORKFLOW = "zero-regression-pipeline.yml"
LIMITE_S = 40 * 60
PAUSA_S = 20


# ¤arbitro
def persona_de_rama(rama: str) -> str:
    """dev/<persona> y tarea/<persona>/... usan la rama Neon de esa persona; lo demás, test-main."""
    return next((persona for persona in PERSONAS if persona in rama), "main")


def consultar_api(ruta: str) -> dict:
    salida = subprocess.run(["gh", "api", ruta], capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return json.loads(salida)


# ¤arbitro
def corridas_por_delante(corridas: list[dict], corrida_actual: int, persona: str) -> list[dict]:
    """Las corridas anteriores (número menor) que usan la misma rama de Neon, de la más vieja a la más nueva."""
    return sorted(
        (c for c in corridas if c["id"] < corrida_actual and persona_de_rama(c.get("head_branch") or "") == persona),
        key=lambda c: c["id"],
    )


def arnes_pendiente(jobs: list[dict]) -> bool:
    """Un arnés omitido o terminado ya no toca Neon; uno en cola o en marcha, sí."""
    return any(job["name"] in ARNESES_NEON and job["status"] != "completed" for job in jobs)


def corridas_activas(repositorio: str, api) -> list[dict]:
    corridas: list[dict] = []
    for estado in ("in_progress", "queued"):
        datos = api(f"repos/{repositorio}/actions/workflows/{WORKFLOW}/runs?status={estado}&per_page=100")
        corridas += datos.get("workflow_runs", [])
    return corridas


def quien_bloquea(repositorio: str, corrida_actual: int, persona: str, api) -> dict | None:
    for corrida in corridas_por_delante(corridas_activas(repositorio, api), corrida_actual, persona):
        jobs = api(f"repos/{repositorio}/actions/runs/{corrida['id']}/jobs?per_page=100").get("jobs", [])
        if not jobs or arnes_pendiente(jobs):  # sin jobs todavía: acaba de encolarse y su arnés vendrá
            return corrida
    return None


# ¤arbitro
def esperar(repositorio: str, corrida_actual: int, persona: str, api=consultar_api, dormir=time.sleep,
            reloj=time.monotonic, limite_s: float = LIMITE_S, pausa_s: float = PAUSA_S) -> str:
    inicio = reloj()
    while True:
        try:
            bloqueo = quien_bloquea(repositorio, corrida_actual, persona, api)
        except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, OSError) as error:
            return f"sin espera: la API no respondió ({type(error).__name__})"
        if bloqueo is None:
            return "turno libre"
        if reloj() - inicio >= limite_s:
            return f"límite de espera agotado tras la corrida {bloqueo['id']}; se sigue adelante"
        print(f"[NEON] Esperando a la corrida {bloqueo['id']} ({bloqueo.get('head_branch')}) en la rama de {persona}...", flush=True)
        dormir(pausa_s)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rama", required=True, help="rama de git de esta corrida; decide la rama de Neon")
    ap.add_argument("--corrida", required=True, type=int, help="número de esta corrida (GITHUB_RUN_ID)")
    ap.add_argument("--repositorio", required=True, help="owner/repo (GITHUB_REPOSITORY)")
    args = ap.parse_args(argv)
    persona = persona_de_rama(args.rama)
    resultado = esperar(args.repositorio, args.corrida, persona)
    print(f"[NEON] Rama de {persona}: {resultado}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
