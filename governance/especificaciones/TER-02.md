# TER-02 · Cuestionario de garantías del encargado por portal externo, con revisión e informe
`¤sdd` `¤seguridad` `¤evidencias`

## 1. Datos

### 1.1 Tabla

Migración `alembic/versions/20261107_terceros_cuestionario.py` (su `down_revision` es la cabeza de `main` al crear la rama, `FUSION_ALEMBIC.md`).

`terceros_cuestionarios`:

| Columna | Tipo |
| :--- | :--- |
| `id` | `String` PK |
| `tenant_id` | `String NOT NULL`, FK a `tenants` |
| `tercero_id` | `String NOT NULL`, FK al tercero de TER-01 |
| `version_cuestionario` | `String NOT NULL` (`"TER-02.1"`) |
| `token_hash` | `String UNIQUE NOT NULL` (SHA-256 del token) |
| `caduca_en` | `timestamptz NOT NULL` |
| `estado` | `VARCHAR(12) CHECK (estado IN ('enviado','respondido','conforme','correccion','rechazado'))` |
| `respuestas` | `JSONB NULL` |
| `evidencias` | `JSONB NULL` (lista de `{pregunta_id, sha256, nombre, tamano}`) |
| `revisado_por`, `revisado_en`, `comentario_revision` | `NULL` |
| `informe_sha256` | `NULL` |
| `proxima_revision` | `DATE NULL` |
| `creado_por`, `creado_en` | `NOT NULL` |

RLS con ENABLE y FORCE, y `USING` y `WITH CHECK` por `tenant_id`. `lopdp_app` tiene `SELECT`, `INSERT` y `UPDATE`; no tiene `DELETE`. El portal resuelve el token con una función `SECURITY DEFINER`, `terceros_cuestionario_por_token(token_hash)`, que devuelve solo `id`, `tenant_id`, el nombre de la organización, `version_cuestionario`, `caduca_en` y `estado`.

### 1.2 Cuestionario de garantías del encargado (versión `TER-02.1`)

Las preguntas viven en `features/terceros/domain/cuestionario.py` como una tupla inmutable. El servidor valida las respuestas contra ella y el portal la recibe de la API. Tipos de campo: `si_no`, `si_no_evidencia` (sí o no; con «sí», un archivo obligatorio), `texto` y `fecha`.

Estado de la cita:
- **V**: verificada. Epígrafe y texto inicial leídos en el R.O. 459, Quinto Suplemento (`governance/artefactos/CITAS_LEGALES_VERIFICADAS.md`, DIAG-16), o con el literal citado en LEG-03 (`governance/apoyo/CITAS_LEGALES_VERIFICADAS.md`).
- **E**: epígrafe verificado; el alcance de la pregunta sale del resumen editorial del corpus (`features/regulacion_rag/domain/corpus.py`), no de un literal leído.
- **P**: pendiente de verificar contra el texto oficial.

| Id | Pregunta | Tipo | Obligatoria | Cita | Estado |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `G01` | ¿Existe un contrato vigente con el responsable que regula el tratamiento de los datos personales? | `si_no_evidencia` | sí | LOPDP art. 34; art. 47 num. 10 | V (art. 47 num. 10); E (art. 34) |
| `G02` | ¿Trata los datos solo según las instrucciones del responsable y para la finalidad del contrato? | `si_no` | sí | LOPDP art. 34 | E |
| `G03` | ¿Todo el personal con acceso a los datos firmó un compromiso de confidencialidad? | `si_no_evidencia` | sí | LOPDP art. 47 num. 10 | V |
| `G04` | ¿Tiene documentadas las medidas técnicas y organizativas de seguridad que aplica a estos datos? | `si_no_evidencia` | sí | LOPDP art. 37; art. 10 lit. j); art. 47 num. 2 | V |
| `G05` | Fecha de la última evaluación de la eficacia de esas medidas | `fecha` | sí | LOPDP art. 47 num. 3; art. 37 | V |
| `G06` | ¿Subcontrata a otros encargados (subencargados) para este tratamiento? | `si_no` | sí | Reglamento General art. 45 | P |
| `G07` | Subencargados y autorización del responsable (nombre, servicio y país de cada uno) | `texto` + evidencia | si `G06` = sí | Reglamento General art. 45 | P |
| `G08` | ¿Tiene un procedimiento para trasladar al responsable las solicitudes de los titulares y ayudarle a atenderlas? | `si_no_evidencia` | sí | LOPDP art. 47 num. 11 | V (epígrafe y texto inicial); alcance P |
| `G09` | ¿Avisa al responsable de toda vulneración de seguridad dentro del término de dos días desde que la conoce? | `si_no_evidencia` | sí | LOPDP art. 43 | V (literal en LEG-03) |
| `G10` | Contacto para avisos de vulneración (nombre, correo y teléfono) | `texto` | sí | LOPDP art. 43 | V |
| `G11` | ¿Devuelve o destruye los datos al terminar el servicio y lo certifica por escrito? | `si_no_evidencia` | sí | LOPDP art. 34 | E |
| `G12` | ¿Permite auditorías o inspecciones del responsable o de un auditor acreditado? | `si_no` | sí | LOPDP art. 47 num. 14 | V (num. 14); su aplicación al encargado: E (art. 47, párrafo final) |
| `G13` | Fecha de la última auditoría externa de protección de datos o de seguridad | `fecha` | no | LOPDP art. 47 num. 14 | V |
| `G14` | ¿Trata, almacena o accede a los datos desde fuera del Ecuador? | `si_no` | sí | LOPDP arts. 55, 56 y 57 | V (56 y 57); epígrafe del 55 en LEG-03 |
| `G15` | Países y garantía de cada transferencia (país con nivel adecuado o garantías adecuadas) | `texto` + evidencia | si `G14` = sí | LOPDP arts. 56 y 57 | V |

La pantalla muestra la pregunta y su cita como «LOPDP, art. 34». No muestra el estado de la cita.

**Lo que queda por verificar (P):** el Reglamento General (Decreto Ejecutivo 904) no se ha leído en su texto oficial. Por eso la cita de `G06` y `G07` está pendiente, y también el alcance de `G08` (si el art. 47 num. 11, u otro artículo, obliga al encargado a asistir en los derechos). Hasta verificarlas, el informe de revisión marca esas preguntas como «base normativa en verificación» (R7).

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /api/v1/terceros/{id}/cuestionarios` | `implementador`, `coordinador` | `{dias_vigencia: int}`, de 1 a 30, por defecto 7 | `201 {id, url, caduca_en}` |
| `GET /api/v1/terceros/{id}/cuestionarios` | `implementador`, `coordinador`, `dpo`, `auditor` | — | `200 [{id, estado, caduca_en, proxima_revision}]` |
| `GET /api/v1/publico/proveedor/{token}` | público | — | `200 {organizacion, preguntas, caduca_en}` |
| `POST /api/v1/publico/proveedor/{token}` | público | `multipart`: `respuestas` (JSON) y archivos (≤ 10 MB cada uno, lista blanca de formatos de evidencias) | `200 {estado: "respondido"}` |
| `POST /api/v1/terceros/cuestionarios/{id}/revision` | `implementador`, `coordinador` | `{decision: conforme \| correccion \| rechazado, comentario, proxima_revision?}` | `200 {estado, informe_sha256?, url_nueva?}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| `CODIGO_ENLACE_NO_VALIDO` | — (cuerpo idéntico en todos los casos) | token desconocido, caducado, ya respondido o revocado |
| 422 | `DIAS_VIGENCIA_FUERA_DE_RANGO` | `dias_vigencia` fuera de 1 a 30 |
| 422 | `RESPUESTA_INCOMPLETA` | falta una obligatoria, una evidencia de `si_no_evidencia` con «sí», o el tipo no casa |
| 409 | `CUESTIONARIO_NO_RESPONDIDO` | revisar un cuestionario en estado `enviado` |
| 422 | `PROXIMA_REVISION_OBLIGATORIA` | `conforme` sin `proxima_revision` |

`CODIGO_ENLACE_NO_VALIDO` es una constante única en `features/terceros/domain/cuestionario.py`. Vale 404 (diseño de SEC-12) hasta que el propietario decida entre 404 y 410. Cambiarla no toca la pantalla ni las pruebas, que leen la constante.

Las páginas del portal llevan `X-Robots-Tag: noindex`, `Referrer-Policy: no-referrer` y `Cache-Control: no-store` (SEC-12). También tienen los límites de abuso de SEC-12.

## 3. Reglas

- **R1 · Token.** Aleatorio de 32 bytes (`secrets.token_urlsafe(32)`). Se guarda solo su SHA-256 y viaja en la ruta. Es de un uso: tras responder, el estado pasa a `respondido` y el token deja de resolver.
- **R2 · Identidad del token.** La organización y el cuestionario salen del token, nunca del cuerpo. Con un token solo se ve su propio cuestionario.
- **R3 · Respuestas validadas.** El servidor valida cada respuesta contra §1.2: tipo, obligatoriedad, condicionales `G07` y `G15`, y evidencia cuando `si_no_evidencia` vale «sí». Las evidencias se guardan con la custodia de evidencias existente (SHA-256 y almacén de Cloud Storage) por el pasillo de esa sala.
- **R4 · Revisión.**
  - `conforme`: genera el informe, lo custodia, guarda `informe_sha256`, exige `proxima_revision` y la copia al tercero. Si el tercero tenía el hallazgo `garantia` de TER-01, lo cierra.
  - `correccion`: crea un cuestionario nuevo con enlace nuevo y la vigencia por defecto, y devuelve `url_nueva`.
  - `rechazado`: abre un hallazgo `tercero` de severidad `alta`.
- **R5 · Portal mínimo.** El portal muestra solo el nombre de la organización, las preguntas y la fecha de caducidad. Para cualquier token no válido muestra una sola pantalla: «Este enlace no está disponible. Pida uno nuevo a quien se lo envió.».
- **R6 · Versión.** Cada cuestionario guarda `version_cuestionario`. Una versión nueva de §1.2 lleva identificador nuevo y no cambia los cuestionarios ya enviados.
- **R7 · Citas en el informe.** El informe lista cada pregunta con su respuesta y su cita. Las preguntas con estado P llevan la nota «base normativa en verificación».
- **R-ADPA · Ortogonalidad ZERAG (`TER-02`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py#TER-02`, con `ImportsCruzados = ∅` (ADR 0001): evidencias, roadmap para los hallazgos y dpo_cockpit. Los códigos de error son `ErrorNegocio` (`app_core.errors`) y se registran en `features/terceros/domain/errores.py#TER-02`.

## 4. Interfaz

**Punto de montaje.** Medido en `origin/main` 3554924e:
- `frontend/src/components/modules/TercerosModule.tsx` (358 líneas) no tiene secciones ADPA;
- sus dueñas son TER-01, FE-07 y FE-17, las tres hechas, y ninguna ficha abierta lo posee;
- `frontend/src/components/terceros/` no existe.

Por eso TER-02 recibe `TercerosModule.tsx` entero, por cesión explícita de TER-01. Su diff en ese archivo se limita a dos bloques marcados `=== TER-02 ===`:
1. la importación de `EnvioCuestionario`;
2. el montaje `<EnvioCuestionario tercero={t} permisos={permisos} />` dentro de cada tercero, junto al botón «Registrar garantías».

El resto de la interfaz va en archivos nuevos de TER-02:
- `frontend/src/components/terceros/EnvioCuestionario.tsx`: botón «Enviar cuestionario» con la vigencia (1 a 30 días, 7 por defecto), enlace para copiar, estado del último cuestionario y acceso a la revisión.
- `frontend/src/components/terceros/RevisionCuestionario.tsx`: respuestas, evidencias y las tres decisiones; `proxima_revision` es obligatoria con «conforme».
- `frontend/src/app/proveedor/[token]/page.tsx`: el portal, con el asistente de FE-23, una pregunta por paso y `noindex` en los metadatos.
- `frontend/src/lib/terceros/cuestionario.ts`: cliente de la API con `fetchAutenticado`; el portal usa `fetch` sin credenciales.

Solo variables del tema (`--ui-*`, `badge-render-*`), textos sin jerga técnica y sin tokens de gobernanza. UX/UI revisa esta sección antes de lanzar la ficha.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un token desconocido, caducado, respondido o revocado, **cuando** se abre, **entonces** la respuesta es `CODIGO_ENLACE_NO_VALIDO` con el mismo cuerpo en los cuatro casos. Mutación: devolver otro cuestionario o un cuerpo distinto hace fallar la prueba. | `tests/test_terceros_cuestionario.py::test_cuestionario_token` |
| **Dado** el token de un cuestionario, **entonces** solo se ven sus preguntas y el nombre de su organización. | `tests/test_terceros_cuestionario.py::test_portal_minimo` |
| **Dado** `dias_vigencia` 0 o 31, **entonces** 422 `DIAS_VIGENCIA_FUERA_DE_RANGO`; **y** sin valor, caduca a los 7 días. | `tests/test_terceros_cuestionario.py::test_vigencia` |
| **Dado** respuestas sin una obligatoria, sin la evidencia de un «sí» de `si_no_evidencia`, o con `G06` = sí y sin `G07`, **entonces** 422 `RESPUESTA_INCOMPLETA`. | `tests/test_terceros_cuestionario.py::test_respuestas_validadas` |
| **Dado** una revisión `conforme` de un tercero con hallazgo de garantía, **entonces** el hallazgo se cierra, hay informe con `informe_sha256` y el tercero recibe `proxima_revision`. | `tests/test_terceros_cuestionario.py::test_revision_conforme` |
| **Dado** `rechazado`, **entonces** hay un hallazgo `tercero` de severidad `alta`; **y** `correccion` devuelve un enlace nuevo. | `tests/test_terceros_cuestionario.py::test_revision_rechazo` |
| **Dado** otra organización, **entonces** RLS no le deja ver ni revisar el cuestionario. | `tests/test_terceros_cuestionario.py::test_rls` y `tests/matriz/TER-02.py` |
| **Dado** el portal, **entonces** sus respuestas llevan `X-Robots-Tag: noindex`, `Referrer-Policy: no-referrer` y `Cache-Control: no-store`. | `tests/test_terceros_cuestionario.py::test_cabeceras_portal` |
| **Dado** la página pública, **cuando** el proveedor responde, **entonces** el estado interno pasa a «respondido». | `frontend/tests/terceros/cuestionario.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/TER-02.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2, cuestionario de garantías por portal externo; SEC-12 (`governance/apoyo/DISENO_PORTALES_EXTERNOS.md`); FE-23 (asistente).
- Citas: `governance/artefactos/CITAS_LEGALES_VERIFICADAS.md` (DIAG-16), `governance/apoyo/CITAS_LEGALES_VERIFICADAS.md` (LEG-03) y `features/regulacion_rag/domain/corpus.py`.
- Decisión pendiente del propietario: el valor de `CODIGO_ENLACE_NO_VALIDO`, 404 o 410.
