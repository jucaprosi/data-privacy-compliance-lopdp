# CI-28b · Comprobación de la revisión de Alembic en todas las cabezas
`¤sdd` `¤arbitro` `¤revision-alembic`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `scripts/verificar_cloudsql_conexion.py` | `comprobar_revision` devuelve 0 si `motivo_revision_por_conjuntos` es `None` y 1 si no |
| `tests/test_gcp04_cloudsql_migration_cutover.py` | las pruebas CI-18 de la comprobación 5 usan conjuntos de cabezas |

Hecho medido en `origin/main` 9ad68eb6: `motivo_revision` solo se llama desde `comprobar_revision` (línea 122) y desde dos pruebas de `test_gcp04_cloudsql_migration_cutover.py` (líneas 87 y 94). Ningún workflow, arnés `.ps1`/`.bat` ni documento de operaciones la llama. `main()` ya usa `motivo_revision_por_conjuntos` (línea 184).

## 2. API

Función pura `comprobar_revision(revision_en_base, cabezas) -> int`, con el docstring «0 si la base está en todas las cabezas del repositorio; 1 si no.»

## 3. Reglas

- **R1 · Una sola comprobación.** La comprobación 5 es la igualdad de conjuntos entre las revisiones de la base y las cabezas del repositorio (CI-28). `comprobar_revision` y `main()` usan la misma función.
- **R-ADPA · Ortogonalidad ZERAG (`CI-28b`).** Solo el script y su prueba.

## 4. Interfaz

No aplica.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** cabezas `{"rama_a", "rama_b"}`, **entonces** la base `{"rama_a", "rama_b"}` da 0; `{"rama_a"}` (falta una) da 1; `{"rama_a", "rama_b", "zz"}` (sobra una) da 1; `None` da 1. Mutación m1: volver a la comprobación de una sola cabeza hace que el caso de dos cabezas iguales dé 1 y la prueba falle. | `test_ci18_05_dos_cabezas_por_conjuntos` |
| **Dado** la base de prueba migrada con todas las cabezas, **entonces** `comprobar_revision(estado.revision, cabezas_del_repositorio())` da 0. | `test_verificador_contra_postgres_16_con_lopdp_app` |

Las pruebas nuevas van sin `import yaml`. La función de una sola cabeza se borra con sus pruebas y no queda ninguna prueba de su ausencia.

## 6. Trazabilidad

- Ficha: `governance/tareas/CI-28b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Cierra CI-28, que añadió `motivo_revision_por_conjuntos` sin conectarla a `comprobar_revision` (CI-18). Pedido del CTO (2026-11-15).
- Depende de CI-18, CI-28 y GCP-04, hechas.
