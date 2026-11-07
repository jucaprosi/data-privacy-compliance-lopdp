# -*- coding: utf-8 -*-
# ¤ci-cd
# ¤arbitro
"""Por qué la misma suite tarda de 7 a 36 minutos contra Neon: mide las corridas que ya existen.

Solo lee GitHub Actions con `gh api`. No lanza corridas, no usa ninguna clave de Neon y no guarda los registros: de
cada uno se conservan cifras, nunca el texto, así que ninguna URL de conexión puede salir por aquí. Las pruebas que
no tocan la base son el control: si también se frenan, la causa es la CPU del ejecutor y no la distancia a Neon.

    python scripts/medir_variacion_ci.py --corridas 300 --salida tabla.md --json datos.json
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
REPOSITORIO = "jucaprosi/data-privacy-compliance-lopdp"
WORKFLOW = "zero-regression-pipeline.yml"
PERSONAS = ("juan-carlos", "aleczandra", "jose")  # personas con rama histórica de pruebas en Neon (CI-12)
ARNESES = ("Arnés completo", "Arnés por salas", "Arnés Físico Determinista")
PASOS_PYTEST = ("Backend Pytest (E2E y Unitarias)", "Backend Pytest (salas tocadas, dependientes y nucleo)")
PASO_TURNO = "Esperar turno en la rama de Neon"
HILOS = 8
UMBRAL_CON_CONSULTA_S = 0.1  # por debajo, la prueba no llegó a Neon aunque su archivo use la base
ARNES_COMPLETOS = ("Arnés completo", "Arnés Físico Determinista")

_LINEA_DE_PRUEBA = re.compile(
    r"^(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d+)Z (tests/\S+?\.py)::.* (?:PASSED|FAILED|SKIPPED|ERROR|XFAIL|XPASS)", re.M
)
_REGION = re.compile(r"Region: *([a-z0-9]+)", re.I)
_USA_LA_BASE = re.compile(
    r"db_engine|db_session|seed_tenants|TEST_DATABASE_URL|DATABASE_URL|get_session|get_tenant_session|create_async_engine"
    r"|ASGITransport|TestClient|psycopg"
)


@dataclass
class Registro:
    region: str | None
    pruebas: int
    mediana_con_consulta_ms: float | None
    media_sin_base_ms: float | None
    primera_con_consulta_s: float | None


@dataclass
class Corrida:
    id: int
    inicio: str
    fin: str
    minutos: float
    arnes: str
    evento: str
    rama: str
    rama_neon: str
    hacia_main: bool
    medible: bool = True
    solapadas_misma_rama: int = 0
    solapadas_otra_rama: int = 0
    reposo_min: float | None = None
    region: str | None = None
    pruebas: int = 0
    mediana_con_consulta_ms: float | None = None
    media_sin_base_ms: float | None = None
    primera_con_consulta_s: float | None = None


def _fecha(texto: str) -> datetime:
    return datetime.fromisoformat(texto[:26].rstrip("Z"))


def rama_neon(rama: str) -> str:
    return next((f"test-{persona}" for persona in PERSONAS if persona in rama), "test-main")


def solapadas(inicio: str, fin: str, otros: list[tuple[str, str]]) -> int:
    """Intervalos que comparten algún instante con [inicio, fin]; dos que solo se tocan en un borde no cuentan."""
    desde, hasta = _fecha(inicio), _fecha(fin)
    return sum(1 for a, b in otros if _fecha(a) < hasta and _fecha(b) > desde)


def spearman(x: list[float], y: list[float]) -> float | None:
    """Correlación por rangos, con empates promediados: no supone que la relación sea lineal."""
    if len(x) < 3 or len(set(x)) < 2 or len(set(y)) < 2:
        return None
    return statistics.correlation(_rangos(x), _rangos(y))


def _rangos(valores: list[float]) -> list[float]:
    ordenados = sorted(valores)
    return [ordenados.index(v) + (ordenados.count(v) + 1) / 2 for v in valores]


def analizar_registro(texto: str, sin_base: set[str]) -> Registro:
    """Cada línea de `-v` lleva marca de tiempo: la diferencia entre dos seguidas es lo que tardó la segunda prueba."""
    region = _REGION.search(texto)
    marcas = [(_fecha(fecha), archivo) for fecha, archivo in _LINEA_DE_PRUEBA.findall(texto)]
    con_consulta, sin = [], []
    for (anterior, _), (actual, archivo) in zip(marcas, marcas[1:]):
        segundos = (actual - anterior).total_seconds()
        if archivo in sin_base:
            sin.append(segundos)
        elif segundos >= UMBRAL_CON_CONSULTA_S:
            con_consulta.append(segundos)
    return Registro(
        region=region.group(1).lower() if region else None,
        pruebas=len(marcas),
        mediana_con_consulta_ms=round(statistics.median(con_consulta) * 1000, 1) if con_consulta else None,
        media_sin_base_ms=round(statistics.fmean(sin) * 1000, 1) if sin else None,
        primera_con_consulta_s=round(con_consulta[0], 2) if con_consulta else None,
    )


def archivos_sin_base(raiz: Path = RAIZ) -> set[str]:
    return {
        f"tests/{ruta.name}" for ruta in (raiz / "tests").glob("test_*.py")
        if not _USA_LA_BASE.search(ruta.read_text(encoding="utf-8-sig", errors="replace"))
    }


def corrida_del_trabajo(run: dict, job: dict) -> Corrida | None:
    """Todo Pytest contra Neon ocupa la rama, también el que falla; solo es medible el completo que terminó bien. Tras
    CI-02 las ramas usan un contenedor, que se reconoce porque en ellas se omite el paso de esperar turno."""
    pasos = {paso["name"]: paso for paso in job.get("steps") or []}
    pytest_ = next((pasos[nombre] for nombre in PASOS_PYTEST if nombre in pasos), None)
    if job["name"] not in ARNESES or not pytest_ or not (pytest_.get("started_at") and pytest_.get("completed_at")):
        return None
    if pytest_.get("conclusion") == "skipped" or pasos.get(PASO_TURNO, {}).get("conclusion") == "skipped":
        return None
    rama = run.get("head_branch") or ""
    bases = [pr["base"]["ref"] for pr in run.get("pull_requests") or []]
    inicio, fin = pytest_["started_at"], pytest_["completed_at"]
    return Corrida(
        id=run["id"], inicio=inicio, fin=fin, minutos=round((_fecha(fin) - _fecha(inicio)).total_seconds() / 60, 1),
        arnes=job["name"], evento=run["event"], rama=rama, rama_neon=rama_neon(rama),
        hacia_main=rama == "main" or "main" in bases,
        medible=job["name"] in ARNES_COMPLETOS and pytest_.get("conclusion") == "success",
    )


def asignar_solapamientos(corridas: list[Corrida]) -> None:
    for corrida in corridas:
        otras = [c for c in corridas if c is not corrida]
        misma = [(c.inicio, c.fin) for c in otras if c.rama_neon == corrida.rama_neon]
        ajena = [(c.inicio, c.fin) for c in otras if c.rama_neon != corrida.rama_neon]
        corrida.solapadas_misma_rama = solapadas(corrida.inicio, corrida.fin, misma)
        corrida.solapadas_otra_rama = solapadas(corrida.inicio, corrida.fin, ajena)
        previas = [c.fin for c in otras if c.rama_neon == corrida.rama_neon and c.fin <= corrida.inicio]
        if previas:
            corrida.reposo_min = round((_fecha(corrida.inicio) - _fecha(max(previas))).total_seconds() / 60, 1)


def varianza_explicada(grupos: list[list[float]]) -> float | None:
    """Parte de la varianza total que se debe a la diferencia entre grupos (eta cuadrado)."""
    todos = [valor for grupo in grupos for valor in grupo]
    if len(todos) < 2 or len(set(todos)) < 2:
        return None
    media = statistics.fmean(todos)
    entre = sum(len(grupo) * (statistics.fmean(grupo) - media) ** 2 for grupo in grupos if grupo)
    return entre / sum((valor - media) ** 2 for valor in todos)


def _por_prueba(corrida: Corrida) -> float:
    return corrida.minutos * 60 / corrida.pruebas


def _por_region(corridas: list[Corrida]) -> dict[str, list[Corrida]]:
    grupos: dict[str, list[Corrida]] = {}
    for corrida in corridas:
        grupos.setdefault(corrida.region or "sin registro", []).append(corrida)
    return grupos


def relativas(corridas: list[Corrida]) -> list[tuple[Corrida, float]]:
    """Cada corrida frente a la mediana de su región: lo que queda por explicar una vez descontada la distancia."""
    salida = []
    for grupo in _por_region(corridas).values():
        mediana = statistics.median(_por_prueba(c) for c in grupo)
        salida += [(c, _por_prueba(c) / mediana) for c in grupo]
    return salida


def _r(valor: float | None) -> str:
    return "n/d" if valor is None else f"{valor:.2f}"


def resumen(corridas: list[Corrida]) -> str:
    medibles = [c for c in corridas if c.medible and c.pruebas]
    filas = [
        f"Corridas medibles: {len(medibles)}; hacia `main`: {sum(c.hacia_main for c in medibles)}.\n",
        "| Región | Corridas | Hacia `main` | Min (mín / mediana / máx) | s por prueba | Consulta (ms) | Sin base (ms) |",
        "| :--- | ---: | ---: | :--- | ---: | ---: | ---: |",
    ]
    grupos = _por_region(medibles)
    for region, grupo in sorted(grupos.items(), key=lambda par: statistics.median(c.minutos for c in par[1])):
        minutos = [c.minutos for c in grupo]
        consulta = [c.mediana_con_consulta_ms for c in grupo if c.mediana_con_consulta_ms]
        control = [c.media_sin_base_ms for c in grupo if c.media_sin_base_ms]
        filas.append(
            f"| {region} | {len(grupo)} | {sum(c.hacia_main for c in grupo)} "
            f"| {min(minutos)} / {statistics.median(minutos)} / {max(minutos)} "
            f"| {statistics.median(_por_prueba(c) for c in grupo):.2f} "
            f"| {statistics.median(consulta):.0f} | {statistics.median(control):.1f} |"
        )
    resto = relativas(medibles)
    reposos = [c for c, _ in resto if c.reposo_min is not None and c.primera_con_consulta_s]
    hora = [_fecha(c.inicio).hour for c, _ in resto]
    razon = [r for _, r in resto]
    filas += [
        "",
        f"- Varianza de los segundos por prueba explicada por la región: "
        f"{_r(varianza_explicada([[_por_prueba(c) for c in g] for g in grupos.values()]))}.",
        f"- Tras descontar la región, Spearman con corridas solapadas en la misma rama: "
        f"{_r(spearman([c.solapadas_misma_rama for c, _ in resto], razon))}.",
        f"- Tras descontar la región, Spearman con corridas solapadas en otras ramas: "
        f"{_r(spearman([c.solapadas_otra_rama for c, _ in resto], razon))}.",
        f"- Tras descontar la región, Spearman con la hora UTC: {_r(spearman(hora, razon))}.",
        f"- Spearman entre minutos de reposo de la rama y primera consulta: "
        f"{_r(spearman([c.reposo_min for c in reposos], [c.primera_con_consulta_s for c in reposos]))}.",
    ]
    return "\n".join(filas) + "\n"


def _gh(ruta: str, *opciones: str) -> str:
    comando = ["gh", "api", ruta, *opciones]
    return subprocess.run(comando, capture_output=True, encoding="utf-8", errors="replace", check=True).stdout


def bajar_corridas(cuantas: int) -> list[dict]:
    corridas: list[dict] = []
    pagina = 1
    while len(corridas) < cuantas:
        ruta = f"repos/{REPOSITORIO}/actions/workflows/{WORKFLOW}/runs?per_page=100&page={pagina}"
        lote = json.loads(_gh(ruta))["workflow_runs"]
        if not lote:
            break
        corridas += lote
        pagina += 1
    return corridas[:cuantas]


def _corridas_de(run: dict) -> list[tuple[Corrida, int]]:
    jobs = json.loads(_gh(f"repos/{REPOSITORIO}/actions/runs/{run['id']}/jobs?per_page=50"))["jobs"]
    return [(c, job["id"]) for job in jobs if (c := corrida_del_trabajo(run, job))]


def _completar_con_registro(par: tuple[Corrida, int], sin_base: set[str]) -> None:
    corrida, job = par
    try:
        registro = analizar_registro(_gh(f"repos/{REPOSITORIO}/actions/jobs/{job}/logs", "--allow-escape-sequences"), sin_base)
    except subprocess.CalledProcessError:  # GitHub borra los registros antiguos: la corrida queda sin esas columnas
        return
    for campo, valor in asdict(registro).items():
        setattr(corrida, campo, valor)


def tabla(corridas: list[Corrida]) -> str:
    filas = [
        "| Corrida | Inicio (UTC) | Rama Neon | Hacia `main` | Región | Min | Pruebas | Consulta (ms) "
        "| Sin base (ms) | Primera consulta (s) | Reposo (min) | Solapadas misma rama | Solapadas otra rama |",
        "| :--- | :--- | :--- | :--- | :--- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for c in sorted((c for c in corridas if c.medible), key=lambda x: x.inicio, reverse=True):
        filas.append(
            f"| {c.id} | {c.inicio[:16].replace('T', ' ')} | `{c.rama_neon}` | {'sí' if c.hacia_main else 'no'} "
            f"| {c.region or 'sin registro'} | {c.minutos} | {c.pruebas or '-'} | {c.mediana_con_consulta_ms or '-'} "
            f"| {c.media_sin_base_ms or '-'} | {c.primera_con_consulta_s or '-'} "
            f"| {c.reposo_min if c.reposo_min is not None else '-'} | {c.solapadas_misma_rama} | {c.solapadas_otra_rama} |"
        )
    return "\n".join(filas) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--corridas", type=int, default=300, help="corridas del flujo que se revisan")
    ap.add_argument("--salida", type=Path, help="escribe aquí la tabla en Markdown; sin esto, a la salida estándar")
    ap.add_argument("--json", type=Path, help="escribe además las cifras por corrida")
    args = ap.parse_args(argv)

    runs = bajar_corridas(args.corridas)
    with ThreadPoolExecutor(HILOS) as hilos:
        pares = [par for lote in hilos.map(_corridas_de, runs) for par in lote]
        sin_base = archivos_sin_base()
        list(hilos.map(lambda par: _completar_con_registro(par, sin_base), pares))
    corridas = [corrida for corrida, _ in pares]
    asignar_solapamientos(corridas)
    print(f"{len(corridas)} corridas, {sum(1 for c in corridas if c.pruebas)} con registro legible.", file=sys.stderr)

    resultado = f"{resumen(corridas)}\n{tabla(corridas)}"
    if args.salida:
        args.salida.write_text(resultado, encoding="utf-8")
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(resultado)
    if args.json:
        args.json.write_text(json.dumps([asdict(c) for c in corridas], indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
