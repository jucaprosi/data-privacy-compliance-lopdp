# FOR-01 · Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación
`¤sdd` `¤evidencias` `¤rbac-tenant`

## 1. Datos

Migración `for01_formacion.py`, sin fecha (sustituye a `20261105_formacion`, que no existe en `main`); `down_revision` = la cabeza de `main` al implementar (FUSION_ALEMBIC). Tablas: `formacion_contenidos (id, tenant_id, titulo, tipo VARCHAR(8) CHECK (tipo IN ('pdf','video')), referencia TEXT, creado_por, creado_en)`, `formacion_preguntas (id, tenant_id, contenido_id, orden SMALLINT, enunciado, opciones JSONB CHECK (jsonb_array_length(opciones) BETWEEN 2 AND 6), correcta SMALLINT CHECK (correcta >= 0), UNIQUE (contenido_id, orden))`, `formacion_acciones (id, tenant_id, contenido_id, nombre, inicio DATE, fin DATE, nota_minima NUMERIC(4,1), creado_por)`, `formacion_participaciones (id, tenant_id, accion_id, persona_id, enviado_en, iniciado_en NULL, terminado_en NULL, nota NUMERIC(4,1) NULL, diploma_sha256 NULL, UNIQUE (accion_id, persona_id))`. RLS ENABLE y FORCE.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET/POST /formacion/contenidos`, `/formacion/acciones` | escriben `implementador`, `coordinador`, `admin_organizacion`; leen todos | campos | `200/201` |
| `GET /formacion/contenidos/{id}/preguntas` | los que escriben | — | `200 [{id, orden, enunciado, opciones, correcta}]` |
| `POST /formacion/contenidos/{id}/preguntas` | los que escriben | `{enunciado, opciones, correcta}` | `201`; `orden` lo asigna el servidor |
| `GET /formacion/participaciones/{id}/examen` | la persona participante | — | `200 {accion, nota_minima, inicio, fin, iniciado_en, terminado_en, preguntas: [{id, orden, enunciado, opciones}]}`, **sin `correcta`** |
| `POST /formacion/participaciones/{id}/iniciar` | la persona participante | — | `200 {iniciado_en}`; idempotente: si ya estaba iniciado devuelve el mismo `iniciado_en` |
| `POST /formacion/acciones/{id}/participantes` | los que escriben | `{persona_ids}` | `201` |
| `POST /formacion/participaciones/{id}/examen` | la persona participante (por `persona.user_id`) | `{respuestas: [int]}` | `200 {nota, aprobado, diploma_sha256?}` |
| `GET /formacion/cobertura` | lectura | — | `200 {formadas, obligadas, cobertura}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 409 | `EXAMEN_YA_RENDIDO` | segundo intento (`terminado_en` no nulo) |
| 409 | `EXAMEN_NO_INICIADO` | `POST …/examen` sin `iniciado_en` |
| 409 | `CONTENIDO_SIN_PREGUNTAS` | añadir participantes a una acción cuyo contenido no tiene preguntas |
| 422 | `RESPUESTAS_INCOMPLETAS` | `len(respuestas) ≠` número de preguntas, o un índice fuera de `opciones` |
| 409 | `PREGUNTAS_CONGELADAS` | crear preguntas en un contenido con alguna participación iniciada |
| 409 | `ACCION_FUERA_DE_FECHAS` | examen fuera de `[inicio, fin]` |

## 3. Reglas

- **R1 · Nota.** `nota = 100 × correctas / total`; `aprobado ⇔ nota ≥ nota_minima`.
- **R2 · Evidencia.** `aprobado ⇒` diploma PDF generado y custodiado en `evidencias` (tipo `capacitacion`, vinculado al control de capacitación del catálogo).
- **R3 · Cobertura.** `formadas / |personas activas con tratamientos asignados|`; personas sin tratamientos no cuentan en el denominador.
- **R4 · Un intento, consumido solo si el examen se registra.** El `POST …/examen` corre en una sola transacción: valida, califica, genera y custodia el diploma si aprueba y, al final, `UPDATE formacion_participaciones SET terminado_en = now(), nota = … WHERE id = :id AND terminado_en IS NULL RETURNING id`. Si cualquier paso falla (422, 409 de fechas o de no iniciado, error de la evidencia o del PDF, 5xx), la transacción se revierte y `terminado_en` sigue nulo: **el intento no se ha consumido**. Solo una respuesta `200` consume el intento. Dos envíos simultáneos: el `UPDATE … WHERE terminado_en IS NULL` deja pasar uno; el otro recibe 409 `EXAMEN_YA_RENDIDO`.
- **R5 · Preguntas sin respuesta correcta para la persona.** Ninguna ruta que lea la persona participante devuelve `correcta`; el esquema de respuesta no tiene el campo (`extra="forbid"` en el modelo de salida). Las preguntas salen en `orden`; `respuestas[i]` corresponde a la pregunta de `orden` i.
- **R6 · Banco congelado.** Una vez iniciada una participación del contenido, no se añaden preguntas (409 `PREGUNTAS_CONGELADAS`), para que la nota no cambie de denominador a mitad de una acción.
- **R7 · Iniciar.** `iniciado_en` lo fija el servidor, una sola vez, dentro de `[inicio, fin]` de la acción (si no, 409 `ACCION_FUERA_DE_FECHAS`); no consume el intento.
- **R-ADPA · Ortogonalidad ZERAG (`FOR-01`).** Toda invocación a otra sala se realiza vía `app_core/pasillo/<otra_sala>.py#FOR-01` (`ImportsCruzados = ∅`, ADR 0001) y los códigos de `ErrorNegocio` (`app_core.errors`) se registran en `features/<sala>/domain/errores.py#FOR-01`.

## 4. Interfaz

Operación › Formación: contenidos, acciones (crear, añadir participantes, ver avance por persona con semáforo) y cobertura; vista «Mi formación» para la persona con el examen.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una nota mínima de 70 y 7 de 10 correctas, **entonces** `aprobado = true` y existe el diploma como evidencia. Mutación: aprobar con 60 hace fallar la prueba. | `test_examen_aprueba_y_diploma` |
| **Dado** un segundo intento, **entonces** 409. | `test_examen_un_intento` |
| **Dado** un `POST …/examen` que falla (422 por respuestas incompletas, o un fallo forzado al custodiar el diploma), **entonces** `terminado_en` sigue nulo y un envío correcto posterior devuelve 200. Mutación: fijar `terminado_en` antes de custodiar el diploma hace fallar la prueba. | `test_examen_fallido_no_consume_intento` |
| **Dado** dos envíos simultáneos del examen, **entonces** uno 200 y otro 409 `EXAMEN_YA_RENDIDO`, y una sola nota. Mutación: quitar `AND terminado_en IS NULL`. | `test_examen_concurrente_un_solo_intento` |
| **Dado** la persona participante, **cuando** pide `GET …/examen`, **entonces** ninguna pregunta trae `correcta`; quien escribe sí la ve en `GET /formacion/contenidos/{id}/preguntas`; otra persona recibe 403. Mutación: incluir `correcta` en la salida. | `test_examen_sin_correcta` |
| **Dado** `POST …/iniciar` dos veces, **entonces** el mismo `iniciado_en`; fuera de fechas, 409. | `test_iniciar_idempotente` |
| **Dado** una participación iniciada, **cuando** se crea una pregunta en su contenido, **entonces** 409 `PREGUNTAS_CONGELADAS`. | `test_banco_congelado` |
| **Dado** 4 personas con tratamientos y 2 formadas, **entonces** `cobertura = 0.5`. | `test_cobertura` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_formacion` |
| **Dado** «Mi formación», **cuando** se rinde el examen, **entonces** muestra la nota y el enlace al diploma. | `frontend/tests/formacion/examen.spec.ts` |

## 6. Trazabilidad

- Pendiente de decisión del CTO (no lo fija esta especificación): contenido del PDF del diploma, si habrá reintento (hoy R4: uno) y el nombre del documento («Constancia» o «Diploma»).

- Ficha: `governance/tareas/FOR-01.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Formación»); catálogo §7.1 (sala `formacion`, por crear).
