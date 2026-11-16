# NORM-01 · Sala Inteligencia Normativa: ingesta y custodia de documentos de la SPDP
`¤sdd` `¤inteligencia-normativa` `¤vigilancia-spdp` `¤adpa`

## 1. Datos

Tablas globales (corpus público, sin `tenant_id`; `lopdp_app` con permiso de solo lectura):

- `normativa_resoluciones`: `id` (UUID PK), `numero_resolucion` (p. ej. `SPDP-SPD-2026-0005-R`), `anio_emision`, `titulo`, `organo_emisor`, `materia`, `fecha_publicacion`, `url_fuente`, `seccion_fuente` (`resoluciones`, `marco_normativo`, `consultas_absueltas`), `archivo_sha256`, `ruta_original`, `tamano_bytes`, `estado` (`pendiente_revision`, `homologada`, `observada`, `vigente`, `reformada`, `derogada`), `detectada_en`, `revisada_por`, `revisada_en`. Único: (`numero_resolucion`, `anio_emision`).
- `normativa_versiones`: `id`, `resolucion_id` (FK), `archivo_sha256`, `ruta_original`, `detectada_en`, `motivo` (`republicacion`, `fe_de_erratas`, `cambio_en_fuente`). Inmutable: sin UPDATE ni DELETE.
- `normativa_monitoreo_logs`: `id`, `inicio`, `fin`, `origen` (`programado`, `manual`), `documentos_vistos`, `nuevos`, `versiones_nuevas`, `errores`, `estado` (`ok`, `parcial`, `fallida`), `codigos_error` (JSONB NOT NULL DEFAULT '[]': lista de códigos de error de la corrida, sin datos personales; `errores` sigue siendo el recuento).

**Escritura y despliegue.** `lopdp_app` solo lee estas tablas. Escribe el monitoreo con el rol `lopdp_normativa` (sin login, creado por la migración): hace `SET LOCAL ROLE lopdp_normativa` en cada transacción. El inicio de sesión del Cloud Run Job debe ser miembro de `lopdp_normativa` (concesión del brief de despliegue del propietario).

## 2. API

Sin router propio en esta tarea (las pantallas y el disparo manual son de NORM-02). La compuerta expone:

- `ejecutar_monitoreo(origen) -> ResumenCorrida`
- `listar_resoluciones(filtros) -> list[ResolucionResumen]`
- `obtener_resolucion(id) -> ResolucionDetalle`

## 3. Reglas

- **R1 · Original intacto (`INV_NORMATIVA_INTEGRITY_SHA256`).** El hash se calcula mientras se descarga y el original se guarda tal cual antes de cualquier extracción.
- **R2 · Solo PDF.** Un archivo sin cabecera `%PDF-` se rechaza con `NORMATIVA_ARCHIVO_NO_PDF` y queda en el registro de la corrida.
- **R3 · Deduplicación en tres capas (`INV_NORMATIVA_DEDUPLICATION_TRIPLE_GATE`).**
  - Mismo número y año con mismo hash: no hace nada.
  - Mismo número y año con otro hash: crea una versión inmutable.
  - Número nuevo: crea la resolución en `pendiente_revision`.
- **R4 · Cortesía con la fuente (`INV_NORMATIVA_SCHEDULED_MONITORING_QUOTA`).**
  - Peticiones en serie, con al menos 2 s entre una y otra.
  - Hasta 3 reintentos con espera exponencial.
  - Si recibe 403, 429 o una página de verificación, detiene la corrida y la marca `fallida`.
- **R5 · Nada vigente sin persona (`INV_NORMATIVA_HUMAN_LEGAL_VALIDATION`).** Esta tarea nunca asigna `vigente`, `reformada` ni `derogada`.

## 4. Interfaz

Sin pantalla; la provee NORM-02.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un servidor simulado que publica un PDF nuevo, **cuando** corre el monitoreo, **entonces** se crea la resolución en `pendiente_revision` con su SHA-256 y el original guardado byte a byte. | `test_resolucion_nueva_con_hash_y_original` |
| **Dado** un enlace que devuelve HTML con extensión `.pdf`, **cuando** se procesa, **entonces** se rechaza con `NORMATIVA_ARCHIVO_NO_PDF` y la corrida lo registra. | `test_rechaza_no_pdf` |
| **Dado** una resolución ya registrada y la fuente publica el mismo número con otro contenido, **cuando** corre el monitoreo, **entonces** se crea una versión y el original anterior sigue intacto. | `test_misma_resolucion_otro_hash_crea_version` |
| **Dado** la fuente responde 429, **cuando** corre el monitoreo, **entonces** la corrida termina `fallida` sin más peticiones a la fuente. | `test_detiene_ante_429` |
| **Dado** la sesión con el rol `lopdp_app`, **cuando** intenta insertar en `normativa_resoluciones`, **entonces** la base lo rechaza. | `test_lopdp_app_solo_lectura` |

## 6. Trazabilidad

- `PRD.md` Módulo 6.1 (`RF-01..05`) e invariantes 39 a 42 de `INVARIANTS.md`.
