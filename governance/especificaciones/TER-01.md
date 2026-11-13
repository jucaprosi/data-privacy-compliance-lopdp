# TER-01 · Hallazgos automáticos de terceros: encargado sin contrato vigente y transferencia internacional sin garantía
`¤sdd` `¤hallazgos` `¤evidencias`

## 1. Datos

Enmienda del Arquitecto ADPA (2026-11-13), contra el esquema real de `main`.

Migración `ter01_terceros_garantias.py`, sin fecha. En `transferencias_terceros` añade siete columnas, todas `NULL` y sin rellenar filas: `pais VARCHAR(2)`, `contrato_sha256`, `contrato_vigente_hasta DATE`, `garantia_tipo VARCHAR(24)`, `garantia_sha256`, `criticidad VARCHAR(8)` y `proxima_revision DATE`. Sin tabla nueva.

- **`rol` no se crea ni se migra.** La columna ya existe con los valores `ENCARGADO`, `SUBENCARGADO` y `DESTINATARIO`, y otras partes del sistema la usan. Esta ficha no cambia sus valores ni añade otros.
- `pais` es el código ISO de dos letras. `pais_destino`, texto libre, sigue existiendo y no se usa en las reglas; la duplicación queda para una ficha de limpieza.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /terceros/garantias` | `implementador`, `coordinador`, `dpo`, `admin_organizacion`, `auditor` | — | `200 {terceros: [Tercero con hallazgos], permisos: {gestionar, evaluar}}` |
| `PUT /terceros/{id}/garantias` | `implementador`, `coordinador` | campos anteriores | `200 Tercero` con `hallazgos: [...]` |
| `POST /terceros/evaluar` | `implementador` | — | `200 {"hallazgos_creados": int, "cerrados": int}` (también cron diario) |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 404 | (tercero no encontrado) | `PUT` sobre un tercero que no es de la organización |
| 422 | `EVIDENCIA_NO_ENCONTRADA` | `contrato_sha256` o `garantia_sha256` inexistentes |

## 3. Reglas

- **R1 · Contrato.** `rol ∈ {ENCARGADO, SUBENCARGADO} ∧ (contrato_sha256 IS NULL ∨ contrato_vigente_hasta < hoy) ⇒ hallazgo(origen='tercero', origen_ref=f"{id}:contrato", severidad='alta')`.
- **R2 · Garantía.** `pais IS NOT NULL ∧ pais ≠ 'EC' ∧ garantia_sha256 IS NULL ⇒ hallazgo(origen_ref=f"{id}:garantia", severidad='critica')`. La regla se decide por el país, no por un rol.
  - Con `pais` nulo no se abre hallazgo: el tercero se lista como «sin país declarado».
  - ESTIMADO: marca todo país distinto de EC, aunque tenga nivel adecuado de protección (art. 56). Es una pregunta para el abogado. El texto del hallazgo dice «garantía no registrada», no afirma un incumplimiento.
- **R3 · Cierre.** Cuando la condición deja de cumplirse, el hallazgo pasa a `cerrado`.
- **R4 · Idempotencia** por `origen_ref`.
- **R5 · Consulta.** `GET /terceros/garantias` solo lee: no evalúa, no abre ni cierra hallazgos. Devuelve los terceros de la organización del token. `permisos` sirve solo para mostrar u ocultar acciones; cada ruta de escritura vuelve a exigir su rol.
- **R6 · Huellas.** `contrato_sha256` y `garantia_sha256` se validan con `huella_registrada` del pasillo de evidencias. Deuda declarada: comprobar que esa función reconoce las mismas huellas que lista `/evidencias/documentos`; hasta comprobarlo, una huella válida de ese listado podría recibir 422.
- **R-ADPA · Ortogonalidad ZERAG (`TER-01`).** Toda invocación a otra sala se realiza vía `app_core/pasillo/<otra_sala>.py#TER-01` (`ImportsCruzados = ∅`, ADR 0001) y los códigos de `ErrorNegocio` (`app_core.errors`) se registran en `features/<sala>/domain/errores.py#TER-01`.

## 4. Interfaz

Módulo Terceros: columnas contrato, garantía, criticidad, próxima revisión; distintivo rojo con enlace al hallazgo.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un encargado sin contrato, **cuando** se evalúa, **entonces** existe un hallazgo `alta`; **y** al registrar contrato vigente, se cierra. | `test_encargado_sin_contrato` |
| **Dado** una transferencia a país distinto de EC sin garantía, **entonces** hallazgo `critica`. Mutación: omitirlo hace fallar la prueba. | `test_transferencia_sin_garantia` |
| **Dado** dos evaluaciones seguidas, **entonces** no se duplican hallazgos. | `test_terceros_idempotente` |
| **Dado** un `dpo` o un `auditor`, **cuando** piden `GET /terceros/garantias`, **entonces** 200 con `permisos.gestionar = false`, y su `PUT` da 403. Tras el `GET` no hay hallazgos nuevos. Mutación: evaluar dentro del `GET` hace fallar la prueba. | `test_listar_garantias_solo_lee` |
| **Dado** un tercero con `pais` nulo y sin garantía, **entonces** no hay hallazgo. Mutación: tratar nulo como extranjero hace fallar la prueba. | `test_pais_nulo_sin_hallazgo` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_terceros_garantias` |
| **Dado** el módulo, **entonces** el tercero sin contrato muestra el distintivo y el enlace. | `frontend/tests/terceros/garantias.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/TER-01.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Terceros con hallazgos automáticos»); RN-TER-01 y RN-TER-02 del documento maestro.
