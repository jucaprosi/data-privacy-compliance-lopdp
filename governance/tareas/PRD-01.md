+++
id = "PRD-01"
titulo = "El índice de tareas y la verificación de alcance leen el PRD y los artefactos de EVYDENTIA"
ola = "backlog"
estado = "pendiente"
sala = "gobernanza"
depende_de = ["ADPA-10", "CI-19", "CI-22", "GOB-02", "CI-23"]
propiedad = ["scripts/generar_indice_tareas.py", "governance/artefactos/TASKS_EVYDENTIA_REVENTA_NUBE.md", "scripts/verificar_alcance_pr.py", "tests/test_verificar_alcance_pr.py", "tests/test_indice_tareas.py"]
crea = []
arbitro = "pytest tests/test_indice_tareas.py tests/test_verificar_alcance_pr.py + python scripts/generar_indice_tareas.py --verificar con código 0; prueba: salas_del_prd(PRD_EVYDENTIA_REVENTA_NUBE.md) devuelve al menos las salas de todas las fichas abiertas; mutación documentada: quitar una fila del 7.1 hace fallar la ficha de esa sala"
rastros = ["¤triaje"]
+++

# PRD-01 · El índice de tareas y la verificación de alcance leen el PRD y los artefactos de EVYDENTIA

Diseño del Arquitecto ADPA, 2026-11-11 (nombre único EVYDENTIA y PRD único; decisión del propietario comunicada por el CTO), medido sobre origin/main 4141c452 por lectura; no se ejecutaron pruebas.

## Orden
PRD-00 (el CTO, en su PR: apartado `### 7.1 Catálogo de salas` en `PRD_EVYDENTIA_REVENTA_NUBE.md` y decisión sobre los 25 INV heredados) se fusiona antes. PRD-01 y PRD-02 pueden ir en paralelo; PRD-03, al final. **Bloqueante:** `PRD_EVYDENTIA_REVENTA_NUBE.md` no tiene el apartado 7.1 que lee `salas_del_prd`; devuelve 0 salas frente a 35 y cambiar solo la ruta rompería todas las fichas.

## Entrega
- `scripts/generar_indice_tareas.py`: `PRD_MD` pasa a `governance/artefactos/PRD_EVYDENTIA_REVENTA_NUBE.md` y `TASKS_MD` a `governance/artefactos/TASKS_EVYDENTIA_REVENTA_NUBE.md`. Comprueba antes que ese archivo trae los marcadores del índice que buscan `extraer_indice` y `aplicar_indice`; si no, la ficha los siembra.
- `scripts/verificar_alcance_pr.py:70`: añade `TASKS_EVYDENTIA_REVENTA_NUBE.md` a la lista de gobernanza permitida y deja `TASKS.md` mientras exista (un PR que lo toque por historia no debe fallar); su prueba (línea 45) cubre el archivo nuevo.
- **Riesgo para el reparto:** después de esta ficha el índice deja de escribirse en `TASKS.md`. Antes de empezar, `git grep 'artefactos/TASKS.md' governance/tareas` mide las fichas vivas que lo declaran y `_exenciones_propiedad.txt` (cada dueña borra su línea, CI-19).
