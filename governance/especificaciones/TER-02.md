# TER-02 · Cuestionario de garantías del encargado por portal externo, con revisión e informe
`¤sdd` `¤seguridad` `¤evidencias`

## 1. Datos

Migración `20261107_terceros_cuestionario`: `terceros_cuestionarios (id, tenant_id, tercero_id, token_hash UNIQUE, caduca_en, estado VARCHAR(12) CHECK (IN ('enviado','respondido','conforme','correccion','rechazado')), respuestas JSONB NULL, evidencias JSONB NULL, revisado_por NULL, informe_sha256 NULL, proxima_revision DATE NULL, creado_por, creado_en)`. RLS ENABLE y FORCE; función `SECURITY DEFINER` para resolver el token.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /terceros/{id}/cuestionarios` | `implementador`, `coordinador` | `{dias_vigencia}` | `201 {url}` |
| `GET/POST /publico/proveedor/{token}` | público | respuestas y subida (≤ 10 MB por archivo) | `200` |
| `POST /terceros/cuestionarios/{id}/revision` | `implementador`, `coordinador` | `{decision, comentario, proxima_revision?}` | `200 {informe_sha256}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 410 | `CUESTIONARIO_CADUCADO` | token caducado o ya respondido |
| 404 | — | token desconocido (idéntico al caducado) |
| 409 | `CUESTIONARIO_NO_RESPONDIDO` | revisar sin respuestas |

## 3. Reglas

- **R1 · Token** de un uso, 32 bytes, hash guardado.
- **R2 · Revisión.** `conforme ⇒` informe generado y custodiado, `proxima_revision` obligatoria, y cierre del hallazgo `garantia` del tercero si existía; `correccion ⇒` nuevo enlace; `rechazado ⇒` hallazgo `tercero` severidad `alta`.
- **R3 · Portal mínimo.** Muestra solo el nombre de la organización y las preguntas.

## 4. Interfaz

Ficha del tercero: botón «Enviar cuestionario», estado y revisión con tres decisiones; página pública `/proveedor/<token>` con el asistente de FE-23.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un token usado, **cuando** se abre, **entonces** 410; **y** con un token ajeno, 404 idéntico. Mutación: devolver otro cuestionario hace fallar la prueba. | `test_cuestionario_token` |
| **Dado** una revisión `conforme` de un tercero con hallazgo de garantía, **entonces** el hallazgo se cierra y hay informe. | `test_revision_conforme` |
| **Dado** `rechazado`, **entonces** hay un hallazgo `alta`. | `test_revision_rechazo` |
| **Dado** la página pública, **cuando** el proveedor responde, **entonces** el estado interno pasa a «respondido». | `frontend/tests/terceros/cuestionario.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/TER-02.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («cuestionario de garantías por portal externo… fase posterior»); SEC-12.
