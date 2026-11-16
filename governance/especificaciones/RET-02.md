# RET-02 · Almacén de evidencias del roadmap en Google Cloud Storage
`¤sdd` `¤evidencias` `¤roadmap` `¤seguridad-tenant`

## 1. Datos

Sin migración. Cambia el almacén de objetos:

- `api/routers/roadmaps.py` y `features/roadmap/services/evidencia_engine.py` usan el `Almacen` de `app_core/storage` (GCS, `FirmaSubida`), el mismo contrato que ya usa la sala evidencias.
- `app_core/storage/limites.py` centraliza `TAMANO_MAXIMO_BYTES` y `motivo_de_rechazo`, utilizados de forma uniforme por `api/routers/roadmaps.py`, `features/evidencias/services/evidencias_engine.py`, `features/evidencias/services/custodia_generados_engine.py` y `features/evidencias/services/paquete_inspeccion_engine.py`.
- `requirements.txt` incluye `google-cloud-storage` para la operación de almacenamiento.
- Clave del objeto: empieza por el `tenant_id` de la sesión. Las claves ya guardadas en `task_evidence` no se reescriben.

## 2. API

Las rutas no cambian de forma: `POST /roadmaps/tasks/{task_id}/evidence/upload-url` devuelve la firma de subida y `POST /roadmaps/tasks/{task_id}/evidence` confirma. Las respuestas exponen URLs firmadas V4 de Google Cloud Storage y el campo `clave_objeto`.

| Código HTTP | `code` | Cuándo |
| :--- | :--- | :--- |
| 403 | (dependencia de roles) | rol fuera de los que suben evidencia |
| 413 o 422 | los de `motivo_de_rechazo` | tipo o tamaño no admitido |
| 503 | código neutro del catálogo | almacén no configurado: falla cerrado, sin nombrar al proveedor |

## 3. Reglas

- **R1 · Aislamiento por organización.** La clave que se firma la arma el servidor con el `tenant_id` del token. Un cliente no puede pedir la firma de una clave de otra organización ni elegir el prefijo.
- **R2 · Confirmación comprobada.** Al confirmar, el servidor verifica que el objeto existe bajo el prefijo de la organización y vuelve a aplicar `motivo_de_rechazo` sobre lo subido.
- **R3 · Falla cerrado.** Fuera de la nube o sin bucket configurado no se firma nada.
- **R4 · Un solo lugar para los límites.** `app_core/storage/limites.py`; ninguna sala guarda su copia del tamaño máximo.
- **R5 · Sin nombre de proveedor en la interfaz ni en los errores.** Sin nombre de proveedor ni de servicio en los textos que ve el usuario.
- **R6 · CSP.** `frontend/next.config.ts` permite exclusivamente el dominio de subida de GCS.
- **R-ADPA · Ortogonalidad ZERAG (`RET-02`).** Toda invocación a otra sala va por `app_core/pasillo/<otra_sala>.py` (`ImportsCruzados = ∅`, ADR 0001). `verificar_adpa` queda sin importaciones huérfanas.

## 4. Interfaz

Hoja de ruta › tarea › evidencia: el flujo de subir y confirmar no cambia. El cliente (`frontend/src/lib/roadmap/subirEvidencia.ts`, `cliente.ts`, los tipos y el servidor simulado) opera con `clave_objeto` y URLs firmadas V4. Pasa por UX/UI solo si cambia algún texto visible.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** un usuario de la organización A, **cuando** pide la firma de subida, **entonces** la clave empieza por el `tenant_id` de A. Mutación: quitar el `tenant_id` de la clave hace fallar la prueba. | `test_clave_lleva_tenant` |
| **Dado** un usuario de A que confirma una clave con prefijo de B, **entonces** se rechaza y no queda fila. | `test_no_confirma_clave_de_otro_tenant` |
| **Dado** un archivo de tipo o tamaño no admitido, **entonces** se rechaza al pedir la firma y al confirmar. | `test_evidencia_validacion_servidor` |
| **Dado** el almacén sin configurar, **entonces** 503 con motivo neutro y ninguna firma. | `test_almacen_no_configurado_falla_cerrado` |
| **Dado** el árbol del proyecto, **entonces** todo el almacenamiento de evidencias pasa por `app_core/storage/gcs.py` y `app_core/storage/limites.py` con CSP de Google Cloud Storage. | `tests/test_ret02_almacen_gcs.py` |
| **Dado** la tarea de la hoja de ruta, **cuando** se sube una evidencia con el almacén doble, **entonces** queda registrada y visible. | `frontend/tests/roadmap/evidencia.spec.ts` |

## 6. Trazabilidad

- Ficha: `governance/tareas/RET-02.md`.
- Especificación de referencia: `governance/especificaciones/README.md`.
- No se tocan `alembic/versions/` ni las ramas `produccion` y `dev/Aleczandra`. `.github/workflows/` y `verificadores/` son del propietario: si hacen falta, va un brief.
- Depende de RET-01 y de EVI-04, que posee `app_core/storage/gcs.py` y añade `Almacen.subir`.
- Orden con RM-25b, que posee `api/routers/roadmaps.py` y `evidencia_engine.py`.
