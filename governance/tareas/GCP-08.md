+++
id = "GCP-08"
titulo = "Frontend en Cloud Run: proxy de /api/v1 con BACKEND_URL leída en cada petición, /health e imagen de menos de 120 MB"
ola = "D"
estado = "pendiente"
sala = "frontend, operaciones"
depende_de = ["GCP-03"]
propiedad = ["frontend/Dockerfile.cloudrun", "frontend/next.config.cloudrun.ts", "governance/operaciones/cloudrun_frontend_service.yaml", "frontend/src/app/api/v1/[...ruta]/route.ts", "frontend/src/app/health/route.ts", "tests/test_gcp08_proxy_e_imagen.py"]
crea = ["frontend/src/app/api/v1/[...ruta]/route.ts", "frontend/src/app/health/route.ts", "tests/test_gcp08_proxy_e_imagen.py"]
arbitro = "pytest tests/test_gcp08_proxy_e_imagen.py tests/test_gcp03_frontend_cloudrun.py tests/test_gcp03_app_env_por_servicio.py + docker build y medición de la imagen + python scripts/generar_indice_tareas.py --verificar"
rastros = ["¤arbitro"]
+++

# GCP-08 · Proxy en tiempo de ejecución, /health e imagen ligera

Validada por el Arquitecto ADPA (2026-11-08) con cambios, recogidos abajo. **Seguridad revisa antes del reparto**, porque cambia por dónde viaja la identidad.

**Origen (2026-11-08).** GCP-03 (#488) quedó con dos criterios que solo estaban en el brief:
- Next fija los rewrites de `/api/v1` al compilar, así que con una sola imagen `BACKEND_URL` por servicio no cambia el destino.
- La imagen pesa 310 MB y la meta era menos de 120.

Además, no hay `/health`, y las sondas usan `/robots.txt`. Estos criterios van aquí como **pruebas**, para que el árbitro los compruebe.

## Entrega
- `frontend/src/app/api/v1/[...ruta]/route.ts`: un route handler que reenvía método, ruta, query, cuerpo y cabeceras de identidad (`Authorization`, `X-Tenant-ID`, `X-Role`) a `process.env.BACKEND_URL`, leída en cada petición. Sin `BACKEND_URL` en la nube (`K_SERVICE`) responde 503 sin detalles. No reenvía `Host` ni cabeceras hop-by-hop, y no registra cuerpos ni tokens.
- `next.config.cloudrun.ts`: sin rewrites de `/api/v1`; standalone.
- `frontend/src/app/health/route.ts`: 200 `{"estado":"ok"}`, sin llamar al backend. Las sondas de `cloudrun_frontend_service.yaml` pasan a `/health`.
- `Dockerfile.cloudrun`: imagen de menos de 120 MB (base mínima, solo `.next/standalone`, `static` y `public`, sin `node_modules` completos).

## Pruebas (`tests/test_gcp08_proxy_e_imagen.py`)
1. **Proxy en tiempo de ejecución:** la misma imagen compilada, arrancada con dos `BACKEND_URL` distintas (dos servidores simulados), reenvía cada vez al que corresponde.
2. Se reenvían las cabeceras de identidad, y no se reenvía `Host`.
3. Sin `BACKEND_URL` y con `K_SERVICE`: 503.
4. `/health` responde 200 sin tráfico al backend.
5. **Tamaño medido:** `docker image inspect` da menos de 120 MB. La prueba se salta solo si no hay Docker, y en ese caso el CI la exige.
6. El YAML del servicio usa `/health` en las sondas de arranque y de vida.
- Mutaciones: M1, volver a los rewrites al compilar, hace fallar la 1; M2, copiar `node_modules` completos, hace fallar la 5.

Fuera de alcance: aplicar en Cloud Run. Va como brief para el propietario y Antigravity.

## Cambios del Arquitecto (2026-11-08); prevalecen sobre la Entrega
- **Petición, lista permitida explícita** (no una lista negra): `Authorization`, `X-Tenant-ID`, `X-Role`, `Content-Type` (JSON y multipart), `Accept`, `Range` y `X-Request-ID` (lo exige la correlación de OPS-07, `api/middleware/correlacion.py`). Con `K_SERVICE` se descarta `X-User-ID`: el modo «headers» de desarrollo la envía (`lib/auth/cabeceras.ts:42`), y en la nube sería suplantación.
- **Respuesta:** devuelve el estado (incluido 206) y las cabeceras `Content-Type`, `Content-Disposition`, `Content-Range`, `Accept-Ranges`, `X-Content-SHA256`, `Retry-After` (el 429 de SEC-13) y `X-Request-ID`. El cuerpo va en streaming, sin `json()` ni `text()`, para no corromper los binarios (biblioteca, niif18, rat_exportacion e informes PDF).
- **Pruebas nuevas:**
  - 7: un binario con bytes no UTF-8 llega idéntico y con su `Content-Disposition`;
  - 8: `X-Request-ID` se conserva de ida y de vuelta;
  - 9: con `K_SERVICE`, `X-User-ID` no llega al backend;
  - 10: un POST JSON llega con su `Content-Type` y su cuerpo, y un 429 vuelve con `Retry-After`;
  - 11: una petición con `Range` recibe 206 con su `Content-Range` (y `Accept-Ranges`), y el cuerpo parcial llega intacto.
- **Mutaciones nuevas:**
  - M3: leer el cuerpo como texto hace fallar la 7;
  - M4: reenviar todas las cabeceras hace fallar la 9 y la de `Host`;
  - M5: reenviar solo las cabeceras de identidad hace fallar la 7 y la 10;
  - M6: no devolver `Content-Range` hace fallar la 11.
- **Decisión del Tech Lead:** el CTO pedía reenviar todas las cabeceras salvo `Host` y las hop-by-hop. Se adopta la lista permitida del Arquitecto, ampliada con `Range`, `Retry-After`, `Content-Range` y `Accept-Ranges`; decisión del propietario, 2026-11-08, porque una lista negra dejaría pasar `X-User-ID` y cualquier cabecera nueva.
