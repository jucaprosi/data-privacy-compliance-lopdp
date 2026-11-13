+++
id = "EVI-02"
titulo = "Vigencia y visibilidad de las evidencias y paquete para inspección ordenado por requisito"
ola = "D"
estado = "hecha"
sala = "evidencias, frontend"
depende_de = ["ADPA-05", "ADPA-07", "EVI-01", "EVI-01b"]
propiedad = ["alembic/versions/20261031_evidencias_vigencia.py", "features/evidencias/domain/vigencia.py", "features/evidencias/services/vigencia_engine.py", "features/evidencias/services/paquete_inspeccion_engine.py", "features/evidencias/evidencias_service.py#EVI-02", "api/routers/evidencias_inspeccion.py", "tests/test_evidencias_vigencia.py", "frontend/src/lib/evidencias/vigencia.ts", "frontend/src/components/evidencias/PaqueteInspeccion.tsx", "frontend/src/components/modules/EvidenciasModule.tsx#EVI-02", "frontend/tests/evidencias/vigencia-activa.spec.ts", "features/evidencias/domain/errores.py#EVI-02", "api/routers/diagnostico_resultados.py#EVI-01"]
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

**Ajuste 2026-11-12 (Tech Lead):** el spec de Playwright pasa a llamarse `frontend/tests/evidencias/vigencia-activa.spec.ts`: la convención de `playwright.config.ts` (CI-16) manda a «desarrollo» los `*-activa.spec.ts`, y la Bóveda de Evidencias solo existe con `window.__LOPDP_EVIDENCIA_PRUEBAS__`, ausente del build de producción. Así EVI-02 no necesita tocar `playwright.config.ts` (que BIB-110 asume en paralelo).
- **El sello futuro exige un documento vigente (Arquitecto, 2026-11-12; propiedad: solo la sección `api/routers/diagnostico_resultados.py#EVI-01`, sin tomar el archivo entero):** la llamada que cambia está en `_controles_documentados`, dentro de la sección «# === EVI-01 ===». En la rama con la bandera encendida se llama a `evidencias_service.controles_con_documento_vigente(session, tenant_id, hoy_negocio())` (`app_core/zona_negocio.hoy_negocio`, el día de Guayaquil y no UTC) en lugar de `controles_con_documento_registrado`. La rama con la bandera apagada (`_controles_con_documento`, la regla anterior) no mira la vigencia: es transitoria y se deja así. **Sellos ya hechos: nada** (la cadena de huellas los hace inmutables); solo afecta al sello futuro. **Criterio de producto decidido por el CTO (2026-11-12):** un tenant con documentos vencidos deja de poder sellar (la evidencia que pierde vigencia reabre su control, §CAPA-02/03); el documento respalda hasta el último día de su vigencia, **ese día incluido** (`vence_en >= hoy`, fecha de negocio de Guayaquil), y una mutación a `>` da rojo; el 4xx al sellar **nombra el documento vencido**, no solo dice que falta evidencia; el aviso previo al sello es una mejora de UX/UI y no bloquea. DIAG-07 y ORG-23 poseen el archivo entero: DIAG-07 depende de EVI-02 (ORG-23 ya depende de DIAG-07).
- **Pruebas en `tests/test_evidencias_vigencia.py`, cada una con su mutación:** un documento con `vence_en` ayer no respalda el sello (volver a `controles_con_documento_registrado` → rojo); un documento con `vence_en` hoy y otro sin `vence_en` sí respaldan (cambiar `>=` por `>` → rojo); con el reloj inyectado a las 23:30 de Guayaquil (04:30 UTC del día siguiente) un documento que vence ese día local respalda (usar `date.today()` o la fecha UTC → rojo); un sello ya hecho con un documento que luego vence conserva su huella y su resultado.
- **El 4xx del sello nombra el documento vencido:** prueba en `tests/test_evidencias_vigencia.py` de que la respuesta incluye el nombre o identificador del documento vencido (mutación: devolver el mensaje genérico de evidencia faltante → rojo).
