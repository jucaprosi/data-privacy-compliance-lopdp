+++
id = "GCP-08"
titulo = "Frontend en Cloud Run: proxy de /api/v1 con BACKEND_URL leída en cada petición, /health e imagen de menos de 120 MB"
ola = "D"
estado = "en_curso"
sala = "frontend, operaciones"
depende_de = ["GCP-03"]
propiedad = ["frontend/Dockerfile.cloudrun", "frontend/next.config.cloudrun.ts", "governance/operaciones/cloudrun_frontend_service.yaml", "frontend/src/app/api/v1/[...ruta]/route.ts", "frontend/src/app/health/route.ts", "tests/test_gcp08_proxy_e_imagen.py"]
crea = ["frontend/src/app/api/v1/[...ruta]/route.ts", "frontend/src/app/health/route.ts", "tests/test_gcp08_proxy_e_imagen.py"]
arbitro = "pytest tests/test_gcp08_proxy_e_imagen.py tests/test_gcp03_frontend_cloudrun.py tests/test_gcp03_app_env_por_servicio.py + docker build y medición de la imagen + python scripts/generar_indice_tareas.py --verificar"
rastros = ["¤arbitro"]
+++

# GCP-08 · Proxy en tiempo de ejecución, /health e imagen ligera

Validada por el Arquitecto ADPA y revisada por Seguridad (2026-11-08), con los cambios recogidos abajo. Antes de desplegar, el propietario decide la autenticación hacia Cloud Run (punto 4 de Seguridad).

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

## Revisión de Seguridad (2026-11-08): apta para el reparto con 1 a 4
**Obligatorios:**
1. **SSRF y salida de ruta:** el destino se arma con `new URL(BACKEND_URL)`, el prefijo fijo `/api/v1/` y cada segmento pasado por `encodeURIComponent`. Los segmentos `..`, `.` y vacíos se rechazan con 400, también codificados (`%2e%2e`, `%2f`). El origen final tiene que coincidir con el de `BACKEND_URL`. **Prueba 12:** `/api/v1/..%2f..%2fadmin` y `/api/v1//otro.host` no salen del backend.
2. **`redirect: 'manual'`:** el proxy no sigue un 3xx; lo devuelve tal cual, y `Location` entra en la lista de respuesta. **Prueba 13.**
3. **Caché:** a la lista de respuesta se suman `Cache-Control`, `Vary`, `X-Content-Type-Options` y `WWW-Authenticate`. Si el backend no manda `Cache-Control`, `/api/v1` responde `Cache-Control: no-store` por defecto; con Cloud CDN (GCP-06), una respuesta con datos personales no puede quedar en caché. **Prueba 14:** la descarga conserva `no-store, private`. **M7:** quitar `Cache-Control` de la lista hace fallar la 14.
4. **Autenticación hacia Cloud Run:** si el backend exige IAM (`roles/run.invoker`), Cloud Run consume `Authorization`. **Lo decide el propietario** y va en el brief; las dos opciones son:
   - backend con ingress interno o del balanceador, y sin IAM;
   - token de servicio en `X-Serverless-Authorization`, con `Authorization` intacto.

   La implementación admite las dos. El token de servicio se obtiene del servidor de metadatos y nunca sale del cliente.

**Recomendaciones que se adoptan:**
5. **Registros:** solo método, ruta sin query, estado y `X-Request-ID`. Nunca la query, porque la descarga de SEC-19 lleva `?token=`.
6. **Límite por IP (SEC-13):** detrás del proxy, las peticiones anónimas comparten la IP de salida del frontend y caen en una sola cubeta. **Se asume y se anota** en esta ficha. Pasar la IP del cliente de forma confiable queda para una ficha futura. No se reenvía el `X-Forwarded-For` del cliente.
7. **Plazos y métodos:**
   - el fetch lleva `AbortSignal.timeout` y responde 504 sin detalle cuando se agota;
   - el cuerpo de la petición va en streaming (`duplex: 'half'`);
   - solo se aceptan GET, HEAD, POST, PUT, PATCH y DELETE; el resto responde 405.
8. **`BACKEND_URL` en la nube:** con `K_SERVICE` tiene que ser https o el host interno; si no, 503. Nunca se deriva de la petición.
9. **Cookies:** `Cookie` y `Set-Cookie` quedan fuera de las dos listas. El descarte de `X-User-ID` es una segunda capa; la primera es que el backend no arranca con `AUTH_MODE=headers` en la nube (`app_core/security.py:55`).

**Nota para el brief del propietario:** SEC-17 sigue exigiendo en el backend un `CORS_ORIGINS` https no vacío, con el dominio del frontend.

**Nota del CTO para el brief del propietario (punto 6):** con el balanceador de GCP-04, `/api/*` va directo al backend y no pasa por el proxy. La cubeta compartida por IP solo existe mientras no hay balanceador, y en ese tramo un cliente anónimo puede agotar el cupo de todos, incluido el login. **El corte a producción va con el balanceador, no con el proxy.**
