# -*- coding: utf-8 -*-
# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤arbitro
"""GOB-06 R5: los briefs de una tanda, en la carpeta local, coinciden con sus fichas.

Para cada ficha no hecha con `tanda = N` comprueba, en `<carpeta>/briefs/`:
  - que existe su brief y su cabecera dice `(tanda N)`;
  - que su «Escribe» es igual a la `propiedad` de la ficha;
  - que su línea «Hecho si» es igual al `arbitro` de la ficha.

La carpeta por defecto es la de R1 (`~/compartido/evydentia`), fuera de todo worktree y sin git. El brief vigente de
una ficha es su versión más alta: R8 añade `<ID>.v2.md` sin sobrescribir `<ID>.md`. Lo corre el Tech Lead antes de
lanzar la tanda; no va en el CI.

Uso: python scripts/verificar_briefs_locales.py --tanda N [--carpeta RUTA]
"""
from __future__ import annotations

import argparse
import importlib.util
import re
import sys
from pathlib import Path

CARPETA_R1 = Path.home() / "compartido" / "evydentia"

_CABECERA = re.compile(r"(?m)^### ([A-Za-z0-9][A-Za-z0-9-]*) · .+?\(tanda (\d+)\)\s*$")
_RUTA = re.compile(r"(?m)^\s+- `([^`]+)`\s*$")
_HECHO = re.compile(r"(?m)^- `([A-Za-z0-9-]+)`: ([^\r\n]*)")
_VERSION = re.compile(r"^(?P<id>.+?)(?:\.v(?P<n>\d+))?\.md$")


# ¤arbitro
def _cargar_indice():
    ruta = Path(__file__).resolve().parent / "generar_indice_tareas.py"
    spec = importlib.util.spec_from_file_location("generar_indice_tareas", ruta)
    modulo = importlib.util.module_from_spec(spec)
    sys.modules["generar_indice_tareas"] = modulo  # las clases de datos lo exigen antes de ejecutar el módulo
    spec.loader.exec_module(modulo)
    return modulo


# ¤arbitro
def _norm(texto: str) -> str:
    return " ".join(texto.split())


# ¤arbitro
def brief_vigente(carpeta_briefs: Path, tarea_id: str) -> Path | None:
    """La versión más alta del brief de `tarea_id` (`<ID>.md` es la 1), o None si no hay ninguna."""
    versiones: list[tuple[int, Path]] = []
    if carpeta_briefs.is_dir():
        for ruta in carpeta_briefs.glob(f"{tarea_id}*.md"):
            m = _VERSION.match(ruta.name)
            if m and m.group("id") == tarea_id:
                versiones.append((int(m.group("n") or 1), ruta))
    return max(versiones)[1] if versiones else None


# ¤arbitro
def revisar_brief(texto: str, tarea) -> list[str]:
    """Los hallazgos de un brief frente a su ficha (vacío = coincide)."""
    texto = texto.replace("\r\n", "\n")
    hallazgos: list[str] = []
    cab = _CABECERA.search(texto)
    if cab is None or cab.group(1) != tarea.id or int(cab.group(2)) != tarea.tanda:
        hallazgos.append(f"{tarea.id}: la cabecera del brief no dice «### {tarea.id} · … (tanda {tarea.tanda})»")
    escribe = texto.split("**Escribe**", 1)[1].split("**No hagas", 1)[0] if "**Escribe**" in texto else ""
    rutas = set(_RUTA.findall(escribe))
    if rutas != set(tarea.propiedad):
        faltan = sorted(set(tarea.propiedad) - rutas)
        sobran = sorted(rutas - set(tarea.propiedad))
        hallazgos.append(f"{tarea.id}: «Escribe» difiere de la `propiedad` (faltan {faltan}, sobran {sobran})")
    hecho = texto.split("**Hecho si**", 1)[1] if "**Hecho si**" in texto else ""
    lineas = {tid: _norm(t) for tid, t in _HECHO.findall(hecho)}
    if lineas.get(tarea.id) != _norm(tarea.arbitro):
        hallazgos.append(f"{tarea.id}: «Hecho si» difiere del `arbitro` de la ficha")
    return hallazgos


# ¤arbitro
def revisar_tanda(tanda: int, tareas: list, carpeta: Path) -> list[str]:
    """R5 para una tanda: un hallazgo por brief que falta o por diferencia con su ficha."""
    hallazgos: list[str] = []
    for t in sorted((t for t in tareas if t.estado != "hecha" and t.tanda == tanda), key=lambda t: t.id):
        ruta = brief_vigente(carpeta / "briefs", t.id)
        if ruta is None:
            hallazgos.append(f"{t.id}: falta briefs/{t.id}.md")
            continue
        hallazgos += revisar_brief(ruta.read_bytes().decode("utf-8"), t)
    return hallazgos


# ¤arbitro
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tanda", type=int, required=True)
    ap.add_argument("--carpeta", type=Path, default=CARPETA_R1, help="carpeta local de R1 (por defecto ~/compartido/evydentia)")
    args = ap.parse_args(argv)
    tareas, errores = _cargar_indice().cargar_tareas()
    hallazgos = list(errores) + revisar_tanda(args.tanda, tareas, args.carpeta)
    fichas = sorted(t.id for t in tareas if t.estado != "hecha" and t.tanda == args.tanda)
    if hallazgos:
        print(f"BRIEFS DE LA TANDA {args.tanda} NO VÁLIDOS:")
        for h in hallazgos:
            print(f"  - {h}")
        return 1
    print(f"BRIEFS DE LA TANDA {args.tanda} OK: fichas sin hacer: {', '.join(fichas) or 'ninguna'}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
