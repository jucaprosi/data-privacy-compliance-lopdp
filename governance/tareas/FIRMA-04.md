+++
id = "FIRMA-04"
titulo = "API HTTP de firma electrónica y webhook HMAC-SHA256"
ola = "backlog"
estado = "en_curso"
sala = "firma_electronica"
depende_de = ["FIRMA-03"]
propiedad = ["api/routers/firma_electronica.py", "tests/test_firma_router.py"]
arbitro = "pytest tests/test_firma_router.py contra la rama Neon de la persona (incluido RLS con lopdp_app) + suite completa + scripts/generar_indice_tareas.py --verificar"
rastros = ["¤firma-electronica", "¤seguridad"]
+++

# FIRMA-04 · API HTTP de firma electrónica y webhook HMAC-SHA256

**Objetivo.** Exponer la sala `firma_electronica` mediante cuatro endpoints REST y un webhook público autenticado por HMAC-SHA256, sin nueva migración: todo acceso a datos pasa por la compuerta `firma_electronica_service` (FIRMA-03).

**Contrato:** `governance/especificaciones/FIRMA-04.md` (manda sobre esta ficha en rutas, reglas y aceptación).

## Entrega
- Router FastAPI `api/routers/firma_electronica.py` con `AUTO_REGISTRO = True` y prefijo `/firma`.
- Tres endpoints de sesiones (crear, obtener, listar) resueltos con el tenant autenticado.
- Endpoint de webhook público (`POST /firma/webhook`) autenticado únicamente por HMAC-SHA256 del cuerpo con la variable de entorno `FIRMA_WEBHOOK_SECRET`; falla cerrada: sin secreto configurado o sin firma siempre devuelve 401.
- Siete pruebas HTTP contra la base de datos real (sin mocks de BD), con prueba de mutación documentada sobre `hmac.compare_digest`.
- Solo backend: sin frontend ni integración real con ANF o UniverselD.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad.
