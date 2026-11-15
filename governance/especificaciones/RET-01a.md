# RET-01a · Guardia pública exigir_base_de_pruebas()
`¤sdd` `¤arbitro` `¤seguridad`

## 1. Datos

Sin tablas ni migraciones. Cambia un archivo de pruebas y se crea otro:

- `tests/conftest.py` define una función pública, `exigir_base_de_pruebas()`, y una excepción, `BaseNoDePruebas(RuntimeError)`.
- `tests/test_ret01a_guardia_base.py` (crea).

Medido en `origin/main` b216ab4e:
- `_variables_con_produccion()` (línea 49) comprueba `TEST_DATABASE_URL` y `DATABASE_URL` contra la marca de host de producción `HOST_PRODUCCION` (línea 36). Devuelve solo nombres de variables.
- `pytest_configure` (línea 57) la llama y detiene la suite con `pytest.exit(..., returncode=3)`.
- `VARIABLES_DE_BASE` (línea 140) lista tres variables: añade `MIGRATION_DATABASE_URL`. Hoy solo la usa el clonado de xdist.
- `tests/` no es un paquete: no tiene `__init__.py`.

## 2. API

Interfaz de Python solo para pruebas; ningún código de producción la importa.

| Pieza | Firma | Comportamiento |
| :--- | :--- | :--- |
| `exigir_base_de_pruebas` | `() -> None` | no hace nada si ninguna variable de `VARIABLES_DE_BASE` apunta a producción; si alguna apunta, lanza `BaseNoDePruebas` |
| `BaseNoDePruebas` | `RuntimeError` con `variables: tuple[str, ...]` | el mensaje y el atributo llevan solo los nombres de las variables, nunca sus valores |

Uso desde una prueba: `from conftest import exigir_base_de_pruebas`. Funciona porque pytest, en el modo de importación por defecto, pone `tests/` en `sys.path`. La prueba la llama antes de abrir una conexión.

## 3. Reglas

- **R1 · Una sola comprobación.** `exigir_base_de_pruebas()` encapsula `_variables_con_produccion()`: es la única función de `tests/` que decide si la base es de pruebas. `pytest_configure` la usa: captura `BaseNoDePruebas` y detiene la suite con `pytest.exit(..., returncode=3)` y el mismo mensaje de hoy. No quedan dos copias de la comprobación.
- **R2 · Qué comprueba.** Lo mismo que hoy: la marca de host de producción. La amplía a las tres variables de `VARIABLES_DE_BASE`, también a `MIGRATION_DATABASE_URL`. Si esa variable apunta a producción mientras corre la suite, la suite se detiene; hoy no se detenía. Es más estricta y no relaja nada.
  - No rechaza cualquier host no local: la base de pruebas remota del entorno de pruebas es válida y debe pasar.
  - «Host no local» en la prueba significa el host de producción.
- **R3 · Falla cerrada, nunca salta.** En una prueba, `BaseNoDePruebas` se propaga y la prueba falla. La función no llama a `pytest.skip` ni a `pytest.xfail`, y no devuelve un booleano que la prueba pueda ignorar.
- **R4 · Sin valores.** Ningún mensaje, excepción ni registro contiene la URL, el host, el usuario ni la contraseña. Solo los nombres de las variables.
- **R5 · Lo que no cambia.**
  - La comprobación del intérprete y la de paralelo sobre una base remota siguen igual y en el mismo orden.
- **R5b · Fuera la guardia del worktree sin `.env` (decisión del CTO, 2026-11-14).** Se eliminan `_worktree_sin_env()`, `_WORKTREE_SIN_ENV` y su `pytest.exit`. Esa guardia existía porque el `.env` de la carpeta principal apuntaba a producción, y esa premisa está retirada (RET-01, R1 y R5). Ningún archivo de `tests/` ni ningún script exige ni busca un `.env`. Lo que impide arrancar sobre producción es `exigir_base_de_pruebas()` (R1).
  - La guardia única de `app_core` es de RET-01 y no se toca ni se duplica.
  - `tests/plataforma_unica/pendientes/RET-01.txt` no cambia.
- **R6 · Copias locales prohibidas.** Este es el respaldo de R5 de RET-00. Ninguna prueba nueva define su propia comprobación de la base, ni compara el host con una lista de literales, ni salta cuando la base no es de pruebas. La versión de CI-28 que hace eso se sustituye por la llamada a esta función cuando CI-28 se rehaga.
- **R-ADPA · Ortogonalidad ZERAG (`RET-01a`).** Solo `tests/`.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** las tres variables con una URL de la base de pruebas, local o remota, **entonces** `exigir_base_de_pruebas()` no lanza nada. | `test_base_de_pruebas_pasa` |
| **Dado** una de las tres variables con el host de producción, **entonces** lanza `BaseNoDePruebas`, cuyo atributo `variables` es el nombre de esa variable. Mutación: una función que no comprueba hace fallar la prueba. | `test_host_de_produccion_falla` |
| **Dado** `MIGRATION_DATABASE_URL` con el host de producción y las otras dos de pruebas, **entonces** falla. Mutación: comprobar solo dos variables hace fallar la prueba. | `test_las_tres_variables` |
| **Dado** el error, **entonces** ni el mensaje ni `repr` contienen la URL, el host ni la contraseña. | `test_sin_valores` |
| **Dado** el código de la función, **entonces** no llama a `pytest.skip` ni a `pytest.xfail` (AST). Mutación: añadir un `skip` hace fallar la prueba. | `test_falla_cerrada` |
| **Dado** `pytest_configure`, **entonces** usa `exigir_base_de_pruebas`: en `tests/conftest.py` ninguna otra función lee `HOST_PRODUCCION` (AST). | `test_una_sola_comprobacion` |
| **Dado** un worktree sin `.env`, **entonces** la suite arranca y no se detiene. Mutación: restaurar la guardia del worktree sin `.env` hace fallar la prueba. | `tests/test_conftest_guardias.py::test_worktree_sin_env_ya_no_se_detiene` |
| **Dado** `tests/test_conftest_guardias.py`, **entonces** ya no tiene `test_worktree_sin_env_se_detiene_con_mensaje_claro` ni `test_worktree_con_env_propio_pasa`, y su docstring no menciona el `.env`. Las demás pruebas del archivo no cambian lo que afirman. | criterio de revisión del PR |
| **Dado** un pytest hijo lanzado con el host de producción, **entonces** termina con código 3 y el mensaje de hoy, sin valores. | `test_configure_detiene_la_suite` |

Todas en `tests/test_ret01a_guardia_base.py`. Las variables se fijan con `monkeypatch`, sin conectarse a ninguna base y sin `import yaml`. Árbitros del PR de código: `test_ret01a_guardia_base.py`, `test_plataforma_unica.py`, la guardia de huellas del proveedor retirado, `test_reparto.py`, `test_indice_tareas.py` y `test_adpa_bulkhead.py`.

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-01a.md` (bloque BL-323). Especificación de referencia: `governance/especificaciones/README.md`.
- Origen: R5 de `governance/especificaciones/RET-00.md`, que exige una función que no existía; es un fallo de secuencia de RET-00. Pedido del CTO, 2026-11-14.
- Propiedad, ya en la ficha: `tests/conftest.py`, cedido por la ficha hecha que lo poseía, y `tests/test_ret01a_guardia_base.py` (crea).
- **Propiedad que añade R5b:** `tests/test_conftest_guardias.py`. Hoy lo listan NEON-00 y NEON-01; si están hechas, lo ceden con cesión explícita en el PR. Las dos pruebas que se retiran y la que se añade van en la tabla de pruebas ajenas del PR (`archivo::prueba | aserción | motivo | R5b`).
- Desbloquea CI-28 (#788) y DIAG-07 (#772). RET-01 la reutiliza y depende de ella.
