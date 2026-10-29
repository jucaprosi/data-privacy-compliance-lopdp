# EVI-02 · Vigencia, visibilidad y paquete para inspección
`¤sdd` `¤evidencias` `¤evidencias-vigencia`

## 1. Datos

Migración `20261031_evidencias_vigencia`, sobre la **tabla de registro de documentos de EVI-01** (el nombre lo fija EVI-01; esta especificación la llama `documentos`):

| Columna nueva | Tipo | Restricción |
| :--- | :--- | :--- |
| `vence_el` | `DATE` | `NULL` (nulo = sin vencimiento) |
| `visibilidad` | `VARCHAR(12)` | `NOT NULL DEFAULT 'organizacion' CHECK (visibilidad IN ('equipo','organizacion','auditor'))` |

Como EVI-01 hace la tabla `SELECT` e `INSERT` solo, estos atributos se cambian con una tabla append-only `documentos_atributos (id, tenant_id, documento_id, vence_el, visibilidad, fijado_por, fijado_en)`; el valor vigente es el último. RLS `ENABLE` y `FORCE`; `lopdp_app`: `SELECT, INSERT`.

Requisitos para ordenar el paquete: la tabla de vínculos documento–control de EVI-01 (`control_ref` P1–P80).

## 2. API

Rutas nuevas en `api/routers/evidencias_inspeccion.py`, prefijo `/evidencias`, `AUTO_REGISTRO = True`.

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `PUT /evidencias/{sha256}/atributos` | `implementador`, `coordinador` | `{"vence_el": "YYYY-MM-DD" \| null, "visibilidad": str}` | `200 {sha256, vence_el, visibilidad, vigente: bool}` |
| `GET /evidencias/paquete-inspeccion` | `implementador`, `coordinador`, `dpo`, `admin_organizacion` | — | `200 application/zip`, `Content-Disposition: attachment; filename="paquete-inspeccion-<tenant>-<fecha>.zip"` |

El ZIP contiene `INDICE.md` (por `control_ref` ascendente: requisito, nombre del archivo, SHA-256, fecha de registro, `vence_el`) y una carpeta `P<nn>/` por control con los archivos (leídos de R2 por `app_core/storage/r2.py`).

`GET /evidencias` (EVI-01) pasa a devolver `vence_el`, `visibilidad` y `vigente`, y a filtrar por visibilidad (R2).

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | `EVIDENCIA_NO_VISIBLE` | el rol del token no alcanza la visibilidad del documento (descarga o atributos) |
| 404 | `EVIDENCIA_NO_ENCONTRADA` | `sha256` fuera de la organización |
| 409 | `PAQUETE_VACIO` | ningún documento vigente y visible vinculado a un control |
| 422 | `VENCIMIENTO_PASADO` | `vence_el` anterior a hoy al fijarlo |

## 3. Reglas

- **R1 · Vigente.** `vigente(d) ⇔ d.vence_el IS NULL ∨ d.vence_el ≥ hoy` (Guayaquil). Un documento no vigente no cuenta para ningún control (`_controles_con_documento` de DIAG-03 lo excluye) ni entra en el paquete.
- **R2 · Visibilidad.** `equipo` ⇒ `implementador`, `coordinador`; `organizacion` ⇒ además `admin_organizacion`, `responsable_area`, `dpo`; `auditor` ⇒ además el rol `auditor` cuando exista. Se aplica en el servidor en listar, descargar y empaquetar.
- **R3 · Compuerta para otras salas.** `evidencias_service.vigencia_de(session, tenant_id, sha256) -> {vence_el, vigente}` y `evidencias_service.existe(session, tenant_id, sha256) -> bool` (las usan CAPA-02 y CAPA-03).
- **R4 · Orden del paquete.** Por `control_ref` numérico ascendente; dentro de un control, por fecha de registro ascendente. Un documento vinculado a varios controles aparece en cada carpeta y una sola vez en el índice por control.
- **R5 · Inmutabilidad.** Fijar atributos no modifica el registro de EVI-01; crea una fila en `documentos_atributos`. Evento `registrar_evento(entity_type='documento', action='atributos_fijados' | 'paquete_generado')`.

## 4. Interfaz

`EvidenciasModule.tsx`: columna «Vence» y «Visibilidad» con edición para `implementador` y `coordinador`; distintivo «Vencida» en rojo; botón «Paquete para inspección» (`PaqueteInspeccion.tsx`) que descarga el ZIP y muestra cuántos controles cubre.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un documento con `vence_el` ayer vinculado a P5, **cuando** se genera el paquete, **entonces** no aparece ni en `P05/` ni en el índice. Mutación: ignorar la vigencia hace fallar la prueba. | `test_paquete_excluye_vencidas` |
| **Dado** un documento `equipo`, **cuando** un `responsable_area` lo lista o descarga, **entonces** no aparece y la descarga da 403. | `test_visibilidad_en_servidor` |
| **Dado** `vence_el` ayer al fijar, **entonces** 422 `VENCIMIENTO_PASADO`. | `test_vencimiento_no_pasado` |
| **Dado** dos documentos en P3 y uno en P1, **entonces** el índice los lista en orden P1, P3, P3. | `test_paquete_ordenado_por_requisito` |
| **Dado** un `sha256` de A, **cuando** `vigencia_de` se llama en el contexto de B, **entonces** no existe. | `test_rls_atributos` |
| **Dado** la pantalla como `coordinador`, **cuando** fija una fecha futura, **entonces** la columna «Vence» la muestra y el distintivo no aparece. | `frontend/tests/evidencias/vigencia.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/EVI-02.md`. PRD: apartado 7 («Repositorio único de evidencias», «Paquete para inspección»), Biblioteca G («Vigencia»). Contraste: O-3, D-3.
- Depende de los nombres de tabla que fije EVI-01; al fusionarse EVI-01, esta especificación se actualiza con los nombres reales antes de programar.
- Decisión abierta: el rol `auditor` no existe aún en `user_tenant_roles`; `visibilidad = 'auditor'` se admite pero no amplía a nadie hasta que exista.
