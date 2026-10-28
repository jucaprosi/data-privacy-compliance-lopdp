# ¤sdd
"""Pruebas del árbitro de especificaciones ejecutables."""
import importlib.util
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("verificar_especificaciones", RAIZ / "scripts" / "verificar_especificaciones.py")
ve = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ve)

COMPLETA = """# X
## 1. Datos
sin datos persistentes
## 2. API
sin API nueva
## 3. Reglas
- R1
## 4. Interfaz
sin interfaz
## 5. Aceptación
| Escenario | Prueba |
| :--- | :--- |
| **Dado** a, **cuando** b, **entonces** c. | `test_x` |
## 6. Trazabilidad
ficha
"""


def test_especificacion_completa_pasa():
    assert ve.revisar("RM-21.md", COMPLETA, {"RM-21"}) == []


def test_falta_apartado():
    texto = COMPLETA.replace("## 4. Interfaz\nsin interfaz\n", "")
    assert any("4. Interfaz" in h for h in ve.revisar("RM-21.md", texto, {"RM-21"}))


def test_orden_alterado():
    texto = COMPLETA.replace("## 2. API\nsin API nueva\n## 3. Reglas\n- R1\n", "## 3. Reglas\n- R1\n## 2. API\nsin API nueva\n")
    assert any("orden" in h for h in ve.revisar("RM-21.md", texto, {"RM-21"}))


def test_escenario_sin_prueba():
    texto = COMPLETA.replace("| `test_x` |", "|  |")
    assert any("no nombra la prueba" in h for h in ve.revisar("RM-21.md", texto, {"RM-21"}))


def test_tarea_inexistente():
    assert any("no existe" in h for h in ve.revisar("ZZ-99.md", COMPLETA, {"RM-21"}))


def test_especificaciones_del_repositorio():
    assert ve.main() == 0
