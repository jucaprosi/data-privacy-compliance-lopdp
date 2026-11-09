+++
id = "SEC-20"
titulo = "La huella de producción reconoce Cloud SQL: función pura por la URL y comprobación de la base en la guardia, con marcador en las bases que no son producción"
ola = "indep"
estado = "hecha"
sala = "pasillo_central"
depende_de = ["SEC-15", "EP-01", "EP-11"]
propiedad = ["app_core/huellas_produccion.py", "app_core/entorno/guardias.py", "tests/test_ep01_guardias_entorno.py", "tests/test_sec20_huella_cloudsql.py"]
crea = ["tests/test_sec20_huella_cloudsql.py"]
arbitro = "pytest tests/test_sec20_huella_cloudsql.py tests/test_ep01_guardias_entorno.py + suite completa; mutaciones M1 a M6 documentadas; revisión de Seguridad hecha (2026-11-08, puntos 1-7 incorporados)"
rastros = ["¤seguridad-tenant", "¤arbitro"]
+++

# SEC-20 · La huella de producción también cubre Cloud SQL

**Origen.** Nota del CTO del 2026-11-08. `apunta_a_produccion()` solo reconoce el host de Neon de producción. Tras el corte a Cloud SQL, la base de producción se alcanza por el conector o por `cloud-sql-proxy` en `127.0.0.1`, y ni la guardia de EP-11 ni la de EP-03 la detectarían. Diseño del Arquitecto ADPA (2026-11-08).

## Entrega
1. **`apunta_a_produccion(url)` sigue pura, sin E/S.** La llaman `security.py` al arrancar, `crear_organizacion_dev.py` y `sembrar_entorno_pruebas.py`; si abriera una conexión, un proceso sin base (pruebas unitarias, build, arranque sin red) se trataría como producción. Ahora reconoce también la instancia `evydentia:us-central1:evydentia-production`:
   - en `host=/cloudsql/…`, en `unix_sock` y en todo el texto de la URL;
   - sin distinguir mayúsculas y después de decodificar (`%3A`, `%2F`);
   - en una lista cerrada de variables del conector: `INSTANCE_CONNECTION_NAME`, `CLOUD_SQL_CONNECTION_NAME` y la que use `deploy-gcp.yml`.
2. **Función nueva `base_es_produccion(conexion, nombre_base=None) -> bool`**, en el mismo archivo. Recibe una conexión ya abierta y no la crea. Da producción si se cumple **cualquiera** de estas señales (OR):
   - `current_database()` es `'evydentia_prod'` (en las pruebas el nombre se simula con el parámetro);
   - no hay marcador válido.
   El OR con la URL lo hace la guardia: `apunta_a_produccion(url) or base_es_produccion(con)`. `base_es_produccion` no recibe la URL.
3. **Marcador invertido, solo como prueba en contra:** las bases que **no** son producción tienen la tabla `public.entorno_marcador(valor)` con `'pruebas'` o `'demo'`. Es válido solo si se cumple todo esto:
   - la consulta va siempre con esquema (`public.entorno_marcador`), nunca sin él, para que una tabla temporal en `pg_temp` no la sombree;
   - el dueño de la tabla (`pg_class.relowner`) es el dueño de la base actual (`pg_database.datdba` de `current_database()`), no basta con que coincida con el de otras tablas y es una tabla normal (`relkind = 'r'`);
   - tiene exactamente una fila, no NULL, con `'pruebas'` o `'demo'`. Con 0 filas, 2 o más, NULL u otro valor: producción.
4. **Consulta acotada:** dentro de un SAVEPOINT de solo lectura con `SET LOCAL statement_timeout = '2s'`. Un error no deja abortada la transacción del llamador. Un error o un tiempo agotado cuentan como producción (falla cerrado). No se usa `inet_server_addr()`: detrás del proxy o del conector devuelve la IP del socket.
5. **La guardia** (`app_core/entorno/guardias.py`), cuando `APP_ENV` es `demo` o `pruebas`:
   - comprueba `DATABASE_URL` y `MIGRATION_DATABASE_URL`;
   - abre ella misma la conexión al arrancar (lo deja escrito en el docstring);
   - corta el arranque con un error si da producción.
   Sin red, el arranque de demo o pruebas se bloquea. Es lo correcto, pero queda anotado por el arranque en frío de Cloud Run.

## Pruebas (`tests/test_sec20_huella_cloudsql.py` y el caso de la guardia en `test_ep01`)
1. Se reconoce como producción una URL simulada con `host=/cloudsql/evydentia:us-central1:evydentia-production`, con `unix_sock`, con la forma codificada o en mayúsculas. También cada variable del conector de la lista cerrada, con una prueba por cada una. Ninguna abre conexiones.
2. `127.0.0.1` sin marcador: producción.
3. Si la consulta del marcador falla o agota el tiempo: producción, y la transacción del llamador sigue usable.
4. Base con un marcador válido `'pruebas'`: no producción.
5. Marcador con un valor distinto de `pruebas` o `demo`: producción.
6. La guardia corta el arranque con los casos 1 y 2.
7. Una tabla temporal `entorno_marcador` con `'pruebas'`, en una base sin marcador: producción.
8. Marcador `'pruebas'` con `current_database()` simulado como `evydentia_prod`: producción.
9. Marcador con 0 filas, 2 filas o NULL: producción.
10. El marcador lo crea un rol que no es el dueño de la base: producción.
11. Prueba de catálogo: `lopdp_app` no tiene CREATE sobre el esquema `public`.

**Mutaciones:**
- M1: quitar el reconocimiento de la instancia hace fallar la prueba 1.
- M2: tratar la ausencia del marcador como «no producción» hace fallar la prueba 2.
- M3: no capturar el error de la consulta hace fallar la prueba 3.
- M4: consultar sin esquema hace fallar la prueba 7.
- M5: quitar la señal de `current_database()` hace fallar la prueba 8.
- M6: no decodificar la URL hace fallar la prueba 1 en su forma codificada.

## Enlace con otras fichas
- **El marcador lo crean quienes crean cada base**, nunca una migración (las migraciones también corren en producción): EP-03 (siembra), EP-05 (aprovisionamiento de pruebas) y DEMO-00 si clona bases. Sin el marcador, la guardia bloquea esos entornos.
- **Orden:** SEC-20 se fusiona después de que la siembra o el aprovisionamiento de pruebas y demo creen el marcador. El Tech Lead abre la ficha de enlace antes de lanzar SEC-20.
- En el CI, si alguna prueba corre con `APP_ENV=pruebas` contra el contenedor, el marcador lo crea la ficha de enlace o un fixture de prueba, nunca una migración.
- `sembrar_entorno_pruebas.py` también debería llamar a `base_es_produccion`. Eso va en la misma ficha de enlace, no aquí.

## No hagas
- No te conectes a producción ni a Cloud SQL: solo URLs y conexiones simuladas, o la PostgreSQL efímera del CI.
