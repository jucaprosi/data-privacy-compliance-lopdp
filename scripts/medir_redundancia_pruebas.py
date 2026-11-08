"""Mide pruebas redundantes de pytest y de Playwright (TEST-05). Solo mide y propone: no borra ni edita pruebas.

Pasos:
  1. ``cobertura``: corre pytest con ``--cov-context=test`` y deja un ``.coverage`` con las líneas de cada prueba.
  2. ``informe``: lee ese ``.coverage``; marca candidata a la prueba cuyas líneas están contenidas en las de otra
     prueba de la misma sala; corre mutación acotada a las líneas de la candidata y registra las mutaciones que
     detecta solo ella; lee el registro de una corrida de Playwright (reporter ``list`` o ``json``) y las rutas de
     cada spec (``page.goto``), y escribe ``governance/operaciones/CONSOLIDACION_PRUEBAS.md``.

Uso:
  python scripts/medir_redundancia_pruebas.py cobertura
  python scripts/medir_redundancia_pruebas.py informe --playwright-log ruta.log --mutar 40
"""
# ¤arbitro
# ¤¤qa-engineer
from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
INFORME = RAIZ / "governance" / "operaciones" / "CONSOLIDACION_PRUEBAS.md"
FUENTES = ("app_core", "features", "api", "scripts", "verificadores", "main.py")
MARCAS_DE_ERROR_REAL = re.compile(r"regresi[oó]n|error real|\bbug\b|incidente|fall[oó] en|corrige|naci[oó]", re.I)

# --------------------------------------------------------------------------------------------------------------
# Salas


def sala_de_archivo(ruta: str) -> str:
    """Sala de un archivo fuente: ``features/<sala>/…`` → ``<sala>``; ``app_core/<sub>/…`` → ``app_core``."""
    partes = Path(ruta.replace("\\", "/")).parts
    if "features" in partes:
        i = partes.index("features")
        if i + 1 < len(partes) - 1:
            return partes[i + 1]
    for raiz in ("app_core", "api", "scripts", "verificadores"):
        if raiz in partes:
            return raiz
    return "otros"


def sala_de_prueba(lineas: set[tuple[str, int]]) -> str:
    """La sala de una prueba es la que reúne más líneas cubiertas; empate por nombre."""
    cuenta: dict[str, int] = {}
    for archivo, _ in lineas:
        s = sala_de_archivo(archivo)
        cuenta[s] = cuenta.get(s, 0) + 1
    if not cuenta:
        return "sin-cobertura"
    return sorted(cuenta.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


# --------------------------------------------------------------------------------------------------------------
# Cobertura por contexto


def nodo_de_contexto(contexto: str) -> str:
    """``tests/x.py::t|run`` → ``tests/x.py::t``. Los contextos vacíos son la importación, no una prueba."""
    return contexto.split("|", 1)[0].strip()


def leer_contextos(ruta_coverage: Path) -> dict[str, set[tuple[str, int]]]:
    from coverage import CoverageData  # importación diferida: solo la necesita el paso de medición

    datos = CoverageData(basename=str(ruta_coverage))
    datos.read()
    por_prueba: dict[str, set[tuple[str, int]]] = {}
    for archivo in datos.measured_files():
        relativo = Path(archivo).resolve()
        try:
            relativo = relativo.relative_to(RAIZ)
        except ValueError:
            continue
        nombre = relativo.as_posix()
        for linea, contextos in (datos.contexts_by_lineno(archivo) or {}).items():
            for ctx in contextos:
                nodo = nodo_de_contexto(ctx)
                if nodo:
                    por_prueba.setdefault(nodo, set()).add((nombre, linea))
    return por_prueba


@dataclass
class Candidata:
    prueba: str
    contenedora: str
    sala: str
    lineas: int
    lineas_contenedora: int
    mutaciones_probadas: int = 0
    mutaciones_exclusivas: list[str] = field(default_factory=list)
    error_real: bool = False

    @property
    def misma_funcion(self) -> bool:
        """Variantes parametrizadas de una misma función: cambian datos de entrada, no líneas; no se fusionan."""
        return self.prueba.split("[", 1)[0] == self.contenedora.split("[", 1)[0]

    @property
    def recomendacion(self) -> str:
        if self.misma_funcion:
            return "conservar (variante parametrizada)"
        if self.mutaciones_exclusivas or self.error_real:
            return "conservar"
        if self.mutaciones_probadas == 0:
            return "pendiente de mutación"
        return "retirar" if self.lineas == self.lineas_contenedora else "fusionar"


def buscar_candidatas(por_prueba: dict[str, set[tuple[str, int]]]) -> list[Candidata]:
    """Una prueba es candidata si sus líneas están contenidas en las de otra prueba de su misma sala.

    Con conjuntos iguales solo la de nombre mayor queda como candidata, para no marcar a las dos.
    Se elige como contenedora la más pequeña que la contiene: es la sustituta más cercana.
    """
    salas: dict[str, list[str]] = {}
    for prueba, lineas in por_prueba.items():
        if lineas:
            salas.setdefault(sala_de_prueba(lineas), []).append(prueba)
    resultado: list[Candidata] = []
    for sala, pruebas in sorted(salas.items()):
        orden = sorted(pruebas, key=lambda p: (len(por_prueba[p]), p))
        for p in orden:
            mias = por_prueba[p]
            for q in orden:  # en orden de tamaño: la primera que la contiene es la más pequeña
                otras = por_prueba[q]
                if q == p or len(otras) < len(mias) or (len(otras) == len(mias) and q > p):
                    continue
                if mias <= otras:
                    resultado.append(Candidata(p, q, sala, len(mias), len(otras)))
                    break
    return resultado


# --------------------------------------------------------------------------------------------------------------
# Mutación acotada

_MUTACIONES = [
    (r"==", "!="), (r"!=", "=="), (r"<=", ">"), (r">=", "<"), (r"(?<![<>=!])<(?![<=])", ">="),
    (r"(?<![<>=!-])>(?![>=])", "<="), (r"\bTrue\b", "False"), (r"\bFalse\b", "True"),
    (r"\band\b", "or"), (r"\bor\b", "and"), (r"\bnot\s+", ""), (r"\bis not\b", "is"), (r"\bis\b(?! not)", "is not"),
    (r"\breturn\s+(?!None\b)\S.*$", "return None"), (r"(?<![+\-*/])\+(?![+=])", "-"),
]


def mutantes_de_linea(texto: str) -> list[str]:
    """Variantes de una línea con un solo operador cambiado. No muta comentarios, docstrings ni decoradores."""
    codigo = texto.split("#", 1)[0].rstrip()
    limpio = codigo.strip()
    if not limpio or limpio.startswith(("@", '"', "'", "def ", "class ", "import ", "from ", "async def ")):
        return []
    vistos: list[str] = []
    for patron, reemplazo in _MUTACIONES:
        m = re.search(patron, codigo)
        if not m:
            continue
        mutado = codigo[: m.start()] + re.sub(patron, reemplazo, m.group(0), count=1) + codigo[m.end():] + "\n"
        if mutado.rstrip() != codigo and mutado not in vistos:
            vistos.append(mutado)
    return vistos


def _resultados_pytest(nodos: list[str]) -> dict[str, bool]:
    """Corre los nodos y devuelve ``{nodo: pasó}``; una prueba que no aparece como PASSED cuenta como fallida."""
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-rA", "-p", "no:cacheprovider", "-o", "addopts=", *nodos],
        cwd=RAIZ, capture_output=True, text=True, timeout=600, encoding="utf-8", errors="replace",
    )
    return resultados_de_salida(r.stdout, nodos)


def resultados_de_salida(salida: str, nodos: list[str]) -> dict[str, bool]:
    pasaron = {m.group(1) for m in re.finditer(r"^PASSED (\S+)", salida, re.M)}
    return {n: n in pasaron for n in nodos}


def medir_mutaciones(c: Candidata, lineas: set[tuple[str, int]], por_candidata: int = 3) -> None:
    """Aplica hasta ``por_candidata`` mutantes en las líneas de la candidata; exclusiva si solo ella la detecta."""
    for archivo, linea in sorted(lineas):
        if c.mutaciones_probadas >= por_candidata:
            return
        ruta = RAIZ / archivo
        original = ruta.read_text(encoding="utf-8")
        filas = original.splitlines(keepends=True)
        if linea - 1 >= len(filas):
            continue
        for mutado in mutantes_de_linea(filas[linea - 1])[:1]:
            nuevo = "".join(filas[: linea - 1] + [mutado if mutado.endswith("\n") else mutado + "\n"] + filas[linea:])
            try:
                ast.parse(nuevo)
            except SyntaxError:
                continue
            try:
                ruta.write_text(nuevo, encoding="utf-8")
                pasa = _resultados_pytest([c.prueba, c.contenedora])
            finally:
                ruta.write_text(original, encoding="utf-8")
            c.mutaciones_probadas += 1
            if not pasa[c.prueba] and pasa[c.contenedora]:
                c.mutaciones_exclusivas.append(f"{archivo}:{linea}")


def nacio_por_error_real(nodo: str) -> bool:
    """La prueba (o su módulo) dice en su docstring que nació por un error real."""
    archivo, _, nombre = nodo.partition("::")
    ruta = RAIZ / archivo
    if not ruta.exists():
        return False
    try:
        arbol = ast.parse(ruta.read_text(encoding="utf-8-sig"))
    except SyntaxError:
        return False
    textos = [ast.get_docstring(arbol) or ""]
    objetivo = nombre.split("::")[-1].split("[")[0]
    for n in ast.walk(arbol):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == objetivo:
            textos.append(ast.get_docstring(n) or "")
    return any(MARCAS_DE_ERROR_REAL.search(t) for t in textos)


# --------------------------------------------------------------------------------------------------------------
# Playwright

_LINEA_LIST = re.compile(r"[✓✘]\s+\d+\s+(?:\[[^\]]+\]\s+›\s+)?(tests/[^\s:]+\.spec\.ts):\d+:\d+.*\(([\d.]+)(ms|s|m)\)\s*$")


def _segundos(valor: str, unidad: str) -> float:
    return float(valor) * {"ms": 0.001, "s": 1.0, "m": 60.0}[unidad]


def duraciones_desde_list(texto: str) -> dict[str, dict]:
    """Suma la duración de cada prueba por spec a partir del reporter ``list`` (también dentro de un log de CI)."""
    specs: dict[str, dict] = {}
    for linea in texto.splitlines():
        m = _LINEA_LIST.search(linea)
        if m:
            d = specs.setdefault(m.group(1), {"duracion_s": 0.0, "pruebas": 0})
            d["duracion_s"] += _segundos(m.group(2), m.group(3))
            d["pruebas"] += 1
    return specs


def duraciones_desde_json(datos: dict) -> dict[str, dict]:
    """Igual que ``duraciones_desde_list`` pero desde el reporter ``json`` de Playwright."""
    specs: dict[str, dict] = {}

    def recorrer(suite: dict) -> None:
        for spec in suite.get("specs", []):
            archivo = "tests/" + spec.get("file", "").replace("\\", "/").removeprefix("tests/")
            d = specs.setdefault(archivo, {"duracion_s": 0.0, "pruebas": 0})
            for prueba in spec.get("tests", []):
                d["pruebas"] += 1
                d["duracion_s"] += sum(r.get("duration", 0) for r in prueba.get("results", [])) / 1000
        for hija in suite.get("suites", []):
            recorrer(hija)

    for suite in datos.get("suites", []):
        recorrer(suite)
    return specs


_GOTO = re.compile(r"""\.goto\(\s*([`"'])(.+?)\1""")
_URL = re.compile(r"""toHaveURL\(\s*([`"'])(.+?)\1""")


def normalizar_ruta(ruta: str) -> str:
    ruta = re.sub(r"\$\{[^}]*\}", ":param", ruta).split("?", 1)[0].split("#", 1)[0]
    return ruta.rstrip("/") or "/"


def rutas_de_spec(texto: str) -> list[str]:
    """Rutas que recorre un spec: destinos de ``page.goto`` y URLs esperadas con ``toHaveURL``."""
    rutas = {normalizar_ruta(m.group(2)) for patron in (_GOTO, _URL) for m in patron.finditer(texto)}
    return sorted(r for r in rutas if r.startswith("/"))


def sala_de_spec(spec: str) -> str:
    partes = Path(spec).parts
    return partes[1] if len(partes) > 2 else "raiz"


def recorridos_repetidos(rutas: dict[str, list[str]]) -> list[list[str]]:
    """Grupos de specs con el mismo conjunto, no vacío, de rutas recorridas."""
    grupos: dict[tuple[str, ...], list[str]] = {}
    for spec, rs in rutas.items():
        if rs:
            grupos.setdefault(tuple(rs), []).append(spec)
    return sorted(sorted(g) for g in grupos.values() if len(g) > 1)


# --------------------------------------------------------------------------------------------------------------
# Informe


def escribir_informe(candidatas: list[Candidata], total_pruebas: int, cobertura_sala: dict[str, int],
                     specs: dict[str, dict], rutas: dict[str, list[str]], fuente_pw: str, nota: str = "") -> str:
    lineas = [
        "# Consolidación de pruebas · informe de TEST-05",
        "",
        "Generado por `python scripts/medir_redundancia_pruebas.py informe`. Solo mide y propone: ninguna prueba "
        "se borró ni se editó. La consolidación se hace después, en una ficha por sala (TEST-05a, TEST-05b…).",
        "",
        "## Criterio",
        "",
        "- **Candidata:** sus líneas cubiertas están contenidas en las de otra prueba de su misma sala "
        "(la contenedora).",
        "- **Retirar:** candidata con las mismas líneas que la contenedora y sin mutaciones exclusivas.",
        "- **Fusionar:** candidata contenida estrictamente y sin mutaciones exclusivas.",
        "- **Conservar:** alguna mutación exclusiva, o su docstring dice que nació por un error real, o es otra "
        "variante parametrizada de la misma función que la contenedora.",
        "- **Pendiente de mutación:** no se le corrió mutación en esta medición; no se decide sin ella.",
        "",
    ]
    if nota:
        lineas += ["## Condiciones de la medición", "", nota, ""]
    lineas += ["## pytest", "", f"Pruebas con cobertura medida: {total_pruebas}. Candidatas: {len(candidatas)}.", ""]
    por_sala: dict[str, list[Candidata]] = {}
    for c in candidatas:
        por_sala.setdefault(c.sala, []).append(c)
    for sala in sorted(set(por_sala) | set(cobertura_sala)):
        grupo = por_sala.get(sala, [])
        lineas += [f"### Sala `{sala}`", "",
                   f"Pruebas de la sala: {cobertura_sala.get(sala, 0)}. Candidatas: {len(grupo)}.", ""]
        if not grupo:
            continue
        lineas += ["| Candidata | Contenida en | Líneas (cand./cont.) | Mutaciones probadas | Mutaciones exclusivas "
                   "| Recomendación |", "|---|---|---|---|---|---|"]
        for c in sorted(grupo, key=lambda x: x.prueba):
            exclusivas = ", ".join(f"`{m}`" for m in c.mutaciones_exclusivas) or "ninguna"
            lineas.append(f"| `{c.prueba}` | `{c.contenedora}` | {c.lineas}/{c.lineas_contenedora} | "
                          f"{c.mutaciones_probadas} | {exclusivas} | {c.recomendacion} |")
        lineas.append("")
    total_pw = sum(d["duracion_s"] for d in specs.values())
    lineas += ["## Playwright", "", f"Fuente de duraciones: {fuente_pw}. Specs: {len(specs)}. "
               f"Duración sumada de las pruebas: {total_pw:.1f} s (suma por prueba; la corrida en paralelo tarda "
               "menos).", "", "En Playwright no se corre mutación: basta la duración y el solapamiento de rutas.", ""]
    repetidos = recorridos_repetidos({s: rutas.get(s, []) for s in specs})
    en_repetido = {s: i + 1 for i, g in enumerate(repetidos) for s in g}
    por_sala_pw: dict[str, list[str]] = {}
    for s in specs:
        por_sala_pw.setdefault(sala_de_spec(s), []).append(s)
    for sala in sorted(por_sala_pw):
        lineas += [f"### Sala `{sala}`", "", "| Spec | Pruebas | Duración (s) | Rutas que recorre | Mismo recorrido |",
                   "|---|---|---|---|---|"]
        for s in sorted(por_sala_pw[sala], key=lambda x: -specs[x]["duracion_s"]):
            rs = ", ".join(f"`{r}`" for r in rutas.get(s, [])) or "sin `page.goto` propio (usa ayudantes)"
            grupo = f"grupo {en_repetido[s]}" if s in en_repetido else "—"
            lineas.append(f"| `{s}` | {specs[s]['pruebas']} | {specs[s]['duracion_s']:.1f} | {rs} | {grupo} |")
        lineas.append("")
    if repetidos:
        lineas += ["### Specs que repiten el mismo recorrido", ""]
        for i, g in enumerate(repetidos, 1):
            lineas.append(f"- Grupo {i}: " + ", ".join(f"`{s}`" for s in g) + f" → {', '.join(rutas[g[0]])}")
        lineas.append("")
    return "\n".join(lineas)


# --------------------------------------------------------------------------------------------------------------
# CLI


def _cmd_cobertura(args: argparse.Namespace) -> int:
    cov = [f"--cov={f.removesuffix('.py')}" for f in FUENTES]
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "-o", "addopts=", *cov,
                           "--cov-context=test", "--cov-report=", *args.pytest], cwd=RAIZ).returncode


def _cmd_informe(args: argparse.Namespace) -> int:
    por_prueba = leer_contextos(Path(args.coverage))
    candidatas = buscar_candidatas(por_prueba)
    cobertura_sala: dict[str, int] = {}
    for lineas in por_prueba.values():
        if lineas:
            s = sala_de_prueba(lineas)
            cobertura_sala[s] = cobertura_sala.get(s, 0) + 1
    for i, c in enumerate(sorted(candidatas, key=lambda x: (x.sala, x.prueba))):
        c.error_real = nacio_por_error_real(c.prueba)
        if i < args.mutar and not c.error_real:
            medir_mutaciones(c, por_prueba[c.prueba], args.por_candidata)
    specs: dict[str, dict] = {}
    fuente = "sin registro de Playwright"
    if args.playwright_json:
        specs = duraciones_desde_json(json.loads(Path(args.playwright_json).read_text(encoding="utf-8")))
        fuente = f"reporte json `{Path(args.playwright_json).name}`"
    elif args.playwright_log:
        specs = duraciones_desde_list(Path(args.playwright_log).read_text(encoding="utf-8", errors="replace"))
        fuente = args.fuente or f"registro `{Path(args.playwright_log).name}`"
    frontend = RAIZ / "frontend"
    rutas = {s: rutas_de_spec((frontend / s).read_text(encoding="utf-8")) for s in specs if (frontend / s).exists()}
    texto = escribir_informe(candidatas, sum(1 for v in por_prueba.values() if v), cobertura_sala, specs, rutas,
                             fuente, args.nota)
    Path(args.salida).write_text(texto + "\n", encoding="utf-8")
    print(f"Informe: {args.salida} ({len(candidatas)} candidatas, {len(specs)} specs)")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="orden", required=True)
    c = sub.add_parser("cobertura", help="Corre pytest con cobertura por contexto.")
    c.add_argument("pytest", nargs="*", help="Argumentos extra para pytest.")
    c.set_defaults(func=_cmd_cobertura)
    i = sub.add_parser("informe", help="Escribe CONSOLIDACION_PRUEBAS.md.")
    i.add_argument("--coverage", default=str(RAIZ / ".coverage"))
    i.add_argument("--playwright-log", help="Registro con el reporter list (por ejemplo, gh run view --log).")
    i.add_argument("--playwright-json", help="Reporte json de Playwright.")
    i.add_argument("--fuente", default="", help="Texto que describe de dónde salió el registro de Playwright.")
    i.add_argument("--mutar", type=int, default=40, help="Cuántas candidatas reciben mutación.")
    i.add_argument("--por-candidata", type=int, default=3, help="Mutantes por candidata.")
    i.add_argument("--nota", default="", help="Condiciones de la medición que el informe debe declarar.")
    i.add_argument("--salida", default=str(INFORME))
    i.set_defaults(func=_cmd_informe)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
