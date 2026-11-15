# RET-01a · La suite toma su configuración del proceso y solo corre contra una base local
`¤sdd` `¤arbitro` `¤seguridad`

## 1. Datos

Sin tablas ni migraciones. Dos archivos de pruebas en su estado final y uno nuevo:

- `tests/conftest.py`: lee la configuración solo de `os.environ`. Define:
  - la función pública `exigir_base_de_pruebas()`;
  - la excepción `BaseNoDePruebas(RuntimeError)`;
  - `VARIABLES_DE_BASE = ("TEST_DATABASE_URL", "DATABASE_URL", "MIGRATION_DATABASE_URL")`;
  - `HOSTS_DE_PRUEBAS = ("localhost", "127.0.0.1", "::1")`.
- `tests/test_conftest_guardias.py`: las pruebas del arranque de la suite.
- `tests/test_ret01a_guardia_base.py` (crea): las pruebas de la función.

Medido en `origin/main`: el CI levanta su base como servicio del runner y la publica en `localhost:5432` (`zero-regression-pipeline.yml`, `TEST_DATABASE_URL` y `MIGRATION_DATABASE_URL`). El servicio de base del CI ya está en la lista. `tests/` no es un paquete (no tiene `__init__.py`).

## 2. API

Interfaz de Python solo para pruebas; ningún código de producción la importa.

| Pieza | Firma | Comportamiento |
| :--- | :--- | :--- |
| `exigir_base_de_pruebas` | `() -> None` | no hace nada si cada variable de `VARIABLES_DE_BASE` que esté definida tiene un host de `HOSTS_DE_PRUEBAS`; en cualquier otro caso lanza `BaseNoDePruebas` |
| `BaseNoDePruebas` | `RuntimeError` con `variables: tuple[str, ...]` | el mensaje y el atributo llevan solo los nombres de las variables |

Uso desde una prueba: `from conftest import exigir_base_de_pruebas`. Funciona porque pytest, en su modo de importación por defecto, pone `tests/` en `sys.path`. La prueba la llama en primer lugar, sin ninguna conexión abierta.

## 3. Reglas

- **R1 · Configuración del proceso.** La suite toma su configuración solo de las variables del proceso. `tests/conftest.py` no lee ningún archivo de configuración ni comprueba si la carpeta es un worktree. Ningún archivo de `tests/` carga un archivo de configuración de entorno.
- **R2 · Lista blanca, falla cerrada.** `exigir_base_de_pruebas()` es la única función de `tests/` que decide si la base es de pruebas.
  - Admite solo los hosts de `HOSTS_DE_PRUEBAS`.
  - Cualquier otro host falla: uno remoto, un socket de Cloud SQL (`/cloudsql/…`), un host vacío o una URL que no se pueda interpretar. En todos esos casos lanza `BaseNoDePruebas`.
  - Una variable no definida no cuenta. Sin ninguna variable definida, las pruebas que usan la base se omiten con un motivo visible (RET-01, R5).
- **R3 · Arranque.** `pytest_configure` llama a `exigir_base_de_pruebas()`, captura `BaseNoDePruebas` y detiene la suite con `pytest.exit(..., returncode=3)` y un mensaje que nombra las variables.
- **R4 · Falla cerrada en las pruebas.** En una prueba, `BaseNoDePruebas` se propaga y la prueba falla. La función no llama a `pytest.skip` ni a `pytest.xfail`, y no devuelve un booleano.
- **R5 · Sin valores.** Ningún mensaje, excepción ni registro de la suite contiene la URL, el host, el usuario ni la contraseña de una base. Solo los nombres de las variables.
- **R6 · Intérprete.** Si al intérprete le faltan paquetes del proyecto, `pytest_configure` detiene la suite con el código 3 y nombra el intérprete y los paquetes que faltan.
- **R7 · Paralelo.** `pytest -n` clona la base en cada trabajador. Como R2 solo admite bases locales, el paralelo no necesita una comprobación propia.
- **R8 · Orden.** `pytest_configure` comprueba la base (R3) y después el intérprete (R6). Luego prepara el trabajador de xdist y el orden por duración.
- **R9 · Sin copias locales.** Una prueba que usa la base llama a `exigir_base_de_pruebas()`. No define su propia lista de hosts, no compara con literales y no salta cuando la base no es de pruebas (R5 de RET-00).
- **R10 · Alcance.** La guardia de arranque de la aplicación en `app_core` pertenece a RET-01. `tests/plataforma_unica/pendientes/RET-01.txt` no cambia.
- **R-ADPA · Ortogonalidad ZERAG (`RET-01a`).** Solo `tests/`.

## 4. Interfaz

No aplica. Quien desarrolla levanta el PostgreSQL 16 local del arnés, fija las variables de base en la ventana de PowerShell y después ejecuta `pytest`. Los comandos los da `governance/operaciones/ENTORNO_LOCAL.md` (RET-01).

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** las tres variables con `127.0.0.1`, `localhost` o `::1`, **entonces** `exigir_base_de_pruebas()` no lanza nada. | `tests/test_ret01a_guardia_base.py::test_hosts_locales_pasan` |
| **Dado** una variable con un host no local (`base.ejemplo.test`), **entonces** lanza `BaseNoDePruebas` con el nombre de esa variable. Mutación: una función que no comprueba hace fallar la prueba. | `…::test_host_no_local_falla` |
| **Dado** una variable con un socket `/cloudsql/proyecto:region:instancia`, **entonces** falla. Mutación: admitir los sockets hace fallar la prueba. | `…::test_socket_de_la_nube_falla` |
| **Dado** una URL sin host o que no se puede interpretar, **entonces** falla. Mutación: admitir el host vacío hace fallar la prueba. | `…::test_url_dudosa_falla` |
| **Dado** `MIGRATION_DATABASE_URL` con un host no local y las otras dos locales, **entonces** falla. Mutación: comprobar solo dos variables hace fallar la prueba. | `…::test_las_tres_variables` |
| **Dado** el error, **entonces** ni el mensaje ni `repr` contienen la URL, el host ni la contraseña. | `…::test_sin_valores` |
| **Dado** el código de la función, **entonces** no llama a `pytest.skip` ni a `pytest.xfail` (AST). Mutación: añadir un `skip` hace fallar la prueba. | `…::test_falla_cerrada` |
| **Dado** `tests/conftest.py`, **entonces** solo `exigir_base_de_pruebas` lee `HOSTS_DE_PRUEBAS`, y ninguna otra función compara hosts (AST). | `…::test_una_sola_comprobacion` |
| **Dado** un proyecto temporal con el `conftest.py` real y una URL de host no local, **cuando** corre `pytest`, **entonces** termina con el código 3 y la salida no contiene la URL ni la contraseña. | `tests/test_conftest_guardias.py::test_base_no_local_detiene_la_suite_sin_imprimir_la_url` |
| **Dado** el mismo proyecto con `127.0.0.1`, **entonces** termina con el código 0. | `…::test_base_local_pasa` |
| **Dado** el proyecto como carpeta principal y como worktree (`.git` archivo), los dos sin ningún archivo de configuración, **entonces** los dos terminan con el código 0. Mutación: una comprobación de worktree o de archivo en `conftest` hace fallar la prueba. | `…::test_arranca_sin_archivos_de_configuracion` |
| **Dado** `tests/`, **entonces** ningún archivo importa `dotenv` ni llama a `load_dotenv`, `dotenv_values` o `find_dotenv`, y `conftest.py` no abre ningún archivo de configuración de entorno (AST). Quedan exentos por nombre los árbitros que listan esos usos como datos: `tests/plataforma_unica/catalogos.py`, `tests/test_gcp10_dockerignore.py` y las listas de pendientes. Mutación: un `from dotenv import load_dotenv` en `conftest.py` hace fallar la prueba. | `…::test_tests_no_cargan_archivos_de_entorno` |

Hosts de las pruebas: `127.0.0.1` para la base de pruebas, y `base.ejemplo.test` o un socket `/cloudsql/` para la base no local. Las variables se fijan con `monkeypatch` o en el entorno del proceso hijo, sin conectarse a ninguna base. Sin `import yaml`. `tests/test_conftest_guardias.py` se escribe entero con estas cuatro pruebas y un docstring que describe el estado final.

Árbitros del PR de código:
- `tests/test_ret01a_guardia_base.py` y `tests/test_conftest_guardias.py`;
- `test_plataforma_unica.py`;
- la guardia de huellas del proveedor retirado;
- `test_reparto.py`, `test_indice_tareas.py` y `test_adpa_bulkhead.py`;
- la suite completa en el CI, contra su servicio en `localhost`.

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-01a.md` (bloque BL-323). Especificación de referencia: `governance/especificaciones/README.md`.
- Origen: R5 de `governance/especificaciones/RET-00.md`, y R1 y R5 de `governance/especificaciones/RET-01.md`. La lista blanca sigue el criterio de RET-01 para su guardia de arranque.
- Propiedad:
  - `tests/conftest.py`;
  - `tests/test_conftest_guardias.py`, con cesión explícita de las fichas hechas que lo listan, anotada en la ficha;
  - `tests/test_ret01a_guardia_base.py` (crea).
- Ejecuciones de pytest contra una base remota, medidas en `origin/main`:
  - El CI corre contra `localhost`, y `scripts/contar_consultas_pruebas.py` ya exige una base local.
  - La guía del propietario `governance/operaciones/PRUEBAS_EN_FISICO.md` (DEV-01), en §6, corre `pytest tests\test_crear_organizacion_dev.py` con una URL de rama remota guardada en un archivo de texto. Con esta especificación esa ejecución falla cerrada. La salida es reescribir §6 contra el PostgreSQL 16 local del arnés, en una ficha de documentación de dominio entorno de pruebas. No se abre ninguna excepción en la lista.
- Secuencia:
  1. RET-01a.
  2. La corrección de la guía del propietario, que puede ir en paralelo.
  3. RET-01, que depende de RET-01a.
- Árbitros: las entradas de `tests/plataforma_unica/pendientes/RET-01.txt` siguen a cargo de RET-01, y `tests/conftest.py` queda cubierto por las pruebas de §5.
- Desbloquea CI-28 (#788) y DIAG-07 (#772).
