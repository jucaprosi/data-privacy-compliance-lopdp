+++
id = "RET-02"
titulo = "Almacén de evidencias del roadmap en Google Cloud Storage"
ola = "backlog"
estado = "pendiente"
sala = "roadmap, evidencias"
depende_de = ["RET-01", "EVI-04", "RM-18", "RM-22", "RM-25a", "RM-25c"]
propiedad = ["api/routers/roadmaps.py", "features/roadmap/services/evidencia_engine.py", "app_core/storage/r2.py", "app_core/storage/gcs.py", "app_core/storage/limites.py", "features/evidencias/services/evidencias_engine.py", "features/evidencias/services/custodia_generados_engine.py", "features/evidencias/services/paquete_inspeccion_engine.py", "frontend/next.config.ts", "frontend/src/lib/roadmap/cliente.ts", "frontend/src/lib/roadmap/mockServer.ts", "requirements.txt", "tests/test_ret02_almacen_gcs.py", "tests/test_evidencias_subida_firmada.py", "tests/test_evidencia_validacion_servidor.py", "frontend/tests/roadmap/evidencia.spec.ts", "tests/plataforma_unica/pendientes/RET-02.txt"]
crea = ["app_core/storage/limites.py", "tests/test_ret02_almacen_gcs.py"]
arbitro = "pytest tests/test_ret02_almacen_gcs.py tests/test_evidencias_subida_firmada.py tests/test_evidencia_validacion_servidor.py contra un PostgreSQL 16 local + Playwright de frontend/tests/roadmap/evidencia.spec.ts + tsc --noEmit + suite completa; prueba de mutación documentada"
rastros = ["¤evidencias", "¤roadmap", "¤seguridad-tenant"]
+++

# RET-02 · Almacén de evidencias en Google Cloud Storage

Diseño del Arquitecto ADPA (2026-11-13): `governance/especificaciones/RET-02.md`. Modelo sugerido: **opus** (la clave del objeto es el aislamiento entre organizaciones). Va después de RET-01 y de EVI-04, que añade `Almacen.subir` en `app_core/storage/gcs.py`.

**Problema.** La evidencia de la hoja de ruta usa un almacén distinto del que usa la sala evidencias. Debe usar el `Almacen` de `app_core/storage` (GCS, `FirmaSubida`), con la clave armada por el servidor con el `tenant_id` de la sesión.

**Entrega.**
- `api/routers/roadmaps.py` y `evidencia_engine.py` pasan al `Almacen` común; las rutas conservan su forma y cambian solo el dominio de la URL y los nombres de campo.
- `app_core/storage/limites.py` (nuevo) concentra `TAMANO_MAXIMO_BYTES` y `motivo_de_rechazo`; los usuarios actuales cambian su import (`evidencias_engine`, `custodia_generados_engine`, `paquete_inspeccion_engine`).
- Se retira `app_core/storage/r2.py` y `boto3` de `requirements.txt`; la CSP de `frontend/next.config.ts` permite el dominio de subida de GCS.
- Falla cerrado si no hay bucket configurado (503 con código neutro).

**Orden.** RM-25b, que posee `api/routers/roadmaps.py` y `evidencia_engine.py`, va después de esta ficha. RET-03 también va después (comparte router y cliente). Si `features/evidencias/evidencias_service.py` necesita cambiar su import, va por una sección propia después de EVI-04.

