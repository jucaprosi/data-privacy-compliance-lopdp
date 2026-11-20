+++
id = "ORG-23"
titulo = "Lectura del auditor en diagnóstico, incidentes y hoja de ruta: auditor en ROLES_CONSULTA"
ola = "backlog"
estado = "en_curso"
sala = "diagnostico, incidentes, roadmap"
depende_de = ["ORG-22", "DIAG-11", "DIAG-07", "EVI-01", "INC-03"]
propiedad = ["api/routers/diagnostico_resultados.py", "features/incidentes/domain/models.py", "api/routers/roadmaps_hallazgos.py", "tests/matriz/RM-21.py", "tests/matriz/roles/auditor.py#ORG-22", "tests/matriz/roles/auditor.py#ORG-23", "tests/test_org23_auditor_lectura.py"]
crea = ["tests/test_org23_auditor_lectura.py"]
arbitro = "pytest tests/test_org23_auditor_lectura.py tests/test_matriz_permisos.py + suites existentes de diagnóstico, incidentes y hoja de ruta; mutación m1"
rastros = ["¤rbac-tenant"]
+++

# ORG-23 · Lectura del auditor fuera de CAPA

**Contrato:** `governance/especificaciones/ORG-23.md` (manda sobre esta ficha).

Diseño del Arquitecto ADPA (2026-11-09). ORG-22 deja al auditor operativo en `auditoria_capa`; esta ficha le abre la lectura en las tres APIs que usan `ROLES_CONSULTA`.

## Entrega
- `auditor` entra en las tres tuplas `ROLES_CONSULTA`: `api/routers/diagnostico_resultados.py`, `features/incidentes/domain/models.py` (la tupla de incidentes vive en la sala) y `api/routers/roadmaps_hallazgos.py`.
- La matriz refleja la lectura de hallazgos: `tests/matriz/RM-21.py` y la sección `ORG-23` de `tests/matriz/roles/auditor.py`.
- **Propiedad, medida en 04292440:** DIAG-11, DIAG-07, EVI-01, INC-03, RM-21 y ORG-22 están hechas; ninguno de estos archivos tiene otra dueña viva. La sección `ORG-23` de `auditor.py` está sembrada.
