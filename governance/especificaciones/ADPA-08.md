# ADPA-08 · Restauración de esquema y RLS para `terceros_encargados` y `transferencias_terceros`
`¤sdd` `¤adpa` `¤rls` `¤terceros` `¤transferencias`

## 1. Datos

Restaura en Alembic las tablas `terceros_encargados` y `transferencias_terceros` con `tenant_id` y RLS forzado.

## 2. API

Sin rutas nuevas (habilita las migraciones y rutas de `TER-01` y `TER-02`).

## 3. Reglas

- **R1 · Existencia física y RLS forzado.** `terceros_encargados` y `transferencias_terceros` existen en el historial de Alembic con `relrowsecurity = true` y `relforcerowsecurity = true`.
- **R2 · Menor privilegio `lopdp_app`.** `lopdp_app` posee `SELECT, INSERT, UPDATE` y no posee `DELETE` sobre ambas tablas.
- **R3 · Separación de modelos por sala.** `features/transferencias/models.py` expone `TransferenciaTercero` sin importar de `features.terceros`.

## 4. Interfaz

Sin interfaz propia.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el esquema migrado a `head`, **cuando** se inspeccionan `terceros_encargados` y `transferencias_terceros`, **entonces** ambas tablas existen con RLS activo y forzado y `lopdp_app` carece de permiso `DELETE`. | `test_tablas_terceros_y_transferencias_existen_con_rls` |

## 6. Trazabilidad

- Hallazgo documentado en `SEC-09` (`governance/tareas/SEC-09.md`).
