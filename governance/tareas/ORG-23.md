+++
id = "ORG-23"
titulo = "Lectura del auditor en diagnóstico, incidentes y hoja de ruta: auditor en ROLES_CONSULTA"
ola = "backlog"
estado = "pendiente"
sala = "diagnostico, incidentes, roadmap"
depende_de = ["ORG-22", "DIAG-11", "DIAG-07", "EVI-01", "INC-03"]
propiedad = ["api/routers/diagnostico_resultados.py", "api/routers/incidentes.py", "api/routers/roadmaps_hallazgos.py", "tests/test_org23_auditor_lectura.py"]
crea = ["tests/test_org23_auditor_lectura.py"]
arbitro = "pytest tests/test_org23_auditor_lectura.py + suites existentes de diagnóstico, incidentes y hoja de ruta; mutación documentada"
rastros = ["¤rbac-tenant"]
+++

# ORG-23 · Lectura del auditor fuera de CAPA

Diseño del Arquitecto ADPA (2026-11-09). ORG-22 deja al auditor operativo en `auditoria_capa`. Esta ficha le abre la lectura en las tres APIs que usan `ROLES_CONSULTA`. Hasta que esté hecha, la demo muestra al auditor solo en CAPA, lo que el Arquitecto considera aceptable.

## Entrega
- Añade `auditor` a `ROLES_CONSULTA` en `diagnostico_resultados.py`, `incidentes.py` y `roadmaps_hallazgos.py`. Solo cambia esa tupla.
- **Propiedad, medida en 811c7b0:** `incidentes.py` y `roadmaps_hallazgos.py` no tienen dueñas vivas. `diagnostico_resultados.py` tiene secciones de DIAG-11 (en curso), DIAG-07 y EVI-01. ORG-23 depende de las tres y toma el archivo entero cuando ya estén hechas. Así no hace falta sembrar una sección ni añadir una exención. Al repartir, se vuelve a medir.

## Pruebas
- El auditor recibe 200 en GET y 403 en cualquier escritura de esas tres APIs.
- Mutación: quitar `auditor` de una tupla deja en rojo el GET correspondiente.
