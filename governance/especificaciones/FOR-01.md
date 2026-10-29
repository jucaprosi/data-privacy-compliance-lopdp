# FOR-01 · Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación
`¤sdd` `¤evidencias` `¤rbac-tenant`

## 1. Datos

Migración `20261105_formacion`: `formacion_contenidos (id, tenant_id, titulo, tipo VARCHAR(8) CHECK (tipo IN ('pdf','video')), referencia TEXT, creado_por, creado_en)`, `formacion_preguntas (id, tenant_id, contenido_id, enunciado, opciones JSONB, correcta SMALLINT)`, `formacion_acciones (id, tenant_id, contenido_id, nombre, inicio DATE, fin DATE, nota_minima NUMERIC(4,1), creado_por)`, `formacion_participaciones (id, tenant_id, accion_id, persona_id, enviado_en, iniciado_en NULL, terminado_en NULL, nota NUMERIC(4,1) NULL, diploma_sha256 NULL, UNIQUE (accion_id, persona_id))`. RLS ENABLE y FORCE.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET/POST /formacion/contenidos`, `/formacion/acciones` | escriben `implementador`, `coordinador`, `admin_organizacion`; leen todos | campos | `200/201` |
| `POST /formacion/acciones/{id}/participantes` | los que escriben | `{persona_ids}` | `201` |
| `POST /formacion/participaciones/{id}/examen` | la persona participante (por `persona.user_id`) | `{respuestas: [int]}` | `200 {nota, aprobado, diploma_sha256?}` |
| `GET /formacion/cobertura` | lectura | — | `200 {formadas, obligadas, cobertura}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 409 | `EXAMEN_YA_RENDIDO` | segundo intento |
| 409 | `ACCION_FUERA_DE_FECHAS` | examen fuera de `[inicio, fin]` |

## 3. Reglas

- **R1 · Nota.** `nota = 100 × correctas / total`; `aprobado ⇔ nota ≥ nota_minima`.
- **R2 · Evidencia.** `aprobado ⇒` diploma PDF generado y custodiado en `evidencias` (tipo `capacitacion`, vinculado al control de capacitación del catálogo).
- **R3 · Cobertura.** `formadas / |personas activas con tratamientos asignados|`; personas sin tratamientos no cuentan en el denominador.
- **R4 · Un intento** por participación.

## 4. Interfaz

Operación › Formación: contenidos, acciones (crear, añadir participantes, ver avance por persona con semáforo) y cobertura; vista «Mi formación» para la persona con el examen.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una nota mínima de 70 y 7 de 10 correctas, **entonces** `aprobado = true` y existe el diploma como evidencia. Mutación: aprobar con 60 hace fallar la prueba. | `test_examen_aprueba_y_diploma` |
| **Dado** un segundo intento, **entonces** 409. | `test_examen_un_intento` |
| **Dado** 4 personas con tratamientos y 2 formadas, **entonces** `cobertura = 0.5`. | `test_cobertura` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_formacion` |
| **Dado** «Mi formación», **cuando** se rinde el examen, **entonces** muestra la nota y el enlace al diploma. | `frontend/tests/formacion/examen.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/FOR-01.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Formación»); catálogo §7.1 (sala `formacion`, por crear).
