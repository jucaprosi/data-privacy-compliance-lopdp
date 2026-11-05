+++
id = "GCP-05"
titulo = "Observabilidad nativa: registro JSON sin datos personales en Cloud Logging, Cloud Trace, Error Reporting, comprobaciones de disponibilidad y alertas de SLO y de presupuesto"
ola = "C"
estado = "pendiente"
sala = "pasillo_central, operaciones"
depende_de = ["GCP-01"]
propiedad = ["app_core/observabilidad/__init__.py", "app_core/observabilidad/registro.py", "app_core/observabilidad/trazas.py", "governance/operaciones/monitoreo_alertas.yaml", "tests/test_gcp05_observabilidad.py"]
arbitro = "pytest tests/test_gcp05_observabilidad.py + suite completa + vigilantes"
rastros = ["¤cloud-run-perf", "¤seguridad", "¤adpa"]
+++
# GCP-05 · Observabilidad nativa: registro JSON sin datos personales en Cloud Logging, Cloud Trace, Error Reporting, comprobaciones de disponibilidad y alertas de SLO y de presupuesto

## Entrega
- Módulo `app_core/observabilidad/registro.py` con un formateador JSON compatible con Cloud Logging (`severity`, `message`, `tenant_id`, `request_id`, `ruta`, `codigo`, `latencia_ms`, `logging.googleapis.com/trace`) que redacta cédulas y RUC válidos por Módulo 10, correos y teléfonos antes de emitir cada registro.
- Módulo `app_core/observabilidad/trazas.py` con un middleware ASGI que propaga `X-Cloud-Trace-Context`, asigna `request_id` y mide la latencia por ruta, sin leer cuerpos de petición ni de respuesta.
- Manifiesto `governance/operaciones/monitoreo_alertas.yaml` con comprobaciones de disponibilidad sobre `/health` del frontend y del backend, políticas de alerta de SLO (disponibilidad mensual ≥ 99,5 % y 5xx < 1 %), presupuestos de Cloud Billing al 50, 80 y 100 % para Vertex AI y Cloud Storage, y su canal de notificación.

## Pruebas
- `pytest tests/test_gcp05_observabilidad.py` comprueba el formato JSON de cada registro, la redacción de datos personales (`INV_OBS_STRUCTURED_LOGS_NO_PERSONAL_DATA`) y que el manifiesto declara disponibilidad, SLO, presupuestos y canal (`INV_OBS_SLO_UPTIME_AND_BUDGET_ALERTS`).
