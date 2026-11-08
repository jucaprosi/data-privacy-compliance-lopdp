+++
id = "BOV-04"
titulo = "Orquestador Comercial de las 10 Dimensiones y Bóveda Cloud: centro de mando de automatizaciones, retenciones, actas SHA-256 y telemetría de paquete"
ola = "D"
estado = "pendiente"
sala = "boveda_cloud"
depende_de = ["BOV-03", "CCTV-02", "GOVW-01", "GOCA-01", "DLP-01", "VTX-01"]
propiedad = ["features/boveda_cloud/services/orquestador_diez_dimensiones.py", "features/boveda_cloud/boveda_cloud_service.py#BOV-04", "features/boveda_cloud/domain/errores.py#BOV-04", "features/boveda_cloud/routes/orquestador_routes.py", "app_core/pasillo/boveda_cloud.py#BOV-04", "app_core/pasillo/dpo_cockpit.py#BOV-04", "frontend/src/components/layout/menus/index.ts#BOV-04", "frontend/src/components/layout/pantallas/index.tsx#BOV-04", "frontend/src/components/pantallas/BOV-04.tsx", "tests/test_bov04_orquestador_diez_dimensiones.py"]
arbitro = "pytest tests/test_bov04_orquestador_diez_dimensiones.py + suite completa + vigilantes"
rastros = ["¤boveda-cloud", "¤videovigilancia-cctv", "¤dpo-cockpit", "¤conservacion"]
+++
# BOV-04 · Orquestador Comercial de las 10 Dimensiones y Bóveda Cloud: centro de mando de automatizaciones, retenciones, actas SHA-256 y telemetría de paquete

## Entrega
- Servicio `features/boveda_cloud/services/orquestador_diez_dimensiones.py` que consolida en tiempo real el estado operativo de las 10 Dimensiones LOPDP y de la Bóveda Cloud del tenant (cuotas de almacenamiento y Egress, cámaras CCTV conformes y clips en Hold Legal, políticas de purga ejecutadas con sus actas `SHA-256`, escaneos DLP muestreados y estado del caché normativo), sin unificar en un porcentaje global engañoso (`INV_LOPDP_MULTIDIMENSIONAL_METRICS`).
- Publicación del resumen auditable hacia el DPO Cockpit vía `app_core/pasillo/dpo_cockpit.py#BOV-04` y pantalla ejecutiva `frontend/src/components/pantallas/BOV-04.tsx`.

## Pruebas
- `pytest tests/test_bov04_orquestador_diez_dimensiones.py` verifica la agregación multidimensional de las 10 dimensiones + Bóveda Cloud, la ausencia de un porcentaje único global y la entrega de actas `SHA-256` verificables para el DPO.
