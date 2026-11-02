# FIRMA-03 · Persistencia de sesiones de firma (`firma_sessions`) y compuerta async
`¤sdd` `¤firma-electronica` `¤rbac-tenant`

## 1. Datos

Migración `20261103_firma_sessions` (`down_revision = 20261030_hallazgos`, la cabeza de `dev/jose` al crearla). Una fila por documento que se envía a firmar.

`firma_sessions (firma_id UUID PK DEFAULT gen_random_uuid(), tenant_id UUID NOT NULL, documento_id TEXT NOT NULL, firmante_id TEXT NOT NULL, estado TEXT NOT NULL, formato TEXT NOT NULL, proveedor TEXT NOT NULL, sha256_original TEXT NOT NULL, sha256_firmado TEXT NULL, timestamp_tsa TIMESTAMPTZ NULL, certificado_json JSONB NULL, metadatos JSONB NOT NULL DEFAULT '{}', creado_en TIMESTAMPTZ NOT NULL DEFAULT now(), actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now())`

- `CHECK (estado IN ('borrador','pendiente_firma','firmado','rechazado','error_validacion'))`. `formato` y `proveedor` no llevan restricción en la base: el motor guarda el texto de `FormatoFirma` y `ProveedorFirma`.
- Índice `idx_firma_sessions_tenant_estado (tenant_id, estado, creado_en DESC)`.
- RLS: `ENABLE` y `FORCE`. Política `firma_sessions_tenant`, `USING` y `WITH CHECK` con `tenant_id::text = current_setting('app.current_tenant_id', true)`, el valor que fija `fijar_contexto_rls`.
- Permisos de `lopdp_app`: `REVOKE ALL`; `GRANT SELECT, INSERT`; `GRANT UPDATE (estado, sha256_firmado, timestamp_tsa, certificado_json, metadatos, actualizado_en)`. Sin `DELETE`. `documento_id`, `firmante_id`, `sha256_original`, `tenant_id`, `formato` y `proveedor` no se pueden reescribir.
- Entidad: `FirmaSession` (`features/firma_electronica/domain/entities.py`), un campo por columna.

## 2. API

Sin API HTTP nueva. La sala se consume por la compuerta `features/firma_electronica/firma_electronica_service.py`, cuyas funciones son `async` y reciben la `AsyncSession` de quien llama, con el tenant ya fijado por `fijar_contexto_rls`:

| Función | Entrada | Salida |
| :--- | :--- | :--- |
| `crear_sesion_firma(db, tenant_id, documento_id, firmante_id, formato, proveedor, sha256_original, usuario_id=None)` | textos; `formato` y `proveedor` aceptan el Enum o su texto | `FirmaSession` en `borrador` |
| `obtener_sesion(db, firma_id, tenant_id)` | UUID o texto | `FirmaSession` o `None` |
| `marcar_firmado(db, firma_id, tenant_id, sha256_firmado, certificado_json, timestamp_tsa, usuario_id=None)` | hash, dict, `datetime` con zona | `FirmaSession` en `firmado` |
| `listar_sesiones(db, tenant_id, estado=None, limit=50)` | `estado` opcional; `limit` se acota a 1..500 | lista, de la más reciente a la más antigua |

| Error | Cuándo |
| :--- | :--- |
| `SesionFirmaNoEncontradaError` | `marcar_firmado` sobre una sesión que no existe en la organización |
| `TransicionFirmaInvalidaError` | `marcar_firmado` sobre una sesión que ya no está en `borrador` ni `pendiente_firma` |
| `ValueError` | `listar_sesiones` con un `estado` fuera de los cinco válidos |

Los `boceto_*` de FIRMA-01 y sus tipos (`EstadoFirma`, `FormatoFirma`, `ProveedorFirma`, `ResultadoFirma`, `DocumentoParaFirma`, `CertificadoInfo`, `SesionFirmaPasarela`) siguen en la compuerta sin cambios, como aliases de compatibilidad.

## 3. Reglas

- **R1 · Estado inicial.** `crear_sesion_firma` siempre deja `estado = 'borrador'`.
- **R2 · Firma única y atómica.** `marcar_firmado` ejecuta un solo `UPDATE … WHERE firma_id = :id AND tenant_id = :t AND estado IN ('borrador','pendiente_firma') RETURNING *`. Cierra la sesión como `firmado` sii ese `UPDATE` devuelve fila; si no la devuelve, distingue «no existe» de «ya cerrada».
- **R3 · Aislamiento.** Toda consulta filtra por `tenant_id` además de la política RLS: la sesión de A pedida por B, con cualquiera de los dos `tenant_id`, devuelve `None` o `[]`. Sin tenant fijado no se ve ninguna fila.
- **R4 · Auditoría.** Crear registra un evento `crear_sesion_firma` y firmar uno `marcar_firmado`, ambos con `entity_type = 'firma_session'` y `entity_id = str(firma_id)`, en la misma transacción que el cambio: si el evento falla, la sesión tampoco queda.
- **R5 · Inmutabilidad.** Tras crearla, `lopdp_app` solo puede cambiar las seis columnas del apartado 1 y nunca borrar la sesión.
- **R6 · Sin SQL interpolado.** Todo SQL usa `text()` con parámetros; ningún valor se concatena en la sentencia.
- **R7 · Sin red ni credenciales.** No hay llamadas a ANF ni a UniverselD ni credenciales en ningún archivo. Quien invoca `marcar_firmado` aporta el resultado de la firma.

## 4. Interfaz

Sin interfaz.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** una sesión creada, **cuando** se lee desde una sesión de BD nueva, **entonces** es la misma fila, en `borrador`, sin hash firmado, sello ni certificado. | `test_crear_sesion_persiste` |
| **Dado** una sesión en `borrador`, **cuando** se marca firmada, **entonces** quedan `firmado`, `sha256_firmado`, `timestamp_tsa` y `certificado_json`; firmarla otra vez falla con `TransicionFirmaInvalidaError` y una inexistente con `SesionFirmaNoEncontradaError`. | `test_marcar_firmado` |
| **Dado** una sesión de la organización A, **cuando** la pide la organización B, **entonces** recibe `None`; B no puede insertar filas de A, y ni A puede reescribir `sha256_original` ni borrar la sesión (`42501`). | `test_rls_aislamiento` |
| **Dado** una sesión creada, **cuando** se consulta `audit_events`, **entonces** hay un evento con `entity_type = 'firma_session'`; tras firmar hay dos. Mutación: no registrar el evento al crear hace fallar la prueba. | `test_audit_event_creado` |
| **Dado** tres sesiones con dos firmadas, **cuando** se lista por `firmado`, **entonces** devuelve las dos; un estado desconocido lanza `ValueError`. | `test_listar_por_estado` |
| **Dado** el boceto `boceto_firmar_documento_anf`, **cuando** se invoca, **entonces** devuelve un `ResultadoFirma` en `FIRMADO` y la compuerta sigue exportando los `boceto_*`. | `test_bocetos_compatibles` |

## 6. Trazabilidad

- Ficha: `governance/tareas/FIRMA-03.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Depende de FIRMA-01, RM-00, RM-02, RM-14 y SEC-05. PRD Biblioteca G («Firmas»), §5.9; Aporte 111.
- **Decisión abierta 1 · Tipos de las claves.** La ficha fija `firma_id` y `tenant_id` como `UUID` y sin clave foránea; la convención del repositorio es `VARCHAR` con UUID en texto y `tenant_id REFERENCES tenants(id)`. Se construyó como pide la ficha; el coordinador decide si se alinea con la convención.
- **Decisión abierta 2 · Nombre del setting.** La ficha cita `app.tenant_id`; el repositorio fija `app.current_tenant_id`. Se usó el segundo, porque con el primero la política falla con «parámetro no reconocido».
- **Decisión abierta 3 · Migración con FIRMA-02.** FIRMA-02 planea `20261103_aceptaciones`; las dos parten de la misma cabeza y la segunda en fusionarse debe volver a encadenarse (`alembic heads` debe mostrar una sola).
- **Decisión abierta 4 · Estado `pendiente_firma`.** El motor crea en `borrador` y acepta firmar desde `borrador` o `pendiente_firma`, pero ninguna función pasa una sesión a `pendiente_firma`, `rechazado` ni `error_validacion`: quedan para la integración con los proveedores.
