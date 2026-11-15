# RET-01a · La suite toma su configuración del proceso y tiene una sola guardia de base
`¤sdd` `¤arbitro` `¤seguridad`

## 1. Datos

Sin tablas ni migraciones. Dos archivos de pruebas en su estado final y uno nuevo:

- `tests/conftest.py`: lee la configuración solo de `os.environ`. Define la función pública `exigir_base_de_pruebas()`, la excepción `BaseNoDePruebas(RuntimeError)` y la tupla `VARIABLES_DE_BASE = ("TEST_DATABASE_URL", "DATABASE_URL", "MIGRATION_DATABASE_URL")`.
- `tests/test_conftest_guardias.py`: las pruebas del arranque de la suite.
- `tests/test_ret01a_guardia_base.py` (crea): las pruebas de la función.

`tests/` no es un paquete (no tiene `__init__.py`).

## 2. API

Interfaz de Python solo para pruebas; ningún código de producción la importa.

| Pieza | Firma | Comportamiento |
| :--- | :--- | :--- |
| `exigir_base_de_pruebas` | `() -> None` | no hace nada si ninguna variable de `VARIABLES_DE_BASE` apunta al host de producción (`HOST_PRODUCCION`); si alguna apunta, lanza `BaseNoDePruebas` |
| `BaseNoDePruebas` | `RuntimeError` con `variables: tuple[str, ...]` | el mensaje y el atributo llevan solo los nombres de las variables |

Uso desde una prueba: `from conftest import exigir_base_de_pruebas`. Funciona porque pytest, en su modo de importación por defecto, pone `tests/` en `sys.path`. La prueba la llama en primer lugar, sin ninguna conexión abierta.

## 3. Reglas

- **R1 · Configuración del proceso.** La suite toma su configuración solo de las variables del proceso.
  - `tests/conftest.py` no importa `dotenv`, no lee ningún archivo de entorno y no comprueba si la carpeta es un worktree.
  - Ningún mensaje de la suite pide crear o copiar un archivo de entorno.
  - Ningún archivo de `tests/` carga un archivo de entorno.
  - Los árbitros que buscan esos usos, como `tests/plataforma_unica/catalogos.py` y `tests/test_gcp10_dockerignore.py`, los nombran como datos y no cuentan como carga.
- **R2 · Una sola guardia de base.** `exigir_base_de_pruebas()` es la única función de `tests/` que decide si la base es de pruebas.
  - Comprueba las tres variables de `VARIABLES_DE_BASE` contra `HOST_PRODUCCION`.
  - La base de pruebas remota del entorno de pruebas es válida y pasa.
  - `pytest_configure` la llama, captura `BaseNoDePruebas` y detiene la suite con `pytest.exit(..., returncode=3)`.
- **R3 · Falla cerrada.** En una prueba, `BaseNoDePruebas` se propaga y la prueba falla. La función no llama a `pytest.skip` ni a `pytest.xfail`, y no devuelve un booleano.
- **R4 · Sin valores.** Ningún mensaje, excepción ni registro de la suite contiene la URL, el host, el usuario ni la contraseña de una base. Solo los nombres de las variables.
- **R5 · Intérprete.** Si al intérprete le faltan paquetes del proyecto, `pytest_configure` detiene la suite con el código 3 y nombra el intérprete y los paquetes que faltan.
- **R6 · Paralelo.** `pytest -n` solo se admite con PostgreSQL local o de contenedor. Con una base remota, `pytest_configure` detiene la suite con el código 3.
- **R7 · Orden.** `pytest_configure` comprueba en este orden: la base (R2), el intérprete (R5) y el paralelo (R6). Después prepara el trabajador de xdist y el orden por duración.
- **R8 · Sin copias locales.** Una prueba que usa la base llama a `exigir_base_de_pruebas()`. No define su propia comprobación, no compara el host con literales y no salta cuando la base no es de pruebas (R5 de RET-00).
- **R9 · Alcance.** La guardia única de `app_core` pertenece a RET-01; esta ficha no la define. `tests/plataforma_unica/pendientes/RET-01.txt` no cambia.
- **R-ADPA · Ortogonalidad ZERAG (`RET-01a`).** Solo `tests/`.

## 4. Interfaz

No aplica. Quien desarrolla fija las variables de base en la ventana de PowerShell y después ejecuta `pytest`; `governance/operaciones/ENTORNO_LOCAL.md` (RET-01) da los comandos.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** las tres variables con una URL de la base de pruebas, local o remota, **entonces** `exigir_base_de_pruebas()` no lanza nada. | `tests/test_ret01a_guardia_base.py::test_base_de_pruebas_pasa` |
| **Dado** una de las tres variables con el host de producción, **entonces** lanza `BaseNoDePruebas` con el nombre de esa variable. Mutación: una función que no comprueba hace fallar la prueba. | `…::test_host_de_produccion_falla` |
| **Dado** `MIGRATION_DATABASE_URL` con el host de producción, **entonces** falla. Mutación: comprobar solo dos variables hace fallar la prueba. | `…::test_las_tres_variables` |
| **Dado** el error, **entonces** ni el mensaje ni `repr` contienen la URL, el host ni la contraseña. | `…::test_sin_valores` |
| **Dado** el código de la función, **entonces** no llama a `pytest.skip` ni a `pytest.xfail` (AST). Mutación: añadir un `skip` hace fallar la prueba. | `…::test_falla_cerrada` |
| **Dado** `tests/conftest.py`, **entonces** solo `exigir_base_de_pruebas` lee `HOST_PRODUCCION` (AST). | `…::test_una_sola_comprobacion` |
| **Dado** un proyecto temporal con el `conftest.py` real y la URL de producción, **cuando** corre `pytest`, **entonces** termina con el código 3 y la salida no contiene la URL ni la contraseña. | `tests/test_conftest_guardias.py::test_produccion_detiene_la_suite_sin_imprimir_la_url` |
| **Dado** el mismo proyecto con la URL de pruebas, **entonces** termina con el código 0. | `…::test_url_de_pruebas_pasa` |
| **Dado** el proyecto como carpeta principal y como worktree (`.git` archivo), los dos sin archivo de entorno, **entonces** los dos terminan con el código 0. Mutación: una comprobación de worktree o de archivo de entorno en `conftest` hace fallar la prueba. | `…::test_sin_archivo_de_entorno_arranca` |
| **Dado** `tests/`, **entonces** ningún archivo importa `dotenv` ni llama a `load_dotenv`, `dotenv_values` o `find_dotenv`, y `conftest.py` no abre ningún archivo de entorno (AST). Los árbitros de R1 que nombran esos usos como datos quedan exentos por nombre. Mutación: un `from dotenv import load_dotenv` en `conftest.py` hace fallar la prueba. | `…::test_tests_no_cargan_archivos_de_entorno` |

Las URL de las pruebas se arman con `HOST_PRODUCCION` importado de `conftest` y con un host de pruebas neutro, sin literales de proveedores. Las variables se fijan con `monkeypatch` o en el entorno del proceso hijo, sin conectarse a ninguna base. Sin `import yaml`. `tests/test_conftest_guardias.py` se escribe entero con estas cuatro pruebas y un docstring que describe el estado final.

Árbitros del PR de código:
- `tests/test_ret01a_guardia_base.py`;
- `tests/test_conftest_guardias.py`;
- `test_plataforma_unica.py`;
- la guardia de huellas del proveedor retirado;
- `test_reparto.py`, `test_indice_tareas.py` y `test_adpa_bulkhead.py`.

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-01a.md` (bloque BL-323). Especificación de referencia: `governance/especificaciones/README.md`.
- Origen: R5 de `governance/especificaciones/RET-00.md` y R1 de `governance/especificaciones/RET-01.md`.
- Propiedad:
  - `tests/conftest.py`;
  - `tests/test_conftest_guardias.py`, con cesión explícita de las fichas hechas que lo listan, anotada en la ficha;
  - `tests/test_ret01a_guardia_base.py` (crea).
- Secuencia:
  1. RET-01a. La suite deja de cargar archivos de entorno, y quien desarrolla fija las variables de base en su ventana de PowerShell. El CI ya las fija en el workflow.
  2. RET-01. `app_core/config.py`, `python-dotenv`, `.env.example` y `scripts/entorno_local.ps1`, que fija esas variables con un comando.
- Árbitros: RET-01a no deja ningún archivo sin árbitro. Las entradas de `tests/plataforma_unica/pendientes/RET-01.txt` (`requirements.txt` y `app_core/config.py`) siguen a cargo de RET-01, y `tests/conftest.py` queda cubierto por las pruebas de §5.
- Desbloquea CI-28 (#788) y DIAG-07 (#772). RET-01 depende de RET-01a.
