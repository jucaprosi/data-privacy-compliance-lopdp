# DPO-03 · Consultas de la organización al DPO con historial como evidencia de asesoría
`¤sdd` `¤dpo-cockpit` `¤evidencias`

## 1. Datos

Migración `20261104_dpo_consultas`: `dpo_consultas (id, tenant_id, asunto TEXT, estado VARCHAR(10) CHECK (estado IN ('abierta','respondida','cerrada')), creado_por, creado_en, cerrada_en NULL, dictamen_id VARCHAR NULL, evidencia_sha256 NULL)` y `dpo_consultas_mensajes (id, tenant_id, consulta_id, autor_id, texto, creado_en)` append-only. RLS ENABLE y FORCE.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET/POST /dpo/consultas` | todos los roles | `{asunto, texto}` | `200/201` |
| `POST /dpo/consultas/{id}/mensajes` | autor o `dpo` | `{texto}` | `201` |
| `POST /dpo/consultas/{id}/cerrar` | `dpo` | `{respuesta}` | `200 {dictamen_id, evidencia_sha256}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 409 | `CONSULTA_CERRADA` | mensaje tras el cierre |

## 3. Reglas

- **R1 · Cierre.** `cerrar ⇒` inserta en `dpo_dictamenes` (`tipo = OPINION_CONSULTIVA`, cadena de hashes de DPO-01) y custodia el hilo completo como evidencia (`tipo = asesoria_dpo`).
- **R2 · Visibilidad.** El autor ve su consulta; `dpo`, `admin_organizacion` y `coordinador` ven todas; nadie ve consultas de otra organización.
- **R3 · Inmutable tras cierre.**

## 4. Interfaz

Operación › Consultas: lista propia y formulario; DPO › Consultas atendidas: bandeja con filtro de estado, hilo y botón «Responder y cerrar».

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una consulta abierta, **cuando** el `dpo` la cierra, **entonces** hay una entrada `OPINION_CONSULTIVA` en la bitácora y una evidencia con el hilo. Mutación: cerrar sin bitácora hace fallar la prueba. | `test_cierre_bitacora_y_evidencia` |
| **Dado** un `coordinador`, **cuando** cierra, **entonces** 403. | `test_solo_dpo_cierra` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_consultas` |
| **Dado** la bandeja del DPO con una consulta abierta, **cuando** responde y cierra, **entonces** pasa a «Cerrada» y el autor ve la respuesta. | `frontend/tests/dpo/consultas.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/DPO-03.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 4 («consultas atendidas»); `INV_LOPDP_DPO_INDEPENDENCE`.
