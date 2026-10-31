# -*- coding: utf-8 -*-
# ¤adpa
"""Árbitro de alcance de un PR: los archivos que cambia caben en la `propiedad` de la ficha de su tarea.

La tarea sale del nombre de la rama: `tarea/<persona>/<id>...`, por ejemplo `adpa-03-roadmap` → ADPA-03.
Una rama sin ficha no se comprueba. Fuera de PREFIJOS_ESTRICTOS, salirse del alcance solo avisa: esa
lista es una decisión del propietario y extenderla bloquea a todo el equipo.

Mismo reparto que R5 de `verificar_reparto.py`, pero contra la ficha: una tarea cerrada ya no tiene bloque.
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PREFIJOS_ESTRICTOS = ("ADPA",)
_ID_EN_RAMA = re.compile(r"^(?:[^/]+/)*?([a-z]+-\d+)(?:-|$)")


# ¤adpa
def _cargar_indice():
    ruta = Path(__file__).resolve().parent / "generar_indice_tareas.py"
    spec = importlib.util.spec_from_file_location("generar_indice_tareas", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["generar_indice_tareas"] = modulo  # las clases de datos lo exigen antes de ejecutar el módulo
    spec.loader.exec_module(modulo)
    return modulo


# ¤adpa
def id_de_rama(rama: str) -> str | None:
    coincidencia = _ID_EN_RAMA.match(rama)
    return coincidencia.group(1).upper() if coincidencia else None


# ¤adpa
def archivos_de_cierre(tarea_id: str) -> set[str]:
    """Lo que cierra una tarea no es parte de su alcance funcional."""
    return {
        "governance/apoyo/BRIEFS_POR_BLOQUE.md",
        "governance/artefactos/TASKS.md",
        f"governance/tareas/{tarea_id}.md",
    }


# ¤adpa
def fuera_de_alcance(archivos: list[str], tarea_id: str, propiedad: tuple[str, ...], indice) -> list[str]:
    patrones = [p.partition("#")[0] for p in propiedad]
    cierre = archivos_de_cierre(tarea_id)
    return [
        a for a in archivos
        if a not in cierre and not any(indice.rutas_se_solapan(a, p) for p in patrones)
    ]


# ¤adpa
def es_estricta(tarea_id: str) -> bool:
    return tarea_id.rsplit("-", 1)[0] in PREFIJOS_ESTRICTOS


# ¤adpa
def _archivos_del_diff(base: str, cabeza: str) -> list[str]:
    salida = subprocess.run(["git", "diff", "--name-only", f"{base}...{cabeza}"], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return [linea.strip() for linea in salida.splitlines() if linea.strip()]


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rama", required=True, help="nombre de la rama del PR")
    ap.add_argument("--base", required=True, help="revisión base del PR")
    ap.add_argument("--cabeza", required=True, help="revisión de la cabeza del PR")
    args = ap.parse_args(argv)

    tarea_id = id_de_rama(args.rama)
    indice = _cargar_indice()
    tarea = next((t for t in indice.cargar_tareas()[0] if t.id == tarea_id), None)
    if tarea is None:
        print(f"ALCANCE: la rama «{args.rama}» no corresponde a ninguna ficha; no se comprueba.")
        return 0

    fuera = fuera_de_alcance(_archivos_del_diff(args.base, args.cabeza), tarea.id, tarea.propiedad, indice)
    if not fuera:
        print(f"ALCANCE OK: {tarea.id} solo toca su propiedad.")
        return 0
    estricta = es_estricta(tarea.id)
    print(f"ALCANCE {'NO VÁLIDO' if estricta else 'EXCEDIDO (solo aviso)'}: {tarea.id} toca archivos ajenos:")
    for archivo in fuera:
        print(f"  - {archivo}")
    return 1 if estricta else 0


if __name__ == "__main__":
    sys.exit(main())
