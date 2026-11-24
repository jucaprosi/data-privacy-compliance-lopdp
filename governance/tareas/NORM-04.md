+++
id = "NORM-04"
titulo = "El monitoreo de la SPDP descarga de verdad: almacén real de originales, lector real y disparo programado con identidad de servicio"
ola = "backlog"
estado = "pendiente"
tanda = 101
sala = "inteligencia_normativa"
depende_de = ["NORM-01", "NORM-02", "EVI-04", "GCP-01"]
propiedad = ["features/inteligencia_normativa/services/monitoreo.py", "features/inteligencia_normativa/services/almacen_normativo.py", "features/inteligencia_normativa/services/disparo_programado.py", "features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-04", "api/routers/inteligencia_normativa.py#NORM-04", "tests/test_norm04_almacen_y_disparo.py"]
crea = ["features/inteligencia_normativa/services/almacen_normativo.py", "features/inteligencia_normativa/services/disparo_programado.py", "tests/test_norm04_almacen_y_disparo.py"]
arbitro = "pytest tests/test_norm04_almacen_y_disparo.py tests/test_norm01_inteligencia_normativa.py tests/test_norm02_centro_vigilancia.py; mutaciones m1 a m6; tras el despliegue, el propietario lee la bitácora y el bucket (brief)."
rastros = ["¤vigilancia-spdp", "¤inteligencia-normativa", "¤seguridad", "¤arbitro"]
+++

# NORM-04 · El monitoreo de la SPDP descarga de verdad

**Contrato:** `governance/especificaciones/NORM-04.md` (manda sobre esta ficha).

**Origen.** Medición del Arquitecto (2026-11-24) en el PR de BIB-403: el módulo normativo no descarga en ningún entorno. El CTO pidió la ficha aparte. BIB-403 R2 usa sus versiones.

## Entrega
- El almacén real de originales sobre `app_core.storage` (EVI-04), con escritura única en `evydentia-corpus-normativo`.
- El lector real de originales.
- Un disparo programado que solo acepta la identidad de servicio de Cloud Scheduler.
- El brief del propietario para lo de GCP: `C:\Users\Juan Carlos\compartido\evydentia\briefs\NORM-04-propietario-gcp.md`.

## Límites
- Nada en `.github/workflows/` ni en GCP desde la ficha. La URL de la SPDP, el bucket, la cuenta de servicio y el Scheduler los configura el propietario.
- Sin migración. Este PR de gobernanza solo siembra las dos secciones vacías `=== NORM-04 ===`.
