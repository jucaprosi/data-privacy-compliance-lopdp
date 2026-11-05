# GCP-06 · Caché sin fuga entre organizaciones: Cloud CDN solo para activos estáticos y caché de lectura por tenant en Memorystore
`¤sdd` `¤cache-aplicacion` `¤grado-productivo` `¤cloud-run-perf` `¤seguridad-tenant`

## 1. Datos

Entrada de caché `ClaveCache` (`tenant_id: UUID`, `recurso: str`, `version: str`). Manifiesto `cloud_cdn.yaml` (`rutas_cacheables: list[str]`, `ttl_s: int`).

## 2. API

- No crea rutas nuevas. Las respuestas con datos de una organización llevan `Cache-Control: no-store`; los activos de `/_next/static/*` se sirven con `Cache-Control: public, max-age=31536000, immutable` desde Cloud CDN.

## 3. Reglas

- **R1 · CDN solo para lo público (`INV_EDGE_CACHE_PUBLIC_STATIC_ONLY`).** Ninguna ruta con datos de organización entra en Cloud CDN.
- **R2 · Caché sin fuga entre tenants.** La clave de la caché de lectura incluye `tenant_id` y versión; un cambio de versión invalida la entrada.
- **R3 · Complemento de GCP-05.** El escalado y la prueba de carga pertenecen a `GCP-05`; esta tarea no toca sus manifiestos.

## 4. Interfaz

Sin cambios visibles: la interfaz responde más rápido y se mantiene estable bajo carga.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el manifiesto `cloud_cdn.yaml`, **cuando** se valida, **entonces** solo declara rutas bajo `/_next/static/`. | `test_cdn_solo_activos_estaticos` |
| **Dado** una respuesta del backend con datos de una organización, **cuando** se inspeccionan sus cabeceras, **entonces** lleva `Cache-Control: no-store`. | `test_datos_de_organizacion_no_cacheables` |
| **Dado** dos organizaciones que leen el mismo catálogo, **cuando** se consulta la caché de lectura, **entonces** cada una obtiene su propia entrada con su `tenant_id`. | `test_cache_lectura_aislada_por_tenant` |

## 6. Trazabilidad

- PRD_EVYDENTIA_REVENTA_NUBE §5.4 pilar 8 y criterio 30; invariante `INV_EDGE_CACHE_PUBLIC_STATIC_ONLY`.
