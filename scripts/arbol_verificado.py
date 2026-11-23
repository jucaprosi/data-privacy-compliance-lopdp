# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
"""Un arnés por árbol (CI-37, R1): el push a main no repite el arnés que el PR ya pasó sobre el mismo árbol.

`registrar --salida <archivo> --modo <salas|completo>` escribe, al final de un arnés en verde del PR,
`{"arbol": <HEAD^{tree}>, "commit": <github.sha>, "modo": <modo>}`. El workflow lo sube como artefacto
`arbol-verificado`. En un PR, `HEAD` es el commit de prueba de la fusión: su árbol es el que tendrá main si
nadie fusiona antes.

`comprobar --sha <push> --modo <modo> --repositorio <r>` sigue tres pasos:
  1. busca el PR fusionado del commit con `GET /repos/<r>/commits/<sha>/pulls`;
  2. toma la última corrida `pull_request` en verde de su cabeza;
  3. descarga su artefacto y compara `arbol` con el `HEAD^{tree}` del push.
Escribe `cubierto=<run_id>` solo si los árboles son iguales y el modo del PR era `completo`, o era `salas` y
el del push también. En cualquier otro caso, también ante cualquier fallo (API, artefacto ausente, PR no
encontrado), escribe `cubierto=` y el arnés corre: la regla falla hacia el lado seguro. Siempre sale con 0.

Se compara el árbol y nunca el commit: el commit de fusión del push no existe cuando corre el PR, y un PR
desactualizado (main cambió entre su corrida y la fusión) da otro árbol aunque su cabeza sea la misma.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import zipfile
from typing import Callable

FLUJO = "zero-regression-pipeline.yml"
ARTEFACTO = "arbol-verificado"
ARCHIVO = "arbol-verificado.json"
MODOS = ("salas", "completo")

Api = Callable[[str], object]
Descarga = Callable[[str], bytes]


def _gh(ruta: str) -> bytes:
    return subprocess.run(["gh", "api", ruta], capture_output=True, check=True).stdout


def api_gh(ruta: str) -> object:
    return json.loads(_gh(ruta).decode("utf-8"))


def arbol_de_head() -> str:
    salida = subprocess.run(["git", "rev-parse", "HEAD^{tree}"], capture_output=True, check=True, text=True)
    return salida.stdout.strip()


def registrar(salida: str, modo: str, commit: str, arbol: str) -> dict:
    if modo not in MODOS:
        raise ValueError(f"modo desconocido: {modo!r}")
    datos = {"arbol": arbol, "commit": commit, "modo": modo}
    with open(salida, "w", encoding="utf-8", newline="\n") as archivo:
        json.dump(datos, archivo)
        archivo.write("\n")
    return datos


def modo_cubre(modo_pr: str, modo_push: str) -> bool:
    """El modo del PR es igual o más amplio que el del push."""
    return modo_pr == "completo" or (modo_pr == "salas" and modo_push == "salas")


def _registro_del_artefacto(zip_bytes: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archivo:
        return json.loads(archivo.read(ARCHIVO).decode("utf-8"))


def buscar_cobertura(sha: str, modo: str, repositorio: str, arbol: str, api: Api, descargar: Descarga) -> str:
    """El id de la corrida del PR que verificó este mismo árbol con un modo que cubre el del push, o ''."""
    prs = [pr for pr in api(f"repos/{repositorio}/commits/{sha}/pulls")
           if pr.get("merged_at") and pr.get("merge_commit_sha") == sha]
    if not prs:
        return ""
    cabeza = prs[0]["head"]["sha"]
    corridas = api(f"repos/{repositorio}/actions/workflows/{FLUJO}/runs"
                   f"?event=pull_request&head_sha={cabeza}&status=success&per_page=100")["workflow_runs"]
    verdes = sorted((c for c in corridas if c.get("conclusion") == "success"),
                    key=lambda c: c.get("created_at", ""), reverse=True)
    if not verdes:
        return ""
    corrida = verdes[0]["id"]
    artefactos = api(f"repos/{repositorio}/actions/runs/{corrida}/artifacts?name={ARTEFACTO}")["artifacts"]
    vigentes = [a for a in artefactos if a.get("name") == ARTEFACTO and not a.get("expired")]
    if not vigentes:
        return ""
    registro = _registro_del_artefacto(descargar(f"repos/{repositorio}/actions/artifacts/{vigentes[0]['id']}/zip"))
    if modo not in MODOS or registro.get("arbol") != arbol or not modo_cubre(registro.get("modo"), modo):
        return ""
    return str(corrida)


def comprobar(sha: str, modo: str, repositorio: str, arbol: str | None = None,
              api: Api = api_gh, descargar: Descarga = _gh) -> str:
    """Nunca lanza: cualquier fallo devuelve '' y el arnés corre."""
    try:
        return buscar_cobertura(sha, modo, repositorio, arbol or arbol_de_head(), api, descargar)
    except Exception as error:  # noqa: BLE001 - la regla falla hacia el lado seguro
        print(f"Sin cobertura ({type(error).__name__}: {error}): el arnés corre.", file=sys.stderr)
        return ""


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="orden", required=True)
    reg = sub.add_parser("registrar", help="escribe el árbol verificado por un arnés en verde")
    reg.add_argument("--salida", required=True)
    reg.add_argument("--modo", required=True, choices=MODOS)
    reg.add_argument("--commit", default=os.environ.get("GITHUB_SHA", ""))
    com = sub.add_parser("comprobar", help="decide si el push está cubierto por la corrida de su PR")
    com.add_argument("--sha", required=True)
    com.add_argument("--modo", required=True)
    com.add_argument("--repositorio", required=True)
    com.add_argument("--salida-github", action="store_true", help="anota cubierto= en $GITHUB_OUTPUT")
    args = ap.parse_args(argv)

    if args.orden == "registrar":
        print(json.dumps(registrar(args.salida, args.modo, args.commit, arbol_de_head())))
        return 0
    cubierto = comprobar(args.sha, args.modo, args.repositorio)
    print(f"cubierto={cubierto}")
    if args.salida_github and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as salida:
            salida.write(f"cubierto={cubierto}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
