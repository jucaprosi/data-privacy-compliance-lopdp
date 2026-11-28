# © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
# ¤¤qa-engineer
# ¤arbitro
"""ARR-04 §5: presupuesto de arranque del backend. `import main` sin pandas, openpyxl ni fpdf y bajo el umbral."""
import json
import os
import statistics
import subprocess
import sys
import time
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
PROHIBIDAS = ("pandas", "openpyxl", "fpdf")

# R2: umbral en segundos. 4,0 s de partida; si la mediana medida en el CI por 1,5 queda por debajo, se usa ese valor.
# Mediana medida en el CI: 3,000 s (run 46090975869, PR 1140); por 1,5 son 4,5 s, no queda por debajo de 4,0 s: el umbral sigue en 4,0 s.
UMBRAL_S = 4.0
IMPORTACIONES = 3

_CODIGO = "import json, sys, main; print(json.dumps(sorted(sys.modules)))"


def _entorno() -> dict:
    """R3: el entorno del arnés tal cual; los .pyc se escriben (PYTHONDONTWRITEBYTECODE vacío)."""
    entorno = dict(os.environ)
    entorno.pop("PYTHONDONTWRITEBYTECODE", None)
    return entorno


def _importar_main(extra: tuple = ()) -> tuple[float, str]:
    inicio = time.perf_counter()
    r = subprocess.run([sys.executable, *extra, "-c", _CODIGO], cwd=RAIZ, env=_entorno(),
                       capture_output=True, text=True, timeout=120)
    duracion = time.perf_counter() - inicio
    assert r.returncode == 0, f"import main falló: {r.stderr[-2000:]}"
    return duracion, r.stdout


def _cargadas(salida: str) -> list[str]:
    modulos = set(json.loads(salida.strip().splitlines()[-1]))
    return sorted(p for p in PROHIBIDAS if p in modulos or any(m.startswith(p + ".") for m in modulos))


def test_r1_main_arranca_sin_pandas_openpyxl_ni_fpdf():
    _importar_main()  # calienta los .pyc
    _, salida = _importar_main(("-X", "importtime"))
    assert _cargadas(salida) == [], f"import main carga {_cargadas(salida)}: impórtalas dentro de la función"


def test_r2_mediana_de_tres_importaciones_bajo_el_umbral():
    _importar_main()  # .pyc ya generados
    mediana = statistics.median(_importar_main()[0] for _ in range(IMPORTACIONES))
    assert mediana < UMBRAL_S, f"mediana {mediana:.2f} s >= umbral {UMBRAL_S} s"


def _con_mutacion(tmp_path, nombre: str, codigo: str) -> subprocess.CompletedProcess:
    """Copia de la raíz sin tocar el árbol: un módulo mutado va delante en sys.path y se importa antes que `main`."""
    (tmp_path / f"{nombre}.py").write_text(codigo, encoding="utf-8")
    entorno = _entorno()
    entorno["PYTHONPATH"] = os.pathsep.join([str(tmp_path), str(RAIZ), entorno.get("PYTHONPATH", "")])
    return subprocess.run([sys.executable, "-c", f"import {nombre}, json, sys, main; print(json.dumps(sorted(sys.modules)))"],
                          cwd=RAIZ, env=entorno, capture_output=True, text=True, timeout=120)


def test_m1_un_import_pandas_al_arrancar_da_rojo(tmp_path):
    r = _con_mutacion(tmp_path, "mutacion_m1", "import pandas\n")
    assert r.returncode == 0, r.stderr[-1000:]
    assert "pandas" in _cargadas(r.stdout), "m1: el detector de R1 debe ver pandas cargado"


def test_m2_un_sleep_de_5_s_al_arrancar_supera_el_umbral(tmp_path):
    _importar_main()
    inicio = time.perf_counter()
    r = _con_mutacion(tmp_path, "mutacion_m2", "import time\ntime.sleep(5)\n")
    assert r.returncode == 0, r.stderr[-1000:]
    assert time.perf_counter() - inicio >= UMBRAL_S, "m2: 5 s de más deben superar el umbral de R2"
