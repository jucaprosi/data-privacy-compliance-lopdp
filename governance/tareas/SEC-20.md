+++
id = "SEC-20"
titulo = "La huella de producción reconoce Cloud SQL: función pura por la URL y comprobación de la base en la guardia, con marcador en las bases que no son producción"
ola = "indep"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-15", "EP-01", "EP-11"]
propiedad = ["app_core/huellas_produccion.py", "app_core/entorno/guardias.py", "tests/test_ep01_guardias_entorno.py", "tests/test_sec20_huella_cloudsql.py"]
crea = ["tests/test_sec20_huella_cloudsql.py"]
arbitro = "pytest tests/test_sec20_huella_cloudsql.py tests/test_ep01_guardias_entorno.py + suite completa; mutaciones M1 a M3 documentadas; revisión de Seguridad antes del reparto"
rastros = ["¤seguridad-tenant", "¤arbitro"]
+++

# SEC-20 · La huella de producción también cubre Cloud SQL

**Origen.** Nota del CTO del 2026-11-08. `apunta_a_produccion()` solo reconoce el host de Neon de producción. Tras el corte a Cloud SQL, la base de producción se alcanza por el conector o por `cloud-sql-proxy` en `127.0.0.1`, y ni la guardia de EP-11 ni la de EP-03 la detectarían. Diseño del Arquitecto ADPA (2026-11-08).

## Entrega
1. **`apunta_a_produccion(url)` sigue pura, sin E/S.** La llaman `security.py` al arrancar, `crear_organizacion_dev.py` y `sembrar_entorno_pruebas.py`; si abriera una conexión, un proceso sin base (pruebas unitarias, build, arranque sin red) se trataría como producción. Ahora reconoce también la instancia `evydentia:us-central1:evydentia-production` en `host=/cloudsql/…`, en `unix_sock` y en la variable del conector (`INSTANCE_CONNECTION_NAME` o la que use el despliegue).
2. **Función nueva `base_es_produccion(conexion) -> bool`**, en el mismo archivo. Recibe una conexión ya abierta y no la crea.
   - **Marcador invertido:** las bases que **no** son producción tienen la tabla `entorno_marcador(valor)` con `'pruebas'` o `'demo'`.
   - Sin marcador, con otro valor o con un error o tiempo agotado: **producción** (falla cerrado). Producción no se toca.
   - No se usa `inet_server_addr()`: detrás del proxy o del conector devuelve la IP del socket.
3. **La guardia** (`app_core/entorno/guardias.py`) llama a `base_es_produccion` cuando `APP_ENV` es `demo` o `pruebas`, y corta el arranque con un error si da producción.

## Pruebas (`tests/test_sec20_huella_cloudsql.py` y el caso de la guardia en `test_ep01`)
1. Una URL simulada con `host=/cloudsql/evydentia:us-central1:evydentia-production`, `unix_sock` o la variable del conector se reconoce como producción, sin abrir conexiones.
2. `127.0.0.1` sin marcador: producción.
3. Si la consulta del marcador falla: producción.
4. Base con marcador `'pruebas'`: no producción.
5. Marcador con un valor distinto de `pruebas` o `demo`: producción.
6. La guardia corta el arranque con los casos 1 y 2.

**Mutaciones:**
- M1: quitar el reconocimiento de la instancia hace fallar la prueba 1.
- M2: tratar la ausencia del marcador como «no producción» hace fallar la prueba 2.
- M3: no capturar el error de la consulta hace fallar la prueba 3.

## Enlace con otras fichas
- **El marcador lo crean quienes crean cada base**, nunca una migración (las migraciones también corren en producción): EP-03 (siembra), EP-05 (aprovisionamiento de pruebas) y DEMO-00 si clona bases. Sin el marcador, la guardia bloquea esos entornos.
- **Orden:** SEC-20 se fusiona después de que la siembra o el aprovisionamiento de pruebas y demo creen el marcador. El Tech Lead abre la ficha de enlace antes de lanzar SEC-20.
- `sembrar_entorno_pruebas.py` también debería llamar a `base_es_produccion`. Eso va en la misma ficha de enlace, no aquí.

## No hagas
- No te conectes a producción ni a Cloud SQL: solo URLs y conexiones simuladas, o la PostgreSQL efímera del CI.
