# RAT-07 · Colectivos de titulares y registro de consentimientos por finalidad, sin base de titulares
`¤sdd` `¤rat` `¤evidencias`

## 1. Datos

Migración `20261102_consentimientos`: `colectivos_titulares (id, tenant_id, tratamiento_id, nombre, base_legitimacion VARCHAR(32), texto_version VARCHAR(16) NULL, creado_por, creado_en)` y `consentimientos_registro (id, tenant_id, colectivo_id, fecha DATE, canal VARCHAR(16) CHECK (canal IN ('web','presencial','telefono','otro')), cantidad INTEGER CHECK (cantidad > 0), texto_version, registrado_por, registrado_en)` append-only. RLS ENABLE y FORCE; `lopdp_app`: SELECT, INSERT (y UPDATE solo en `colectivos_titulares`). `extra='forbid'` en los modelos de entrada.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET/POST /rat/{id}/colectivos`, `PUT /rat/colectivos/{id}` | escriben `implementador`, `coordinador`, `admin_organizacion`; leen además `dpo`, `responsable_area` | campos de la tabla | `200/201 Colectivo` |
| `POST /rat/colectivos/{id}/consentimientos` | los que escriben | `{fecha, canal, cantidad, texto_version}` | `201 Registro` |
| `GET /rat/colectivos/{id}/consentimientos?desde=&hasta=` | lectura | — | `200 {"registros": [...], "total": int}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 422 | `TITULAR_IDENTIFICADO` | el cuerpo trae `email`, `cedula`, `nombre_titular` o cualquier campo fuera del modelo |
| 404 | `COLECTIVO_NO_ENCONTRADO` | fuera de la organización |

## 3. Reglas

- **R1 · Minimización.** Ningún modelo admite datos de un titular individual; `extra='forbid'` y lista negra explícita de nombres de campo.
- **R2 · Agregación.** `total = Σ cantidad` en el rango; nunca se listan personas.
- **R3 · Consentimiento individual.** Una prueba de consentimiento (PDF firmado, captura) se custodia en `evidencias` vinculada al colectivo por `sha256`; `rat` solo guarda la referencia.

## 4. Interfaz

Pestaña «Titulares» del RAT: colectivos por tratamiento y, por colectivo, registro agregado de consentimientos por fecha y canal; aviso fijo «Esta plataforma no guarda bases de titulares».

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un cuerpo de registro con `email`, **entonces** 422 `TITULAR_IDENTIFICADO`. Mutación: aceptar el campo hace fallar la prueba. | `test_consentimiento_sin_identidad` |
| **Dado** 2 registros de 10 y 5, **cuando** se consulta el rango, **entonces** `total = 15`. | `test_consentimiento_agrega` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_consentimientos` |
| **Dado** la pestaña, **cuando** se registra un consentimiento, **entonces** el total sube y no aparece ningún campo de identidad. | `frontend/tests/rat/consentimientos.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RAT-07.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («titulares: solo colectivos y registros de consentimiento»); Doctrina 8; contraste D-6.
