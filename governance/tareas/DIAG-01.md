+++
id = "DIAG-01"
titulo = "El diagnóstico se guarda en el servidor por organización (hoy solo vive en el navegador)"
ola = "D"
estado = "hecha"
sala = "diagnostico, frontend"
depende_de = ["QA-04", "ENT-02", "RM-00"]
propiedad = ["features/diagnostico/services/respuestas_engine.py", "features/diagnostico/diagnostico_service.py#DIAG-01", "api/routers/diagnostico_respuestas.py", "alembic/versions/20261024_diagnostico_respuestas.py", "tests/test_diagnostico_respuestas.py", "frontend/src/lib/diagnostico/clienteRespuestas.ts", "frontend/src/store/useAuditStore.ts", "frontend/tests/diagnostico/persistencia.spec.ts"]
arbitro = "pytest tests/test_diagnostico_respuestas.py contra una rama Neon de revisión (incluido el aislamiento RLS entre organizaciones) + suite completa + Playwright de frontend/tests/diagnostico + tsc --noEmit; prueba de mutación documentada"
rastros = ["¤diagnostico", "¤rbac-tenant"]
+++

# DIAG-01 · Diagnóstico persistido en el servidor

**Hallazgo (2026-10-23).** Las respuestas del diagnóstico solo se guardan en el `localStorage` del navegador (`useAuditStore.ts`, `persist` con nombre `jubys-audit-storage`). El backend no las conoce: otro usuario de la misma organización no las ve, se pierden al cambiar de equipo y la generación de la hoja de ruta las recibe vacías (`assessment = {}`). Es la precondición de RM-19 y de la plantilla sectorial (RAT-02).

## Entrega
- Tabla `diagnostico_respuestas` (migración Alembic, id de revisión de 32 caracteres como máximo): `tenant_id`, `pregunta_id`, `control` (nombre del control del banco), `dimension` (D01-D10), estado de cumplimiento, nivel de evidencia, criticidad, `es_critica`, `riesgo_base`, `respondido_por`, `actualizado_en`, con restricciones CHECK de cada escala. Una fila por organización y pregunta. **RLS** por `tenant_id`, como el resto de tablas con datos de organización (QA-04).
- `GET` y `PUT /api/v1/diagnostico/respuestas`: leer y guardar las respuestas de la organización del usuario. Escriben `implementador` y `coordinador`; leen además `dpo` y `admin_organizacion`. Cada cambio deja un evento en `audit_events`.
- El store carga del servidor al entrar y guarda al responder. `localStorage` queda solo como caché; las respuestas de referencia (`esReferencia`) nunca se envían.
- Pruebas: guardar y leer; otra organización no ve las respuestas (RLS); rol sin permiso (403); dimensión fuera de D01-D10 o control sin nombre (422, sin guardar nada).
- **Prueba de mutación documentada:** quitar el filtro por `tenant_id` y comprobar que la prueba de aislamiento falla.

## Límites
- No cambia las preguntas, el cálculo de madurez ni la ficha organizacional.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.

## Corrección del coordinador al implementar (2026-10-24)
- **Sin código P1-P73.** El banco de preguntas del diagnóstico tiene **80** preguntas (ids 1-80) con nombre y dimensión, pero sin código P, y no existe en el código una correspondencia con el catálogo P1-P73 de la hoja de ruta. Se guarda `pregunta_id` + nombre del control; la correspondencia queda como hallazgo para **RM-19**, que no debe inventarla.
- Se guardan también `es_critica` y `riesgo_base`, para que otra persona recupere la respuesta completa.
- El navegador guarda solo la respuesta que cambia (un evento de auditoría por guardado). Al abrir, carga lo del servidor, y si el servidor está vacío sube lo que hubiera en ese navegador. Si falla, el motivo queda en `errorSincronizacion`.
- El router se registra solo (`AUTO_REGISTRO`): `main.py` no cambia.
