# ¤sdd
"""Árbitro de las especificaciones ejecutables (governance/especificaciones).

Comprueba que cada `<ID>.md` corresponde a una tarea existente, tiene los seis apartados en orden,
que cada fila de aceptación nombra su prueba, y que toda tarea que la cita existe.

    python scripts/verificar_especificaciones.py   # código 1 si hay hallazgos
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ESPECIFICACIONES = RAIZ / "governance" / "especificaciones"
TAREAS = RAIZ / "governance" / "tareas"

APARTADOS = ("## 1. Datos", "## 2. API", "## 3. Reglas", "## 4. Interfaz", "## 5. Aceptación", "## 6. Trazabilidad")
_ID = re.compile(r"^[A-Z]+-\d+$")


# ¤sdd
def revisar(nombre: str, texto: str, ids_tareas: set[str]) -> list[str]:
    """Hallazgos de una especificación; lista vacía si cumple."""
    hallazgos: list[str] = []
    tid = nombre.removesuffix(".md")
    if not _ID.match(tid):
        return [f"{nombre}: el nombre debe ser el id de una tarea (p. ej. RM-21.md)"]
    if tid not in ids_tareas:
        hallazgos.append(f"{nombre}: no existe governance/tareas/{tid}.md")
    posiciones = [texto.find(a) for a in APARTADOS]
    for apartado, pos in zip(APARTADOS, posiciones):
        if pos < 0:
            hallazgos.append(f"{nombre}: falta el apartado «{apartado}»")
    presentes = [p for p in posiciones if p >= 0]
    if presentes != sorted(presentes):
        hallazgos.append(f"{nombre}: los apartados no están en el orden 1 a 6")
    if all(p >= 0 for p in posiciones):
        aceptacion = texto[posiciones[4]:posiciones[5]]
        filas = [f for f in aceptacion.splitlines() if f.startswith("| **Dado**")]
        if not filas:
            hallazgos.append(f"{nombre}: el apartado 5 no tiene escenarios «Dado / Cuando / Entonces»")
        for fila in filas:
            celdas = [c.strip() for c in fila.strip().strip("|").split("|")]
            if len(celdas) < 2 or not celdas[-1]:
                hallazgos.append(f"{nombre}: un escenario no nombra la prueba que lo fija")
    return hallazgos


# ¤sdd
def main() -> int:
    ids_tareas = {p.stem for p in TAREAS.glob("*.md") if p.name != "README.md"}
    hallazgos: list[str] = []
    archivos = sorted(p for p in ESPECIFICACIONES.glob("*.md") if p.name != "README.md")
    for archivo in archivos:
        hallazgos += revisar(archivo.name, archivo.read_text(encoding="utf-8"), ids_tareas)
    if hallazgos:
        print("ESPECIFICACIONES NO VÁLIDAS:")
        for h in hallazgos:
            print(f"  - {h}")
        return 1
    print(f"ESPECIFICACIONES OK: {len(archivos)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
