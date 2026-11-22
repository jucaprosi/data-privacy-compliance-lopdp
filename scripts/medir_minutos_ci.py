# -*- coding: utf-8 -*-
# ¤arbitro
"""Minutos facturables de GitHub Actions por fusión a main (CI-37, R6).

GitHub factura cada job por separado y redondea su duración al minuto siguiente. Por cada PR fusionado a
main entre `--desde` y `--hasta` se suma `ceil(duración/60)` de cada job de dos corridas del workflow
`zero-regression-pipeline.yml`: la última del PR (evento `pull_request` sobre su cabeza) y la del push de la
fusión (evento `push` sobre el commit de fusión). Los datos salen de `GET /repos/<r>/actions/runs/<id>/jobs`,
solo de lectura, con `gh api`.

Imprime la media, la mediana y el total, y sale con código 2 si hay menos de `--min` fusiones medidas.

    python scripts/medir_minutos_ci.py --desde 2026-11-15 --hasta 2026-11-22
"""
from __future__ import annotations

import argparse
import json
import math
import statistics
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Callable, Iterable

REPOSITORIO = "jucaprosi/data-privacy-compliance-lopdp"
FLUJO = "zero-regression-pipeline.yml"

Api = Callable[[str], object]


def api_gh(ruta: str) -> object:
    """`gh api` de solo lectura; devuelve el JSON de la respuesta."""
    salida = subprocess.run(["gh", "api", ruta], capture_output=True, check=True, text=True, encoding="utf-8")
    return json.loads(salida.stdout)


def _instante(texto: str | None) -> datetime | None:
    return datetime.fromisoformat(texto.replace("Z", "+00:00")) if texto else None


def minutos_de_job(job: dict) -> int:
    """Minutos facturables de un job: su duración redondeada al minuto siguiente; un job omitido no factura."""
    inicio, fin = _instante(job.get("started_at")), _instante(job.get("completed_at"))
    if inicio is None or fin is None or fin <= inicio:
        return 0
    return math.ceil((fin - inicio).total_seconds() / 60)


def minutos_de_corrida(jobs: Iterable[dict]) -> int:
    return sum(minutos_de_job(job) for job in jobs)


def _jobs(api: Api, repositorio: str, corrida: int) -> list[dict]:
    jobs, pagina = [], 1
    while True:
        respuesta = api(f"repos/{repositorio}/actions/runs/{corrida}/jobs?per_page=100&page={pagina}")
        jobs += respuesta.get("jobs", [])
        if len(jobs) >= respuesta.get("total_count", 0) or not respuesta.get("jobs"):
            return jobs
        pagina += 1


def _ultima_corrida(api: Api, repositorio: str, evento: str, sha: str) -> dict | None:
    respuesta = api(f"repos/{repositorio}/actions/workflows/{FLUJO}/runs?event={evento}&head_sha={sha}&per_page=100")
    corridas = sorted(respuesta.get("workflow_runs", []), key=lambda c: c.get("created_at", ""), reverse=True)
    return corridas[0] if corridas else None


def fusiones(api: Api, repositorio: str, desde: datetime, hasta: datetime) -> list[dict]:
    """PR fusionados a main con `desde <= merged_at < hasta`, del más reciente al más antiguo."""
    encontradas, pagina = [], 1
    while True:
        prs = api(f"repos/{repositorio}/pulls?state=closed&base=main&sort=updated&direction=desc"
                  f"&per_page=100&page={pagina}")
        if not prs:
            break
        for pr in prs:
            fusion = _instante(pr.get("merged_at"))
            if fusion is not None and desde <= fusion < hasta:
                encontradas.append(pr)
        if _instante(prs[-1].get("updated_at")) < desde:
            break
        pagina += 1
    return sorted(encontradas, key=lambda pr: pr["merged_at"], reverse=True)


def medir(api: Api, repositorio: str, desde: datetime, hasta: datetime) -> list[dict]:
    """Una fila por fusión con su corrida de push: minutos del PR, del push y su suma."""
    filas = []
    for pr in fusiones(api, repositorio, desde, hasta):
        push = _ultima_corrida(api, repositorio, "push", pr["merge_commit_sha"])
        if push is None:
            continue
        del_pr = _ultima_corrida(api, repositorio, "pull_request", pr["head"]["sha"])
        minutos_pr = minutos_de_corrida(_jobs(api, repositorio, del_pr["id"])) if del_pr else 0
        minutos_push = minutos_de_corrida(_jobs(api, repositorio, push["id"]))
        filas.append({"pr": pr["number"], "pr_min": minutos_pr, "push_min": minutos_push,
                      "total": minutos_pr + minutos_push})
    return filas


def resumen(filas: list[dict]) -> dict:
    totales = [fila["total"] for fila in filas]
    return {"fusiones": len(totales), "media": statistics.mean(totales) if totales else 0.0,
            "mediana": statistics.median(totales) if totales else 0.0, "total": sum(totales)}


def _fecha(texto: str) -> datetime:
    return datetime.combine(date.fromisoformat(texto), datetime.min.time(), tzinfo=timezone.utc)


def main(argv: list[str] | None = None, api: Api = api_gh) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--desde", required=True, help="fecha inicial (AAAA-MM-DD), incluida")
    ap.add_argument("--hasta", required=True, help="fecha final (AAAA-MM-DD), incluida")
    ap.add_argument("--min", type=int, default=20, help="mínimo de fusiones medidas (por defecto 20)")
    ap.add_argument("--repositorio", default=REPOSITORIO)
    args = ap.parse_args(argv)

    filas = medir(api, args.repositorio, _fecha(args.desde), _fecha(args.hasta) + timedelta(days=1))
    for fila in filas:
        print(f"#{fila['pr']}: PR {fila['pr_min']} min + push {fila['push_min']} min = {fila['total']} min")
    datos = resumen(filas)
    print(f"fusiones={datos['fusiones']} media={datos['media']:.2f} mediana={datos['mediana']:.1f} "
          f"total={datos['total']} (minutos facturables, PR + push)")
    if datos["fusiones"] < args.min:
        print(f"Hay {datos['fusiones']} fusiones medidas y hacen falta {args.min}: amplíe las fechas.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
