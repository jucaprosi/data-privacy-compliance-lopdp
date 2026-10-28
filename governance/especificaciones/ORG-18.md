# ORG-18 · Sedes de la organización y clientes cuando actúa como encargada
`¤sdd` `¤rbac-tenant` `¤inventario`

## 1. Datos

Migración `20261102_sedes_clientes`: `sedes (id, tenant_id, nombre, direccion, ciudad, provincia, es_principal BOOLEAN, contacto_spdp TEXT, contacto_titulares TEXT, medidas TEXT, retirada_en, creado_por, creado_en, actualizado_en)` con índice único parcial `(tenant_id) WHERE es_principal`; `clientes_encargo (id, tenant_id, razon_social, ruc VARCHAR(13), contrato_sha256 VARCHAR(64) NULL, vigente_hasta DATE NULL, retirado_en, creado_por, creado_en)`. RLS ENABLE y FORCE; `lopdp_app`: SELECT, INSERT, UPDATE.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `GET/POST /organizacion/sedes`, `PUT /organizacion/sedes/{id}`, `POST /organizacion/sedes/{id}/retirar` | escriben `admin_organizacion`, `implementador`, `coordinador`; leen todos | campos | `200/201 Sede` |
| `GET/POST /organizacion/clientes`, `PUT /organizacion/clientes/{id}`, `POST /organizacion/clientes/{id}/retirar` | los mismos | campos | `200/201 Cliente` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 409 | `SEDE_PRINCIPAL_DUPLICADA` | marcar principal cuando ya hay otra |
| 409 | `NO_ES_ENCARGADA` | clientes cuando `rol_datos = responsable` |
| 422 | `CONTRATO_NO_ENCONTRADO` | `contrato_sha256` inexistente (`evidencias_service.existe`) |

## 3. Reglas

- **R1 · Principal única.** `|{s : s.es_principal ∧ s.retirada_en IS NULL}| ≤ 1`.
- **R2 · Encargada.** `clientes_encargo` solo si `tenants.rol_datos ∈ {encargado, ambos}` (ORG-16).
- **R3 · Contrato.** Referencia a evidencia por `sha256`; no se custodia aquí.

## 4. Interfaz

Inventario › Sedes y áreas (lista de sedes con la principal marcada; las áreas siguen en su pantalla de ORG-07) e Inventario › Clientes, visible solo si la organización es encargada.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una sede principal, **cuando** se marca otra, **entonces** 409 `SEDE_PRINCIPAL_DUPLICADA`. Mutación: permitirlo hace fallar la prueba. | `test_sede_principal_unica` |
| **Dado** `rol_datos = responsable`, **cuando** se crea un cliente, **entonces** 409 `NO_ES_ENCARGADA`. | `test_clientes_solo_encargada` |
| **Dado** registros de A, **cuando** se consulta en B con `lopdp_app`, **entonces** 0 filas. | `test_rls_sedes` |
| **Dado** una organización encargada, **entonces** el submenú Clientes aparece; como responsable, no. | `frontend/tests/organizacion/sedes.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/ORG-18.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Módulo 2 («Inventario ampliado»); estructura, menú 3.
