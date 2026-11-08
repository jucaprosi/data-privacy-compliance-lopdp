# -*- coding: utf-8 -*-
# ¤ci-cd
"""Verificador de migraciones compatibles (expand/contract): una migración nueva no rompe la revisión en servicio.

Durante el despliegue progresivo (GCP-07) la revisión estable y la candidata comparten la base. Por eso
el `upgrade()` de una migración nueva no puede borrar ni renombrar columnas o tablas: la revisión estable
aún las usa. El borrado va en una migración de contracción posterior, que declara `CONTRACCION = True`
en el módulo y se aplica cuando ninguna revisión en servicio usa ya lo que borra.

Uso al desplegar: `python scripts/verificar_migracion_compatible.py --desde-revision <rev>`, con <rev> la
revisión de Alembic que tiene hoy la base (`alembic current`): revisa las migraciones entre ella y las
cabezas. También `--base <rev-git>` (migraciones añadidas desde esa revisión de git) o `python scripts/verificar_migracion_compatible.py ruta1.py ruta2.py`.
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
VERSIONES = "alembic/versions"
_OPS_DESTRUCTIVAS = {"drop_column", "drop_table", "rename_table"}
_SQL_DESTRUCTIVO = re.compile(
    r"\bDROP\s+(?:TABLE|COLUMN)\b|\bRENAME\s+(?:TO|COLUMN)\b|\bALTER\s+TABLE\b[^;]*\bDROP\b(?!\s+(?:CONSTRAINT|DEFAULT|NOT\s+NULL))",
    re.IGNORECASE,
)


# ¤ci-cd
def _nombre_llamada(nodo: ast.Call) -> str | None:
    f = nodo.func
    if isinstance(f, ast.Attribute):
        return f.attr
    return f.id if isinstance(f, ast.Name) else None


# ¤ci-cd
def _kw(nodo: ast.Call, nombre: str) -> ast.expr | None:
    return next((k.value for k in nodo.keywords if k.arg == nombre), None)


# ¤ci-cd
def _columna_obligatoria_sin_defecto(nodo: ast.Call) -> bool:
    """Los INSERT de la revisión estable no traen la columna: sin valor por defecto fallan."""
    for arg in nodo.args:
        if isinstance(arg, ast.Call) and _nombre_llamada(arg) == "Column":
            nullable = _kw(arg, "nullable")
            if isinstance(nullable, ast.Constant) and nullable.value is False and _kw(arg, "server_default") is None:
                return True
    return False


# ¤ci-cd
def _es_contraccion(arbol: ast.Module) -> bool:
    for nodo in arbol.body:
        if isinstance(nodo, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "CONTRACCION" for t in nodo.targets):
            return isinstance(nodo.value, ast.Constant) and nodo.value.value is True
    return False


# ¤ci-cd
def operaciones_destructivas(codigo: str) -> list[str]:
    """Lo que el `upgrade()` borra o renombra, una línea por operación."""
    arbol = ast.parse(codigo)
    upgrade = next((n for n in arbol.body if isinstance(n, ast.FunctionDef) and n.name == "upgrade"), None)
    if upgrade is None:
        return []
    hallazgos = []
    for nodo in ast.walk(upgrade):
        if not isinstance(nodo, ast.Call):
            continue
        nombre = _nombre_llamada(nodo)
        if nombre in _OPS_DESTRUCTIVAS:
            hallazgos.append(f"línea {nodo.lineno}: op.{nombre}")
        elif nombre == "alter_column" and _kw(nodo, "new_column_name") is not None:
            hallazgos.append(f"línea {nodo.lineno}: op.alter_column(new_column_name=...)")
        elif nombre == "alter_column" and _kw(nodo, "type_") is not None:
            hallazgos.append(f"línea {nodo.lineno}: op.alter_column(type_=...), cambio de tipo")
        elif nombre == "add_column" and _columna_obligatoria_sin_defecto(nodo):
            hallazgos.append(f"línea {nodo.lineno}: op.add_column con nullable=False sin server_default")
        elif nombre == "execute":
            for arg in nodo.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and _SQL_DESTRUCTIVO.search(arg.value):
                    hallazgos.append(f"línea {nodo.lineno}: SQL destructivo en op.execute")
    return hallazgos


# ¤ci-cd
def verificar(codigo: str) -> list[str]:
    """Vacío si la migración es compatible: aditiva, o de contracción declarada."""
    if _es_contraccion(ast.parse(codigo)):
        return []
    return operaciones_destructivas(codigo)


# ¤ci-cd
def _migraciones_nuevas(base: str) -> list[Path]:
    salida = subprocess.run(["git", "diff", "--name-only", "--diff-filter=A", f"{base}...HEAD", "--", VERSIONES],
                            cwd=RAIZ, capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return [RAIZ / linea.strip() for linea in salida.splitlines() if linea.strip().endswith(".py")]


# ¤ci-cd
def migraciones_desde_revision(revision: str, ubicacion: Path | None = None) -> list[Path]:
    """Las migraciones posteriores a `revision` hasta las cabezas, por el grafo de Alembic."""
    from alembic.script import ScriptDirectory

    guion = ScriptDirectory(str(ubicacion or RAIZ / "alembic"))
    return [Path(r.path) for r in guion.iterate_revisions("heads", revision)]


# ¤ci-cd
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("rutas", nargs="*", type=Path, help="migraciones a revisar")
    ap.add_argument("--base", help="revisión base de git: revisa las migraciones añadidas desde ella")
    ap.add_argument("--desde-revision", help="revisión de Alembic de la base en servicio (alembic current)")
    args = ap.parse_args(argv)
    rutas = list(args.rutas) + (_migraciones_nuevas(args.base) if args.base else [])
    if args.desde_revision:
        rutas += migraciones_desde_revision(args.desde_revision)
    fallos = 0
    for ruta in rutas:
        hallazgos = verificar(ruta.read_text(encoding="utf-8"))
        for h in hallazgos:
            print(f"INCOMPATIBLE: {ruta.name} {h}; sepárelo en una migración con CONTRACCION = True")
        fallos += bool(hallazgos)
    print(f"MIGRACIONES: {len(rutas)} revisadas, {fallos} incompatibles.")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
