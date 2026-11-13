+++
id = "GCP-06"
titulo = "Caché sin fuga entre organizaciones: Cloud CDN solo para activos estáticos y caché de lectura por tenant en Memorystore"
ola = "C"
estado = "en_curso"
sala = "pasillo_central, operaciones"
depende_de = ["GCP-05"]
propiedad = ["app_core/cache/__init__.py", "app_core/cache/cache_lectura.py", "governance/operaciones/cloud_cdn.yaml", "tests/test_gcp06_cache.py"]
arbitro = "pytest tests/test_gcp06_cache.py + suite completa + vigilantes"
rastros = ["¤cloud-run-perf", "¤seguridad-tenant"]
+++
# GCP-06 · Caché sin fuga entre organizaciones: Cloud CDN solo para activos estáticos y caché de lectura por tenant en Memorystore

## Entrega
- Manifiesto `governance/operaciones/cloud_cdn.yaml` que activa Cloud CDN solo para `/_next/static/*` en el balanceador de `GCP-04`.
- Módulo `app_core/cache/cache_lectura.py` con caché de lectura en Memorystore cuya clave incluye siempre `tenant_id` y versión del recurso, para catálogos y paquetes normativos, con invalidación al cambiar la versión.
- Cabecera `Cache-Control: no-store` en toda respuesta con datos de una organización, y `public, max-age=31536000, immutable` en los activos estáticos.

## Pruebas
- `pytest tests/test_gcp06_cache.py` comprueba que Cloud CDN solo cubre activos estáticos, que las respuestas con datos de organización llevan `Cache-Control: no-store` y que la clave de caché incluye `tenant_id` y versión (`INV_EDGE_CACHE_PUBLIC_STATIC_ONLY`).
