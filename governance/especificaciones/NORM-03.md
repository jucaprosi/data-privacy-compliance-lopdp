# NORM-03 · Análisis de impacto normativo con validación humana
`¤sdd` `¤inteligencia-normativa` `¤copiloto-ia` `¤vertex-cache` `¤dpo-independencia`

## 1. Datos

Tabla `normativa_analisis_impacto` (RLS forzado por `tenant_id`):
- `id` (UUID PK), `tenant_id`, `resolucion_id` (FK a `normativa_resoluciones`), `modelo` (`gemini-2.5-pro`), `corpus_sha256`;
- `propuesta` (JSONB: lista de `{tipo: pregunta|tratamiento|tarea|plantilla, referencia_id, motivo, articulos_citados}`), `sin_base_normativa` (bool);
- `estado` (`propuesta`, `aceptada`, `rechazada`), `decidida_por`, `decidida_en`, `nota`.

## 2. API

- `POST /api/v1/normativa/resoluciones/{id}/impacto` -> `202 Accepted` (administrador o DPO de la organización).
- `GET /api/v1/normativa/impacto?resolucion_id=` -> `200 OK`, solo de la propia organización.
- `POST /api/v1/normativa/impacto/{id}/decision` con `{"decision": "aceptar"|"rechazar", "nota"}` -> `200 OK`; solo el DPO; `403` para otro rol.

## 3. Reglas

- **R1 · Validación humana inviolable (`INV_NORMATIVA_HUMAN_LEGAL_VALIDATION`).** Una propuesta de IA no modifica ningún assessment, ficha del RAT, tarea ni plantilla. Solo la aceptación del DPO genera hallazgos hacia el plan de acción, y estos siguen su flujo normal.
- **R2 · Cita cerrada (`INV_LOPDP_AI_RAG_STRICT_CITATION`).** Cada elemento de la propuesta cita artículos de la resolución; si no hay sustento, `sin_base_normativa` es verdadero y la propuesta queda vacía.
- **R3 · Independencia del DPO (`INV_LOPDP_DPO_INDEPENDENCE`).** Decide el DPO; el administrador puede pedir el análisis, pero no aceptarlo.
- **R4 · Caché al día (`INV_LOPDP_VERTEX_CONTEXT_CACHE_SHA256`).** Un cambio de estado de una resolución a `vigente`, `reformada` o `derogada` pide a VTX-01 regenerar la caché con el nuevo `corpus_sha256`.
- **R5 · Aislamiento.** Una organización nunca ve el análisis de otra.

## 4. Interfaz

Pestaña «Impacto» dentro del detalle de una resolución en la pantalla de NORM-02:
- lista de elementos afectados, con su cita y enlace al elemento;
- botones «Aceptar» y «Rechazar» para el DPO, con nota obligatoria;
- aviso visible de que la propuesta la generó una IA y requiere revisión.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un análisis en estado `propuesta`, **cuando** se consulta el assessment y el RAT de la organización, **entonces** no cambió nada. | `test_propuesta_no_modifica_nada` |
| **Dado** el DPO acepta la propuesta, **cuando** se consulta el plan de acción, **entonces** hay un hallazgo por elemento aceptado. | `test_aceptacion_genera_hallazgos` |
| **Dado** el modelo simulado sin sustento en la resolución, **cuando** se analiza, **entonces** `sin_base_normativa` es verdadero y la propuesta está vacía. | `test_sin_base_normativa` |
| **Dado** el administrador, **cuando** intenta aceptar, **entonces** recibe 403. | `test_solo_dpo_decide` |
| **Dado** dos organizaciones con análisis de la misma resolución, **cuando** B lista sus análisis, **entonces** solo ve los suyos. | `test_impacto_aislamiento_rls` |
| **Dado** una resolución que pasa a `vigente`, **cuando** se confirma, **entonces** se pide regenerar la caché con el nuevo `corpus_sha256`. | `test_regenera_cache_al_cambiar_estado` |

## 6. Trazabilidad

- `PRD.md` Módulo 6.3 y 6.5; invariantes 21, 22 y 41 de `INVARIANTS.md`.
