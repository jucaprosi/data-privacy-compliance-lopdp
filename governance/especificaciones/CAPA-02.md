# CAPA-02 · Controles periódicos
`¤sdd` `¤controles-periodicos` `¤hallazgos`

## 1. Datos

Migración `20261030_controles_periodicos`.

**`controles_periodicos`**

| Columna | Tipo | Restricción |
| :--- | :--- | :--- |
| `id` | `VARCHAR` | PK, UUID v4 |
| `tenant_id` | `VARCHAR` | `NOT NULL REFERENCES tenants(id)` |
| `nombre` | `TEXT` | `NOT NULL`, 1–200 |
| `control_ref` | `VARCHAR(5)` | `NULL`; `CHECK (control_ref ~ '^P([1-9]\|[1-7][0-9]\|80)$')` |
| `frecuencia` | `VARCHAR(10)` | `NOT NULL CHECK (frecuencia IN ('mensual','trimestral','semestral','anual'))` |
| `responsable_user_id` | `VARCHAR` | `NOT NULL`; rol vigente en la organización (R2) |
| `proxima_verificacion` | `DATE` | `NOT NULL` |
| `estado` | `VARCHAR(10)` | `NOT NULL DEFAULT 'vigente' CHECK (estado IN ('vigente','vencido','retirado'))` |
| `hallazgo_vigente_id` | `VARCHAR` | `NULL REFERENCES hallazgos(id)`; el hallazgo abierto de este vencimiento |
| `creado_por`, `creado_en`, `actualizado_en` | `VARCHAR`, `TIMESTAMPTZ`, `TIMESTAMPTZ` | `NOT NULL` |

**`verificaciones_control`** (append-only)

| Columna | Tipo | Restricción |
| :--- | :--- | :--- |
| `id` | `VARCHAR` | PK |
| `tenant_id` | `VARCHAR` | `NOT NULL REFERENCES tenants(id)` |
| `control_id` | `VARCHAR` | `NOT NULL REFERENCES controles_periodicos(id)` |
| `verificado_por` | `VARCHAR` | `NOT NULL` |
| `verificado_en` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |
| `evidencia_sha256` | `VARCHAR(64)` | `NULL`; referencia a una evidencia de la organización (O-3), no se custodia |
| `nota` | `TEXT` | `NULL` |

RLS `ENABLE` y `FORCE` por `tenant_id` en ambas. `lopdp_app`: `controles_periodicos` `SELECT, INSERT, UPDATE`; `verificaciones_control` `SELECT, INSERT`.

## 2. API

Router `api/routers/auditoria_capa_controles.py`, prefijo `/auditoria-capa`, `AUTO_REGISTRO = True`.

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /auditoria-capa/controles?estado=` | `implementador`, `coordinador`, `dpo`, `admin_organizacion`, `responsable_area` (solo los suyos) | — | `200 {"controles": [Control]}` |
| `POST /auditoria-capa/controles` | `implementador`, `coordinador` | `{nombre, control_ref?, frecuencia, responsable_user_id, proxima_verificacion}` | `201 Control` |
| `POST /auditoria-capa/controles/{id}/verificaciones` | `implementador`, o el `responsable_user_id` del control | `{evidencia_sha256?, nota?}` | `201 {"control": Control, "verificacion": Verificacion}` |
| `POST /auditoria-capa/controles/{id}/retirar` | `implementador`, `coordinador` | `{motivo}` | `200 Control` |
| `POST /auditoria-capa/controles/vencer` | `implementador` | — | `200 {"vencidos": int, "hallazgos_creados": int}` (R4; lo llama la pantalla al abrirla el `implementador`) |

`Control` = `{id, nombre, control_ref, frecuencia, responsable_user_id, proxima_verificacion, estado, hallazgo_vigente_id, ultima_verificacion_en}`.

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | `dpo` al crear o verificar; `responsable_area` sobre un control ajeno |
| 404 | `CONTROL_NO_ENCONTRADO` | id fuera de la organización |
| 409 | `CONTROL_RETIRADO` | verificar o vencer uno `retirado` |
| 422 | `RESPONSABLE_SIN_ROL` | `responsable_user_id` sin rol vigente en la organización |
| 422 | `EVIDENCIA_NO_ENCONTRADA` | `evidencia_sha256` no existe en la organización (`evidencias_service`) |

## 3. Reglas

- **R1 · Siguiente fecha.** Al verificar, `proxima_verificacion := fecha(verificado_en) + Δ(frecuencia)` con Δ = 1, 3, 6 o 12 meses (mismo día del mes; si no existe, el último del mes); `estado := 'vigente'`; si había `hallazgo_vigente_id`, el hallazgo pasa a `cerrado` por la compuerta de `roadmap` (`roadmap_service.cerrar_hallazgo`, sección `#CAPA-02`) y el campo se limpia.
- **R2 · Responsable.** `has_active_role(responsable_user_id, tenant_id)` debe ser verdadero al crear; el `dpo` no puede ser responsable (D-2).
- **R3 · Vencimiento.** Un control está vencido si `estado = 'vigente' ∧ proxima_verificacion < hoy` (Guayaquil).
- **R4 · Un hallazgo por vencimiento.** Al vencer: `estado := 'vencido'` y `registrar_hallazgo(origen='control_periodico', origen_ref=f"{id}:{proxima_verificacion}", severidad='alta', control_ref, titulo=f"Control vencido: {nombre}")`; `hallazgo_vigente_id := id del hallazgo`. La clave de origen hace idempotente la operación: ejecutar `vencer` dos veces no crea otro hallazgo. `auditoria_capa` nunca inserta en `roadmap_tasks`.
- **R5 · Sin vigencia propia.** Esta tarea no lee ni guarda vencimiento de evidencias; `evidencia_sha256` es una referencia (CAPA-03 añade la reapertura).
- **R6 · Auditoría.** `registrar_evento(entity_type='control_periodico', action='creado' | 'verificado' | 'vencido' | 'retirado')`.

## 4. Interfaz

Pantalla Riesgos y auditoría › Controles periódicos (`menus/CAPA-02.ts`, `pantallas/CAPA-02.tsx`): lista con nombre, frecuencia, responsable, próxima verificación y estado (semáforo: vigente, vence en ≤ 7 días, vencido); botón «Registrar verificación» para quien puede; formulario de alta para `implementador` y `coordinador`. Un control vencido muestra el enlace a su hallazgo.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un control con `proxima_verificacion` ayer, **cuando** se ejecuta `vencer` dos veces, **entonces** queda `vencido` y existe exactamente un hallazgo `control_periodico`. Mutación: crear una tarea directamente hace fallar la prueba de «sin tareas creadas desde auditoria_capa». | `test_vencimiento_un_hallazgo` |
| **Dado** un control vencido, **cuando** su responsable registra una verificación, **entonces** vuelve a `vigente`, la próxima fecha es hoy + Δ y el hallazgo queda `cerrado`. | `test_verificacion_cierra_ciclo` |
| **Dado** `responsable_user_id` sin rol, **entonces** 422 `RESPONSABLE_SIN_ROL`; **y dado** un `dpo`, 403 al crear. | `test_responsable_y_roles` |
| **Dado** una verificación con `evidencia_sha256` inexistente, **entonces** 422. | `test_evidencia_referenciada` |
| **Dado** controles de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_controles` |
| **Dado** la pantalla con un control que vence en 3 días, **entonces** se ve en ámbar; vencido, en rojo con enlace al hallazgo. | `frontend/tests/controles/controles.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/CAPA-02.md`. PRD: Módulo 3 («Controles periódicos»), criterio 17. Invariante: `INV_LOPDP_SINGLE_ACTION_PLAN` (vía RM-21). Contraste: O-8.
- Decisión del coordinador (2026-10-30): `vencer` lo dispara la pantalla al abrirla el `implementador`. Un cron diario necesita recorrer todas las organizaciones sin `BYPASSRLS` y se decide aparte.
- Decisión del coordinador (2026-10-30): RM-21 no dejó función de cierre y el cierre por tareas de RM-23 no cubre R1; CAPA-02 añade `cerrar_hallazgo` (cierre por el origen) en su sección de la compuerta de `roadmap`.
