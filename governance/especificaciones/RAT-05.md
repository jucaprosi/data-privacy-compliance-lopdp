# RAT-05 · Validaciones del RAT por regla y versionado de cada ficha de tratamiento
`¤sdd` `¤rat` `¤hallazgos`

## 1. Datos

Migración `20261102_rat_versiones`: tabla `rat_versiones (id PK, tenant_id NOT NULL REFERENCES tenants(id), tratamiento_id NOT NULL, numero INTEGER NOT NULL, contenido JSONB NOT NULL, creado_por, creado_en TIMESTAMPTZ DEFAULT now())`, `UNIQUE (tenant_id, tratamiento_id, numero)`, append-only (`lopdp_app`: SELECT, INSERT). RLS ENABLE y FORCE.

La misma migración añade `rat_actividades.condicion_habilitante TEXT NULL` con CHECK sobre los siete valores de R5 y amplía `ck_hallazgos_origen` con `rat`.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /rat/{id}/validaciones` | `implementador`, `coordinador`, `dpo`, `admin_organizacion`, `responsable_area` | — | `200 {"reglas": [{codigo, cumple: bool, mensaje}], "hallazgo_id": str \| null}` |
| `GET /rat/{id}/versiones` | los mismos | — | `200 {"versiones": [{numero, creado_por, creado_en}]}` |
| `GET /rat/{id}/versiones/{numero}` | los mismos | — | `200` contenido de esa versión |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 404 | `RAT_NO_ENCONTRADO` | ficha fuera de la organización, o versión inexistente |

Una ficha dada de baja sigue respondiendo en estas tres rutas: su histórico se conserva. `hallazgo_id` es el hallazgo no cerrado de mayor severidad entre las cuatro reglas de la ficha.

## 3. Reglas

- **R1 · Reglas.** `RAT-SENS`: `datos_sensibles ≠ ∅ ⇒ condicion_habilitante ≠ null`. `RAT-EIPD`: `(menores ∨ perfilamiento ∨ biometria) ⇒ marcar_eipd = true`. `RAT-BASE`: `base_legitimacion ≠ null`. `RAT-PLAZO`: `plazo_conservacion ≠ null`. Correspondencia con `ActividadRAT`: `datos_sensibles` es booleano (`≠ ∅` equivale a `true`); `marcar_eipd` es `requiere_eipd`; `base_legitimacion` es `base_legal`; `menores` es `MENORES_EDAD ∈ categorias_titulares`; `perfilamiento` es `decisiones_automatizadas`; `biometria` es una entrada de `categorias_datos` que contiene «biometr», sin distinguir tildes ni mayúsculas. Una cadena vacía cuenta como `null`.
- **Limitación de `RAT-BASE`.** La regla se aplica como dice R1 y se prueba en el validador puro con `base_legal = null`, pero hoy no falla por la API: `base_legal` tiene valor por defecto (`CONSENTIMIENTO`) y no admite nulo. Ese valor por defecto no se cambia, porque rompería fichas y formularios existentes.
- **R2 · Hallazgo.** Por cada regla incumplida al guardar: `registrar_hallazgo(origen='rat', origen_ref=f"{tratamiento_id}:{codigo_regla}", severidad='alta' si RAT-SENS o RAT-EIPD, 'media' en otro caso, control_ref='P10', dimension='D02')`; al cumplirse, el hallazgo pasa a `cerrado` con `cerrar_hallazgo` (motivo `origen_resuelto`). `P10` es el control «Registro de Actividades de Tratamiento (RAT)» del banco; sin él, el hallazgo no se convertiría en tarea (`HALLAZGO_SIN_CONTROL`).
- **R3 · Versión.** `numero = max(numero) + 1` por tratamiento; el contenido es la ficha completa serializada; nunca se edita una versión. Versión y hallazgos se escriben en la misma transacción del guardado, también al crear desde una plantilla.
- **R4 · Reincidencia.** Un hallazgo `rat` cerrado cuya regla vuelve a incumplirse se reabre con `reabrir_hallazgo` (`roadmap_service`): vuelve a `abierto`, o a `en_tratamiento` si ya tiene tarea, y registra el evento `reabierto` con motivo `origen_reincidente`. No se crea otro hallazgo.
- **R5 · Condición habilitante.** `condicion_habilitante ∈` los literales del art. 26 LOPDP (Registro Oficial Suplemento 459, 26-may-2021; texto verificado en la copia escaneada de la Asamblea Nacional que publica el Ministerio de Telecomunicaciones): a) `CONSENTIMIENTO_EXPLICITO`, b) `LABORAL_SEGURIDAD_SOCIAL`, c) `INTERESES_VITALES`, d) `DATOS_PUBLICOS`, e) `ORDEN_JUDICIAL`, f) `ARCHIVO_INVESTIGACION_ESTADISTICA`, g) `SALUD_SEGUN_LEY`.
- **R6 · Baja.** Dar de baja conserva las versiones y cierra los hallazgos de las cuatro reglas: la ficha ya no se puede corregir.

## 4. Interfaz

Panel lateral «Validaciones» en la ficha del RAT: reglas en verde o rojo con el mensaje; enlace al hallazgo; pestaña «Versiones» con lista y vista de una versión.

Excepción acotada al límite «no cambia el formulario»: el campo `condicion_habilitante` aparece en el formulario de alta cuando la ficha trata datos sensibles, y en el panel para el `coordinador` cuando `RAT-SENS` no se cumple. Sin él la regla no se podría corregir.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una ficha con datos sensibles sin condición habilitante, **cuando** se guarda, **entonces** `RAT-SENS.cumple = false` y existe un hallazgo `rat` de severidad `alta`. Mutación: no generar hallazgo hace fallar la prueba. | `test_rat_sens_genera_hallazgo` |
| **Dado** la ficha corregida, **cuando** se guarda, **entonces** el hallazgo queda `cerrado` y hay dos versiones. | `test_rat_correccion_cierra_y_versiona` |
| **Dado** la misma ficha guardada dos veces sin corregir, **entonces** sigue habiendo un solo hallazgo. | `test_rat_hallazgo_idempotente` |
| **Dado** un hallazgo cerrado, **cuando** la regla vuelve a incumplirse, **entonces** el mismo hallazgo se reabre con el evento `reabierto`. | `test_rat_reincidencia_reabre` |
| **Dado** `base_legal` nulo, **cuando** se evalúa en el validador puro, **entonces** `RAT-BASE.cumple = false`. | `test_rat_base_con_valor_nulo` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_rat_versiones` |
| **Dado** la pantalla con una regla incumplida, **entonces** se ve en rojo con su mensaje y el enlace al hallazgo. | `frontend/tests/rat/validaciones.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RAT-05.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («RAT con validaciones y versiones»). Invariante `INV_LOPDP_COMPLIANCE_GRAPH_SSOT`, `INV_LOPDP_SINGLE_ACTION_PLAN`. Decisión abierta: las reglas pasan al paquete normativo con REG-01.
