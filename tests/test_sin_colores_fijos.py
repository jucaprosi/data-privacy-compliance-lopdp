# ¤frontend-ide
# ¤arbitro
"""Árbitro estático: ningún componente del frontend usa colores fijos del tema oscuro (FE-18).

Invariante: los fondos y bordes del tema oscuro se definen mediante variables CSS de tema
(ej. ``var(--ui-campo)``, ``var(--ui-superficie)``, ``var(--ui-borde)``), nunca mediante clases
Tailwind con colores hexadecimales fijos del tema oscuro en ``className``.

Al fallar, indica archivo, línea y la clase prohibida encontrada.
"""
from __future__ import annotations

import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
FRONTEND_SRC = RAIZ / "frontend" / "src"

# Lista de colores fijos prohibidos del tema oscuro para fondos y bordes
COLORES_PROHIBIDOS = [
    "#0a0a0c",
    "#141417",
    "#18181b",
    "#1b1b20",
    "#1e1e24",
    "#1a1a20",
    "#1e1e23",
    "#23232a",
    "#26262b",
    "#121214",
]

# Patrón que detecta bg-[#...] o border-[#...] con cualquiera de los colores prohibidos
PATRON_COLOR_FIJO = re.compile(
    r"\b(?:bg|border)-\[(?:" + "|".join(re.escape(c) for c in COLORES_PROHIBIDOS) + r")\]"
)

# Exenciones pendientes documentadas con archivo, línea y tarea responsable
# (Límites de FE-18: no cambia componentes; si el árbitro encuentra un color fijo pendiente,
# se documenta en no verificado para que el coordinador o la tarea responsable lo corrija).
EXENCIONES_PENDIENTES: dict[tuple[str, int], str] = {}


def buscar_colores_fijos_en_archivo(ruta: Path) -> list[str]:
    """Escanea un archivo .tsx y retorna una lista de hallazgos con ruta, línea y coincidencia."""
    hallazgos = []
    rel_path = ruta.relative_to(RAIZ).as_posix()
    try:
        lineas = ruta.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception as e:
        return [f"{rel_path}:0: error al leer archivo: {e}"]

    for numero_linea, linea in enumerate(lineas, 1):
        for coincidencia in PATRON_COLOR_FIJO.finditer(linea):
            clave = (rel_path, numero_linea)
            if clave in EXENCIONES_PENDIENTES:
                continue
            hallazgos.append(
                f"{rel_path}:{numero_linea}: color fijo prohibido '{coincidencia.group(0)}'"
            )
    return hallazgos


def test_sin_colores_fijos_tema_oscuro():
    """Verifica que ningún archivo .tsx en frontend/src use fondos o bordes fijos del tema oscuro."""
    archivos_tsx = sorted(FRONTEND_SRC.rglob("*.tsx"))
    assert len(archivos_tsx) > 0, "No se encontraron archivos .tsx en frontend/src"

    todos_hallazgos = []
    for archivo in archivos_tsx:
        todos_hallazgos.extend(buscar_colores_fijos_en_archivo(archivo))

    assert not todos_hallazgos, (
        f"Se encontraron {len(todos_hallazgos)} usos de colores fijos del tema oscuro en componentes:\n"
        + "\n".join(todos_hallazgos)
    )
