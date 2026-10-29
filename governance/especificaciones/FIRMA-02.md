# FIRMA-02 · Aceptación simple con acuse (nombre, correo, fecha, IP y sello hash) y verificación de documentos por hash
`¤sdd` `¤firma-electronica` `¤evidencias`

## 1. Datos

Migración `20261103_aceptaciones`: `aceptaciones (id, tenant_id, documento_id, documento_sha256 VARCHAR(64), persona_id, token_hash VARCHAR(64) UNIQUE, caduca_en TIMESTAMPTZ, aceptado_en TIMESTAMPTZ NULL, nombre TEXT, email TEXT, ip INET NULL, acuse_sha256 VARCHAR(64) NULL, creado_por, creado_en)`. RLS ENABLE y FORCE; `lopdp_app`: SELECT, INSERT, UPDATE (aceptado_en, ip, acuse_sha256). La ruta pública resuelve el token con una función `SECURITY DEFINER` que solo devuelve la fila de ese token.

## 2. API

| Método y ruta | Roles | Entrada | Respuesta |
| :--- | :--- | :--- | :--- |
| `POST /firma/aceptaciones` | `implementador`, `coordinador`, `admin_organizacion` | `{documento_id, persona_ids: [str], dias_vigencia: 1..30}` | `201 {"enlaces": [{persona_id, url}]}` |
| `GET /firma/aceptaciones?documento_id=` | lectura | — | `200 {"aceptaciones": [...]}` sin `token` |
| `GET /aceptar/{token}` (público) | — | — | `200 {nombre_documento, organizacion, sha256}` |
| `POST /aceptar/{token}` (público) | — | `{"acepto": true}` | `200 {"acuse_sha256": str}` |
| `POST /firma/verificar` | lectura | archivo (≤ 10 MB) | `200 {"coincide": bool, "tipo": "documento"\|"acuse"\|null}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 410 | `ACEPTACION_CADUCADA` | token caducado o ya aceptado |
| 404 | `ACEPTACION_NO_ENCONTRADA` | token inexistente (misma respuesta que caducado para no revelar) |
| 409 | `DOCUMENTO_NO_APROBADO` | enviar un documento que no está `aprobado` |

## 3. Reglas

- **R1 · Token.** Aleatorio de 32 bytes; se guarda su `sha256`; caduca en `dias_vigencia`; un solo uso.
- **R2 · Acuse.** `acuse = sha256(documento_sha256 ‖ persona_id ‖ aceptado_en ‖ ip)`; se registra como evidencia en `evidencias_service` con tipo `acuse` y visibilidad `organizacion`.
- **R3 · Verificar.** `coincide ⇔ sha256(archivo) ∈ {documentos aprobados} ∪ {acuses}` de la organización del token.
- **R4 · Sin datos de más.** La ruta pública no muestra el contenido del documento ni otras aceptaciones.

## 4. Interfaz

Biblioteca › Firmas: lista de envíos por documento con estado (pendiente, aceptado, caducado) y botón «Enviar a aceptación»; página pública `/aceptar/<token>` con el nombre del documento, su hash y el botón «Acepto»; Configuración › Verificar documento con zona de arrastre y resultado.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un enlace vigente, **cuando** la persona acepta, **entonces** la fila tiene `aceptado_en`, `ip` y `acuse_sha256`, y existe una evidencia tipo `acuse`. Mutación: no registrar la IP hace fallar la prueba. | `test_aceptacion_registra_acuse` |
| **Dado** el mismo enlace, **cuando** se acepta otra vez, **entonces** 410. | `test_aceptacion_un_uso` |
| **Dado** el archivo aprobado alterado en un byte, **cuando** se verifica, **entonces** `coincide = false`. | `test_verificar_hash` |
| **Dado** un documento `borrador`, **cuando** se envía, **entonces** 409 `DOCUMENTO_NO_APROBADO`. | `test_solo_aprobados` |
| **Dado** la página pública, **cuando** se pulsa «Acepto», **entonces** muestra el acuse y el enlace deja de funcionar. | `frontend/tests/firma/aceptacion.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/FIRMA-02.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- PRD Biblioteca G («Firmas»), §5.9; decisión 4 del propietario; Aporte 111 (proveedores de firma con certificado, fuera de alcance).
