# -*- coding: utf-8 -*-
# ¤cloud-run-perf ¤adpa ¤arbitro
"""Selector TIA (Test Impact Analysis) determinista por grafo ADPA (GCP-02).

Dado el diff de una rama (`git diff --name-only`), decide qué suites de `pytest` corren, si hace falta
compilar `frontend/` y cuántos shards de Playwright se necesitan. Es una función pura del diff, de la matriz
`governance/operaciones/ci_tia_matrix.json` y del árbol: mismo diff y mismo árbol, mismo resultado.

Principio: ante la duda corre todo. Solo se acota un diff cuando cada archivo se reconoce con certeza:
  features/<sala>/**              la sala y sus dependientes (import directo o por app_core.pasillo)
  app_core/pasillo/<sala>.py      R2: la sala, sus dependientes y las salas dueñas de las secciones #ID
  tests/test_*.py                 esa prueba
  frontend/**, governance/**, docs/**   zona: corren las pruebas que la nombran
  app_core/db/**, alembic/**      R3: transversal, corre todo
  cualquier otro archivo          corre todo

Lo que nunca se omite en un diff acotado: el piso de la matriz (`test_alembic_cabeza_por_sala`,
`test_sin_sql_interpolado`, los vigilantes ADPA y los arneses) y el núcleo, es decir, las pruebas sin sala o
que recorren todo el repositorio. Si falta alguna prueba del piso, el resultado es «completo».

La heurística de qué prueba pertenece a qué sala no se duplica: se carga de `scripts/seleccionar_pruebas.py`
(ADPA §3, ADR 0001) por su ruta. Si ese archivo no está o no se puede leer, el resultado es «completo».
Este módulo es una herramienta de verificación local y de CI, no de la ruta de ejecución de la aplicación.

    python -m app_core.cloud.tia_adpa_selector --base origin/main --cabeza HEAD
    python -m app_core.cloud.tia_adpa_selector --archivos features/rat/rat_service.py
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Sequence

RAIZ = Path(__file__).resolve().parents[2]
MATRIZ = RAIZ / "governance" / "operaciones" / "ci_tia_matrix.json"
COMPLETO = "completo"
SALAS = "salas"
ZONAS = {"frontend": "frontend", "governance": "governance", "docs": "docs/"}


@dataclass(frozen=True)
class ImpactoPruebasADPA:
    salas_afectadas: list[str]
    archivos_pytest: list[str]
    requiere_frontend_build: bool
    playwright_shards: int
    modo: str = SALAS
    motivos: list[str] = field(default_factory=list)

    @property
    def es_completo(self) -> bool:
        return self.modo == COMPLETO


def cargar_matriz(ruta: Path = MATRIZ) -> dict:
    matriz = json.loads(ruta.read_text(encoding="utf-8"))
    for clave in ("piso_siempre", "contratos_cliente", "playwright", "pendientes"):
        if clave not in matriz:
            raise ValueError(f"la matriz no declara «{clave}»")
    return matriz


@lru_cache(maxsize=4)
def _selector_base(raiz: str):
    ruta = Path(raiz) / "scripts" / "seleccionar_pruebas.py"
    if not ruta.is_file():
        return None
    spec = importlib.util.spec_from_file_location("_tia_seleccionar_pruebas", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modulo  # los dataclasses del módulo base lo buscan por nombre
    spec.loader.exec_module(modulo)
    return modulo


@dataclass(frozen=True)
class ArbolADPA:
    """Lo que se lee del árbol: salas, pruebas con su sala y quién depende de quién. Se calcula una vez por corrida."""

    base: object
    salas_reales: tuple[str, ...]
    pruebas: list
    usada_por: dict


def analizar_arbol(raiz: Path = RAIZ) -> ArbolADPA | None:
    """`None` si no hay selector base que cargar: el llamador responde «completo»."""
    base = _selector_base(str(raiz))
    if base is None:
        return None
    salas = base.salas_del_repositorio(raiz)
    return ArbolADPA(base, salas, base.mapa_de_pruebas(raiz, salas), base.dependientes_de_salas(raiz, salas))


def _glob_a_regex(patron: str) -> re.Pattern[str]:
    salida, i = "", 0
    while i < len(patron):
        if patron.startswith("**", i):
            salida, i = salida + ".*", i + 2
        elif patron[i] == "*":
            salida, i = salida + "[^/]*", i + 1
        else:
            salida, i = salida + re.escape(patron[i]), i + 1
    return re.compile(salida + r"\Z")


def _normalizar(ruta: str) -> str | None:
    """Ruta relativa con barras normales; `None` si no es una ruta del repositorio (absoluta o con `..`)."""
    limpia = ruta.strip().replace("\\", "/")
    while limpia.startswith("./"):
        limpia = limpia[2:]
    if not limpia or limpia.startswith("/") or re.match(r"[A-Za-z]:", limpia) or ".." in limpia.split("/"):
        return None
    return limpia


def _carpetas_de_playwright(raiz: Path, fuera: Sequence[str]) -> set[str]:
    base = raiz / "frontend" / "tests"
    if not base.is_dir():
        return set()
    return {p.name for p in base.iterdir() if p.is_dir() and p.name not in fuera}


def _dueñas_de_pasillo(raiz: Path, sala: str, salas: set[str]) -> set[str] | None:
    """Salas dueñas de las secciones `app_core/pasillo/<sala>.py#<ID>`, leídas de la propiedad de las fichas."""
    patron = re.compile(r"app_core/pasillo/" + re.escape(sala) + r"\.py#")
    dueñas: set[str] = set()
    for ficha in sorted((raiz / "governance" / "tareas").glob("*.md")):
        texto = ficha.read_text(encoding="utf-8")
        propiedad = re.search(r"^propiedad\s*=\s*\[(.*?)\]", texto, re.MULTILINE | re.DOTALL)
        if not propiedad or not patron.search(propiedad.group(1)):
            continue
        sala_de_la_ficha = re.search(r'^sala\s*=\s*"([^"]*)"', texto, re.MULTILINE)
        if not sala_de_la_ficha:
            return None
        dueñas |= {t.strip() for t in sala_de_la_ficha.group(1).split(",")} & salas
    return dueñas


def _completo(motivos: list[str], salas: Sequence[str], total_shards: int) -> ImpactoPruebasADPA:
    return ImpactoPruebasADPA(sorted(salas), ["tests"], True, total_shards, COMPLETO, motivos)


def _piso(raiz: Path, matriz: dict) -> tuple[list[str], list[str]]:
    """(pruebas del piso que existen, entradas literales del piso que faltan en el árbol)."""
    existentes, faltan = set(), []
    for patron in matriz["piso_siempre"]:
        encontradas = sorted(raiz.glob(patron))
        if not encontradas and not any(c in patron for c in "*?["):
            faltan.append(patron)
        existentes.update(p.relative_to(raiz).as_posix() for p in encontradas if p.is_file())
    return sorted(existentes), faltan


def calcular_impacto_adpa(
    archivos_diff: Sequence[str],
    *,
    raiz: Path = RAIZ,
    matriz: dict | None = None,
    arbol: ArbolADPA | None = None,
    solo_existentes: bool = False,
) -> ImpactoPruebasADPA:
    """Impacto de un diff. Con `solo_existentes`, las pruebas declaradas de salas pendientes que aún no existen se omiten.

    `arbol` permite reutilizar la lectura del árbol entre varias consultas (cuesta unos segundos)."""
    try:
        matriz = matriz if matriz is not None else cargar_matriz(raiz / "governance" / "operaciones" / "ci_tia_matrix.json")
        arbol = arbol if arbol is not None else analizar_arbol(raiz)
    except (OSError, ValueError, SyntaxError) as error:
        return _completo([f"no se pudo leer la matriz o el selector base: {type(error).__name__}"], [], 0)
    if arbol is None:
        return _completo(["falta scripts/seleccionar_pruebas.py"], [], 0)

    base, salas_reales = arbol.base, arbol.salas_reales
    pendientes = matriz["pendientes"]
    conocidas = set(salas_reales) | set(pendientes)
    carpetas = _carpetas_de_playwright(raiz, matriz["playwright"].get("fuera", []))
    todas = sorted(conocidas)

    archivos = []
    for original in archivos_diff:
        if not original or not original.strip():
            continue
        ruta = _normalizar(original)
        if ruta is None:
            return _completo([f"ruta que no es del repositorio: {original!r}"], todas, len(carpetas))
        archivos.append(ruta)
    archivos = sorted(set(archivos))
    if not archivos:
        return _completo(["sin lista de cambios"], todas, len(carpetas))

    tocadas: set[str] = set()
    zonas: set[str] = set()
    directas: set[str] = set()
    completo: list[str] = []
    for ruta in archivos:
        partes = ruta.split("/")
        if ruta.startswith(("app_core/db/", "alembic/")):
            completo.append(f"transversal (R3): {ruta}")
        elif partes[0] == "features" and len(partes) > 2 and partes[1] in conocidas:
            tocadas.add(partes[1])
        elif partes[:2] == ["app_core", "pasillo"] and len(partes) == 3 and partes[2].endswith(".py") and partes[2] != "__init__.py":
            sala = partes[2][:-3]
            dueñas = _dueñas_de_pasillo(raiz, sala, conocidas) if sala in conocidas else None
            if dueñas is None:
                completo.append(f"pasillo sin sala o sin dueña resoluble: {ruta}")
            else:
                tocadas |= {sala} | dueñas
        elif partes[0] == "tests" and len(partes) == 2 and re.fullmatch(r"test_.*\.py", partes[1]):
            directas.add(ruta)
        elif partes[:2] == ["tests", "deuda_adpa"] and len(partes) == 3 and Path(partes[2]).stem in conocidas:
            tocadas.add(Path(partes[2]).stem)
        elif partes[0] in ZONAS and len(partes) > 1:
            zonas.add(ZONAS[partes[0]])
        else:
            completo.append(f"archivo no reconocido: {ruta}")
    if completo:
        return _completo(completo, todas, len(carpetas))

    piso, faltan = _piso(raiz, matriz)
    if faltan:
        return _completo([f"falta una prueba del piso: {', '.join(faltan)}"], todas, len(carpetas))

    usada_por = arbol.usada_por
    alcanzadas = set(tocadas)
    for sala in tocadas:
        alcanzadas |= base.cierre_dependientes(usada_por, sala)
    elegidas = {
        p.ruta for p in arbol.pruebas
        if p.es_nucleo or p.salas & alcanzadas or any(zona in p.texto for zona in zonas)
    }
    elegidas |= {d for d in directas if (raiz / d).is_file()}
    elegidas |= set(piso)
    for sala in sorted(alcanzadas & set(pendientes)):
        declaradas = pendientes[sala]["pruebas"]
        elegidas |= {t for t in declaradas if not solo_existentes or (raiz / t).is_file()}

    contratos = [_glob_a_regex(g) for g in matriz["contratos_cliente"]]
    disparan = [a for a in archivos if any(c.match(a) for c in contratos)]
    requiere = bool(disparan)
    sala_a_carpeta = matriz["playwright"]["sala_a_carpeta"]
    shards: set[str] = set()
    todos = False
    for ruta in disparan:
        partes = ruta.split("/")
        if partes[:2] == ["frontend", "tests"] and len(partes) > 3 and partes[2] in carpetas:
            shards.add(partes[2])
        elif partes[0] == "features" and len(partes) > 2 and partes[1] in conocidas:
            for sala in {partes[1]} | base.cierre_dependientes(usada_por, partes[1]):
                if sala in sala_a_carpeta and sala_a_carpeta[sala] in carpetas:
                    shards.add(sala_a_carpeta[sala])
                else:
                    todos = True
        else:
            todos = True
    cuantos = 0 if not requiere else (len(carpetas) if todos or not shards else len(shards))

    motivos = []
    if tocadas:
        motivos.append(f"salas tocadas: {', '.join(sorted(tocadas))}")
    if alcanzadas - tocadas:
        motivos.append(f"dependientes: {', '.join(sorted(alcanzadas - tocadas))}")
    if zonas:
        motivos.append(f"zonas: {', '.join(sorted(zonas))}")
    if directas:
        motivos.append(f"pruebas tocadas: {len(directas)}")
    motivos.append("frontend: se compila" if requiere else "frontend: se omite la compilación y la E2E")
    return ImpactoPruebasADPA(sorted(alcanzadas), sorted(elegidas), requiere, cuantos, SALAS, motivos)


def _archivos_del_diff(base: str, cabeza: str, raiz: Path) -> list[str]:
    salida = subprocess.run(
        ["git", "diff", "--name-only", f"{base}...{cabeza}"],
        cwd=raiz, capture_output=True, text=True, encoding="utf-8", check=True,
    ).stdout
    return [linea.strip() for linea in salida.splitlines() if linea.strip()]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="", help="revisión base; vacía corre todo")
    ap.add_argument("--cabeza", default="HEAD")
    ap.add_argument("--archivos", nargs="*", help="lista explícita de archivos cambiados")
    ap.add_argument("--todas-las-declaradas", action="store_true",
                    help="incluye las pruebas declaradas de salas pendientes aunque aún no existan")
    args = ap.parse_args(argv)
    if args.archivos is not None:
        archivos = args.archivos
    elif args.base:
        archivos = _archivos_del_diff(args.base, args.cabeza, RAIZ)
    else:
        archivos = []
    impacto = calcular_impacto_adpa(archivos, solo_existentes=not args.todas_las_declaradas)
    print(json.dumps({
        "modo": impacto.modo,
        "salas_afectadas": impacto.salas_afectadas,
        "archivos_pytest": impacto.archivos_pytest,
        "requiere_frontend_build": impacto.requiere_frontend_build,
        "playwright_shards": impacto.playwright_shards,
        "motivos": impacto.motivos,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
