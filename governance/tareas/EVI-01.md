+++
id = "EVI-01"
titulo = "Las evidencias se guardan en el servidor: el documento en el almacén de archivos, su registro en la base y la huella calculada por el servidor"
ola = "D"
estado = "pendiente"
sala = "evidencias, frontend"
depende_de = ["DIAG-03", "DIAG-01", "FE-14", "FE-16", "SEC-05", "CAPA-01", "DIAG-02", "DPO-01", "MTGE-01", "RAT-01", "ORG-00", "ORG-08", "TEST-01", "DIAG-08", "DIAG-09", "ADPA-05", "ADPA-07", "DIAG-11", "FE-26"]
propiedad = ["alembic/versions/20261029_evidencias_documentales.py", "features/evidencias/**", "app_core/storage/r2.py", "api/routers/evidencias.py", "api/routers/diagnostico_resultados.py#EVI-01", "tests/test_evidencias_persistencia.py", "tests/test_evidencias_contrato.py", "tests/test_evidencia_http.py", "tests/test_api_gateway.py", "frontend/src/lib/evidencias/**", "frontend/src/components/evidencias/**", "frontend/src/components/modules/EvidenciasModule.tsx#EVI-01", "frontend/src/components/config/CargaEvidencias.tsx", "frontend/src/components/DiagnosticCanvas.tsx#EVI-01", "frontend/src/store/useAuditStore.ts", "frontend/tests/evidencias/**", "features/evidencias/evidencias_service.py#EVI-01", "features/evidencias/domain/errores.py#EVI-01", "app_core/pasillo/diagnostico.py#EVI-01"]
arbitro = "pytest tests/test_evidencias_persistencia.py contra una rama Neon de revisión (incluido RLS con lopdp_app y el almacén de archivos simulado) + suite completa + vigilantes + Playwright de frontend/tests/evidencias + suite Playwright completa + tsc --noEmit + npm run build; prueba de mutación documentada"
rastros = ["¤evidencias", "¤diagnostico", "¤rbac-tenant"]
+++

# EVI-01 · Evidencias guardadas y comprobadas por el servidor

**Hallazgo (2026-10-27, revisión del coordinador durante DIAG-03).** Ningún documento de evidencia llega al servidor:
- La pantalla registra cada documento solo en el navegador (`frontend/src/lib/evidencias/registro.ts` y el store `useAuditStore.ts`). Calcula ahí su huella SHA-256 y nunca lo envía.
- La API de evidencias (`api/routers/evidencias.py`) guarda los registros en la memoria del servidor (`InMemoryEvidenciasRepository`): cada reinicio o despliegue los borra.
  - Acepta la huella que manda el cliente sin ver el archivo.
  - Solo comprueba la organización, no el rol.
  - La pantalla no la usa.
- **Consecuencia:** DIAG-03 sella como E0 todo control cuyo documento el servidor no puede comprobar. Hoy son todos, así que la madurez sellada queda en 20 % o menos.

**Decisiones del coordinador** (diseño propio; cada una en un solo sitio para poder cambiarla):
- **Dónde se guarda:** el documento, en el almacén de archivos que ya usa la Hoja de Ruta (Cloudflare R2, `app_core/storage/r2.py`, SEC-05); su registro, en la base.
- **La huella la calcula el servidor:** al confirmar una subida, descarga el archivo y calcula su SHA-256. La huella del navegador solo se compara con la del servidor; nunca la sustituye.
- **Quién hace qué** (decisión del propietario del 2026-11-05; `PRD_EVYDENTIA_REVENTA_NUBE.md` §3 y Módulo 1, invariantes 58 y 59 de `INVARIANTS_EVYDENTIA_REVENTA_NUBE.md`):
  - **hasta que se sella el diagnóstico real** (`DIAG-11`), es decir, durante el de prueba y el real, sube documentos y los **vincula o desvincula** con sus controles **solo el `dpo`**. El `admin_organizacion` y las personas designadas para contestar (DIAG-07) le entregan los documentos y no los suben: 403;
  - **sellado el diagnóstico real**, el `dpo` ya no sube (403) y nadie vincula ni desvincula documentos de un diagnóstico sellado (409). La evidencia nueva la suben el `responsable_area`, o el `coordinador` si no hay responsables, como en la Hoja de Ruta; el `dpo` solo la valida o la rechaza;
  - el `implementador` no sube en ningún momento: revisa;
  - consultan el `dpo`, el `coordinador`, el `implementador` y el `admin_organizacion`.
  - Si el diagnóstico real está sellado se pregunta a la sala del diagnóstico por su pasillo (`app_core/pasillo/diagnostico.py#EVI-01`, con la consulta que publica `DIAG-11`), nunca leyendo sus tablas.

## Entrega
- **Migración** `20261029_evidencias_documentales` (id de 32 caracteres como máximo), con `down_revision` igual a la cabeza de `main` al empezar. Compruébalo con `alembic heads` al empezar y otra vez antes de empujar.
  - Registro de documentos por organización: código, nombre, tipo, tamaño, huella calculada por el servidor, normativa, clave en el almacén, quién lo subió y cuándo.
  - Vínculos documento–control (pregunta 1 a 80): quién vinculó y cuándo.
  - RLS en las dos tablas (ENABLE y FORCE; USING y WITH CHECK por `tenant_id`).
  - Permisos de `lopdp_app`:
    - registro de documentos: **solo SELECT e INSERT**; un documento registrado no se edita ni se borra;
    - vínculos: pueden quitarse, y cada alta o baja deja un evento en `audit_events`.
- **Subida en tres pasos** (rutas en `api/routers/evidencias.py`):
  1. **Pedir la subida.** El servidor valida nombre, tipo y tamaño con las reglas de SEC-05 (`r2.motivo_de_rechazo`) y con la lista de formatos de la normativa. Arma una clave con el prefijo de la organización y un identificador aleatorio, y devuelve la URL prefirmada.
  2. **El navegador sube el archivo** a esa URL.
  3. **Confirmar.** El servidor:
     - comprueba que la clave es de la organización de quien confirma;
     - descarga el archivo y comprueba tamaño y firma del formato (los primeros bytes);
     - calcula la huella y la compara con la del navegador: si no coinciden, responde 422 y no registra nada;
     - deduplica por organización, huella y normativa.
- **Se retiran:**
  - `InMemoryEvidenciasRepository`;
  - toda ruta que registre una evidencia con la huella que manda el cliente.

  Ninguna prueba ni ruta queda dependiendo de la memoria del servidor.
- **DIAG-03:** los controles con documento comprobable (`_controles_con_documento` en `api/routers/diagnostico_resultados.py`) salen de la base: vínculos vigentes de documentos registrados por el servidor.
- **Pantalla:**
  - `registro.ts` sube por el flujo de tres pasos. El archivo se sigue recordando en la sesión para el preanálisis.
  - El store carga las evidencias de la organización desde el servidor al hidratarse y al iniciar sesión, como las respuestas (DIAG-01). Vincular y desvincular pasan por el servidor.
  - Hasta el sello del real, solo el `dpo` ve el botón de subir y los controles para vincular (`CargaEvidencias.tsx`). Después, el `dpo` no ve el botón de subir: ve las evidencias nuevas para validarlas o rechazarlas.
  - `DiagnosticCanvas.tsx`: se retira el aviso de DIAG-03 que dice que los documentos «se guardan solo en este navegador». El resumen previo al sellado cuenta como respaldados solo los controles con documento registrado en el servidor.
  - `EvidenciasModule.tsx` muestra, para cada documento, si está registrado y comprobado en el servidor.
  - Un error de subida (almacén no configurado, tipo rechazado, huella distinta) se muestra tal cual. Nunca se registra el documento solo en el navegador como si se hubiera guardado.
  - Colores, solo con las variables del tema.
- **Pruebas:**
  - El almacén de archivos se simula en memoria, solo dentro de las pruebas. La base es real: rama Neon de revisión.
  - Casos que deben probarse:
    - confirmar una subida registra la huella que calcula el servidor; si la del navegador es otra, 422 y nada registrado;
    - una clave de otra organización da 403 o 404;
    - una firma de formato que no corresponde se rechaza;
    - antes del sello del real, el `admin_organizacion`, un encargado designado, el `implementador` y el `coordinador` reciben 403 al subir, y un rol distinto del `dpo` recibe 403 al vincular;
    - después del sello del real, el `dpo` recibe 403 al subir y cualquier rol 409 al vincular o desvincular; el `responsable_area` sube;
    - el registro sobrevive a una sesión nueva;
    - `lopdp_app` no puede actualizar ni borrar un documento registrado (42501);
    - RLS entre organizaciones con `SET LOCAL ROLE lopdp_app`;
    - **de extremo a extremo con DIAG-03:** un control con documento vinculado y comprobado se sella con su nivel declarado; sin documento, como E0.
    - Playwright: el DPO sube un documento y lo vincula; otra pestaña lo ve tras cargar del servidor; un error de subida se muestra y no deja el documento como guardado.
  - Las pruebas que hoy usan la memoria (`test_evidencias_contrato.py`, `test_evidencia_http.py`, `test_api_gateway.py`) pasan al flujo nuevo, sin perder lo que verifican.
  - Las pruebas deben correr también en la rama Neon `test` del CI; la única base prohibida es producción (`ep-late-hall`).
- **Prueba de mutación documentada:**
  - aceptar la huella del navegador sin descargar el archivo: la prueba de huella distinta debe fallar;
  - quitar la comprobación del sello del real: la prueba del 403 del `dpo` después de ese sello debe fallar.

## Escala de evidencia

La calidad de evidencia pasa de E0 a E3 a la escala 0 a 4 de `governance/ESCALA_MADUREZ.md`: `NivelCalidadEvidencia` en `features/evidencias/domain/models.py`, su valor por defecto en `api/routers/evidencias.py` y la etiqueta «Temprano explícito» de `frontend/src/store/useAuditStore.ts`. Al terminar, esas anotaciones salen de `consumidores_pendientes` con `python scripts/verificar_escala_madurez.py --escribir`.

## Límites
- No añade antivirus: sigue pendiente la decisión del propietario sobre el boceto de SEC-05.
- No toca las evidencias de la Hoja de Ruta (`api/routers/roadmaps.py`). Ver la nota sobre ellas abajo.
- No migra las evidencias que hoy viven en los navegadores: quedan locales hasta que el DPO las vuelva a subir.
- No cambia el cálculo de indicadores (DIAG-02) ni la regla de E0 (DIAG-03).

## Notas para el propietario
- **Antes de fusionar:**
  - comprobar que el backend de Vercel tiene las variables `R2_*` (`governance/operaciones/VARIABLES_VERCEL.md`);
  - comprobar que el bucket admite subidas (PUT) desde el dominio del frontend (CORS).
- **Ubicación del bucket:** los documentos pueden contener datos personales de los clientes y la plataforma los guarda como encargada del tratamiento. Conviene confirmar en qué país queda el bucket. Si está fuera del Ecuador, hay que revisar las reglas de transferencia internacional de la LOPDP y reflejarlo en el contrato de encargo.
- **BIB-110** (de Aleczandra) también posee `useAuditStore.ts`. Por eso depende de EVI-01: se hace después y parte del store ya cargando las evidencias del servidor. BIB-101 cedió ese archivo a BIB-110 y ya no depende de EVI-01 (PMV de Biblioteca, PR #199).
- **Hallazgo relacionado, fuera de esta tarea:** la Hoja de Ruta registra una evidencia con la clave, el tipo, el tamaño y la huella que manda el navegador. No comprueba que la clave sea de la organización ni que el archivo exista. Hoy no hay descarga, así que no expone nada, pero merece la misma comprobación que esta tarea.
- **Migraciones:** la rama Neon `test` antes del CI del PR; producción después de fusionar.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.


## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)

- **Prohibición de imports laterales directos (`ImportsCruzados = ∅`)**: Esta tarea **nunca** debe importar `features.<otra_sala>.*` directamente. Toda consulta o invocación hacia otra sala se realiza exclusivamente a través del pasillo tipado `app_core/pasillo/<otra_sala>.py#EVI-01` (ADR 0001).
- **Errores de negocio en la capa de dominio**: Todo error de negocio lanza `ErrorNegocio` importado desde `app_core.errors` (nunca desde `api.errores`) y registra sus códigos en `features/<sala>/domain/errores.py#EVI-01` sin modificar `app_core/errors.py`.

Nota (2026-11-05): depende de FE-26, que puso la evidencia física tras `EVIDENCIA_FISICA` / `NEXT_PUBLIC_EVIDENCIA_FISICA` y es dueña de la sección `tests/test_evidencia_http.py#FE-26`. EVI-01 es quien la enciende en EVYDENTIA.
