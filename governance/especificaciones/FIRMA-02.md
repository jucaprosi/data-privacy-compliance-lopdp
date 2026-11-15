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
| `POST /aceptar/{token}` (público) | — | `{"acepto": true}` | `200 {"acuse_sha256": str, "acuse_pdf": str}` (`acuse_pdf` en base64) |
| `POST /firma/verificar` | lectura | archivo (≤ 10 MB) | `200 {"coincide": bool, "tipo": "documento"\|"acuse"\|null}` |

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de la tabla |
| 410 | `ACEPTACION_CADUCADA` | token caducado o ya aceptado |
| 404 | `ACEPTACION_NO_ENCONTRADA` | token inexistente (misma respuesta que caducado para no revelar) |
| 409 | `DOCUMENTO_NO_APROBADO` | enviar un documento que no está `aprobado` |

## 3. Reglas

- **R1 · Token.** Aleatorio de 32 bytes; se guarda su `sha256`; caduca en `dias_vigencia`; un solo uso.
- **R2 · Acuse.** Al aceptar, en la misma transacción:
  1. `features/firma_electronica/services/aceptacion_engine.py` genera un único PDF con ReportLab, la biblioteca que ya usan los informes de la plataforma. El PDF contiene el nombre de la organización, el nombre del documento, `documento_sha256`, el nombre y el correo de la persona, `aceptado_en` en UTC (ISO 8601), la IP y el id de la aceptación.
  2. Lo custodia con `app_core/pasillo/evidencias.py::custodiar_documento_generado` (sección `#FIRMA-02`): `tipo_mime="application/pdf"`, `tipo_evidencia="acuse"` (EVI-05), `nombre="acuse-<id[:8]>.pdf"`, y como `control_refs` los controles vinculados al documento en la biblioteca (`app_core/pasillo/biblioteca.py#FIRMA-02`) o `["P1"]` si no tiene ninguno.
  3. Guarda en `aceptaciones.acuse_sha256` el `sha256` que devuelve la custodia, calculado sobre esos bytes. La sala de firma no calcula un hash propio.
  4. La respuesta pública devuelve `acuse_sha256` y los mismos bytes en `acuse_pdf`, para que la persona conserve su comprobante.
  Se elige PDF y no texto porque es un comprobante para una persona ajena a la plataforma: se abre, se imprime y se archiva tal cual, y la custodia ya valida su firma de formato. Las marcas de tiempo internas del PDF no afectan a la verificación, porque la huella de referencia es la de los bytes custodiados.
- **R3 · Verificar.** Para un archivo, `h = sha256(bytes)`. `coincide` es verdadero y `tipo = "documento"` si `h` es la huella de un documento `aprobado` de la organización. Es verdadero y `tipo = "acuse"` si `h` es el `acuse_sha256` de una aceptación de la organización y la custodia tiene esa huella (`huella_custodiada`). En otro caso, `coincide = false` y `tipo = null`. El acuse descargado de la respuesta pública verifica tal cual; con un byte cambiado, no.
- **R4 · Sin datos de más.** La ruta pública no muestra el contenido del documento ni otras aceptaciones.
- **R-ADPA · Ortogonalidad ZERAG (`FIRMA-02`).** Toda invocación a otra sala se realiza vía `app_core/pasillo/<otra_sala>.py#FIRMA-02` (`ImportsCruzados = ∅`, ADR 0001) y los códigos de `ErrorNegocio` (`app_core.errors`) se registran en `features/<sala>/domain/errores.py#FIRMA-02`.

## 4. Interfaz

Biblioteca › Firmas: lista de envíos por documento con estado (pendiente, aceptado, caducado) y botón «Enviar a aceptación»; página pública `/aceptar/<token>` con el nombre del documento, su hash y el botón «Acepto»; Configuración › Verificar documento con zona de arrastre y resultado.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un enlace vigente, **cuando** la persona acepta, **entonces** la fila tiene `aceptado_en`, `ip` y `acuse_sha256`, y existe una evidencia tipo `acuse` en PDF. Mutación: no registrar la IP hace fallar la prueba. | `test_aceptacion_registra_acuse` |
| **Dado** la aceptación, **entonces** `acuse_sha256` es igual al `sha256` de la evidencia custodiada y al `sha256` de los bytes de `acuse_pdf`. Mutación: guardar un hash calculado por la sala de firma sobre otros datos hace fallar la prueba. | `test_acuse_hash_es_el_de_la_custodia` |
| **Dado** el `acuse_pdf` descargado, **cuando** se verifica, **entonces** `coincide = true` y `tipo = "acuse"`. Con un byte cambiado, `coincide = false` y `tipo = null`. | `test_verificar_acuse` |
| **Dado** el mismo enlace, **cuando** se acepta otra vez, **entonces** 410. | `test_aceptacion_un_uso` |
| **Dado** el archivo aprobado alterado en un byte, **cuando** se verifica, **entonces** `coincide = false`. | `test_verificar_hash` |
| **Dado** un documento `borrador`, **cuando** se envía, **entonces** 409 `DOCUMENTO_NO_APROBADO`. | `test_solo_aprobados` |
| **Dado** la página pública, **cuando** se pulsa «Acepto», **entonces** muestra el acuse y el enlace deja de funcionar. | `frontend/tests/firma/aceptacion.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/FIRMA-02.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de EVI-05, que añade el tipo `acuse` a la custodia de evidencias.
- PRD Biblioteca G («Firmas»), §5.9; decisión 4 del propietario; Aporte 111 (proveedores de firma con certificado, fuera de alcance).
