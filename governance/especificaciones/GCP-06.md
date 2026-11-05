# GCP-06 · Escalado acotado de Cloud Run, Cloud CDN para activos estáticos, caché de lectura por tenant y prueba de carga reproducible
`¤sdd` `¤escalabilidad` `¤cache-aplicacion` `¤grado-productivo` `¤cloud-run-perf` `¤seguridad-tenant`

## 1. Datos

Escalado `EscaladoServicio` (`servicio: str`, `min_scale: int`, `max_scale: int`, `concurrencia: int`, `conexiones_por_instancia: int`). Entrada de caché `ClaveCache` (`tenant_id: UUID`, `recurso: str`, `version: str`). Informe de carga `InformeCarga` (`usuarios: int`, `p50_ms: float`, `p95_ms: float`, `tasa_error: float`, `fecha: datetime`).

## 2. API

- No crea rutas nuevas. Las respuestas con datos de una organización llevan `Cache-Control: no-store`; los activos de `/_next/static/*` se sirven con `Cache-Control: public, max-age=31536000, immutable` desde Cloud CDN.

## 3. Reglas

- **R1 · Escalado acotado (`INV_CLOUD_RUN_BOUNDED_AUTOSCALING`).** `max_scale × conexiones_por_instancia ≤ límite de conexiones de Cloud SQL` para cada servicio que abre conexiones.
- **R2 · CDN solo para lo público (`INV_EDGE_CACHE_PUBLIC_STATIC_ONLY`).** Ninguna ruta con datos de organización entra en Cloud CDN.
- **R3 · Caché sin fuga entre tenants.** La clave de la caché de lectura incluye `tenant_id` y versión; un cambio de versión invalida la entrada.

## 4. Interfaz

Sin cambios visibles: la interfaz responde más rápido y se mantiene estable bajo carga.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el manifiesto `cloudrun_escalado.yaml`, **cuando** se valida, **entonces** cada servicio declara `min_scale`, `max_scale` y concurrencia y el pool cabe en el límite de Cloud SQL. | `test_escalado_acotado_y_pool_dimensionado` |
| **Dado** una respuesta del backend con datos de una organización, **cuando** se inspeccionan sus cabeceras, **entonces** lleva `Cache-Control: no-store` y no coincide con las rutas de Cloud CDN. | `test_datos_de_organizacion_no_cacheables` |
| **Dado** dos organizaciones que leen el mismo catálogo, **cuando** se consulta la caché de lectura, **entonces** cada una obtiene su propia entrada con su `tenant_id`. | `test_cache_lectura_aislada_por_tenant` |

## 6. Trazabilidad

- PRD_EVYDENTIA_REVENTA_NUBE §5.4 pilares 8 y 9 y criterio 30; invariantes `INV_CLOUD_RUN_BOUNDED_AUTOSCALING` e `INV_EDGE_CACHE_PUBLIC_STATIC_ONLY`.
