# RAT-05 · Validaciones del RAT por regla y versionado de cada ficha de tratamiento
`¤sdd` `¤rat` `¤hallazgos`

## 1. Datos

Migración `20261102_rat_versiones`: tabla `rat_versiones (id PK, tenant_id NOT NULL REFERENCES tenants(id), tratamiento_id NOT NULL, numero INTEGER NOT NULL, contenido JSONB NOT NULL, creado_por, creado_en TIMESTAMPTZ DEFAULT now())`, `UNIQUE (tenant_id, tratamiento_id, numero)`, append-only (`lopdp_app`: SELECT, INSERT). RLS ENABLE y FORCE.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /rat/{id}/validaciones` | `implementador`, `coordinador`, `dpo`, `admin_organizacion`, `responsable_area` | — | `200 {"reglas": [{codigo, cumple: bool, mensaje}], "hallazgo_id": str \| null}` |
| `GET /rat/{id}/versiones` | los mismos | — | `200 {"versiones": [{numero, creado_por, creado_en}]}` |
| `GET /rat/{id}/versiones/{numero}` | los mismos | — | `200` contenido de esa versión |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 404 | `RAT_NO_ENCONTRADO` | ficha fuera de la organización |

## 3. Reglas

- **R1 · Reglas.** `RAT-SENS`: `datos_sensibles ≠ ∅ ⇒ condicion_habilitante ≠ null`. `RAT-EIPD`: `(menores ∨ perfilamiento ∨ biometria) ⇒ marcar_eipd = true`. `RAT-BASE`: `base_legitimacion ≠ null`. `RAT-PLAZO`: `plazo_conservacion ≠ null`.
- **R2 · Hallazgo.** Por cada regla incumplida al guardar: `registrar_hallazgo(origen='rat', origen_ref=f"{tratamiento_id}:{codigo_regla}", severidad='alta' si RAT-SENS o RAT-EIPD, 'media' en otro caso)`; al cumplirse, el hallazgo pasa a `cerrado`.
- **R3 · Versión.** `numero = max(numero) + 1` por tratamiento; el contenido es la ficha completa serializada; nunca se edita una versión.

## 4. Interfaz

Panel lateral «Validaciones» en la ficha del RAT: reglas en verde o rojo con el mensaje; enlace al hallazgo; pestaña «Versiones» con lista y vista de una versión.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una ficha con datos sensibles sin condición habilitante, **cuando** se guarda, **entonces** `RAT-SENS.cumple = false` y existe un hallazgo `rat` de severidad `alta`. Mutación: no generar hallazgo hace fallar la prueba. | `test_rat_sens_genera_hallazgo` |
| **Dado** la ficha corregida, **cuando** se guarda, **entonces** el hallazgo queda `cerrado` y hay dos versiones. | `test_rat_correccion_cierra_y_versiona` |
| **Dado** la misma ficha guardada dos veces sin corregir, **entonces** sigue habiendo un solo hallazgo. | `test_rat_hallazgo_idempotente` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_rat_versiones` |
| **Dado** la pantalla con una regla incumplida, **entonces** se ve en rojo con su mensaje y el enlace al hallazgo. | `frontend/tests/rat/validaciones.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RAT-05.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («RAT con validaciones y versiones»). Invariante `INV_LOPDP_COMPLIANCE_GRAPH_SSOT`, `INV_LOPDP_SINGLE_ACTION_PLAN`. Decisión abierta: las reglas pasan al paquete normativo con REG-01.
