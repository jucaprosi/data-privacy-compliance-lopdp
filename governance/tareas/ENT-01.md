+++
id = "ENT-01"
titulo = "Un intérprete sin las dependencias detiene la suite con un solo mensaje"
ola = "indep"
estado = "hecha"
sala = "pruebas"
depende_de = []
propiedad = ["tests/conftest.py", "tests/test_entorno_arnes.py", "tests/test_conftest_entorno.py"]
arbitro = "pytest tests/test_conftest_entorno.py + suite completa con el intérprete del proyecto en verde"
rastros = ["¤arbitro", "¤seguridad"]
+++

# ENT-01 · Un intérprete sin las dependencias detiene la suite con un solo mensaje

**Objetivo.** Con el Python global (3.14, sin `redis`, `boto3`, `pytest-cov` ni `aiosqlite`) la suite no falla en un sitio: falla en tres, lejos de la causa. `test_el_interprete_de_las_pruebas_cumple_requirements_txt` dice la verdad; `test_api_health_check` (503) y `test_limite_cuerpo_no_afecta_a_otras_rutas` son su consecuencia, porque un router no carga. Quien lee tres fallos no ve que el problema es el intérprete. La suite debe detenerse al inicio, con un único mensaje que diga qué falta y cómo resolverlo (`scripts/entorno.bat`).

## Entrega
- `tests/conftest.py` comprueba al inicio de la sesión, con `faltantes` de `scripts/verificar_entorno.py`, que el intérprete tiene los requisitos de `requirements.txt`; si falta alguno, aborta la sesión de pruebas con un mensaje claro y el código de salida distinto de cero.
- Una prueba que simula un intérprete incompleto y comprueba que la sesión se detiene con ese mensaje, y que con las dependencias completas no se detiene.
- Se retira de `tests/test_entorno_arnes.py` solo `test_el_interprete_de_las_pruebas_cumple_requirements_txt`, porque la guardia hace esa misma comprobación al iniciar la sesión; el resto de ese archivo (lectura de `requirements.txt`, `.bat` sin rutas de una máquina) sigue protegiendo algo distinto.

## Límites
- No instala dependencias ni cambia `requirements.txt`.
- No omite ni marca como esperadas las pruebas que hoy fallan por el intérprete: se detiene antes de ejecutarlas.
- No modifica `scripts/entorno.bat` ni `scripts/verificar_entorno.py`.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa con el intérprete del proyecto y, con el global, se detiene con un solo mensaje. El check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad y dejó `estado = "hecha"` en esta especificación.
