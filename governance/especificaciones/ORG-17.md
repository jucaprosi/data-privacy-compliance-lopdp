# ORG-17 · Inventario de activos, soportes y personas
`¤sdd` `¤organizacion` `¤inventario`

## 1. Datos

Migración `*_inventario_activos` (id ≤ 32 caracteres), tres tablas por organización con RLS `ENABLE` y `FORCE`; `lopdp_app`: `SELECT, INSERT, UPDATE` (baja lógica con `retirado_en`, sin `DELETE`).

**`activos`**: `id, tenant_id, nombre TEXT NOT NULL, tipo VARCHAR(12) CHECK (tipo IN ('aplicacion','nube','equipo','otro')), proveedor TEXT NULL, ubicacion_datos VARCHAR(2) NULL (ISO 3166-1), medidas TEXT NULL, retirado_en TIMESTAMPTZ NULL, creado_por, creado_en, actualizado_en`.

**`soportes`**: `id, tenant_id, nombre, tipo VARCHAR(10) CHECK (tipo IN ('fisico','digital')), ubicacion TEXT NULL, responsable_user_id VARCHAR NULL, retirado_en, creado_por, creado_en, actualizado_en`; tabla hija append-only `soportes_movimientos (id, tenant_id, soporte_id, tipo VARCHAR(10) CHECK (tipo IN ('salida','devolucion')), persona TEXT, registrado_por, registrado_en)`.

**`personas`**: `id, tenant_id, nombre TEXT NOT NULL, cargo TEXT NULL, area_id VARCHAR NULL REFERENCES areas(id), email TEXT NULL, user_id VARCHAR NULL, retirada_en, creado_por, creado_en, actualizado_en`. **Sin columna de cédula** (D-6): si una firma la exige, la pide `firma_electronica` y la guarda cifrada en su sala.

**`activos_tratamientos`**: `(tenant_id, activo_id, tratamiento_id)` PK compuesta; el `tratamiento_id` se valida por `rat_service.existe_tratamiento`.

## 2. API

Router `api/routers/organizacion_inventario.py`, prefijo `/organizacion/inventario`, `AUTO_REGISTRO = True`. Escriben `implementador`, `coordinador`, `admin_organizacion`; leen además `dpo` y `responsable_area`.

| Método y ruta | Entrada | Respuesta |
| :--- | :--- | :--- |
| `GET/POST /activos`, `PUT /activos/{id}`, `POST /activos/{id}/retirar` | campos de la tabla | `200/201 Activo` |
| `PUT /activos/{id}/tratamientos` | `{"tratamiento_ids": [str]}` | `200 Activo` (reemplaza el conjunto) |
| `GET/POST /soportes`, `PUT /soportes/{id}`, `POST /soportes/{id}/movimientos` | campos; movimiento `{tipo, persona}` | `200/201` |
| `GET/POST /personas`, `PUT /personas/{id}`, `POST /personas/{id}/retirar` | campos de la tabla | `200/201 Persona` |
| `POST /personas/importar` | CSV `nombre,cargo,area_codigo,email` (≤ 500 filas) | `201 {"creadas": int, "errores": [{fila, motivo}]}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | `dpo` o `responsable_area` al escribir |
| 404 | `INVENTARIO_NO_ENCONTRADO` | id fuera de la organización |
| 409 | `INVENTARIO_RETIRADO` | editar un registro retirado |
| 422 | `TRATAMIENTO_NO_ENCONTRADO` | id de tratamiento inexistente |
| 422 | `PERSONA_CON_IDENTIFICACION` | el CSV o el cuerpo traen una columna de cédula o pasaporte |

## 3. Reglas

- **R1 · Minimización.** El servidor rechaza cualquier campo que no esté en la tabla (`extra='forbid'`); en particular `cedula`, `pasaporte`, `identificacion`.
- **R2 · Baja lógica.** Retirar fija `retirado_en`; el registro sigue visible con filtro `incluir_retirados=true`.
- **R3 · Movimiento de soporte.** Una `salida` sin `devolucion` posterior deja el soporte «fuera»; el estado se deriva del último movimiento.
- **R4 · Vínculo con el RAT.** Solo por `rat_service`; `organizacion` no lee tablas de `rat`.
- **R5 · Auditoría.** Evento por alta, edición, retiro, movimiento e importación (`entity_type` = nombre de la tabla).

## 4. Interfaz

Menú Inventario › Activos y sistemas, Soportes, Personas (`menus/ORG-17.ts`, `pantallas/ORG-17.tsx`): listas con filtros guardados, ficha lateral con tratamientos vinculados (activos) o movimientos (soportes), y carga masiva de personas con plantilla CSV descargable.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un cuerpo de persona con `cedula`, **entonces** 422 `PERSONA_CON_IDENTIFICACION`. Mutación: permitir el campo hace fallar la prueba. | `test_persona_sin_identificacion` |
| **Dado** un activo vinculado a un tratamiento inexistente, **entonces** 422. | `test_activo_tratamiento_valido` |
| **Dado** un soporte con `salida` y sin devolución, **entonces** su estado es «fuera»; tras `devolucion`, «en sitio». | `test_soporte_movimientos` |
| **Dado** un CSV de 3 filas con una `area_codigo` inexistente, **entonces** `creadas = 2` y un error con su fila. | `test_importar_personas` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_inventario` |
| **Dado** la pantalla de Personas, **cuando** se sube el CSV de ejemplo, **entonces** la lista muestra las filas creadas. | `frontend/tests/organizacion/inventario.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/ORG-17.md` (backlog). PRD: Módulo 2 («Inventario ampliado»). Contraste: menú 3, D-6.
