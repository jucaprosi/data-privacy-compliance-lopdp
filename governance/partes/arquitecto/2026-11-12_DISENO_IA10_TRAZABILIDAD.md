# Diseño ADPA: IA-10, trazabilidad de la IA y tres niveles de uso

Arquitecto ADPA, 2026-11-12. Pedido del CTO (brief de IA-10). Fuente: PR #645 (PRD §6.5, invariantes 64 `INV_AI_RESULT_TRACEABILITY` y 65 `INV_AI_THREE_TIER_USE`), todavía abierto. Medido sobre `origin/main` 89880993. Los ids definitivos los pone el Tech Lead. Los nombres de este documento son provisionales.

## 1. Lo que ya existe y cambia el pedido

- **IA-05** (pendiente, sala ai_copilot) ya dice: «se retiran el filtro de log de la clave, la línea `Intentando invocar LLM con API KEY` y el plan simulado». La fuga de la clave (hallazgo d) ya está en una ficha, pero espera a IA-03, que está en curso. Para no esperar, la saco en una ficha corta (SEC-22) que va antes que IA-05.
- **IA-06** (pendiente, sala roadmap) solo posee `features/roadmap/ai/client.py`. Pasar la Hoja de Ruta a Vertex también exige tocar `generacion_engine.py`, `roadmap_prompts.py` y `generacion_en_linea.py`. Propongo **ampliar la propiedad de IA-06**, que no ha empezado, en vez de abrir una ficha paralela sobre los mismos archivos. El cambio de alcance lo cierra el Tech Lead.
- **IA-03** (en curso) tiene `generar_estructurado`, que devuelve solo el `BaseModel` y pierde la versión del modelo que devuelve Vertex (`respuesta.model_version`). Sin ese dato no se puede cumplir el invariante 64. Lo resuelve IA-10, que depende de IA-03 y toma sus archivos cuando IA-03 esté hecha.
- **No existe ninguna transición de `generated` a `active`** en la Hoja de Ruta: hoy no hay revisión humana. El nivel 2 del invariante 65 exige una ficha nueva (RM-27).
- Hay un segundo incumplimiento que el brief no menciona: el copiloto **inventa un plan simulado** cuando falla la llamada (`inference_engine.py:79-97`), y su `impacto_riesgo` simulado sale de `scoring_global < 3.0`. Lo retira IA-05.

## 2. Fichas y orden

```
SEC-22 ───────────────┐
IA-03 → IA-10 ─┬──────┴─→ IA-05 (ampliada)
               ├→ IA-11 (evaluación)
               └→ RM-26 → IA-06 (ampliada) → RM-27
```

SEC-22 entra ya, sin dependencias. IA-11 y RM-26 pueden correr en paralelo después de IA-10.

### SEC-22 · Sin clave de API en el registro del copiloto
- Sala: ai_copilot. Depende de: nada.
- Propiedad: `features/ai_copilot/services/inference_engine.py`, `tests/test_sec22_sin_clave_en_log.py`. Crea la prueba.
- Entrega: se borra la línea 38 (`logger.info(f"Intentando invocar LLM con API KEY {api_key}")`) y el `APILoggerFilter`. El filtro no protege: solo mira `record.msg`, solo en ese logger, y la fuga venía del mismo módulo. No se toca nada más.
- Árbitro: la prueba captura los registros con `caplog`, fija `OPENAI_API_KEY=clave-falsa-123` y comprueba que la cadena no aparece en ningún registro. Mutación: reponer la línea 38 → rojo.
- IA-05 pasa a depender de SEC-22, porque las dos poseen el mismo archivo.

### IA-10 · Trazabilidad de cada resultado de IA y prompts versionados
- Sala: inferencia. Depende de: IA-03.
- Propiedad: `features/inferencia/inferencia_service.py`, `features/inferencia/domain/prompts.py`, `features/inferencia/domain/traza.py`, `features/inferencia/services/cliente_vertex.py`, `app_core/pasillo/inferencia.py`, `alembic/versions/20261112_ia10_trazas_ia.py`, `tests/test_ia10_trazabilidad.py`, `tests/test_ia10_rls_trazas.py`, `tests/test_ia10_huellas_prompts.py`, `evaluacion/ia/huellas_prompts.json`.
- Crea: `features/inferencia/domain/prompts.py`, `features/inferencia/domain/traza.py`, la migración, las tres pruebas y `evaluacion/ia/huellas_prompts.json`.
- **Una sola migración y una sola tabla**, `trazas_ia`: `id`, `tenant_id`, `sala`, `entidad` (por ejemplo `roadmaps` o `tareas_mitigacion`), `entidad_id`, `modelo_version` (lo que devuelve Vertex, no el alias), `modelo_solicitado` (alias), `prompt_id`, `prompt_version`, `corpus_sha256` (nulo si no se usó el corpus) y `creado_en`. RLS por `tenant_id` con `FORCE`, igual que las demás tablas del tenant. No se agregan columnas a `roadmaps`, `tareas_mitigacion` ni a tablas futuras (NORM-03, preanálisis): cada sala escribe una fila aquí, y ninguna otra ficha necesita migración para cumplir el invariante 64. La migración aplica FUSION_ALEMBIC antes de fusionar, y la simulación tiene que dar una sola cabeza.
- **Prompts versionados.** `domain/prompts.py` define `PromptVersionado(id, version, sistema, plantilla)`. Cada sala declara los suyos en su propio módulo (`features/<sala>/ai/prompts.py`) con un diccionario `VERSIONES = {1: ..., 2: ...}` y una constante `VIGENTE`. Las versiones anteriores no se borran, que es lo que exige el invariante 64.
- **Compuerta.** Nueva función `generar_trazado(prompt, valores, esquema, *, modelo, org_id, corpus_sha256=None) -> (resultado, Traza)`. La traza lleva `respuesta.model_version`. Si Vertex no devuelve la versión, la función falla cerrada (`InferenciaNoDisponible`). Que el SDK la devuelve hay que comprobarlo en la prueba de humo de IA-03 (ESTIMADO hasta entonces). También `registrar_traza(session, traza, entidad, entidad_id)`, que escribe la fila en la sesión del llamador, en la misma transacción que el resultado. `generar_estructurado` queda solo para las pruebas existentes y se retira cuando IA-05 e IA-06 dejen de usarlo.
- **Huellas de prompts.** `evaluacion/ia/huellas_prompts.json` guarda el sha256 de cada `(id, version)`. La prueba recorre todos los `VERSIONES` del repositorio y recalcula las huellas. Si se cambia el texto de una versión existente sin subir el número, la prueba falla.
- Árbitro: `pytest` de las tres pruebas y de las suites de IA-03. Mutaciones: (1) guardar el alias en vez de `model_version` → rojo; (2) editar el texto de un prompt sin subir la versión → rojo; (3) quitar `FORCE ROW LEVEL SECURITY` → rojo; (4) que `registrar_traza` haga su propio commit → rojo, porque la prueba exige que un rollback del llamador también se lleve la traza.

### IA-11 · Conjunto fijo de evaluación de modelos y prompts
- Sala: inferencia. Depende de: IA-10.
- Propiedad: `evaluacion/ia/casos/**`, `evaluacion/ia/resultados/**`, `scripts/evaluar_ia.py`, `tests/test_ia11_evaluacion.py`. Crea todos.
- `evaluacion/ia/casos/<prompt_id>.json`: casos ficticios (entrada más criterio verificable: campos obligatorios, cita presente, sin cifras inventadas). Están en JSON, no en YAML (regla de los tests). Ninguno lleva datos de clientes: la prueba exige que `sanitizar_texto_pii(caso) == caso`.
- `scripts/evaluar_ia.py <prompt_id> <version> <modelo>` llama a Vertex y escribe `evaluacion/ia/resultados/<prompt_id>_v<n>_<modelo>.json` con el puntaje, la fecha y `modelo_version`. **Correrlo es una compuerta humana del propietario**, porque gasta Vertex y usa sus credenciales de GCP. El CI nunca llama a Vertex.
- El CI comprueba sin red que para cada `VIGENTE` y cada modelo de `MODELOS_PERMITIDOS` que se use exista un resultado, y que su puntaje no sea menor que el de la versión anterior.
- Árbitro: `pytest tests/test_ia11_evaluacion.py`. Mutaciones: (1) subir la versión de un prompt sin resultado → rojo; (2) un resultado con puntaje menor que el anterior → rojo; (3) un caso con un correo o una cédula → rojo.

### RM-26 · Las cifras de la Hoja de Ruta las calcula código determinista
- Sala: roadmap. Depende de: IA-10 (para la forma del esquema de redacción) y RM-19 (hecha).
- Propiedad: `features/roadmap/services/cifras_engine.py`, `features/roadmap/domain/esfuerzo_controles.py`, `tests/test_rm26_cifras_deterministas.py`. Crea todos.
- Entrada: el contexto real que ya arma `contexto_generacion.py` (madurez por dimensión, nivel asignado por control y brechas), más `PlanningVariables.plazo_meses`.
- Salida: un esqueleto `PlanCifrado` con las olas, los controles de cada ola, la prioridad, las horas, las fechas de inicio y fin y el `score_objetivo`. El LLM ya no produce ninguno de esos campos.
- Reglas (decisión del CTO, 2026-11-12):
  - Prioridad por nivel del control: 0-1 crítica, 2 alta, 3 media; con nivel 4 o más no hay tarea.
  - Horas provisionales por prioridad en `esfuerzo_controles.py`: crítica 40, alta 24, media 16. Están marcadas como dato de negocio que el propietario puede afinar por control.
  - Las fechas se reparten por olas en proporción a las horas dentro de `plazo_meses`.
  - `score_objetivo` se calcula con la misma función de puntaje del diagnóstico real, por su compuerta, aplicada a la proyección en que cada control con tarea llega a nivel 4. No hay fórmula nueva. Es una proyección: nunca sube la madurez acreditada (DIAG-12).
  - RM-26 ya no está bloqueada.
- Árbitro: `pytest tests/test_rm26_cifras_deterministas.py`. Con el mismo diagnóstico, dos corridas dan exactamente el mismo `PlanCifrado`. Mutaciones: (1) usar un número aleatorio o la hora del sistema → rojo; (2) cambiar el nivel de un control → cambia la prioridad esperada; (3) calcular `score_objetivo` con una fórmula propia en vez de la del diagnóstico → rojo; (4) que la proyección escriba la madurez acreditada → rojo.

### IA-06 ampliada · La Hoja de Ruta sobre la compuerta, y el LLM solo redacta
- Sala: roadmap. Depende de: IA-03, IA-10 y RM-26.
- Propiedad, ampliada: `features/roadmap/ai/client.py`, `features/roadmap/ai/roadmap_prompts.py` (pasa a `VERSIONES` y `VIGENTE`), `features/roadmap/services/generacion_engine.py`, `features/roadmap/services/generacion_en_linea.py`, `tests/test_ia06_roadmap_inferencia.py`.
- El esquema que se pide a Gemini (`response_schema`) contiene **solo texto**: el resumen ejecutivo, el nombre y el objetivo de cada ola, y para cada control el título, la descripción, el entregable, el KPI y la evidencia requerida. Puede proponer el orden de las tareas dentro de una ola, pero no puede cambiar de ola a una tarea ni tocar su prioridad. Lo que persiste `generacion_en_linea.py` es el `PlanCifrado` de RM-26 más ese texto, y una fila en `trazas_ia` (`entidad='roadmaps'`) dentro de la misma transacción.
- Se retiran el reintento que reinyecta el error en el prompt (lo reemplaza el `response_schema`), DeepSeek y el texto de error del LLM guardado en `summary`.
- Árbitro: `pytest tests/test_ia06_roadmap_inferencia.py` más las suites del roadmap. Con un cliente falso que devuelve cifras absurdas (prioridad, horas o fechas inventadas, aunque el esquema ya no las admite), lo que se guarda es igual a lo que calcula RM-26. Mutaciones: (1) volver a guardar `kpis_globales.score_objetivo` del LLM → rojo; (2) no escribir la traza → rojo.

### IA-05 ampliada · El copiloto sobre la compuerta, sin cifras del modelo
- Sala: ai_copilot. Depende de: ADPA-03, IA-03, IA-10 y SEC-22.
- Propiedad, ampliada: `features/ai_copilot/services/inference_engine.py`, `features/ai_copilot/ai_copilot_service.py#IA-05` y `tests/test_ia05_motor_inferencia.py`. La sección `#IA-05` de `ai_copilot_service.py` todavía no existe: VTX-01 y NORM-03 poseen secciones de ese archivo y `ejecutar_diagnostico_y_crear_tareas` no está dentro de ninguna. El Tech Lead decide quién crea la sección.
- `impacto_riesgo` deja de venir del modelo: se calcula del nivel de la brecha en el diagnóstico, con la misma tabla de prioridad de RM-26, que se expone por `app_core/pasillo/roadmap.py` (sección de RM-26). El modelo solo redacta la descripción. Cada tarea guardada lleva una fila en `trazas_ia` (`entidad='tareas_mitigacion'`).
- Árbitro: la prueba existente más mutaciones: (1) volver a tomar `impacto_riesgo` del LLM → rojo; (2) reponer el plan simulado → rojo.

### RM-27 · Revisión humana antes de que la Hoja de Ruta valga (nivel 2)
- Sala: roadmap, frontend. Depende de: IA-06. **Pasa por el UX/UI**, porque cambia pantallas.
- Propiedad: `alembic/versions/20261112_rm27_revision_hoja_ruta.py`, `features/roadmap/services/revision_engine.py`, `api/routers/roadmap_revision.py` (`AUTO_REGISTRO = True`, sin tocar `main.py`), `tests/test_rm27_revision_humana.py`, más la carpeta de componentes y de pruebas de frontend que fije el UX/UI.
- La migración agrega `revisado_por` y `revisado_en` a `roadmaps`. Es otra migración, aparte de la de IA-10, porque la revisión no es trazabilidad. La transición `generated → active` solo la hace un coordinador o el DPO vigente, con `ErrorNegocio` y un código del catálogo si no.
- Cuatro ojos (decisión de producto del CTO, 2026-11-12): la transición `generated → active` no la hace quien pidió la generación. Es el mismo criterio de personas distintas que la doble validación de RM-25. Por eso la migración también agrega `generado_por`.
- Árbitro: `pytest tests/test_rm27_revision_humana.py`, con RLS de las columnas nuevas, más la prueba de frontend. Mutaciones: (1) dejar activar a un rol que no es coordinador ni DPO → rojo; (2) que la exportación o el informe usen una hoja `generated` → rojo; (3) que quien generó la hoja intente activarla → rojo.

## 3. Choques revisados

- `inference_engine.py`: SEC-22 → IA-05, en serie.
- `inferencia_service.py`, `cliente_vertex.py` y `pasillo/inferencia.py`: IA-03 → IA-10, en serie.
- `ai_copilot_service.py`: secciones de VTX-01, NORM-03 y la nueva de IA-05. Sin solapamiento si se crea la sección.
- `roadmap_prompts.py`, `generacion_engine.py` y `generacion_en_linea.py`: sus dueñas anteriores (RM-12, RM-19) están hechas. Ninguna ficha viva los posee además de IA-06 ampliada.
- Migraciones: dos (IA-10 y RM-27) en fichas en serie. Ninguna otra ficha viva crea `trazas_ia`.
- IA-08 (guardia sin OpenAI ni DeepSeek) sigue dependiendo de IA-05 e IA-06. No cambia.

## 4. Decisiones del CTO (2026-11-12, diseño aceptado)

1. RM-26: las reglas de prioridad, horas, fechas y `score_objetivo` están en su sección. Ya no está bloqueada.
2. RM-27: cuatro ojos, sí.
3. IA-11: la evaluación la corre el propietario con sus credenciales, nunca el CI. Va a sus pendientes con un brief en PowerShell.
4. SEC-22 entra en la tanda de hoy (chat `ia`). Las demás esperan a IA-03 y al PR #645.
