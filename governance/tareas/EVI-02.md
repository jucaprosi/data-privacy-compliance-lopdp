+++
id = "EVI-02"
titulo = "Vigencia y visibilidad de las evidencias y paquete para inspección ordenado por requisito"
ola = "D"
estado = "pendiente"
sala = "evidencias, frontend"
depende_de = ["ADPA-05", "ADPA-07", "EVI-01", "EVI-01b"]
propiedad = ["alembic/versions/20261031_evidencias_vigencia.py", "features/evidencias/domain/vigencia.py", "features/evidencias/services/vigencia_engine.py", "features/evidencias/services/paquete_inspeccion_engine.py", "features/evidencias/evidencias_service.py#EVI-02", "api/routers/evidencias_inspeccion.py", "tests/test_evidencias_vigencia.py", "frontend/src/lib/evidencias/vigencia.ts", "frontend/src/components/evidencias/PaqueteInspeccion.tsx", "frontend/src/components/modules/EvidenciasModule.tsx#EVI-02", "frontend/tests/evidencias/vigencia.spec.ts", "features/evidencias/domain/errores.py#EVI-02"]
arbitro = "pytest tests/test_evidencias_vigencia.py y tests/test_evidencias_persistencia.py contra un PostgreSQL 16 local en contenedor con el almacén simulado + suite completa + Playwright de frontend/tests/evidencias + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤evidencias", "¤evidencias-vigencia"]
+++

# EVI-02 · Vigencia y visibilidad de las evidencias y paquete para inspección ordenado por requisito

**Cambio 2026-11-07 (todo en Google Cloud, decisión del propietario):** el almacén es GCS (EVI-01), no R2.

**Origen.** Optimización O-3 y conflicto D-3 de `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`: `evidencias` es la única sala de custodia; las demás enlazan.

## Entrega
- **Vigencia:** fecha de vencimiento opcional por evidencia; una evidencia vencida no cuenta como vigente para ningún requisito. «Vencido» es atributo, no un estado que sustituya a «verificado eficaz» (D-3).
- **Visibilidad:** quién de la organización puede ver cada evidencia (por rol), aplicada en el servidor.
- **Paquete para inspección:** descarga ordenada por requisito con índice, huellas SHA-256 y fecha; solo evidencias vigentes y visibles para quien lo pide.
- Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
- Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10: la que se fusione después se vuelve a encadenar). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.
- Pruebas contra un PostgreSQL 16 local en contenedor; nunca producción (`ep-late-hall`).

## Pruebas
- Una evidencia vencida no entra en el paquete; un rol sin visibilidad no la ve ni la descarga (403).
- Mutación documentada: ignorar la vigencia y comprobar que la prueba falla.

## Límites
- Espera a EVI-01 (que pasa a GCS). La reapertura de controles por evidencia vencida es CAPA-03.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#EVI-02` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#EVI-02` sin modificar `app_core/errors.py`.
