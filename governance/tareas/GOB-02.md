+++
id = "GOB-02"
titulo = "Verificador de especificaciones de tareas"
ola = "indep"
estado = "hecha"
sala = "gobernanza"
depende_de = []
propiedad = ["scripts/generar_indice_tareas.py", "tests/test_indice_tareas.py", "governance/tareas/README.md"]
arbitro = "pytest tests/test_indice_tareas.py"
rastros = ["¤arbitro", "¤bbap"]
+++

# GOB-02 · Verificador de especificaciones de tareas

**Objetivo.** Hacer comprobable la independencia entre tareas en lugar de afirmarla.

## Entrega
- Valida ids, dependencias, ciclos y que dos tareas que pueden ejecutarse a la vez no posean el mismo archivo; genera el índice de `TASKS.md`.

## Hecho cuando
- Entregado junto con las especificaciones de la Fase 7.
