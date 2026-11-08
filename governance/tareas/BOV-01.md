+++
id = "BOV-01"
titulo = "Sala Bóveda Cloud: paquetes de reventa de almacenamiento, cuotas de GB/Egress y aprovisionamiento Multi-Tenant"
ola = "D"
estado = "pendiente"
sala = "boveda_cloud"
depende_de = ["ADPA-06", "ADPA-07", "GCP-01"]
propiedad = ["alembic/versions/20260501_01_bov01_boveda_paquetes_cuotas.py", "features/boveda_cloud/__init__.py", "features/boveda_cloud/models.py", "features/boveda_cloud/schemas.py", "features/boveda_cloud/boveda_cloud_service.py#BOV-01", "features/boveda_cloud/domain/__init__.py", "features/boveda_cloud/domain/errores.py#BOV-01", "features/boveda_cloud/routes/__init__.py", "features/boveda_cloud/routes/boveda_paquetes_routes.py", "app_core/pasillo/boveda_cloud.py#BOV-01", "main.py#BOV-01", "frontend/src/components/layout/menus/index.ts#BOV-01", "frontend/src/components/layout/pantallas/index.tsx#BOV-01", "frontend/src/components/layout/pantallas/BOV-01.tsx", "tests/test_bov01_paquetes_cuotas.py"]
arbitro = "pytest tests/test_bov01_paquetes_cuotas.py + suite completa + vigilantes"
rastros = ["¤boveda-cloud", "¤seguridad-tenant", "¤adpa"]
+++
# BOV-01 · Sala Bóveda Cloud: paquetes de reventa de almacenamiento, cuotas de GB/Egress y aprovisionamiento Multi-Tenant

## Entrega
- Tabla `boveda_suscripciones_tenant` con RLS forzado por `tenant_id` (`paquete_codigo`, `cuota_almacenamiento_bytes`, `uso_almacenamiento_bytes`, `cuota_egress_mensual_bytes`, `uso_egress_mensual_bytes`, `certificaciones_heredadas` JSONB con ISO 27001/27701/SOC 2, `estado` en `{ACTIVA, CUOTA_EXCEDIDA, SUSPENDIDA}`).
- Compuerta `features/boveda_cloud/boveda_cloud_service.py#BOV-01`, errores `features/boveda_cloud/domain/errores.py#BOV-01` (`BOVEDA_CUOTA_ALMACENAMIENTO_EXCEDIDA`, `BOVEDA_CUOTA_EGRESS_EXCEDIDA`, `BOVEDA_SUSCRIPCION_NO_ENCONTRADA`) y pasillo `app_core/pasillo/boveda_cloud.py#BOV-01`.
- Router `/api/v1/boveda-cloud/suscripcion` y pantalla `frontend/src/components/layout/pantallas/BOV-01.tsx` con medidores de consumo de almacenamiento y transferencia mensual.

## Pruebas
- `pytest tests/test_bov01_paquetes_cuotas.py` verifica el alta de paquete de nube por organización, el bloqueo con 409 `BOVEDA_CUOTA_EGRESS_EXCEDIDA` al superar el límite mensual de descarga y el aislamiento RLS entre inquilinos.
