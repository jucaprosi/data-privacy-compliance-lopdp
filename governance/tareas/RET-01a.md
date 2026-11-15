+++
id = "RET-01a"
titulo = "Guardia pública exigir_base_de_pruebas() en tests/conftest.py"
ola = "backlog"
estado = "pendiente"
sala = "pruebas"
depende_de = ["CI-08", "CI-09", "ENT-01"]
propiedad = ["tests/conftest.py", "tests/test_conftest_guardias.py", "tests/test_ret01a_guardia_base.py"]
crea = ["tests/test_ret01a_guardia_base.py"]
arbitro = "pytest tests/test_ret01a_guardia_base.py tests/test_conftest_guardias.py tests/test_reparto.py tests/test_indice_tareas.py tests/test_adpa_bulkhead.py; mutación: una función que no comprueba da rojo"
rastros = ["¤arbitro", "¤seguridad"]
+++

# RET-01a · Guardia pública exigir_base_de_pruebas()

Pedido del CTO (2026-11-14); primera pieza de RET-01. Modelo sugerido: sonnet. Libre y pequeña; prioridad máxima: desbloquea #788 (CI-28) y toda prueba nueva que use la base.

**Problema.** R5 de RET-00 exige que toda prueba que lea `TEST_DATABASE_URL` o `DATABASE_URL`, o abra una conexión, llame a `exigir_base_de_pruebas()`. La función no existe en ningún sitio: hasta que exista, ninguna prueba nueva con base puede pasar R5. Es un fallo de secuencia de RET-00, no de las fichas.

**Entrega.** La especificación `governance/especificaciones/RET-01a.md` (estado final) manda sobre esta ficha:
- `tests/conftest.py` define la función pública `exigir_base_de_pruebas()` con lista blanca local, falla cerrada (`BaseNoDePruebas`, nunca `skip`) y nunca imprime valores; `pytest_configure` la usa (una sola comprobación) y `conftest` lee solo `os.environ`, sin carga de entorno ni comprobación de worktree.
- `tests/test_conftest_guardias.py` se reescribe entero según la especificación.
- `tests/test_ret01a_guardia_base.py` (nuevo): escenarios y mutaciones de la especificación, con `monkeypatch` y sin base.
- No toca `tests/plataforma_unica/pendientes/RET-01.txt`. La función única en `app_core` (guardia de RET-01) sigue siendo de RET-01, que la reutiliza, no la duplica.

**Propiedad de `tests/conftest.py`.** La ficha anterior que poseía el archivo está hecha y cede su propiedad en este PR (decisión del CTO, 2026-11-14): una ficha hecha no debe seguir bloqueando un archivo vivo. RET-01a lo toma y RET-01 lo hereda por dependencia de RET-01a.

**Dónde importa cada cosa.** Las pruebas importan la función de `tests/conftest.py`; ningún código de producción la importa.

**Cesión de `tests/test_conftest_guardias.py`.** Ninguna ficha lo lista hoy en su propiedad (solo lo mencionan en su texto fichas ya hechas), así que no hay cesión que anotar: RET-01a lo toma sin choque.
