+++
id = "EVI-02"
titulo = "Vigencia y visibilidad de las evidencias y paquete para inspección ordenado por requisito"
ola = "D"
estado = "pendiente"
sala = "evidencias, frontend"
depende_de = ["EVI-01"]
propiedad = ["alembic/versions/20261031_evidencias_vigencia.py", "features/evidencias/domain/vigencia.py", "features/evidencias/services/vigencia_engine.py", "features/evidencias/services/paquete_inspeccion_engine.py", "features/evidencias/evidencias_service.py#EVI-02", "api/routers/evidencias_inspeccion.py", "tests/test_evidencias_vigencia.py", "frontend/src/lib/evidencias/vigencia.ts", "frontend/src/components/evidencias/PaqueteInspeccion.tsx", "frontend/src/components/modules/EvidenciasModule.tsx", "frontend/tests/evidencias/vigencia.spec.ts"]
arbitro = "pytest tests/test_evidencias_vigencia.py y tests/test_evidencias_persistencia.py contra una rama Neon de revisión con el almacén simulado + suite completa + Playwright de frontend/tests/evidencias + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤evidencias", "¤evidencias-vigencia"]
+++

# EVI-02 · Vigencia y visibilidad de las evidencias y paquete para inspección ordenado por requisito

**Origen.** Optimización O-3 y conflicto D-3 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`: `evidencias` es la única sala de custodia; las demás enlazan.

## Entrega
- **Vigencia:** fecha de vencimiento opcional por evidencia; una evidencia vencida no cuenta como vigente para ningún requisito. «Vencido» es atributo, no un estado que sustituya a «verificado eficaz» (D-3).
- **Visibilidad:** quién de la organización puede ver cada evidencia (por rol), aplicada en el servidor.
- **Paquete para inspección:** descarga ordenada por requisito con índice, huellas SHA-256 y fecha; solo evidencias vigentes y visibles para quien lo pide.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra una rama Neon de revisión hija de `revision`; nunca producción (`ep-late-hall`).

## Pruebas
- Una evidencia vencida no entra en el paquete; un rol sin visibilidad no la ve ni la descarga (403).
- Mutación documentada: ignorar la vigencia y comprobar que la prueba falla.

## Límites
- Espera a EVI-01 (pausada hasta configurar R2). La reapertura de controles por evidencia vencida es CAPA-03.
