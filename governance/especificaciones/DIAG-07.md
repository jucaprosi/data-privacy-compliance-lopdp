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
- **R6 · Evidencia, propuesta de la IA y nivel (decisión del CTO, 2026-11-13; `INV_LOPDP_DIAG_EVIDENCE_DPO_UNTIL_SEAL`).** El flujo de una pregunta es:
  1. quien responde entrega los documentos al `dpo`;
  2. el `dpo` los sube y los vincula a la pregunta (EVI-01, sin cambios);
  3. quien cumple `puede_escribir` (R1) pide la propuesta de la IA y elige `nivel_declarado`;
  4. el `dpo` verifica, objeta y sella.
  - La propuesta solo se puede pedir si la pregunta tiene al menos una evidencia vinculada. Sin evidencia, el botón «Analizar con IA» está deshabilitado y el servidor responde 409 `PREGUNTA_SIN_EVIDENCIA`.
  - El servidor exige `puede_escribir` en `POST /preanalisis/analizar` cuando la llamada es del diagnóstico. Medido en `origin/main`: hoy esa ruta solo comprueba la organización, así que un `dpo` podría pedir la propuesta por API. Con esta regla responde 403.
  - El `dpo` nunca fija `nivel_declarado`, ni por la pantalla ni por la API (R1 ya le prohíbe guardar respuestas). La propuesta de la IA no fija ningún nivel: quien responde elige.
- **R5 · Auditoría.** `registrar_evento(entity_type='diagnostico_objecion', action='abierta' | 'resuelta')`.
- **R-ADPA · Ortogonalidad ZERAG (`DIAG-07`).** Toda invocación a otra sala se realiza vía `app_core/pasillo/<otra_sala>.py#DIAG-07` (`ImportsCruzados = ∅`, ADR 0001) y los códigos de `ErrorNegocio` (`app_core.errors`) se registran en `features/<sala>/domain/errores.py#DIAG-07`.

## 4. Interfaz

`GrillaRevision.tsx` (Diagnóstico › Revisión, visible para el `dpo`): una fila por pregunta con declarado (estado, nivel de evidencia, justificación si «No aplica»), nivel verificado (editable solo por el DPO) y objeción (botón «Objetar» con motivo; distintivo «Objetada» hasta que se resuelva). El botón «Sellar» se deshabilita con objeciones abiertas y lo dice.

En `DiagnosticCanvas.tsx`, el botón de sellar depende de quién sella y no de quién responde: el `dpo` lo ve y no puede editar respuestas; quien responde edita y no lo ve. El aviso de solo lectura distingue a quien sella de quien solo consulta.

En el bloque de respuesta de `DiagnosticCanvas.tsx`, «Analizar con IA» se muestra a quien cumple `puede_escribir` y se habilita solo cuando la pregunta tiene evidencia vinculada; sin evidencia, el botón explica que el DPO debe vincularla. El `dpo` no ve el selector de nivel declarado. Textos: UX/UI.

El aviso al respondiente en la pregunta objetada se trasladó a DIAG-15 (decisión del CTO, 2026-11-13): no es entrega de esta ficha.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un `dpo`, **cuando** guarda una respuesta, **entonces** 403; **y** el `admin_organizacion` guarda cualquier dimensión. Mutación: permitir al `dpo` escribir hace fallar la prueba. | `test_dpo_no_responde` |
| **Dado** un encargado asignado a `D04`, **cuando** guarda una pregunta de `D07`, **entonces** 403 `RESPUESTA_FUERA_DE_ASIGNACION`. | `test_encargado_solo_su_dimension` |
| **Dado** una objeción abierta en la pregunta 12, **cuando** el `dpo` sella, **entonces** 409 `OBJECIONES_ABIERTAS`; **y** tras guardar la 12, sella. | `test_sello_sin_objeciones` |
| **Dado** una objeción abierta, **cuando** se objeta la misma pregunta, **entonces** 409 `OBJECION_DUPLICADA`. | `test_objecion_unica` |
| **Dado** objeciones de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_objeciones` |
| **Dado** el lienzo como `dpo`, **entonces** ve «Sellar» y no puede editar respuestas; como `admin_organizacion`, edita y no ve «Sellar». Mutación: atar el botón a quien responde hace fallar la prueba. | `frontend/tests/diagnostico/sello-por-rol.spec.ts` |
| **Dado** una pregunta sin evidencia vinculada, **cuando** quien responde pide la propuesta, **entonces** 409 `PREGUNTA_SIN_EVIDENCIA`; **y** un `dpo` que la pide sobre una pregunta con evidencia recibe 403. Mutación: quitar la comprobación de evidencia o la de `puede_escribir` hace fallar la prueba. | `test_propuesta_ia_por_rol_y_evidencia` |
| **Dado** un `dpo`, **cuando** intenta fijar `nivel_declarado` por la API, **entonces** 403, y el lienzo como `dpo` no muestra el selector de nivel. Mutación: dejar al DPO elegir el nivel hace fallar la prueba. | `test_dpo_no_elige_nivel` |
| **Dado** tres usuarios reales, cada uno con un solo rol (ORG-13): un `dpo` sube y vincula la evidencia de una pregunta, un `admin_organizacion` pide la propuesta de la IA y elige el nivel, y el `dpo` sella. **Entonces** el recorrido termina con el diagnóstico sellado. Mutación: con la pregunta sin evidencia, «Analizar con IA» está deshabilitado para el admin; con la sesión del `dpo`, el selector de nivel no aparece. | `frontend/tests/diagnostico/escala-activa.spec.ts` |
| **Dado** la grilla como `dpo` con una objeción abierta, **entonces** «Sellar» está deshabilitado y la fila 12 muestra «Objetada». | `frontend/tests/diagnostico/revision.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DIAG-07.md`. PRD: Módulo 1 («Assessment por dominios con responsables», «Revisión del DPO»). Invariante: `INV_LOPDP_DPO_INDEPENDENCE`. Sustituye la decisión de DIAG-03 del 2026-10-27 por la del 2026-10-28.
- Depende de DIAG-04 (asignaciones) y DIAG-05 (router de respuestas y «No aplica»).
- R6: decisión del CTO del 2026-11-13, que retiró la opción de que quien responde suba la evidencia porque la invariante 59 y el PRD (Módulo 1, línea 139; tabla de roles, línea 114) prevalecen. No hay EVI-05 y EVI-01 no cambia. Se registrará como ADR con ARQ-01.
- **Propiedad que añade R6:** `api/routers/preanalisis.py`, solo la comprobación de R6 en `analizar` (ninguna ficha abierta lo posee; si alguna lo posee, va por sección `#DIAG-07`), y `frontend/tests/diagnostico/escala-activa.spec.ts`, que se reescribe con roles reales. El código `PREGUNTA_SIN_EVIDENCIA` se registra en `features/diagnostico/domain/errores.py#DIAG-07`.
- Pregunta abierta para el CTO: la grilla dice «nivel verificado (editable solo por el DPO)» y R3 guarda `nivel_sellado`. R6 prohíbe al DPO fijar el nivel declarado, no el verificado. Si «el DPO no elige nivel nunca» incluye el verificado, R3 y la grilla cambian, y `nivel_sellado` sale solo de `calcular_nivel_efectivo`.
