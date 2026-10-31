# -*- coding: utf-8 -*-
# ¤adpa ¤arbitro
"""Selección de pruebas por el alcance del cambio: salas o repositorio completo (ADPA §3, ADR 0001).

Un cambio confinado a salas corre las pruebas de esas salas, las de las salas que dependen de ellas y
el núcleo. Un cambio en lo compartido (app_core, api, alembic, main.py, conftest, CI...) corre todo.

Clasificación de cada archivo cambiado:
  features/<sala>/**             la sala
  api/routers/<r>.py             las salas que importa ese router
  tests/test_*.py                esa prueba
  tests/deuda_adpa/<sala>.txt    la sala
  frontend/**, governance/**, docs/**              zona: corren las pruebas que la nombran
  scripts/*, verificadores/*, documentos de la raíz   zona: corren las pruebas que nombran el archivo
  cualquier otro archivo         compartido: corre todo

Una prueba pertenece a una sala si importa `features.<sala>` o `app_core.pasillo.<sala>`, o si nombra el
prefijo HTTP de un router de esa sala. Las pruebas sin sala son el núcleo y corren siempre.

Es una heurística que solo amplía lo elegido y nunca sustituye a la corrida completa: el push a
dev/<persona> y a main corre siempre toda la suite.
"""
from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ZONAS_POR_CARPETA = {"frontend": "frontend", "governance": "governance", "docs": "docs/"}
CARPETAS_CON_ZONA_POR_ARCHIVO = ("scripts", "verificadores")
DOCUMENTOS_RAIZ = (".md", ".pdf", ".png", ".jpg", ".xlsx", ".docx")
COMPARTIDO = "compartido"


# ¤adpa
def salas_del_repositorio(raiz: Path = RAIZ) -> tuple[str, ...]:
    return tuple(sorted(p.name for p in (raiz / "features").iterdir() if p.is_dir() and not p.name.startswith("__")))


# ¤adpa
def modulos_importados(fuente: str) -> set[str]:
    """Módulos que nombra un archivo, también en imports dentro de funciones; `from features import x` es features.x."""
    modulos: set[str] = set()
    for nodo in ast.walk(ast.parse(fuente)):
        if isinstance(nodo, ast.Import):
            modulos.update(alias.name for alias in nodo.names)
        elif isinstance(nodo, ast.ImportFrom) and nodo.module and nodo.level == 0:
            modulos.add(nodo.module)
            if nodo.module in ("features", "app_core.pasillo") or re.fullmatch(r"features\.[a-z_0-9]+", nodo.module):
                modulos.update(f"{nodo.module}.{alias.name}" for alias in nodo.names)
    return modulos


# ¤adpa
def salas_de_modulos(modulos: set[str], salas: tuple[str, ...]) -> set[str]:
    """`features.<sala>` y `app_core.pasillo.<sala>` cuentan igual: por el pasillo también se depende de la sala."""
    encontradas = set()
    for modulo in modulos:
        partes = modulo.split(".")
        if partes[0] == "features" and len(partes) > 1 and partes[1] in salas:
            encontradas.add(partes[1])
        elif partes[:2] == ["app_core", "pasillo"] and len(partes) > 2 and partes[2] in salas:
            encontradas.add(partes[2])
    return encontradas


def salas_de_archivo(ruta: Path, salas: tuple[str, ...]) -> set[str]:
    try:
        return salas_de_modulos(modulos_importados(ruta.read_text(encoding="utf-8")), salas)
    except (SyntaxError, UnicodeDecodeError, OSError):
        return set()


# ¤adpa
def prefijos_de_routers(raiz: Path, salas: tuple[str, ...]) -> dict[str, frozenset[str]]:
    """Prefijo HTTP de cada router -> salas que importa. Varios routers comparten prefijo (/diagnostico, /roadmaps)."""
    prefijos: dict[str, set[str]] = {}
    for ruta in sorted((raiz / "api" / "routers").glob("*.py")):
        coincidencia = re.search(r'APIRouter\(\s*prefix\s*=\s*"([^"]+)"', ruta.read_text(encoding="utf-8"))
        if coincidencia:
            prefijos.setdefault(coincidencia.group(1), set()).update(salas_de_archivo(ruta, salas))
    return {prefijo: frozenset(encontradas) for prefijo, encontradas in prefijos.items() if encontradas}


def patron_prefijo(prefijo: str) -> re.Pattern[str]:
    """`/rat` nombra la sala en "/rat/eipd" o '/rat', pero no en "/rated"."""
    return re.compile(re.escape(prefijo) + r"(?=[/\"'?\s])")


# ¤adpa
def dependientes_de_salas(raiz: Path, salas: tuple[str, ...]) -> dict[str, set[str]]:
    """sala -> salas que la usan, por import directo o por app_core.pasillo.<sala>."""
    usada_por: dict[str, set[str]] = {sala: set() for sala in salas}
    for ruta in (raiz / "features").rglob("*.py"):
        partes = ruta.relative_to(raiz / "features").parts
        if len(partes) < 2:
            continue
        for destino in salas_de_archivo(ruta, salas):
            if destino != partes[0]:
                usada_por[destino].add(partes[0])
    return usada_por


def cierre_dependientes(usada_por: dict[str, set[str]], sala: str) -> set[str]:
    vistas, pila = set(), [sala]
    while pila:
        for dependiente in usada_por.get(pila.pop(), ()):
            if dependiente not in vistas:
                vistas.add(dependiente)
                pila.append(dependiente)
    vistas.discard(sala)
    return vistas


@dataclass(frozen=True)
class Prueba:
    ruta: str
    salas: frozenset[str]
    texto: str = field(repr=False, compare=False)

    @property
    def es_nucleo(self) -> bool:
        """Sin sala no hay mamparo que la confine: corre siempre."""
        return not self.salas


# ¤adpa
def mapa_de_pruebas(raiz: Path = RAIZ, salas: tuple[str, ...] | None = None) -> list[Prueba]:
    salas = salas or salas_del_repositorio(raiz)
    prefijos = prefijos_de_routers(raiz, salas)
    patrones = {prefijo: patron_prefijo(prefijo) for prefijo in prefijos}
    pruebas = []
    for ruta in sorted((raiz / "tests").glob("test_*.py")):
        texto = ruta.read_text(encoding="utf-8")
        encontradas = set(salas_de_archivo(ruta, salas))
        for prefijo, patron in patrones.items():
            if patron.search(texto):
                encontradas |= prefijos[prefijo]
        pruebas.append(Prueba(ruta.relative_to(raiz).as_posix(), frozenset(encontradas), texto))
    return pruebas


@dataclass(frozen=True)
class Objetivo:
    tipo: str  # sala | zona | prueba | compartido
    nombre: str


# ¤adpa
def clasificar(ruta: str, salas: tuple[str, ...], raiz: Path = RAIZ) -> tuple[Objetivo, ...]:
    partes = Path(ruta).as_posix().split("/")
    carpeta = partes[0]
    if carpeta == "features" and len(partes) > 2 and partes[1] in salas:
        return (Objetivo("sala", partes[1]),)
    if partes[:2] == ["api", "routers"] and len(partes) == 3 and partes[2] != "__init__.py":
        importadas = salas_de_archivo(raiz / ruta, salas)
        return tuple(Objetivo("sala", s) for s in sorted(importadas)) or (Objetivo(COMPARTIDO, ruta),)
    if carpeta == "tests":
        if len(partes) == 2 and re.fullmatch(r"test_.*\.py", partes[1]):
            return (Objetivo("prueba", ruta),)
        if len(partes) == 3 and partes[1] == "deuda_adpa" and Path(partes[2]).stem in salas:
            return (Objetivo("sala", Path(partes[2]).stem),)
        return (Objetivo(COMPARTIDO, ruta),)
    if carpeta in ZONAS_POR_CARPETA and len(partes) > 1:
        return (Objetivo("zona", ZONAS_POR_CARPETA[carpeta]),)
    if carpeta in CARPETAS_CON_ZONA_POR_ARCHIVO and len(partes) > 1:
        return (Objetivo("zona", Path(partes[-1]).stem),)
    if len(partes) == 1 and ruta.endswith(DOCUMENTOS_RAIZ):
        return (Objetivo("zona", partes[0]),)
    return (Objetivo(COMPARTIDO, ruta),)


@dataclass
class Seleccion:
    modo: str  # salas | completo
    motivos: list[str]
    salas: list[str] = field(default_factory=list)
    zonas: list[str] = field(default_factory=list)
    pruebas: list[str] = field(default_factory=list)
    necesita_node: bool = True

    @property
    def etiqueta(self) -> str:
        if self.modo == "completo":
            return "completo"
        partes = [f"salas: {', '.join(self.salas)}"] if self.salas else []
        if self.zonas:
            partes.append(f"zonas: {', '.join(self.zonas)}")
        return "; ".join(partes) or "núcleo"


# ¤adpa
def seleccionar(archivos: list[str], raiz: Path = RAIZ, pruebas: list[Prueba] | None = None) -> Seleccion:
    """Sin cambios conocidos o con un archivo compartido se corre todo; si no, salas, dependientes, zonas y núcleo."""
    if not archivos:
        return Seleccion("completo", ["sin lista de cambios"])
    salas = salas_del_repositorio(raiz)
    objetivos = [objetivo for archivo in archivos for objetivo in clasificar(archivo, salas, raiz)]
    compartidos = [o.nombre for o in objetivos if o.tipo == COMPARTIDO]
    if compartidos:
        return Seleccion("completo", [f"archivo compartido: {nombre}" for nombre in compartidos])

    usada_por = dependientes_de_salas(raiz, salas)
    tocadas = {o.nombre for o in objetivos if o.tipo == "sala"}
    alcanzadas = set(tocadas)
    for sala in tocadas:
        alcanzadas |= cierre_dependientes(usada_por, sala)
    zonas = {o.nombre for o in objetivos if o.tipo == "zona"}
    directas = {o.nombre for o in objetivos if o.tipo == "prueba"}
    pruebas = pruebas if pruebas is not None else mapa_de_pruebas(raiz, salas)
    elegidas = [
        p for p in pruebas
        if p.es_nucleo or p.salas & alcanzadas or p.ruta in directas or any(zona in p.texto for zona in zonas)
    ]
    motivos = []
    if tocadas:
        motivos.append(f"salas tocadas: {', '.join(sorted(tocadas))}")
    if alcanzadas - tocadas:
        motivos.append(f"dependientes: {', '.join(sorted(alcanzadas - tocadas))}")
    if zonas:
        motivos.append(f"zonas: {', '.join(sorted(zonas))}")
    if directas:
        motivos.append(f"pruebas tocadas: {len(directas)}")
    return Seleccion(
        "salas", motivos, sorted(alcanzadas), sorted(zonas), sorted(p.ruta for p in elegidas),
        necesita_node=any('"node"' in p.texto for p in elegidas),
    )


def _git(args: list[str], raiz: Path) -> list[str]:
    salida = subprocess.run(["git", *args], cwd=raiz, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return [linea.strip() for linea in salida.splitlines() if linea.strip()]


def archivos_del_diff(base: str, cabeza: str, raiz: Path = RAIZ) -> list[str]:
    """Lo que un PR cambia: el diff entre la base y la cabeza desde su antecesor común."""
    return _git(["diff", "--name-only", f"{base}...{cabeza}"], raiz)


def archivos_cambiados_localmente(base: str, raiz: Path = RAIZ) -> list[str]:
    """Lo que hay en el worktree frente a una revisión, incluidos los archivos aún sin añadir."""
    return sorted(set(_git(["diff", "--name-only", base], raiz)) | set(_git(["ls-files", "--others", "--exclude-standard"], raiz)))


def escribir_salida_github(seleccion: Seleccion, ruta: str) -> None:
    with open(ruta, "a", encoding="utf-8") as salida:
        salida.write(f"modo={seleccion.modo}\n")
        salida.write(f"etiqueta={seleccion.etiqueta}\n")
        salida.write(f"pruebas={' '.join(seleccion.pruebas)}\n")
        salida.write(f"frontend={'true' if 'frontend' in seleccion.zonas else 'false'}\n")
        salida.write(f"node={'true' if seleccion.necesita_node else 'false'}\n")


def imprimir_mapa(raiz: Path) -> None:
    pruebas = mapa_de_pruebas(raiz)
    for prueba in pruebas:
        print(f"{prueba.ruta:48} {'núcleo' if prueba.es_nucleo else ', '.join(sorted(prueba.salas))}")
    print(f"\n{len(pruebas)} archivos de prueba, {sum(p.es_nucleo for p in pruebas)} del núcleo.")


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="", help="revisión base del PR; vacía en un push, que corre todo")
    ap.add_argument("--cabeza", default="", help="revisión de la cabeza del PR (por defecto HEAD)")
    ap.add_argument("--local", metavar="REV", help="cambios del worktree frente a REV, con los archivos sin añadir")
    ap.add_argument("--archivos", nargs="*", help="lista explícita de archivos cambiados")
    ap.add_argument("--mapa", action="store_true", help="imprime la sala de cada prueba y termina")
    ap.add_argument("--salida-github", action="store_true", help="anota modo, pruebas y banderas en $GITHUB_OUTPUT")
    args = ap.parse_args(argv)

    if args.mapa:
        imprimir_mapa(RAIZ)
        return 0
    if args.archivos is not None:
        seleccion = seleccionar(args.archivos, RAIZ)
    elif args.local:
        seleccion = seleccionar(archivos_cambiados_localmente(args.local, RAIZ), RAIZ)
    elif args.base:
        seleccion = seleccionar(archivos_del_diff(args.base, args.cabeza or "HEAD", RAIZ), RAIZ)
    else:
        seleccion = Seleccion("completo", ["sin base de comparación: un push corre toda la suite"])

    print(f"ALCANCE: {seleccion.etiqueta}" + (f" | {len(seleccion.pruebas)} archivos de prueba" if seleccion.modo == "salas" else ""))
    for motivo in seleccion.motivos:
        print(f"  - {motivo}")
    if args.salida_github and os.environ.get("GITHUB_OUTPUT"):
        escribir_salida_github(seleccion, os.environ["GITHUB_OUTPUT"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
