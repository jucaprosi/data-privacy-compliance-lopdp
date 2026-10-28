# DIAG-04 · Asignación de dominios a responsables de área
`¤sdd` `¤diagnostico` `¤rbac-tenant`

## 1. Datos

Migración `20261030_diagnostico_asignaciones`, tabla `diagnostico_asignaciones` (append-only; la vigente es la última por dominio):

| Columna | Tipo | Restricción |
| :--- | :--- | :--- |
| `id` | `VARCHAR` | PK |
| `tenant_id` | `VARCHAR` | `NOT NULL REFERENCES tenants(id)` |
| `dimension` | `VARCHAR(3)` | `NOT NULL CHECK (dimension ~ '^D(0[1-9]\|10)$')` |
| `responsable_user_id` | `VARCHAR` | `NULL` (nulo = desasignado) |
| `asignado_por` | `VARCHAR` | `NOT NULL` |
| `asignado_en` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |

Índice `ix_diag_asig_tenant_dim (tenant_id, dimension, asignado_en DESC)`. RLS `ENABLE` y `FORCE`. `lopdp_app`: `SELECT, INSERT`.

Los «dominios» asignables son las diez dimensiones `D01`–`D10` de `features/diagnostico/services/dimensiones_sgpdp.py` (no los 16 grupos `G01`–`G16`, que no están en la base).

## 2. API

Router `api/routers/diagnostico_asignaciones.py`, prefijo `/diagnostico`, `AUTO_REGISTRO = True`.

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /diagnostico/asignaciones` | `implementador`, `coordinador`, `dpo`, `admin_organizacion`, `responsable_area` | — | `200 {"asignaciones": [{dimension, nombre_dimension, responsable_user_id, asignado_en}]}` (10 filas, una por dimensión; sin responsable ⇒ `null`) |
| `PUT /diagnostico/asignaciones/{dimension}` | `implementador`, `coordinador` | `{"responsable_user_id": str \| null}` | `200` la asignación vigente |
| `GET /diagnostico/asignaciones/historial?dimension=` | `implementador`, `coordinador`, `dpo` | — | `200 {"historial": [...]}` más reciente primero |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | `dpo` o `responsable_area` al asignar |
| 422 | `RESPONSABLE_SIN_ROL` | el usuario no tiene rol `responsable_area` vigente en la organización |
| 422 | (FastAPI) | `dimension` fuera de `D01`–`D10` |

## 3. Reglas

- **R1 · Solo responsables de área.** `∃ r ∈ user_tenant_roles : r.user_id = responsable_user_id ∧ r.tenant_id = tenant ∧ r.role = 'responsable_area' ∧ vigente`; se comprueba con `organizacion_service.has_active_role`.
- **R2 · Vigente = última.** La asignación vigente de `d` es la fila con mayor `asignado_en`; `null` desasigna.
- **R3 · Sin efecto sobre quién responde.** Esta tarea no cambia `PUT /diagnostico/respuestas` (hoy solo escribe el `dpo`, DIAG-03). Ver la decisión abierta.
- **R4 · Auditoría.** `registrar_evento(entity_type='diagnostico_asignacion', entity_id=dimension, action='asignada' | 'desasignada', payload={responsable_user_id})`.

## 4. Interfaz

Pantalla Diagnóstico › Asignación (`menus/DIAG-04.ts`, `pantallas/DIAG-04.tsx`, `AsignacionDominios.tsx`): tabla de diez dimensiones con un selector de responsable (lista de `responsable_area` vigentes por `/organizacion` existente) para `implementador` y `coordinador`; solo lectura para los demás; enlace al historial.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un usuario sin rol `responsable_area`, **cuando** se asigna a `D04`, **entonces** 422 `RESPONSABLE_SIN_ROL`. Mutación: aceptar cualquier usuario hace fallar la prueba. | `test_asignacion_exige_responsable` |
| **Dado** dos asignaciones sucesivas de `D04`, **entonces** `GET` devuelve la última y el historial las dos. | `test_asignacion_vigente_es_ultima` |
| **Dado** un `dpo`, **cuando** asigna, **entonces** 403; **y** puede leer. | `test_dpo_no_asigna` |
| **Dado** asignaciones de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_asignaciones` |
| **Dado** la pantalla como `coordinador`, **cuando** elige un responsable para `D07`, **entonces** la fila muestra su nombre tras recargar. | `frontend/tests/diagnostico/asignaciones.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DIAG-04.md`. PRD: Módulo 1 («Assessment por dominios con responsables»). Contraste: apartado 6 (DIAG).
- **Contradicción abierta (para el propietario):** `DIAG-03` (decisión del 2026-10-27) hace que **solo el DPO responda y selle** el assessment; el PRD tras #210 y la estructura EVYDENTIA dicen que los **responsables de área responden** su dominio y el **DPO revisa** (D-2: el DPO no ejecuta). Esta especificación no toca quién responde; la tarea que lo cambie necesita una decisión explícita y, si procede, una revisión de DIAG-03.
