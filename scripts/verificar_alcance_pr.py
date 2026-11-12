# -*- coding: utf-8 -*-
# ¤adpa
"""Árbitro de alcance de un PR: los archivos que cambia caben en la `propiedad` de la ficha de su tarea.

La tarea sale del nombre de la rama: `tarea/<persona>/<id>...`, por ejemplo `adpa-03-roadmap` → ADPA-03.
Una rama sin ficha (CI-23) no se comprueba contra un alcance, pero se advierte de los archivos que
ninguna ficha viva posee (`::warning::` y `sin_ficha=true`) y, con `--estricto-sin-ficha`, falla. Las ramas
`pmv/**` (trabajo del PMV hacia `pmv/consolidacion`) no llevan ficha y quedan fuera. Fuera de PREFIJOS_ESTRICTOS, salirse del alcance solo avisa: esa
lista es una decisión del propietario y extenderla bloquea a todo el equipo.

Mismo reparto que R5 de `verificar_reparto.py`, pero contra la ficha: una tarea cerrada ya no tiene bloque.
"""
from __future__ import annotations

import argparse
import os
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PREFIJOS_ESTRICTOS = ("ADPA",)
_ID_EN_RAMA = re.compile(r"^(?:[^/]+/)*?([a-z]+-\d+[a-z]?)(?:-|$)")
PREFIJO_SIN_FICHA = "pmv/"  # CI-23: ramas del PMV, sin ficha por decisión del CTO
EXENCIONES = "governance/tareas/_exenciones_propiedad.txt"


# ¤adpa
def _cargar_indice():
    ruta = Path(__file__).resolve().parent / "generar_indice_tareas.py"
    spec = importlib.util.spec_from_file_location("generar_indice_tareas", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["generar_indice_tareas"] = modulo  # las clases de datos lo exigen antes de ejecutar el módulo
    spec.loader.exec_module(modulo)
    return modulo


# ¤adpa
def id_de_rama(rama: str, ids_conocidos) -> str | None:
    """El id de la rama con la grafía de su ficha (`sec-13a` → `SEC-13a`); sin ficha → None."""
    coincidencia = _ID_EN_RAMA.match(rama)
    if not coincidencia:
        return None
    candidato = coincidencia.group(1).lower()
    return next((i for i in ids_conocidos if i.lower() == candidato), None)


# ¤adpa
def retira_solo_exenciones_propias(diff: str, tarea_id: str) -> bool:
    """El diff (`git diff --unified=0`) de EXENCIONES solo borra líneas que empiezan por `<tarea_id>|`."""
    prefijo = f"{tarea_id}|"
    borradas = 0
    for linea in diff.splitlines():
        if linea.startswith(("deleted file", "new file", "rename ", "copy ", "+++ /dev/null", "--- /dev/null")):
            return False
        if linea.startswith(("+++", "---")):
            continue
        if linea.startswith("+"):
            return False
        if linea.startswith("-"):
            if not linea[1:].startswith(prefijo):
                return False
            borradas += 1
    return borradas > 0


# ¤adpa
def archivos_de_cierre(tarea_id: str) -> set[str]:
    """Lo que cierra una tarea no es parte de su alcance funcional."""
    return {
        "governance/apoyo/BRIEFS_POR_BLOQUE.md",
        "governance/artefactos/TASKS.md",
        f"governance/tareas/{tarea_id}.md",
    }


# ¤adpa
def fuera_de_alcance(archivos: list[str], tarea_id: str, propiedad: tuple[str, ...], indice,
                     exenciones_propias: bool = False) -> list[str]:
    patrones = [p.partition("#")[0] for p in propiedad]
    cierre = archivos_de_cierre(tarea_id) | ({EXENCIONES} if exenciones_propias else set())
    return [
        a for a in archivos
        if a not in cierre and not any(indice.rutas_se_solapan(a, p) for p in patrones)
    ]


# ¤adpa
def sin_duena_viva(archivos: list[str], tareas, indice) -> list[str]:
    """CI-23: archivos que ninguna ficha no hecha posee."""
    patrones = [p.partition("#")[0] for t in tareas if getattr(t, "estado", "pendiente") != "hecha"
                for p in t.propiedad]
    return [a for a in archivos if not any(indice.rutas_se_solapan(a, p) for p in patrones)]


# ¤adpa
def _salida_github(clave: str, valor: str) -> None:
    ruta = os.environ.get("GITHUB_OUTPUT")
    if ruta:
        with open(ruta, "a", encoding="utf-8") as f:
            f.write(f"{clave}={valor}" + chr(10))


# ¤adpa
def es_estricta(tarea_id: str) -> bool:
    return tarea_id.rsplit("-", 1)[0].upper() in PREFIJOS_ESTRICTOS


# ¤adpa
def _archivos_del_diff(base: str, cabeza: str) -> list[str]:
    salida = subprocess.run(["git", "diff", "--name-only", f"{base}...{cabeza}"], cwd=RAIZ,
                            capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return [linea.strip() for linea in salida.splitlines() if linea.strip()]


# ¤adpa
def _diff_de_exenciones(base: str, cabeza: str) -> str:
    return subprocess.run(["git", "diff", "--unified=0", "-M", f"{base}...{cabeza}", "--", EXENCIONES], cwd=RAIZ,
                          capture_output=True, text=True, encoding="utf-8", check=True).stdout


# ¤adpa
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--rama", required=True, help="nombre de la rama del PR")
    ap.add_argument("--base", required=True, help="revisión base del PR")
    ap.add_argument("--cabeza", required=True, help="revisión de la cabeza del PR")
    ap.add_argument("--estricto-sin-ficha", action="store_true",
                    help="sale con 1 si una rama sin ficha toca archivos sin dueña viva (CI-23)")
    args = ap.parse_args(argv)

    indice = _cargar_indice()
    tareas = indice.cargar_tareas()[0]
    tarea_id = id_de_rama(args.rama, [t.id for t in tareas])
    tarea = next((t for t in tareas if t.id == tarea_id), None)
    if tarea is None:
        print(f"ALCANCE: la rama «{args.rama}» no corresponde a ninguna ficha; no se comprueba.")
        if args.rama.startswith(PREFIJO_SIN_FICHA):
            return 0
        huerfanos = sin_duena_viva(_archivos_del_diff(args.base, args.cabeza), tareas, indice)
        _salida_github("sin_ficha", "true" if huerfanos else "false")
        for archivo in huerfanos:
            print(f"::warning::ALCANCE: «{archivo}» no es propiedad de ninguna ficha viva (rama sin ficha)")
        return 1 if huerfanos and args.estricto_sin_ficha else 0

    archivos = _archivos_del_diff(args.base, args.cabeza)
    propias = EXENCIONES in archivos and retira_solo_exenciones_propias(
        _diff_de_exenciones(args.base, args.cabeza), tarea.id)
    fuera = fuera_de_alcance(archivos, tarea.id, tarea.propiedad, indice, propias)
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
