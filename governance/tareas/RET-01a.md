+++
id = "RET-01a"
titulo = "Guardia pública exigir_base_de_pruebas() en tests/conftest.py"
ola = "backlog"
estado = "pendiente"
sala = "pruebas"
depende_de = ["CI-08", "CI-09", "ENT-01"]
propiedad = ["tests/conftest.py", "tests/test_ret01a_guardia_base.py"]
crea = ["tests/test_ret01a_guardia_base.py"]
arbitro = "pytest tests/test_ret01a_guardia_base.py tests/test_plataforma_unica.py tests/test_reparto.py tests/test_indice_tareas.py tests/test_adpa_bulkhead.py; mutación: una función que no comprueba da rojo"
rastros = ["¤arbitro", "¤seguridad"]
+++

# RET-01a · Guardia pública exigir_base_de_pruebas()

Pedido del CTO (2026-11-14); primera pieza de RET-01. Modelo sugerido: sonnet. Libre y pequeña; prioridad máxima: desbloquea #788 (CI-28) y toda prueba nueva que use la base.

**Problema.** R5 de RET-00 exige que toda prueba que lea `TEST_DATABASE_URL` o `DATABASE_URL`, o abra una conexión, llame a `exigir_base_de_pruebas()`. La función no existe en ningún sitio: hasta que exista, ninguna prueba nueva con base puede pasar R5. Es un fallo de secuencia de RET-00, no de las fichas.

**Entrega.**
- `tests/conftest.py` define la función pública `exigir_base_de_pruebas()`, que encapsula la comprobación que `conftest` ya hace (`_variables_con_produccion()` sobre `VARIABLES_DE_BASE`). Mismo comportamiento: falla cerrada si alguna variable apunta a producción o a un host que no es de pruebas, y nunca imprime valores, solo el nombre de la variable.
- `pytest_configure` pasa a usar la misma función: una sola comprobación, no dos copias.
- `tests/test_ret01a_guardia_base.py` (nuevo): con una URL de pruebas la llamada pasa; con un host no local falla; mutación documentada (una función que no comprueba) en rojo.
- No cambia ninguna regla ni retira nada de RET-01. La función única en `app_core` (guardia de RET-01) sigue siendo de RET-01, que la reutiliza, no la duplica.
- No toca `tests/plataforma_unica/pendientes/RET-01.txt`: añadir una función no retira ninguna entrada.

**Propiedad de `tests/conftest.py`.** La ficha anterior que poseía el archivo está hecha y cede su propiedad en este PR (decisión del CTO, 2026-11-14): una ficha hecha no debe seguir bloqueando un archivo vivo. RET-01a lo toma y RET-01 lo hereda por dependencia de RET-01a.

**Dónde importa cada cosa.** Las pruebas importan la función de `tests/conftest.py`; ningún código de producción la importa.
