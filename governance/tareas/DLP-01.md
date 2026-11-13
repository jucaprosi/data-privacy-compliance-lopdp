+++
id = "DLP-01"
titulo = "Sala Descubrimiento DLP Muestreado: escaneo de archivos y tablas con Cloud DLP Sampling y validador Módulo 10 para poblar el RAT"
ola = "D"
estado = "en_curso"
sala = "dlp_discovery"
depende_de = ["ADPA-06", "ADPA-07", "GCP-01", "MARCA-01"]
propiedad = ["alembic/versions/dlp01_escaneos_muestreados.py", "features/dlp_discovery/__init__.py", "features/dlp_discovery/models.py", "features/dlp_discovery/schemas.py", "features/dlp_discovery/dlp_discovery_service.py#DLP-01", "features/dlp_discovery/domain/__init__.py", "features/dlp_discovery/domain/errores.py#DLP-01", "features/dlp_discovery/services/__init__.py", "features/dlp_discovery/services/cloud_dlp_sampler.py", "features/dlp_discovery/routes/__init__.py", "features/dlp_discovery/routes/dlp_discovery_routes.py", "app_core/pasillo/dlp_discovery.py#DLP-01", "app_core/pasillo/rat.py#DLP-01", "main.py#DLP-01", "frontend/src/components/layout/menus/index.ts#DLP-01", "frontend/src/components/layout/pantallas/index.tsx#DLP-01", "frontend/src/components/layout/pantallas/DLP-01.tsx", "tests/test_dlp01_sampling_discovery.py"]
arbitro = "pytest tests/test_dlp01_sampling_discovery.py + suite completa + vigilantes"
rastros = ["¤dlp-muestreo", "¤rat", "¤seguridad-tenant"]
+++
# DLP-01 · Sala Descubrimiento DLP Muestreado: escaneo de archivos y tablas con Cloud DLP Sampling y validador Módulo 10 para poblar el RAT

## Entrega
- Tabla `dlp_escaneos_muestreados` con RLS forzado por `tenant_id` (`origen_objeto_id`, `tamano_muestra_filas`, `infotypes_detectados` JSONB acotado a `EC_CEDULA_MOD10`, `EC_RUC`, `EMAIL`, `TELEFONO`, `DATOS_SALUD`, `nivel_sensibilidad`, `sugerencia_rat_generada` BOOL).
- Motor `features/dlp_discovery/services/cloud_dlp_sampler.py` que combina el validador determinista Módulo 10 de cédula ecuatoriana con muestreo acotado (*sampling* <= 500 filas / fragmentos) hacia Sensitive Data Protection (Cloud DLP), sin almacenar jamás los datos personales crudos hallados.
- Integración vía `app_core/pasillo/rat.py#DLP-01` para sugerir o auditar categorías de datos en las actividades del RAT y pantalla `frontend/src/components/layout/pantallas/DLP-01.tsx`.

## Pruebas
- `pytest tests/test_dlp01_sampling_discovery.py` verifica que el muestreo detecta cédulas ecuatorianas válidas (Módulo 10) y categorías sensibles en una fracción del archivo sin persistir el dato personal en claro y respetando el límite de muestreo.

## Decisiones del Tech Lead (2026-11-13)
- Manda `governance/especificaciones/DLP-01.md`: infoTypes PHONE y SALUD; CHECK `limite_muestra <= 1000`; columnas `fuente_nombre`, `limite_muestra`, `contiene_datos_sensibles` y `actividad_rat_id`, sin `nivel_sensibilidad`. Donde la ficha diga otra cosa, prevalece la especificación.
- Se entregan el puerto y el doble. El adaptador real queda desactivado y falla cerrado hasta que el propietario lo autorice con su brief y el CTO decida la región y el encargo.
- Modelo: sube a opus por riesgo alto (cédulas y datos de salud).
