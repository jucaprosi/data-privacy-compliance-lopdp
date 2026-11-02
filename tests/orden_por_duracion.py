# ¤arbitro
# ¤¤qa-engineer
"""Orden de ejecución de más lenta a más rápida para Pytest en paralelo.

pytest deja las pruebas en orden alfabético y xdist reparte los archivos en ese orden: los lentos que caen al final
dejan trabajadores parados. Se ordena por archivo y no por prueba porque el arnés reparte con --dist loadfile y los
fixtures de módulo no admiten archivos intercalados. Regenerar cada mes desde una corrida completa:

    pytest tests/ -n auto --dist loadfile --durations=0 -vv > salida.txt
    python tests/orden_por_duracion.py salida.txt
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

ARCHIVO_DE_DURACIONES = Path(__file__).with_name("duraciones.json")
_LINEA_DE_DURACION = re.compile(r"^\s*(\d+(?:\.\d+)?)s\s+(?:setup|call|teardown)\s+(tests/[^:\s]+\.py)(?:::|\s|$)", re.M)


def cargar(ruta: Path = ARCHIVO_DE_DURACIONES) -> dict[str, float]:
    """Sin archivo no hay orden que aplicar. Un JSON dañado sí falla: viene versionado y no debe pasar inadvertido."""
    return json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else {}


def ordenar(items: list, duraciones: dict[str, float]) -> None:
    """El sort es estable: cada archivo queda contiguo y conserva su orden interno. Un archivo sin duración va al final,
    y con la misma entrada todos los trabajadores obtienen la misma lista, que es lo que xdist exige."""
    if duraciones:
        items.sort(key=lambda item: -duraciones.get(item.nodeid.split("::")[0], 0))


def duraciones_de_la_salida(salida: str) -> dict[str, float]:
    """Suma preparación, llamada y limpieza de cada archivo a partir de la tabla de --durations=0."""
    totales: Counter = Counter()
    for segundos, archivo in _LINEA_DE_DURACION.findall(salida):
        totales[archivo] += float(segundos)
    return {archivo: round(total, 1) for archivo, total in totales.most_common()}


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print(__doc__)
        return 2
    duraciones = duraciones_de_la_salida(Path(argv[0]).read_text(encoding="utf-8", errors="replace"))
    if not duraciones:
        print("[DURACIONES] La salida no trae la tabla de --durations=0; no se escribe nada.")
        return 1
    ARCHIVO_DE_DURACIONES.write_text(json.dumps(duraciones, indent=2) + "\n", encoding="utf-8")
    print(f"[DURACIONES] {len(duraciones)} archivos escritos en {ARCHIVO_DE_DURACIONES.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
