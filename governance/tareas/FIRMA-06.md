+++
id = "FIRMA-06"
titulo = "Firma con ANF STB v2 en ambiente TEST: cliente real y API de envío y sincronización"
ola = "backlog"
estado = "en_curso"
sala = "firma_electronica"
depende_de = ["FIRMA-04", "RM-00", "SEC-05"]
propiedad = ["features/firma_electronica/services/anf_stb_client.py", "features/firma_electronica/services/anf_stb_engine.py", "features/firma_electronica/firma_electronica_service.py#FIRMA-06", "api/routers/firma_anf.py", "app_core/config.py#FIRMA-06", "app_core/errors.py#FIRMA-06", ".env.example#FIRMA-06", "tests/test_firma_anf_stb.py", "governance/especificaciones/FIRMA-06.md"]
arbitro = "pytest tests/test_firma_anf_stb.py contra la rama Neon de la persona + test_ciclo_real_contra_anf_test con ANF_STB_PRUEBA_REAL=1 y credenciales TEST + suite completa + scripts/generar_indice_tareas.py --verificar"
rastros = ["¤firma-electronica", "¤seguridad"]
+++

# FIRMA-06 · Firma con ANF STB v2 en ambiente TEST

**Objetivo.** Consumir de verdad el servicio WS 1 STB v2 de ANF en su ambiente TEST, con `firmar_documento_anf_stb` como método real y `boceto_firmar_documento_anf` como fallback exclusivo de pruebas, y exponer el firmado por API. Las llaves entran por configuración; ninguna vive en código.

**Contrato:** `governance/especificaciones/FIRMA-06.md` (manda sobre esta ficha en rutas, reglas y aceptación).

## Entrega
- Cliente `anf_stb_client` de `POST /auth`, `POST /signs` y `GET /signs/{id}/get-signed-documents`, siempre con `entorno = DEV`.
- Compuerta con `solicitar_firma_anf_stb`, `consultar_firma_anf_stb` y `firmar_documento_anf_stb`.
- Router `api/routers/firma_anf.py` con `enviar` y `sincronizar`. ANF no ofrece webhooks: el nombre inicial de la tarea («router de webhooks») no se corresponde con su API, y el cierre se hace consultando.
- Solo backend y solo TEST: sin frontend, sin producción y sin custodia del PDF firmado en R2.

## Hecho cuando
- Su árbitro pasa, la suite completa pasa y el check `Arnés Físico Determinista` del PR está en verde. No modificó ningún archivo fuera de su propiedad.
