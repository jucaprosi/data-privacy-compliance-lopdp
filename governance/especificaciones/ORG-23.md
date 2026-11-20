# ORG-23 · Lectura del auditor en diagnóstico, incidentes y hoja de ruta
`¤sdd` `¤rbac-tenant` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `api/routers/diagnostico_resultados.py` | `ROLES_CONSULTA = ("dpo", "implementador", "coordinador", "admin_organizacion", "auditor")` |
| `features/incidentes/domain/models.py` | `ROLES_CONSULTA = ROLES_REGISTRO + ("dpo", "auditor")` |
| `api/routers/roadmaps_hallazgos.py` | `ROLES_CONSULTA = ("implementador", "coordinador", "dpo", "admin_organizacion", "auditor")` |
| `tests/matriz/RM-21.py` | la fila `listar_hallazgos` incluye `auditor` |
| `tests/matriz/roles/auditor.py` | `"listar_hallazgos": True` en la sección `ORG-23`; la clave sale de la sección `ORG-22` |
| `tests/test_org23_auditor_lectura.py` (nuevo) | casos de §5 |

Hecho medido en `origin/main` 04292440:
- Las tres tuplas no incluyen `auditor`. `ROLES_CONSULTA` protege, en diagnóstico, `GET /api/v1/diagnostico/resultados` y `GET /api/v1/diagnostico/etapa`; en incidentes, `GET /api/v1/incidentes`; en hoja de ruta, `GET /api/v1/roadmaps/hallazgos`.
- Solo `GET /api/v1/roadmaps/hallazgos` está bajo `PREFIJOS_MATRIZ`; hoy `auditor.py` lo marca `False`.
- Las objeciones (`_lee_objeciones`, DIAG-07) y la revisión del DPO no usan `ROLES_CONSULTA` y no cambian.

## 2. API

| Método y ruta | Roles tras ORG-23 |
| :--- | :--- |
| `GET /api/v1/diagnostico/resultados`, `GET /api/v1/diagnostico/etapa` | dpo, implementador, coordinador, admin_organizacion y auditor |
| `GET /api/v1/incidentes` | admin_organizacion, coordinador, responsable_area, implementador, dpo y auditor |
| `GET /api/v1/roadmaps/hallazgos` | implementador, coordinador, dpo, admin_organizacion y auditor |

Las escrituras de esas tres APIs (`POST /diagnostico/resultados`, `POST /incidentes` y sus cambios de estado, y las rutas de gestión de hallazgos) siguen con sus roles y dan 403 al auditor.

## 3. Reglas

- **R1 · Lectura del auditor.** El auditor lee los resultados sellados y la etapa del diagnóstico, la bitácora de incidentes y los hallazgos de la hoja de ruta de su organización. Solo cambian las tres tuplas `ROLES_CONSULTA`.
- **R2 · Sin escritura.** El auditor no sella, no registra incidentes ni cambia su estado y no gestiona hallazgos.
- **R-ADPA · Ortogonalidad ZERAG (`ORG-23`).** Cada tupla en su archivo; sin imports nuevos entre salas.

## 4. Interfaz

No aplica: las pantallas ya muestran estas lecturas a quien recibe 200.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un auditor del tenant, **cuando** hace GET de `/diagnostico/resultados`, `/diagnostico/etapa`, `/incidentes` y `/roadmaps/hallazgos`, **entonces** 200. Mutación m1: quitar `auditor` de una de las tres tuplas deja en rojo el GET correspondiente. | `test_auditor_lee_las_tres_apis` |
| **Dado** un auditor, **cuando** sella un resultado, registra un incidente o gestiona hallazgos, **entonces** 403. | `test_auditor_no_escribe` |
| **Dado** la matriz, **entonces** `listar_hallazgos` permite al auditor y la carga de roles no deja claves sin decidir. | `tests/test_matriz_permisos.py` |

La prueba nueva va sin `import yaml`.

## 6. Trazabilidad

- Ficha: `governance/tareas/ORG-23.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Diseño del Arquitecto ADPA (2026-11-09) tras ORG-22. Depende de ORG-22, DIAG-11, DIAG-07, EVI-01 e INC-03, hechas.
