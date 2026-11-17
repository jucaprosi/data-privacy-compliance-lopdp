# Brief de Lanzamiento: Tanda de Tareas Secuenciales (Relevos Ordenados)
`¤adpa` `¤arbitro` `¤roadmap` `¤frontend`

> **Objetivo:** Ejecutar de manera ordenada y secuencial 6 tareas que comparten puntos de integración globales (menús del frontend y pasillos comunes), evitando conflictos de merge y sobrescritura de componentes compartidos.
> **Motivo de Secuencialidad:** Estas tareas convergen en `frontend/src/components/layout/menus/index.ts`, `frontend/src/components/layout/pantallas/index.tsx` y compuertas comunes como `app_core/pasillo/organizacion.py` y `app_core/pasillo/evidencias.py`.

## Orden de Relevos Recomendado

| Paso | Tarea | Sala | Archivos Compartidos que Modifica | Relevo Siguiente |
| :--- | :--- | :--- | :--- | :--- |
| **1** | **`API-02`** | `pasillo_central, frontend` | `menus/index.ts`, `pantallas/index.tsx` | Entrega claves de integración al menú de ajustes |
| **2** | **`CAPA-04`** | `auditoria_capa, frontend` | `menus/index.ts`, `pantallas/index.tsx`, `pasillo/evidencias.py`, `pasillo/organizacion.py` | Incorpora la grilla de verificación de auditoría |
| **3** | **`FOR-01`** | `formacion, frontend` | `menus/index.ts`, `pantallas/index.tsx`, `pasillo/evidencias.py`, `pasillo/organizacion.py` | Añade el módulo de formación de personal |
| **4** | **`DER-02`** | `derechos_arco, frontend` | `menus/index.ts`, `pantallas/index.tsx`, `derechos_arco_service.py` | Despliega portal público de solicitudes |
| **5** | **`RAT-08`** | `rat, frontend` | `pasillo/organizacion.py`, `rat_service.py`, `RAT.tsx` | Ajusta referencias de áreas organizacionales |
| **6** | **`TER-02`** | `terceros, frontend` | `menus/index.ts`, `pantallas/index.tsx`, `terceros_service.py` | Añade portal y cuestionario de encargados |

## Protocolo de Ejecución de Relevo
1. **Una sola rama activa:** Solo un agente trabaja en la tarea del Paso `N`.
2. **Fusión previa obligatoria:** El Paso `N+1` NO inicia hasta que el PR del Paso `N` esté fusionado en `main`.
3. **Rebase inmediato:** Al iniciar el Paso `N+1`, se hace `git pull --ff-only origin main` para heredar las entradas de menú y pasillo ya consolidadas.
4. **Secciones `#ID` en pasillos:** En archivos como `app_core/pasillo/organizacion.py`, agregar las funciones respetando los límites de sección `#<ID>` sin alterar el código previo.

## Fichas de Tarea Detalladas

### API-02 · Claves de integración por organización con techo del paquete

- **Ficha:** [`governance/tareas/API-02.md`](../tareas/API-02.md)
- **Sala:** `pasillo_central, frontend`
- **Rama recomendada:** `tarea/juan-carlos/api-02`
- **Árbitro:** `pytest tests/test_api02_integraciones.py + suite completa + vigilantes`
- **Dependencias directas:** `SEC-13`, `OPS-07`, `BOV-01`
- **Escribe (lista exclusiva):**
  - `alembic/versions/api02_claves_integracion.py`
  - `app_core/integraciones/__init__.py`
  - `app_core/integraciones/claves.py`
  - `app_core/integraciones/techos.py`
  - `api/routers/integraciones_claves.py`
  - `tests/test_api02_integraciones.py`
  - `tests/matriz/API-02.py`
  - `frontend/src/components/integraciones/IntegracionesView.tsx`
  - `frontend/src/lib/integraciones/clavesIntegracion.ts`
  - `frontend/src/components/layout/menus/API-02.ts`
  - `frontend/src/components/layout/pantallas/API-02.tsx`
  - `frontend/src/components/layout/menus/index.ts#API-02`
  - `frontend/src/components/layout/pantallas/index.tsx#API-02`
  - `frontend/tests/integraciones/integraciones.spec.ts`
- **Resumen de Entrega:**
  - Tabla `claves_integracion` con RLS forzada (`tenant_id`, `nombre`, `prefijo`, `hash_sha256`, `alcances[]`, `creada_en`, `rotada_en`, `revocada_en`) y su migración; la clave en claro se muestra una sola vez al crearla.
  - Módulo `app_core/integraciones/claves.py` que autentica la cabecera `Authorization: Bearer evk_…`, resuelve la organización y comprueba el alcance (`rat:lectura`, `tareas:lectura`, `evidencias:lectura`), registrando cada uso en `audit_events`.
  - Módulo `app_core/integraciones/webhooks.py` que firma cada evento saliente con HMAC-SHA256 (`X-Evydentia-Firma`, `X-Evydentia-Marca-Tiempo`) y reintenta con backoff exponencial.
  - Vista `IntegracionesView.tsx` en el menú Organización para crear, rotar y revocar claves y suscribir webhooks, respetando los techos del paquete (§2.3 del PRD).

### CAPA-04 · Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción

- **Ficha:** [`governance/tareas/CAPA-04.md`](../tareas/CAPA-04.md)
- **Sala:** `auditoria_capa, frontend`
- **Rama recomendada:** `tarea/juan-carlos/capa-04`
- **Árbitro:** `pytest tests/test_auditoria_grilla.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/auditoria + tsc --noEmit + npm run build; prueba de mutación documentada`
- **Dependencias directas:** `CAPA-02`, `RM-21`, `EVI-02`, `DIAG-03`, `ADPA-05`, `ADPA-06`, `ADPA-07`, `ORG-22`, `CAPA-03`, `DIAG-07`, `DPO-03`, `RM-23`
- **Escribe (lista exclusiva):**
  - `alembic/versions/capa04_auditoria_grilla.py`
  - `features/auditoria_capa/domain/auditoria.py`
  - `features/auditoria_capa/services/grilla_engine.py`
  - `features/auditoria_capa/auditoria_capa_service.py#CAPA-04`
  - `api/routers/auditoria_grilla.py`
  - `tests/test_auditoria_grilla.py`
  - `tests/matriz/CAPA-04.py`
  - `frontend/src/components/layout/menus/CAPA-04.ts`
  - `frontend/src/components/layout/pantallas/CAPA-04.tsx`
  - `features/auditoria_capa/domain/errores.py#CAPA-04`
  - `app_core/pasillo/auditoria_capa.py#CAPA-04`
  - `frontend/src/components/layout/menus/index.ts#CAPA-04`
  - `frontend/src/components/layout/pantallas/index.tsx#CAPA-04`
  - `features/roadmap/services/cierre_hallazgos_engine.py#CAPA-04`
  - `app_core/pasillo/roadmap.py#CAPA-04`
  - `app_core/pasillo/diagnostico.py#CAPA-04`
  - `app_core/pasillo/evidencias.py#CAPA-04`
  - `app_core/pasillo/organizacion.py#CAPA-04`
  - `frontend/src/components/auditoria/AuditoriasView.tsx`
  - `frontend/src/components/auditoria/GrillaAuditoria.tsx`
  - `frontend/src/components/auditoria/ActasPorArea.tsx`
  - `frontend/src/components/auditoria/CierresPorVerificar.tsx`
  - `frontend/src/lib/auditoria/auditorias.ts`
  - `frontend/tests/auditoria/auditorias.spec.ts`
- **Resumen de Entrega:**
  - Auditoría con alcance (tratamientos, áreas, equipo auditor); grilla por control: lo declarado (último resultado sellado, DIAG-03), riesgo inicial, lo verificado, evidencia (referencia EVI-02), riesgo final, revisado por.
  - Conclusiones y **acta por área** (alcance, lo verificado, evidencia revisada) custodiada como evidencia; la palabra «certificado» no aparece.
  - Cada fila `verificado < declarado` produce un hallazgo `auditoria`. El auditor no audita controles que él ejecutó (SoD).
  - Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.

### FOR-01 · Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación

- **Ficha:** [`governance/tareas/FOR-01.md`](../tareas/FOR-01.md)
- **Sala:** `formacion, frontend`
- **Rama recomendada:** `tarea/juan-carlos/for-01`
- **Árbitro:** `pytest tests/test_formacion.py contra un PostgreSQL 16 local en contenedor (incluido RLS con lopdp_app) + suite completa + Playwright de frontend/tests/formacion + tsc --noEmit + npm run build; adpa_linter (sala nueva con compuerta formacion_service.py); prueba de mutación documentada`
- **Dependencias directas:** `ORG-17`, `EVI-02`, `FE-22`, `ADPA-06`, `ADPA-07`, `ADPA-09`, `EVI-04`
- **Escribe (lista exclusiva):**
  - `alembic/versions/for01_formacion.py`
  - `features/formacion/models.py`
  - `features/formacion/schemas.py`
  - `features/formacion/domain/formacion.py`
  - `features/formacion/services/__init__.py`
  - `features/formacion/services/contenidos_engine.py`
  - `features/formacion/services/acciones_engine.py`
  - `features/formacion/services/examen_engine.py`
  - `features/formacion/services/diploma_engine.py`
  - `features/formacion/services/cobertura_engine.py`
  - `features/formacion/formacion_service.py#FOR-01`
  - `features/formacion/domain/errores.py#FOR-01`
  - `app_core/pasillo/formacion.py#FOR-01`
  - `app_core/pasillo/evidencias.py#FOR-01`
  - `app_core/pasillo/dpo_cockpit.py#FOR-01`
  - `app_core/pasillo/organizacion.py#FOR-01`
  - `features/organizacion/organizacion_service.py#FOR-01`
  - `api/routers/formacion.py`
  - `tests/test_formacion.py`
  - `tests/matriz/FOR-01.py`
  - `frontend/src/lib/formacion/formacion.ts`
  - `frontend/src/components/formacion/ContenidosPanel.tsx`
  - `frontend/src/components/formacion/AccionesPanel.tsx`
  - `frontend/src/components/formacion/CoberturaTarjeta.tsx`
  - `frontend/src/components/formacion/MiFormacion.tsx`
  - `frontend/src/components/layout/menus/FOR-01.ts`
  - `frontend/src/components/layout/pantallas/FOR-01.tsx`
  - `frontend/src/components/layout/menus/index.ts#FOR-01`
  - `frontend/src/components/layout/pantallas/index.tsx#FOR-01`
  - `frontend/tests/formacion/examen.spec.ts`
  - `frontend/tests/formacion/gestion.spec.ts`
- **Resumen de Entrega:**
  - Sala nueva `features/formacion/` con compuerta `formacion_service.py` (la primera tarea de una sala crea la sala, ADPA).
  - Contenidos (PDF o enlace a video) y banco de preguntas; acción formativa con personas (ORG-17), fechas, examen, nota mínima; seguimiento por persona (enviado, iniciado, terminado, nota) y cobertura = personas formadas / personas que tratan datos.
  - El diploma y el registro de notas se custodian como evidencia del control de capacitación (EVI-02, control P-correspondiente del catálogo).
  - Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.

### DER-02 · Portal público de solicitudes de titulares por organización, con enlace de seguimiento

- **Ficha:** [`governance/tareas/DER-02.md`](../tareas/DER-02.md)
- **Sala:** `derechos_arco, frontend`
- **Rama recomendada:** `tarea/juan-carlos/der-02`
- **Árbitro:** `pytest tests/test_derechos_portal.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/derechos/portal.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; cumple el diseño de SEC-12`
- **Dependencias directas:** `DER-01`, `DER-06b`, `SEC-12`, `ADPA-05`, `DER-03`
- **Escribe (lista exclusiva):**
  - `alembic/versions/20261105_derechos_portal.py`
  - `features/derechos_arco/services/portal_engine.py`
  - `features/derechos_arco/derechos_arco_service.py#DER-02`
  - `api/routers/publico_derechos.py`
  - `tests/test_derechos_portal.py`
  - `frontend/src/app/solicitud/**`
  - `frontend/tests/derechos/portal.spec.ts`
  - `features/derechos_arco/domain/errores.py#DER-02`
- **Resumen de Entrega:**
  - Página pública `/solicitud/<organizacion>` con la marca de la organización: tipo de derecho, datos de contacto mínimos y descripción; crea la solicitud y devuelve un código de seguimiento.
  - Seguimiento `/solicitud/seguir/<codigo>`: solo estado y fechas, nunca el contenido de la respuesta ni datos de otros titulares.
  - Límites de abuso según SEC-12 (tasa por IP, tamaño de adjuntos, sin enumeración de organizaciones).
  - Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.

### RAT-08 · Área responsable del tratamiento como referencia al área de la organización

- **Ficha:** [`governance/tareas/RAT-08.md`](../tareas/RAT-08.md)
- **Sala:** `rat, frontend`
- **Rama recomendada:** `tarea/juan-carlos/rat-08`
- **Árbitro:** `pytest tests/test_rat08_area_id.py contra PostgreSQL 16 local + alembic heads con una sola cabeza + tsc --noEmit; mutaciones m1 a m3`
- **Dependencias directas:** `RAT-01`, `RAT-05`, `RAT-02`, `RAT-06`, `API-01`, `RAT-07`, `CORE-01`
- **Escribe (lista exclusiva):**
  - `alembic/versions/rat08_area_id.py`
  - `tests/test_rat08_area_id.py`
  - `frontend/src/types/rat_area.ts`
  - `features/rat/domain/models.py`
  - `features/rat/services/rat_engine.py`
  - `features/rat/services/exportacion_engine.py`
  - `api/routers/rat.py`
  - `frontend/src/components/modules/RatModule.tsx`
  - `features/rat/rat_service.py#RAT-08`
  - `app_core/pasillo/organizacion.py#RAT-08`
- **Resumen de Entrega:**
  - `rat_actividades.area_id` como FK a las áreas de organización (por su compuerta), con migración de datos que empareja por nombre (en minúsculas y sin espacios en los extremos) y deja `NULL` lo que no case; `area_responsable` se conserva como texto mientras haya filas sin emparejar.
  - Migración sin fecha, con FUSION_ALEMBIC.
  - Cuando exista, FOR-01 o una ficha hija puede afinar el denominador de la cobertura por área.
  ## Mutaciones

### TER-02 · Cuestionario de garantías del encargado por portal externo, con revisión e informe

- **Ficha:** [`governance/tareas/TER-02.md`](../tareas/TER-02.md)
- **Sala:** `terceros, frontend`
- **Rama recomendada:** `tarea/juan-carlos/ter-02`
- **Árbitro:** `pytest tests/test_terceros_cuestionario.py contra un PostgreSQL 16 local en contenedor + suite completa + Playwright de frontend/tests/terceros/cuestionario.spec.ts + tsc --noEmit + npm run build; prueba de mutación documentada; cumple el diseño de SEC-12`
- **Dependencias directas:** `TER-01`, `SEC-12`, `FE-23`, `ADPA-05`, `ADPA-06`, `ADPA-08`
- **Escribe (lista exclusiva):**
  - `alembic/versions/20261107_terceros_cuestionario.py`
  - `features/terceros/domain/cuestionario.py`
  - `features/terceros/services/cuestionario_engine.py`
  - `features/terceros/terceros_service.py#TER-02`
  - `features/terceros/domain/errores.py#TER-02`
  - `api/routers/publico_terceros.py`
  - `api/routers/terceros_cuestionario.py`
  - `tests/test_terceros_cuestionario.py`
  - `tests/matriz/TER-02.py`
  - `frontend/src/app/proveedor/[token`
- **Resumen de Entrega:**
  - Envío del cuestionario desde la ficha del tercero por enlace con caducidad; el proveedor responde por portal externo con evidencias; revisión por el responsable (conforme, pedir corrección, rechazar); informe y próxima fecha de revisión.
  - Límites de abuso de SEC-12; el portal no muestra datos de la organización más allá del nombre.
  - Lo que necesite de otra sala, por su compuerta (`<sala>_service.py`); errores de negocio con `ErrorNegocio` y códigos del catálogo de `app_core/errors.py`; identidad y organización salen del token, nunca del cuerpo.
  - Migración con `down_revision` igual a la cabeza de `main` al empezar; compruébalo con `alembic heads` al empezar y antes de empujar (regla 10). Tablas por organización con RLS (ENABLE y FORCE, USING y WITH CHECK por `tenant_id`) y permisos mínimos de `lopdp_app`.

