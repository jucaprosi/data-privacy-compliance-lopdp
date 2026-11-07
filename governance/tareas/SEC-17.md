+++
id = "SEC-17"
titulo = "Configuración mínima en la nube: DATABASE_URL de PostgreSQL con lopdp_app y CORS_ORIGINS explícito, sin valores por defecto"
ola = "D"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-15", "SEC-16", "FIRMA-06", "SEC-06", "RM-13"]
propiedad = ["app_core/config.py#SEC-17", "api/index.py", "tests/test_sec17_configuracion_nube.py"]
arbitro = "pytest tests/test_sec17_configuracion_nube.py + suite completa + vigilantes; prueba de mutación documentada"
rastros = ["¤seguridad", "¤rbac-tenant", "¤arbitro"]
+++

# SEC-17 · Configuración mínima en la nube

**Cambio 2026-11-07 (todo en Google Cloud, decisión del propietario):** la nube es Cloud Run. La detección de nube es solo `K_SERVICE`, que Cloud Run define siempre; donde esta ficha dice `VERCEL=1` o `VERCEL_ENV=production`, se lee `K_SERVICE` definida. Se elimina la rama de vistas previas (`VERCEL_ENV=preview`): Cloud Run no tiene vistas previas por PR. «Antes de fusionar» sobre Vercel queda para el PMV congelado; en EVYDENTIA, `DATABASE_URL` y `CORS_ORIGINS` van por servicio en Cloud Run.

**Hallazgo (2026-11-05, preparación de `SEC-16`).** `api/index.py:10-11` y `app_core/config.py:46-47` ponen valores por defecto cuando falta la variable. En la nube, los dos fallan abiertos:
- **`DATABASE_URL`** pasa a `sqlite+aiosqlite:////tmp/test.db`. Un despliegue sin la variable, o con ella mal escrita, arranca contra un SQLite vacío en `/tmp` en lugar de fallar. Nada avisa de que no hay base real.
- **`CORS_ORIGINS`** pasa a `"*"`. `main.py:68-72` monta `CORSMiddleware` con `allow_credentials=True`. Con el comodín, Starlette 1.7 responde con el origen de cada petición, porque la especificación no admite `*` con credenciales. Así cualquier sitio puede hacer peticiones con credenciales a la API y leer sus respuestas.
- **El rol de la base.** El 2026-10-22, producción conectaba con el rol dueño en lugar de `lopdp_app` (`governance/operaciones/CREDENCIALES_Y_ROLES_BD.md`). Nada en el arranque lo impide hoy.

**Contrato:** `INV_LOPDP_CLOUD_CONFIG_FAILS_CLOSED` (`governance/artefactos/INVARIANTS.md`). Principio: Saltzer y Schroeder (1975), «Fail-safe defaults».

## Entrega
- **`app_core/config.py#SEC-17`:** la función `exigir_configuracion_en_la_nube()` se llama junto a la de `SEC-16` y usa `corre_en_la_nube()` de `SEC-15`.
  - En la nube, lanza `RuntimeError` si `DATABASE_URL` falta, no empieza por `postgresql` o su usuario no es `lopdp_app`. El usuario se lee con el analizador de URL, y el mensaje no muestra ni la URL ni la contraseña.
  - En **producción** (`VERCEL_ENV=production` o `K_SERVICE` definida), lanza `RuntimeError` si `CORS_ORIGINS` falta, contiene `*`, tiene un origen vacío, o tiene uno que no empieza por `https://` o que lleva ruta.
  - Las vistas previas de Vercel (`VERCEL_ENV=preview`) quedan fuera de la regla de CORS, porque sus direcciones cambian en cada despliegue. Para ellas sigue valiendo lo que diga `OPS-01`.
  - En una vista previa, `DATABASE_URL` nunca apunta a producción: si `apunta_a_produccion()` (`app_core/huellas_produccion.py`, `SEC-15`) es verdadero con `VERCEL_ENV=preview`, lanza `RuntimeError`. Las vistas previas ejecutan código de PR sin aprobar.
  - Fuera de la nube se conservan los valores de desarrollo de hoy.
- **`api/index.py`:** se retiran los `setdefault` de `DATABASE_URL` y `CORS_ORIGINS`. Ya no queda ninguno, porque `SEC-16` retira el de `JWT_SECRET`. Si algo falla, responde la API de emergencia con 503 `STARTUP_ERROR`.

## Pruebas
- `tests/test_sec17_configuracion_nube.py`:
  - en la nube:
    - sin `DATABASE_URL`: falla;
    - con SQLite: falla;
    - con PostgreSQL y otro usuario (el dueño): falla;
    - con `lopdp_app`: arranca;
    - el mensaje no contiene la URL ni la contraseña;
  - en producción:
    - sin `CORS_ORIGINS`: falla;
    - con `*`: falla;
    - con `http://`: falla;
    - con una lista de `https://` válidos: arranca;
  - en una vista previa (`VERCEL_ENV=preview`), sin `CORS_ORIGINS`: no falla por CORS;
  - en una vista previa, con `DATABASE_URL` de `lopdp_app` en el host de producción: falla;
  - fuera de la nube, sin ninguna variable: arranca, como hoy;
  - importar `api.index` en un subproceso con `VERCEL=1`, `VERCEL_ENV=production` y sin `DATABASE_URL`: `/health` responde 503 `STARTUP_ERROR`.
- Las pruebas usan URL ficticias, nunca credenciales reales.
- Mutación documentada: aceptar `*` en `CORS_ORIGINS`; el caso «con `*`» debe fallar.

## Antes de fusionar
- En Vercel, **Production** del backend debe tener `DATABASE_URL` con `lopdp_app` y `CORS_ORIGINS` con los dominios `https://` del frontend. Se comprueba por nombre con `vercel env ls production` (`PUBLICACION_PMV.md`, paso 2.2). El valor de `CORS_ORIGINS` se revisa en el panel.
- **Preview** del backend no tiene `DATABASE_URL` (comprobado el 2026-11-06 con `vercel env ls`). Si se le da una, es aparte y contra un PostgreSQL 16 local en contenedor, con `lopdp_app`. Sin ella, las vistas previas del backend no arrancan, y es lo esperado. `PROCEDIMIENTO_VERCEL.md`, apartado 5, anotó que Preview no tenía `CORS_ORIGINS`; esta tarea no lo exige.
- **En Google Cloud,** el secreto `DATABASE_URL` debe conectar como `lopdp_app`, no como `evydentia_app`. `evydentia_app` queda como dueño para migrar.

## Límites
- No cambia `main.py` ni la lista de métodos y cabeceras de CORS.
- No cambia la conexión ni el pool de `app_core/db/session.py`.
- No valida que la base responda: eso lo hace `/health` y `verificar_despliegue.py`.
