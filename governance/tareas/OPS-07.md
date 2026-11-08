+++
id = "OPS-07"
titulo = "Observabilidad: registro estructurado sin datos personales, errores, disponibilidad y alertas de gasto"
ola = "C"
estado = "hecha"
sala = "pasillo_central, operaciones"
depende_de = ["GCP-01"]
propiedad = ["app_core/observabilidad/__init__.py", "app_core/observabilidad/registro.py", "api/middleware/correlacion.py", "main.py#OPS-07", "governance/operaciones/monitoreo/alertas.json", "governance/operaciones/OBSERVABILIDAD.md", "tests/test_ops07_observabilidad.py"]
arbitro = "pytest tests/test_ops07_observabilidad.py + suite completa + vigilantes"
rastros = ["¤observabilidad", "¤seguridad-tenant", "¤cloud-run-perf"]
+++
# OPS-07 · Observabilidad: registro estructurado sin datos personales, errores, disponibilidad y alertas de gasto

**Origen.** Revisión de la constitución de la reventa en la nube contra los diez requisitos de una aplicación vendible, 2026-11-04. Hoy solo hay un registro JSON en `main.py` y `/health`; no hay captura de errores, trazas, comprobación de disponibilidad ni alertas. Las menciones de «monitoreo» del PRD son de la vigilancia normativa de la SPDP, no de la salud de la plataforma.

**Contrato:** `governance/especificaciones/OPS-07.md`.

## Entrega
- Registro estructurado en `app_core/observabilidad/registro.py`, compatible con Cloud Logging: severidad, `request_id`, `tenant_id`, ruta, código y duración. Antes de escribir, todo mensaje pasa por el saneador DLP existente (`app_core/dlp_sanitizer.py`): ninguna cédula, RUC, correo ni teléfono llega al registro.
- Middleware `api/middleware/correlacion.py` que asigna o propaga `X-Request-ID`. La configuración del registro sale de `main.py` y queda en la sección `#OPS-07`, con el middleware registrado allí.
- Errores no controlados en formato que Error Reporting agrupa, con la traza saneada.
- Políticas como código en `governance/operaciones/monitoreo/alertas.json`: comprobación de disponibilidad de `/health`, tasa de 5xx, latencia p95, presupuesto de facturación al 50, 90 y 100 % y gasto diario de Vertex AI.
- Guía `governance/operaciones/OBSERVABILIDAD.md`: qué alerta existe, a quién avisa, cómo leer un incidente y cuánto se conservan los registros.

## Decisiones asumidas
- Se conservan los registros 30 días, el período por defecto de Cloud Logging; los registros no son evidencia probatoria (la evidencia va a la Bóveda).
- El identificador de usuario se registra como identificador interno, nunca el correo.

## Pruebas
- `pytest tests/test_ops07_observabilidad.py` comprueba el formato JSON, la propagación del `X-Request-ID`, el saneamiento de datos personales en mensajes y trazas, y que `alertas.json` declara las cinco políticas.
