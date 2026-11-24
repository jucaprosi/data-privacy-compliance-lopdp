+++
id = "NORM-04"
titulo = "El monitoreo de la SPDP descarga de verdad: un Cloud Run Job con la cuenta del monitoreo escribe los originales y el backend solo los lee"
ola = "backlog"
estado = "pendiente"
tanda = 101
sala = "inteligencia_normativa"
depende_de = ["NORM-01", "NORM-02", "EVI-04", "GCP-01"]
propiedad = ["features/inteligencia_normativa/services/monitoreo.py", "features/inteligencia_normativa/services/almacen_normativo.py", "features/inteligencia_normativa/trabajo_monitoreo.py", "features/inteligencia_normativa/inteligencia_normativa_service.py#NORM-04", "tests/test_norm04_almacen_y_trabajo.py"]
crea = ["features/inteligencia_normativa/services/almacen_normativo.py", "features/inteligencia_normativa/trabajo_monitoreo.py", "tests/test_norm04_almacen_y_trabajo.py"]
arbitro = "pytest tests/test_norm04_almacen_y_trabajo.py tests/test_norm01_inteligencia_normativa.py tests/test_norm02_centro_vigilancia.py; mutaciones m1 a m6; tras crear el Job, el propietario lee la bitácora y el bucket (brief)."
rastros = ["¤vigilancia-spdp", "¤inteligencia-normativa", "¤seguridad", "¤arbitro"]
+++

# NORM-04 · El monitoreo de la SPDP descarga de verdad

**Contrato:** `governance/especificaciones/NORM-04.md` (manda sobre esta ficha).

**Origen.** Medición del Arquitecto (2026-11-24): el módulo normativo no descarga en ningún entorno. Diseño del bucket y de la cuenta del monitoreo de NORM-01 (`governance/operaciones/BRIEF_PROPIETARIO_BUCKET_NORMATIVO.md`, 2026-11-12, decisiones 4, 5 y 8), ya ejecutado por el propietario.

## Entrega
- El almacén real de originales sobre `app_core.storage` (EVI-04), con escritura única en `evydentia-corpus-normativo`. Solo lo usa el Job del monitoreo.
- El lector real de originales para el backend, que solo lee.
- El punto de entrada `python -m features.inteligencia_normativa.trabajo_monitoreo` que ejecuta el Cloud Run Job `evydentia-monitoreo-normativo` con la cuenta `sa-evydentia-normativa`, disparado por Cloud Scheduler.
- El brief del propietario: `C:\Users\Juan Carlos\compartido\evydentia\briefs\NORM-04-propietario-gcp.v3.md`.

## Límites
- Sin rutas nuevas en la API: el disparo manual del operador (`POST /api/v1/normativa/monitoreo`) no cambia.
- Nada en `.github/workflows/` ni en GCP desde la ficha. Sin migración.
