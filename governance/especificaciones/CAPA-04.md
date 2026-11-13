# CAPA-04 · Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción
`¤sdd` `¤auditoria-capa` `¤hallazgos`

Decisiones del CTO incorporadas el 2026-11-13 (dos cierres, ruta del acta, escala única de niveles). La especificación manda sobre la ficha.

## 1. Datos

Migración `capa04_auditoria_grilla.py`, sin fecha; `down_revision` = la cabeza de `main` al implementar (FUSION_ALEMBIC). Sustituye a `20261106_auditoria_grilla`, que no existe en `main`.

- `auditorias (id, tenant_id, nombre, alcance JSONB, equipo JSONB, estado VARCHAR(10) CHECK (IN ('abierta','cerrada')), creado_por, creado_en, cerrada_en)`. Pasa a `cerrada` cuando todas las áreas del alcance tienen acta firmada.
- `auditoria_filas (id, tenant_id, auditoria_id, area_id, control_ref, declarado SMALLINT, riesgo_inicial SMALLINT, verificado SMALLINT NULL CHECK (verificado BETWEEN 1 AND 5), evidencia_sha256 NULL, riesgo_final SMALLINT NULL, revisado_por NULL, hallazgo_id NULL, UNIQUE (auditoria_id, control_ref))`.
- `auditoria_actas (id, tenant_id, auditoria_id, area_id, evidencia_id, acta_sha256, firmada_por, firmada_en, UNIQUE (auditoria_id, area_id))`. Sin columna de texto: el contenido vive en la evidencia (R4).
- `auditoria_verificaciones_cierre (id, tenant_id, hallazgo_id, accion_ref, verificado_por, resultado CHECK (IN ('conforme','no_conforme')), motivo TEXT NOT NULL CHECK (length(trim(motivo)) >= 10), registrado_en)`. Es una tabla de eventos que solo se agregan.
- RLS `ENABLE` y `FORCE` con `USING` y `WITH CHECK` por `tenant_id` en las cuatro tablas.
- `lopdp_app`:
  - `SELECT, INSERT` en `auditorias`, `auditoria_actas` y `auditoria_verificaciones_cierre`;
  - `UPDATE` solo en `auditoria_filas` y en `auditorias.estado` y `cerrada_en`;
  - sin `DELETE`.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /auditoria-capa/auditorias` | `implementador`, `coordinador` | `{nombre, alcance, equipo}` | `201` con filas precargadas desde el último resultado sellado |
| `PUT /auditoria-capa/auditorias/{id}/filas/{control_ref}` | `auditor` miembro del equipo | `{verificado, evidencia_sha256?, riesgo_final}` | `200` |
| `POST /auditoria-capa/auditorias/{id}/areas/{area_id}/acta` | `auditor` miembro del equipo | — | `201 {area_id, acta_sha256}` (levanta y firma el acta del área) |
| `GET /auditoria-capa/auditorias/{id}/areas/{area_id}/acta` | `auditor`, `dpo`, `admin_organizacion` | — | `200 {area_id, acta_sha256, contenido}`; el contenido se lee por la compuerta de evidencias |
| `POST /auditoria-capa/hallazgos/{hallazgo_id}/verificar-cierre` | `auditor` | `{resultado, motivo}` | `201`; con `conforme`, el hallazgo pasa a `resuelto` |

El cierre de la acción del plan lo hace el `implementador` en la ruta propia del plan de acción (sala de hallazgos y planes), no en esta sala. Esta sala solo verifica ese cierre.

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 403 | `AUDITOR_EJECUTOR` | el revisor ejecutó tareas de ese control (responsable de tareas con ese `control_ref`) o cerró la acción que verifica |
| 409 | `AUDITORIA_INCOMPLETA` | levantar el acta de un área con filas sin `verificado` |
| 409 | `ACTA_YA_FIRMADA` | segunda acta para la misma área |
| 409 | `ACCION_NO_CERRADA` | verificar el cierre de un hallazgo cuya acción no está cerrada por el implementador |
| 404 | `DIAG_SIN_RESULTADO` | crear sin resultado sellado |
| 404 | `ACTA_NO_ENCONTRADA` | `GET` del acta de un área sin acta firmada |

## 3. Reglas

- **R0 · Escala única.** `declarado` y `verificado` usan la escala SMARTCIDI del diagnóstico (`NIVELES_ASIGNADOS`, 1 a 5, DIAG-08). Esta sala lee la escala y sus etiquetas por la compuerta de diagnóstico (`app_core/pasillo/diagnostico.py#CAPA-04`) y no copia etiquetas ni topes.
  - **Sin nivel 0.** En el assessment de SMARTCIDI, el nivel 1 ya significa «No existe o se gestiona informalmente». La falta de evidencia es otra escala, `NIVELES_EVIDENCIA` (0 «Verbal: sin evidencia»), y se registra con `evidencia_sha256` nulo, no con un nivel de madurez.
  - Por eso no se propone ninguna etiqueta «Sin evidencia verificable».
- **R1 · Precarga.** `declarado = nivel_sellado` del último resultado por control. `riesgo_inicial = (5 − declarado) × criticidad`, la misma fórmula del diagnóstico, con el tope 5 leído de la compuerta (`NIVEL_ASIGNADO_MAX`).
- **R2 · Hallazgo.** Si `verificado < declarado`, se llama a `registrar_hallazgo` con:
  - `origen='auditoria'`;
  - `origen_ref=f"{auditoria_id}:{control_ref}"`;
  - `severidad`: `'critica'` si `riesgo_final ≥ 15`, `'alta'` si `≥ 9`, y si no `'media'`.
- **R3 · SoD (ORG-22).**
  - `revisado_por ∉ {owner de tareas con ese control_ref}`.
  - Quien verifica el cierre de un hallazgo no es quien cerró su acción ni quien ejecutó el control.
  - Solo el `auditor` levanta y firma actas, y nunca cierra acciones del plan.
- **R4 · Acta por área (primer cierre).**
  - El auditor levanta y firma un acta por área del alcance cuando todas las filas del área tienen `verificado`. Con eso cierra la auditoría de esa área.
  - El texto es fijo: alcance, filas del área, evidencias, firmante y fecha. Está prohibida la palabra «certificado».
  - Se custodia como evidencia de tipo `acta_auditoria` por la compuerta de evidencias (EVI-02). La sala no tiene almacenamiento propio: guarda `evidencia_id` y `acta_sha256`.
  - El `GET` devuelve el contenido leído por esa compuerta y la huella.
- **R5 · Hallazgo resuelto (segundo cierre).**
  - El implementador cierra la acción del plan de cada hallazgo.
  - El hallazgo queda `resuelto` solo cuando el auditor registra una verificación `conforme` de ese cierre.
  - Con `no_conforme`, la acción se reabre en el plan y el hallazgo sigue abierto.
- **R-ADPA · Ortogonalidad ZERAG (`CAPA-04`).**
  - Toda invocación a otra sala se hace por `app_core/pasillo/<otra_sala>.py#CAPA-04`: diagnóstico (escala y último resultado), evidencias (custodia y lectura del acta), hallazgos (registrar, estado de la acción y marcar resuelto) y organización (roles). Así `ImportsCruzados = ∅` (ADR 0001).
  - Los códigos de `ErrorNegocio` (`app_core.errors`) se registran en `features/<sala>/domain/errores.py#CAPA-04`.

## 4. Interfaz

Riesgos y auditoría › Auditorías:
- la lista de auditorías;
- la grilla, editable por el equipo auditor, con evidencia por fila y la etiqueta del nivel leída de la escala del diagnóstico;
- por área, el botón «Levantar y firmar acta», que se habilita con todas las filas del área verificadas, y la descarga del acta firmada;
- en los hallazgos de la auditoría, «Verificar cierre» para el auditor cuando la acción está cerrada.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una fila con declarado 3 y verificado 1, **entonces** se crea un hallazgo `auditoria`. | `test_grilla_genera_hallazgo` |
| **Dado** un revisor que es responsable de una tarea de P12, **cuando** verifica P12, **entonces** 403 `AUDITOR_EJECUTOR`. Mutación: permitirlo hace fallar la prueba. | `test_auditor_no_ejecutor` |
| **Dado** un área con todas sus filas verificadas, **cuando** el auditor levanta el acta, **entonces** queda una sola acta firmada del área, custodiada como evidencia `acta_auditoria`, y no contiene «certificado». Un segundo intento da 409 `ACTA_YA_FIRMADA`. Mutación: guardar el texto en la sala en vez de en evidencias hace fallar la prueba. | `test_acta_por_area_firmada` |
| **Dado** un área con una fila sin verificar, **cuando** se levanta el acta, **entonces** 409 `AUDITORIA_INCOMPLETA`. | `test_acta_exige_area_completa` |
| **Dado** un acta firmada, **cuando** la piden el `auditor`, el `dpo` o el `admin_organizacion`, **entonces** 200 con `{area_id, acta_sha256, contenido}`, y la huella coincide con el contenido. El `implementador` recibe 403. | `test_get_acta_roles_y_huella` |
| **Dado** un hallazgo con su acción cerrada por el implementador, **cuando** el auditor verifica `conforme`, **entonces** el hallazgo queda `resuelto`. Sin verificación sigue abierto. Mutación: resolver al cerrar la acción hace fallar la prueba. | `test_hallazgo_resuelto_solo_con_verificacion` |
| **Dado** que quien verifica el cierre es quien cerró la acción, **entonces** 403 `AUDITOR_EJECUTOR`. | `test_verificador_no_cierra` |
| **Dado** la escala del diagnóstico, **cuando** se precarga la grilla, **entonces** `declarado` y `verificado` admiten solo 1 a 5 y las etiquetas son las de `NIVELES_ASIGNADOS` por la compuerta. Mutación: aceptar `verificado = 0` hace fallar la prueba. | `test_escala_unica_diagnostico` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas en las cuatro tablas. | `test_rls_auditorias` |
| **Dado** un área de la grilla, **cuando** se completa su última fila, **entonces** «Levantar y firmar acta» se habilita para el auditor. | `frontend/tests/auditoria/grilla.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/CAPA-04.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 3 («Grilla de verificación», «acta de auditoría por área»); Doctrina 1; D-4.
- Rol auditor y SoD: ORG-22. Custodia del acta: EVI-02. Escala: DIAG-08 (`features/diagnostico/domain/models.py`, `NIVELES_ASIGNADOS`, `NIVELES_EVIDENCIA`).
