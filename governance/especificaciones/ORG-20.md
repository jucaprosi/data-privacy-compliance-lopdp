# ORG-20 · Papelera (archivar y restaurar) y exportación completa de los datos de la organización
`¤sdd` `¤rbac-tenant` `¤seguridad`

## 1. Datos

Migración `20261107_papelera`: `exportaciones (id, tenant_id, solicitado_por, solicitada_en, lista_en NULL, r2_key NULL, sha256 NULL, caduca_en NULL, estado VARCHAR(10) CHECK (IN ('pendiente','lista','caducada')))`. RLS ENABLE y FORCE. Se verifica que `lopdp_app` no tiene `DELETE` en ninguna tabla por organización (consulta a `information_schema.role_table_grants`).

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET /organizacion/papelera?entidad=` | `admin_organizacion`, `implementador` | — | `200 {"registros": [{entidad, id, nombre, retirado_en}]}` |
| `POST /organizacion/papelera/{entidad}/{id}/restaurar` | los mismos | — | `200` |
| `POST /organizacion/exportaciones` | `admin_organizacion` | — | `202 {id}` |
| `GET /organizacion/exportaciones/{id}` | `admin_organizacion` | — | `200 {estado, url?, sha256?}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 409 | `EXPORTACION_EN_CURSO` | ya hay una pendiente |
| 410 | `EXPORTACION_CADUCADA` | enlace vencido (7 días) |

## 3. Reglas

- **R1 · Sin borrado.** Ninguna ruta ejecuta `DELETE`; prueba sobre `role_table_grants`.
- **R2 · Exportación completa.** JSON por entidad de la organización + documentos y evidencias por su clave de R2 + `MANIFIESTO.sha256`.
- **R3 · Enlace** prefirmado con caducidad de 7 días; evento `exportacion_generada`.
- **R4 · Cierre de organización** solo por `plataforma_service` y solo con una exportación `lista` de los últimos 30 días.

## 4. Interfaz

Configuración › Papelera (lista por entidad, botón «Restaurar») y Configuración › Exportar datos (botón, estado y descarga).

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un activo retirado, **cuando** se restaura, **entonces** vuelve a listarse como activo. Mutación: borrar al retirar hace fallar la prueba. | `test_papelera_restaura` |
| **Dado** `lopdp_app`, **entonces** no tiene `DELETE` en ninguna tabla por organización. | `test_sin_delete` |
| **Dado** una exportación lista, **entonces** el ZIP contiene el manifiesto y una entrada por entidad con datos. | `test_exportacion_completa` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_exportaciones` |
| **Dado** Configuración › Exportar datos, **cuando** se pide, **entonces** aparece «En preparación» y luego el enlace. | `frontend/tests/organizacion/papelera.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/ORG-20.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD apartado 7 («Papelera y exportación»); documento maestro RN-DAT-01 y RNF-09; `INV_LOPDP_AUDIT_LOG_APPEND_ONLY`.
