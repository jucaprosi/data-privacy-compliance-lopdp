# TER-01 · Hallazgos automáticos de terceros: encargado sin contrato vigente y transferencia internacional sin garantía
`¤sdd` `¤hallazgos` `¤evidencias`

## 1. Datos

Migración `20261106_terceros_garantias`: en `transferencias_terceros` columnas `rol VARCHAR(16) CHECK (IN ('encargado','destinatario','corresponsable','transferencia'))`, `pais VARCHAR(2)`, `contrato_sha256 NULL`, `contrato_vigente_hasta DATE NULL`, `garantia_tipo VARCHAR(24) NULL`, `garantia_sha256 NULL`, `criticidad VARCHAR(8)`, `proxima_revision DATE NULL`. Sin tabla nueva.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `PUT /terceros/{id}/garantias` | `implementador`, `coordinador` | campos anteriores | `200 Tercero` con `hallazgos: [...]` |
| `POST /terceros/evaluar` | `implementador` | — | `200 {"hallazgos_creados": int, "cerrados": int}` (también cron diario) |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 422 | `EVIDENCIA_NO_ENCONTRADA` | `contrato_sha256` o `garantia_sha256` inexistentes |

## 3. Reglas

- **R1 · Contrato.** `rol = 'encargado' ∧ (contrato_sha256 IS NULL ∨ contrato_vigente_hasta < hoy) ⇒ hallazgo(origen='tercero', origen_ref=f"{id}:contrato", severidad='alta')`.
- **R2 · Garantía.** `(rol = 'transferencia' ∨ pais ∉ {EC}) ∧ garantia_sha256 IS NULL ⇒ hallazgo(origen_ref=f"{id}:garantia", severidad='critica')`.
- **R3 · Cierre.** Cuando la condición deja de cumplirse, el hallazgo pasa a `cerrado`.
- **R4 · Idempotencia** por `origen_ref`.

## 4. Interfaz

Módulo Terceros: columnas contrato, garantía, criticidad, próxima revisión; distintivo rojo con enlace al hallazgo.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un encargado sin contrato, **cuando** se evalúa, **entonces** existe un hallazgo `alta`; **y** al registrar contrato vigente, se cierra. | `test_encargado_sin_contrato` |
| **Dado** una transferencia a país distinto de EC sin garantía, **entonces** hallazgo `critica`. Mutación: omitirlo hace fallar la prueba. | `test_transferencia_sin_garantia` |
| **Dado** dos evaluaciones seguidas, **entonces** no se duplican hallazgos. | `test_terceros_idempotente` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_terceros_garantias` |
| **Dado** el módulo, **entonces** el tercero sin contrato muestra el distintivo y el enlace. | `frontend/tests/terceros/garantias.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/TER-01.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Terceros con hallazgos automáticos»); RN-TER-01 y RN-TER-02 del documento maestro.
