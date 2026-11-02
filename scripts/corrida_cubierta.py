# -*- coding: utf-8 -*-
# ¤arbitro
"""Un arnés por commit: el PR reutiliza la corrida del push sobre el mismo commit.

Un push a dev/<persona> y el PR de esa rama hacia main corren sobre el mismo commit. Si la rama está al
día con su base, el árbol que probaría el PR es el mismo que probó el push, así que el PR espera esa
corrida y adopta su resultado en vez de repetir el arnés. Si no hubo push, si falló o fue cancelado, o
si la rama está detrás de la base, el PR corre su propio arnés. Nunca se da por cubierto lo que no pasó.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time

ARNESES_NEON = ("Arnés por salas", "Arnés completo")
WORKFLOW = "zero-regression-pipeline.yml"
ESPERA_APARICION_S = 90  # el push y el PR nacen casi a la vez; la corrida del push puede tardar en listarse
LIMITE_S = 40 * 60
PAUSA_S = 20


def consultar_api(ruta: str) -> dict:
    salida = subprocess.run(["gh", "api", ruta], capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return json.loads(salida)


def ejecutar_git(args: list[str]) -> int:
    return subprocess.run(["git", *args], capture_output=True).returncode


# ¤arbitro
def al_dia(base: str, sha: str, git=ejecutar_git) -> bool:
    """Con la base ya contenida en la cabeza, la fusión de prueba del PR tiene el mismo árbol que la cabeza."""
    return git(["merge-base", "--is-ancestor", base, sha]) == 0


def corridas_push(repositorio: str, sha: str, corrida_actual: int, api) -> list[dict]:
    datos = api(f"repos/{repositorio}/actions/workflows/{WORKFLOW}/runs?head_sha={sha}&event=push&per_page=20")
    return sorted((c for c in datos.get("workflow_runs", []) if c["id"] != corrida_actual), key=lambda c: c["id"])


# ¤arbitro
def resultado_del_arnes(jobs: list[dict]) -> str | None:
    """'success' si un arnés de Neon pasó; None mientras alguno no haya terminado; si no, cómo terminó."""
    arneses = [j for j in jobs if j["name"] in ARNESES_NEON]
    if not arneses:
        return None
    if any(j["status"] == "completed" and j["conclusion"] == "success" for j in arneses):
        return "success"
    if any(j["status"] != "completed" for j in arneses):
        return None
    conclusiones = {j["conclusion"] for j in arneses} - {"skipped"}
    return ", ".join(sorted(conclusiones)) if conclusiones else "sin arnés"


# ¤arbitro
def decidir(repositorio: str, sha: str, base: str, corrida_actual: int, api=consultar_api, git=ejecutar_git,
            dormir=time.sleep, reloj=time.monotonic, limite_s: float = LIMITE_S, pausa_s: float = PAUSA_S,
            espera_aparicion_s: float = ESPERA_APARICION_S) -> tuple[int | None, str]:
    if not base:
        return None, "sin base de comparación: solo un PR reutiliza la corrida del push"
    if not al_dia(base, sha, git):
        return None, "la rama no está al día con la base; el PR prueba su propia fusión"
    inicio = reloj()
    try:
        while True:
            corridas = corridas_push(repositorio, sha, corrida_actual, api)
            if corridas or reloj() - inicio >= espera_aparicion_s:
                break
            dormir(pausa_s)
        if not corridas:
            return None, "ningún push corrió sobre este commit"
        corrida = corridas[0]["id"]
        while True:
            jobs = api(f"repos/{repositorio}/actions/runs/{corrida}/jobs?per_page=100").get("jobs", [])
            resultado = resultado_del_arnes(jobs)
            if resultado == "success":
                return corrida, f"cubierta por la corrida {corrida} del push, que ya verificó este commit"
            if resultado is not None:
                return None, f"la corrida {corrida} del push terminó sin éxito ({resultado}); el PR corre su arnés"
            if reloj() - inicio >= limite_s:
                return None, f"límite de espera agotado tras la corrida {corrida}; el PR corre su arnés"
            print(f"[COMMIT] Esperando el arnés de la corrida {corrida} del push sobre {sha[:7]}...", flush=True)
            dormir(pausa_s)
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError, OSError) as error:
        return None, f"sin reutilización: la API no respondió ({type(error).__name__}); el PR corre su arnés"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sha", required=True, help="commit de la cabeza del PR")
    ap.add_argument("--base", default="", help="commit de la base del PR; vacío fuera de un PR")
    ap.add_argument("--corrida", required=True, type=int, help="número de esta corrida (GITHUB_RUN_ID)")
    ap.add_argument("--repositorio", required=True, help="owner/repo (GITHUB_REPOSITORY)")
    ap.add_argument("--salida-github", action="store_true", help="anota cubierta=<corrida o vacío> en $GITHUB_OUTPUT")
    args = ap.parse_args(argv)
    corrida, motivo = decidir(args.repositorio, args.sha, args.base, args.corrida)
    print(f"[COMMIT] {motivo}.")
    if args.salida_github and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as salida:
            salida.write(f"cubierta={corrida or ''}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
