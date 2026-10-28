# DIAG-07 · Quién responde, quién revisa y quién sella
`¤sdd` `¤diagnostico` `¤dpo-independencia`

## 1. Datos

Migración `20261101_diagnostico_objeciones`, tabla `diagnostico_objeciones` (append-only):

| Columna | Tipo | Restricción |
| :--- | :--- | :--- |
| `id` | `VARCHAR` | PK |
| `tenant_id` | `VARCHAR` | `NOT NULL REFERENCES tenants(id)` |
| `pregunta_id` | `INTEGER` | `NOT NULL CHECK (pregunta_id BETWEEN 1 AND 80)` |
| `motivo` | `TEXT` | `NOT NULL`, `length(trim(motivo)) >= 20` |
| `objetado_por` | `VARCHAR` | `NOT NULL` (el `dpo` del token) |
| `objetado_en` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()` |
| `resuelta_en` | `TIMESTAMPTZ` | `NULL`; la pone el servidor cuando el respondiente vuelve a guardar la pregunta |

Índice `ix_diag_obj_tenant_pregunta (tenant_id, pregunta_id, objetado_en DESC)`. RLS `ENABLE` y `FORCE`. `lopdp_app`: `SELECT, INSERT, UPDATE (resuelta_en)`.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `PUT /diagnostico/respuestas` (DIAG-05) | `admin_organizacion`; encargado asignado (DIAG-04) solo en sus dimensiones | sin cambio | sin cambio; guardar una pregunta objetada la resuelve |
| `POST /diagnostico/objeciones` | `dpo` | `{"pregunta_id": int, "motivo": str}` | `201 Objecion` |
| `GET /diagnostico/objeciones?abiertas=true` | `dpo`, `admin_organizacion`, encargados, `implementador`, `coordinador` | — | `200 {"objeciones": [Objecion]}` |
| `POST /diagnostico/resultados` (sellar, DIAG-03) | `dpo` | sin cambio | sin cambio |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | `RESPUESTA_FUERA_DE_ASIGNACION` | un encargado guarda una pregunta de una dimensión que no tiene asignada |
| 403 | (dependencia de roles) | `dpo`, `implementador` o `coordinador` al guardar respuestas; cualquiera que no sea `dpo` al objetar |
| 409 | `OBJECIONES_ABIERTAS` | sellar con alguna objeción sin `resuelta_en` |
| 409 | `OBJECION_DUPLICADA` | objetar una pregunta que ya tiene objeción abierta |

## 3. Reglas

- **R1 · Quién escribe.** `puede_escribir(u, pregunta) ⇔ rol(u) = admin_organizacion ∨ (asignacion_vigente(dimension(pregunta)).responsable_user_id = u)`. El `dpo` nunca cumple el predicado, aunque tenga otra condición (no puede: ORG-13).
- **R2 · Objeción.** Solo una objeción abierta por pregunta. Guardar la pregunta (R1) fija `resuelta_en := now()` en la objeción abierta; el historial se conserva.
- **R3 · Sello.** `sellar ⇒ ¬∃ o : o.resuelta_en IS NULL`. El sellado conserva por pregunta `nivel_declarado` (lo guardado por el respondiente) y `nivel_sellado` (lo que el DPO verifica); con evidencia insuficiente, `nivel_sellado` queda topado por `calcular_nivel_efectivo` como hoy.
- **R4 · Sustitución de DIAG-03.** `ROLES_SELLO = ("dpo",)` no cambia; `_escritura` del router de respuestas deja de ser `require_role("dpo")`.
- **R5 · Auditoría.** `registrar_evento(entity_type='diagnostico_objecion', action='abierta' | 'resuelta')`.

## 4. Interfaz

`GrillaRevision.tsx` (Diagnóstico › Revisión, visible para el `dpo`): una fila por pregunta con declarado (estado, nivel de evidencia, justificación si «No aplica»), nivel verificado (editable solo por el DPO) y objeción (botón «Objetar» con motivo; distintivo «Objetada» hasta que se resuelva). El botón «Sellar» se deshabilita con objeciones abiertas y lo dice. El respondiente ve en `DiagnosticCanvas` (vía `objeciones.ts`) un aviso en la pregunta objetada con el motivo.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un `dpo`, **cuando** guarda una respuesta, **entonces** 403; **y** el `admin_organizacion` guarda cualquier dimensión. Mutación: permitir al `dpo` escribir hace fallar la prueba. | `test_dpo_no_responde` |
| **Dado** un encargado asignado a `D04`, **cuando** guarda una pregunta de `D07`, **entonces** 403 `RESPUESTA_FUERA_DE_ASIGNACION`. | `test_encargado_solo_su_dimension` |
| **Dado** una objeción abierta en la pregunta 12, **cuando** el `dpo` sella, **entonces** 409 `OBJECIONES_ABIERTAS`; **y** tras guardar la 12, sella. | `test_sello_sin_objeciones` |
| **Dado** una objeción abierta, **cuando** se objeta la misma pregunta, **entonces** 409 `OBJECION_DUPLICADA`. | `test_objecion_unica` |
| **Dado** objeciones de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_objeciones` |
| **Dado** la grilla como `dpo` con una objeción abierta, **entonces** «Sellar» está deshabilitado y la fila 12 muestra «Objetada». | `frontend/tests/diagnostico/revision.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DIAG-07.md`. PRD: Módulo 1 («Assessment por dominios con responsables», «Revisión del DPO»). Invariante: `INV_LOPDP_DPO_INDEPENDENCE`. Sustituye la decisión de DIAG-03 del 2026-10-27 por la del 2026-10-28.
- Depende de DIAG-04 (asignaciones) y DIAG-05 (router de respuestas y «No aplica»).
