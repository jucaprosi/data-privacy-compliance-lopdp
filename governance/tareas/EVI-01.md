+++
id = "EVI-01"
titulo = "Evidencias guardadas y comprobadas por el servidor: migración, registro en base, almacén en Cloud Storage y rutas nuevas detrás de una bandera"
ola = "backlog"
estado = "hecha"
sala = "evidencias"
depende_de = ["DEP-01", "DIAG-03", "DIAG-01", "SEC-05", "DIAG-11", "ADPA-05", "ADPA-07", "ADPA-11", "ORG-00", "ORG-08"]
propiedad = ["alembic/versions/20261029_evidencias_documentales.py", "features/evidencias/domain/models.py", "features/evidencias/domain/retencion.py", "features/evidencias/services/evidencias_engine.py", "app_core/storage/gcs.py", "api/routers/evidencias.py", "api/routers/diagnostico_resultados.py#EVI-01", "features/evidencias/evidencias_service.py#EVI-01", "features/evidencias/domain/errores.py#EVI-01", "app_core/pasillo/diagnostico.py#EVI-01", "tests/test_evidencias_persistencia.py", "tests/test_evidencias_subida_firmada.py", "tests/test_evidencias_retencion.py", "tests/test_evidencias_rutas_estables.py", "tests/snapshots/openapi_evidencias_antiguas.json"]
crea = ["alembic/versions/20261029_evidencias_documentales.py", "features/evidencias/domain/retencion.py", "app_core/storage/gcs.py", "tests/test_evidencias_persistencia.py", "tests/test_evidencias_subida_firmada.py", "tests/test_evidencias_retencion.py", "tests/test_evidencias_rutas_estables.py", "tests/snapshots/openapi_evidencias_antiguas.json"]
arbitro = "pytest tests/test_evidencias_persistencia.py tests/test_evidencias_subida_firmada.py tests/test_evidencias_retencion.py tests/test_evidencias_rutas_estables.py contra un PostgreSQL 16 local en contenedor (RLS con lopdp_app y almacén simulado), con tests/test_evidencia_http.py, tests/test_evidencias_contrato.py y tests/test_api_gateway.py sin tocarlos, + tests/test_sin_sql_interpolado.py + suite completa; mutaciones documentadas"
rastros = ["¤evidencias", "¤diagnostico", "¤rbac-tenant"]
+++

# EVI-01 · Evidencias guardadas y comprobadas por el servidor: migración, registro en base, almacén en Cloud Storage y rutas nuevas detrás de una bandera

Parte backend de la ficha original, partida el 2026-11-09 por el Arquitecto ADPA (una ficha, una sala) y aprobada por el CTO. La parte de pantalla es **EVI-01b**, que depende de esta. Lo que sigue manda sobre cualquier versión anterior del texto.

**Cambio 2026-11-07 (todo en Google Cloud, decisión del propietario):** el almacén de archivos es **Google Cloud Storage**, con URL firmada V4 para subir y bajar, en `app_core/storage/gcs.py`, y el bucket sale de `GCP_STORAGE_BUCKET`. Las reglas de SEC-05 (`motivo_de_rechazo`) se conservan. Nada en Vercel: las variables van por servicio en Cloud Run. R2 era del PMV congelado.

**Hallazgo (2026-10-27, DIAG-03).** Ningún documento de evidencia llega al servidor: la pantalla los registra solo en el navegador y la API de evidencias los guarda en la memoria del servidor (`InMemoryEvidenciasRepository`), que cada reinicio borra; acepta la huella que manda el cliente sin ver el archivo. DIAG-03 sella como E0 todo control cuyo documento el servidor no puede comprobar.

## Decisiones
- **Dónde se guarda:** el documento, en Cloud Storage; su registro, en la base.
- **La huella la calcula el servidor:** al confirmar la subida descarga el archivo y calcula su SHA-256; la del navegador solo se compara.
- **Quién hace qué** (decisión del propietario del 2026-11-05; invariantes 58 y 59): hasta el sello del diagnóstico real (DIAG-11) sube y vincula solo el `dpo`; sellado el real, el `dpo` ya no sube (403) y nadie vincula ni desvincula (409); sube el `responsable_area` o el `coordinador`; el `implementador` no sube nunca; consultan `dpo`, `coordinador`, `implementador` y `admin_organizacion`. Si el diagnóstico real está sellado se pregunta a la sala del diagnóstico por su pasillo (`app_core/pasillo/diagnostico.py#EVI-01`), nunca leyendo sus tablas.

## Condición del CTO: ninguna ruta que el frontend usa hoy cambia
Esta ficha **añade** rutas y **no cambia ni retira ninguna** de las que usa la pantalla actual. Las rutas nuevas van detrás de la bandera `EVIDENCIAS_SUBIDA_FIRMADA`, leída solo en el backend y **apagada por defecto**: apagada, responden 404 y el estado del servicio dice `subida_firmada: false`. EVI-01b la enciende. Por eso se despliega sin romper la pantalla.
- **No se retira nada aquí:** `InMemoryEvidenciasRepository` y las rutas que registran con la huella del cliente se quedan hasta que una ficha de contracción posterior (a escribir cuando EVI-01b esté hecha) las retire.
- **Prueba de que la pantalla actual no cambia:** `tests/test_evidencia_http.py`, `tests/test_evidencias_contrato.py` y `tests/test_api_gateway.py` pasan **sin tocarlos** (esta ficha no los posee), y `tests/test_evidencias_rutas_estables.py` compara el OpenAPI de las rutas antiguas con una copia guardada de `main` (`tests/snapshots/openapi_evidencias_antiguas.json`). Mutación: la bandera encendida por defecto la deja en rojo.

## Entrega
- **Migración** `20261029_evidencias_documentales` (id de 32 caracteres como máximo). **Se fusiona de una en una con FUSION_ALEMBIC:** su `down_revision` es la cabeza de `main` al empezar (hoy `20261122_merge_heads_sec13_bib106`; mídela con `ScriptDirectory.get_heads()`, no con un regex) y, si otra migración entra antes, la rehaces sobre la nueva.
  - Registro de documentos por organización: código, nombre, tipo, tamaño, huella calculada por el servidor, normativa, clave en el almacén, quién lo subió y cuándo; y la retención que se fijó.
  - Vínculos documento–control (pregunta 1 a 80): quién vinculó y cuándo.
  - RLS en las dos tablas (ENABLE y FORCE; USING y WITH CHECK por `tenant_id`).
  - Permisos de `lopdp_app`: registro de documentos solo SELECT e INSERT (un documento registrado no se edita ni se borra); vínculos pueden quitarse y cada alta o baja deja un evento en `audit_events`.
- **Subida en tres pasos** (rutas nuevas, detrás de la bandera): (1) pedir la subida: el servidor valida nombre, tipo y tamaño con las reglas de SEC-05 y la lista de formatos de la normativa, arma una clave con el prefijo de la organización y un identificador aleatorio y devuelve la URL firmada; (2) el navegador sube a esa URL; (3) confirmar: el servidor comprueba que la clave es de la organización, descarga el archivo, comprueba tamaño y firma del formato, calcula la huella y la compara con la del navegador (si no coinciden, 422 y nada registrado), y deduplica por organización, huella y normativa.
- **`app_core/storage/gcs.py`:** credenciales por defecto de la cuenta de servicio, **sin claves**. Firma con IAM Credentials `signBlob`. **Escritura única:** la URL de subida se firma con la cabecera `x-goog-if-generation-match: 0`, así que una segunda subida de la misma clave se rechaza. Fuera de la nube falla cerrado sin intentar conectar; en las pruebas se inyecta un almacén simulado.
- **Retención por objeto, de un solo lugar:** `retencion_dias(tenant_id)` en `features/evidencias/domain/retencion.py` devuelve **1825** mientras no exista BOV-01, que la sustituirá por la del paquete contratado (PRD §2.2: hasta 5, 7 o 10 años según el paquete; invariante del pool: 3 a 10 años). Ningún literal 1825 fuera de esa función. Tras subir, el servidor fija la retención del objeto en modo **desbloqueado**; **si no logra fijarla, no registra el documento** (falla cerrada).
- **DIAG-03:** los controles con documento comprobable (`_controles_con_documento` en `api/routers/diagnostico_resultados.py#EVI-01`) salen de la base: vínculos vigentes de documentos registrados por el servidor, detrás de la misma bandera.
- **Estado del servicio:** el estado de evidencias devuelve `subida_firmada` (verdadero solo con la bandera encendida).

## Pruebas (PostgreSQL 16 local en contenedor; el almacén se simula solo en las pruebas)
- Confirmar una subida registra la huella del servidor; si la del navegador es otra, 422 y nada registrado; una clave de otra organización da 403 o 404; una firma de formato que no corresponde se rechaza.
- Antes del sello del real, `admin_organizacion`, encargado designado, `implementador` y `coordinador` reciben 403 al subir y un rol distinto del `dpo` recibe 403 al vincular; después del sello, el `dpo` recibe 403 al subir y cualquier rol 409 al vincular o desvincular; el `responsable_area` sube.
- El registro sobrevive a una sesión nueva; `lopdp_app` no puede actualizar ni borrar un documento registrado (42501); RLS entre organizaciones con `SET LOCAL ROLE lopdp_app`; de extremo a extremo con DIAG-03 (control con documento vinculado y comprobado se sella con su nivel; sin documento, como E0).
- **Firma:** la URL de subida lleva `x-goog-if-generation-match: 0` firmada; el cliente falso rechaza la segunda subida de la misma clave. El cliente falso de IAM no debe pedir `delete`.
- **Retención:** ningún literal 1825 fuera de `retencion_dias`; si fijar la retención falla, el documento no se registra.
- **Mutaciones documentadas:** aceptar la huella del navegador sin descargar el archivo; quitar la comprobación del sello del real; quitar la cabecera `x-goog-if-generation-match`; omitir el paso de la retención; reintroducir el literal 1825; encender la bandera por defecto.
- Todo SQL es texto literal con parámetros enlazados, sin f-strings (corre `tests/test_sin_sql_interpolado.py` antes de pedir revisión).

## Escala de evidencia
La calidad de evidencia pasa de E0 a E3 en la escala 0 a 4 de `governance/ESCALA_MADUREZ.md`: `NivelCalidadEvidencia` en `features/evidencias/domain/models.py` y su valor por defecto en `api/routers/evidencias.py`. Al terminar, esas anotaciones salen de `consumidores_pendientes` con `python scripts/verificar_escala_madurez.py --escribir`. La etiqueta «Temprano explícito» del store es de EVI-01b.

## Límites
- No añade antivirus. No toca las evidencias de la Hoja de Ruta (`api/routers/roadmaps.py`). No migra las evidencias que hoy viven en los navegadores. No cambia el cálculo de indicadores (DIAG-02) ni la regla de E0 (DIAG-03).
- No toca `requirements.txt`: lo pone DEP-01. No pide fusión antes de que DEP-01 esté en `main`.

## Notas para el propietario
- **Bucket de evidencias:** `BRIEF_PROPIETARIO_BUCKET_EVIDENCIAS.md` (en `governance/operaciones`). No se usa `gs://evydentia`: hoy `deploy-gcp.yml` fija `GCP_STORAGE_BUCKET` al ID del proyecto, un bucket sin retención donde el backend tiene `objectAdmin`. El diseño usa el bucket de retención larga del PRD, con retención por objeto activada **sin bloquear** y un rol personalizado de escritura única para el backend. El código no espera al bucket.
- **Por probar en el bucket de pruebas:** fijar la retención de un objeto necesita `storage.objects.setRetention`, que solo trae `objectAdmin`; el brief da al backend un rol personalizado con `create`, `get` y `setRetention`. No se sabe si fijarla tras la subida exige también `update`: se prueba en el bucket de pruebas y, si lo exige, se ajustan rol y brief antes de producción.
- **Ubicación:** los documentos pueden contener datos personales de los clientes. Lo que se declara sobre la ubicación es el hecho, tomado de la configuración, sin base legal; el dictamen sobre transferencias sigue pendiente.
- **Migraciones:** la base del CI se migra en el propio job; producción después de fusionar.

## Hecho cuando
Su árbitro pasa, la suite completa pasa y los checks del PR están en verde. No modificó ningún archivo fuera de su propiedad.

## Ortogonalidad ADPA y Desacoplamiento Entre Salas (Doctrina ZERAG)
- **Sin imports laterales directos (`ImportsCruzados = ∅`):** esta tarea nunca importa `features.<otra_sala>.*`; toda consulta a otra sala va por el pasillo tipado `app_core/pasillo/<otra_sala>.py#EVI-01`.
- **Errores de negocio en la capa de dominio:** todo error lanza `ErrorNegocio` de `app_core.errors` y registra sus códigos en `features/<sala>/domain/errores.py#EVI-01` sin modificar `app_core/errors.py`.
