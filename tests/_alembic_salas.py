# ¤arbitro ¤adpa
"""Reglas del grafo de Alembic por sala (CI-28), como funciones puras sobre un `ScriptDirectory`.

Las usan `tests/test_alembic_cabeza_por_sala.py` (sobre el grafo real y sobre grafos armados en un
directorio temporal) y las pruebas de la sala `biblioteca` por `cabeza_de_sala`.

`alembic/salas.py` se carga por ruta: la carpeta `alembic/` del repositorio se llama igual que el
paquete instalado y no puede importarse como `alembic.salas`.
"""
from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory

RAIZ = Path(__file__).resolve().parent.parent
FEATURES = RAIZ / "features"


def cargar_salas():
    nombre = "_alembic_salas_repo"
    if nombre in sys.modules:
        return sys.modules[nombre]
    spec = importlib.util.spec_from_file_location(nombre, RAIZ / "alembic" / "salas.py")
    modulo = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = modulo
    spec.loader.exec_module(modulo)  # type: ignore[union-attr]
    return modulo


def guion_del_repositorio() -> ScriptDirectory:
    config = Config(str(RAIZ / "alembic.ini"))
    config.set_main_option("script_location", str(RAIZ / "alembic"))
    return ScriptDirectory.from_config(config)


def guion_de(directorio: Path) -> ScriptDirectory:
    config = Config()
    config.set_main_option("script_location", str(directorio))
    return ScriptDirectory.from_config(config)


def cabeza_de_sala(sala: str, guion: ScriptDirectory | None = None, base_comun: str | None = None) -> str:
    """Revisión cabeza de la rama de una sala.

    Mientras la sala no tenga una primera migración propia, su cabeza es `BASE_COMUN`: toda su historia
    está por debajo. Si la sala tiene varias cabezas, falla (regla R7).
    """
    guion = guion or guion_del_repositorio()
    base_comun = base_comun or cargar_salas().BASE_COMUN
    cabezas = cabezas_por_etiqueta(guion).get(sala, [])
    if not cabezas:
        assert guion.get_revision(base_comun) is not None, f"BASE_COMUN {base_comun} no está en el grafo"
        return base_comun
    assert len(cabezas) == 1, f"la sala «{sala}» tiene {len(cabezas)} cabezas: {sorted(cabezas)}"
    return cabezas[0]


def _revisiones(guion: ScriptDirectory) -> dict:
    return {r.revision: r for r in guion.walk_revisions()}


def _hijos_por_down_revision(revs: dict) -> dict[str, set[str]]:
    hijos: dict[str, set[str]] = {r: set() for r in revs}
    for r in revs.values():
        abajo = r.down_revision if isinstance(r.down_revision, tuple) else (r.down_revision,)
        for padre in abajo:
            if padre in hijos:
                hijos[padre].add(r.revision)
    return hijos


def historia_de(guion: ScriptDirectory, base_comun: str) -> set[str]:
    """La base común y todo lo que hay por debajo: la historia que no se reescribe."""
    return {r.revision for r in guion.iterate_revisions(base_comun, "base")}


def posteriores(guion: ScriptDirectory, base_comun: str) -> dict:
    historia = historia_de(guion, base_comun)
    return {k: v for k, v in _revisiones(guion).items() if k not in historia}


def _etiquetas(rev) -> set[str]:
    return set(rev.branch_labels or ())


def cabezas_por_etiqueta(guion: ScriptDirectory) -> dict[str, list[str]]:
    """Por etiqueta, las revisiones de la etiqueta sin hijas en la misma etiqueta (por `down_revision`)."""
    revs = _revisiones(guion)
    hijos = _hijos_por_down_revision(revs)
    etiquetas = {e for r in revs.values() for e in _etiquetas(r)}
    salida = {}
    for etiqueta in sorted(etiquetas):
        miembros = {k for k, r in revs.items() if etiqueta in _etiquetas(r)}
        salida[etiqueta] = sorted(k for k in miembros if not (hijos[k] & miembros))
    return salida


# -- Reglas (cada una devuelve la lista de fallos; vacía si se cumple) ---------------------------

def fallos_una_cabeza_por_etiqueta(guion: ScriptDirectory, base_comun: str) -> list[str]:
    fallos = []
    por_etiqueta = cabezas_por_etiqueta(guion)
    for etiqueta, cabezas in por_etiqueta.items():
        if len(cabezas) != 1:
            fallos.append(f"la etiqueta «{etiqueta}» tiene {len(cabezas)} cabezas: {cabezas}")
    revs = _revisiones(guion)
    dependidas = {d for r in revs.values() for d in (r.dependencies or ())
                  if isinstance(r.dependencies, (tuple, list))} | {r.dependencies for r in revs.values()
                                                                    if isinstance(r.dependencies, str)}
    esperadas = {c[0] for c in por_etiqueta.values() if len(c) == 1}
    if not posteriores(guion, base_comun):
        esperadas.add(base_comun)
    reales = set(guion.get_heads())
    sueltas = reales - esperadas
    if sueltas:
        fallos.append(f"cabezas sueltas, sin etiqueta de sala: {sorted(sueltas)}")
    faltan = {c for c in esperadas if c not in reales and c not in dependidas}
    if faltan:
        fallos.append(f"cabezas esperadas que no son cabezas del grafo: {sorted(faltan)}")
    return fallos


def fallos_toda_migracion_con_sala(guion: ScriptDirectory, base_comun: str) -> list[str]:
    if guion.get_revision(base_comun) is None:
        return [f"BASE_COMUN {base_comun} no está en el grafo"]
    return [f"{k}: es posterior a BASE_COMUN y no pertenece a ninguna sala (falta branch_labels)"
            for k, r in sorted(posteriores(guion, base_comun).items()) if not _etiquetas(r)]


def fallos_etiquetas_son_salas(guion: ScriptDirectory, features: Path = FEATURES) -> list[str]:
    salas = {p.name for p in features.iterdir() if p.is_dir()}
    etiquetas = {e for r in _revisiones(guion).values() for e in _etiquetas(r)}
    return [f"la etiqueta «{e}» no es una carpeta de features/" for e in sorted(etiquetas - salas)]


def fallos_sin_merges_entre_salas(guion: ScriptDirectory, base_comun: str) -> list[str]:
    revs = _revisiones(guion)
    fallos = []
    for k, r in sorted(posteriores(guion, base_comun).items()):
        if not isinstance(r.down_revision, tuple) or len(r.down_revision) < 2:
            continue
        salas = set()
        for padre in r.down_revision:
            salas |= _etiquetas(revs[padre]) if padre in revs else set()
        if len(salas) > 1:
            fallos.append(f"{k}: su down_revision une salas distintas {sorted(salas)}; use depends_on")
    return fallos


def tablas_creadas_en(archivo: Path) -> set[str]:
    return {a.args[0].value for a in ast.walk(ast.parse(archivo.read_text(encoding="utf-8")))
            if isinstance(a, ast.Call) and _es_op(a, "create_table") and a.args
            and isinstance(a.args[0], ast.Constant) and isinstance(a.args[0].value, str)}


def _es_op(llamada: ast.Call, metodo: str | None = None) -> bool:
    f = llamada.func
    return (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name) and f.value.id == "op"
            and (metodo is None or f.attr == metodo))


def _cadenas(nodo: ast.AST):
    for n in ast.walk(nodo):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            yield n.value


def tablas_nombradas_en(archivo: Path, tablas: set[str]) -> set[str]:
    """Tablas de `tablas` que la migración nombra en llamadas `op.*`, `sa.ForeignKey` o SQL en texto."""
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    cuerpo = list(arbol.body)
    if cuerpo and isinstance(cuerpo[0], ast.Expr) and isinstance(getattr(cuerpo[0], "value", None), ast.Constant):
        cuerpo = cuerpo[1:]  # el docstring del módulo no es código
    encontradas: set[str] = set()
    patron = re.compile(r"\b(" + "|".join(re.escape(t) for t in sorted(tablas, key=len, reverse=True)) + r")\b") if tablas else None
    for nodo in cuerpo:
        for n in ast.walk(nodo):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            es_fk = isinstance(f, ast.Attribute) and f.attr == "ForeignKey"
            es_texto = isinstance(f, ast.Attribute) and f.attr == "text"
            if not (_es_op(n) or es_fk or es_texto):
                continue
            for cadena in _cadenas(n):
                if cadena in tablas:
                    encontradas.add(cadena)
                elif "." in cadena and cadena.split(".")[0] in tablas and es_fk:
                    encontradas.add(cadena.split(".")[0])
                elif patron is not None and (len(cadena) > 20 or " " in cadena):
                    encontradas.update(patron.findall(cadena))
    return encontradas


def _dependencias(rev) -> tuple[str, ...]:
    d = rev.dependencies
    return (d,) if isinstance(d, str) else tuple(d or ())


def fallos_dependencias_entre_salas(guion: ScriptDirectory, base_comun: str,
                                    tablas_por_sala: dict[str, str]) -> list[str]:
    """R4: una migración de la sala X que nombra una tabla de la sala Y declara `depends_on` hacia Y."""
    revs = _revisiones(guion)
    nuevas = posteriores(guion, base_comun)
    # Las tablas que crean las migraciones de sala también tienen dueña.
    dueñas = dict(tablas_por_sala)
    for r in nuevas.values():
        for sala in _etiquetas(r):
            for t in tablas_creadas_en(Path(r.path)):
                dueñas.setdefault(t, sala)
    con_revisiones = {e for r in nuevas.values() for e in _etiquetas(r)}
    fallos = []
    for k, r in sorted(nuevas.items()):
        propias = _etiquetas(r)
        if not propias:
            continue
        otras = {dueñas[t] for t in tablas_nombradas_en(Path(r.path), set(dueñas)) if dueñas[t] not in propias}
        for sala_y in sorted(otras & con_revisiones):
            apuntadas = set()
            for d in _dependencias(r):
                if d in revs:
                    apuntadas |= _etiquetas(revs[d])
            if sala_y not in apuntadas:
                fallos.append(f"{k} (sala {sorted(propias)}) nombra tablas de «{sala_y}» sin depends_on hacia esa sala")
    return fallos


def fallos_del_grafo(guion: ScriptDirectory, base_comun: str, tablas_por_sala: dict[str, str],
                     features: Path = FEATURES) -> list[str]:
    return (fallos_una_cabeza_por_etiqueta(guion, base_comun) + fallos_toda_migracion_con_sala(guion, base_comun)
            + fallos_etiquetas_son_salas(guion, features) + fallos_sin_merges_entre_salas(guion, base_comun)
            + fallos_dependencias_entre_salas(guion, base_comun, tablas_por_sala))


# -- Grafos de prueba en un directorio temporal ---------------------------------------------------

def escribir_migracion(versiones: Path, revision: str, down, *, labels=None, depends_on=None, cuerpo: str = "pass") -> None:
    versiones.mkdir(parents=True, exist_ok=True)
    texto = (
        f"revision = {revision!r}\ndown_revision = {down!r}\nbranch_labels = {labels!r}\ndepends_on = {depends_on!r}\n\n"
        "from alembic import op\nimport sqlalchemy as sa\n\n\n"
        f"def upgrade():\n    {cuerpo}\n\n\ndef downgrade():\n    pass\n"
    )
    (versiones / f"{revision}.py").write_text(texto, encoding="utf-8", newline="\n")
