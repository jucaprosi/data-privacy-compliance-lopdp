+++
id = "SEC-20"
titulo = "apunta_a_produccion reconoce Cloud SQL de producción por conector, por proxy local y por un marcador en la base"
ola = "indep"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-15", "EP-11"]
propiedad = ["app_core/huellas_produccion.py", "tests/test_sec20_huella_cloudsql.py"]
crea = ["tests/test_sec20_huella_cloudsql.py"]
arbitro = "pytest tests/test_sec20_huella_cloudsql.py tests/test_ep01_guardias_entorno.py + suite completa; mutación documentada; revisión de Seguridad y del Arquitecto antes del reparto"
rastros = ["¤seguridad-tenant", "¤arbitro"]
+++

# SEC-20 · La huella de producción también cubre Cloud SQL

**Origen.** Nota del CTO del 2026-11-08. `apunta_a_produccion()` solo reconoce el host de Neon de producción (`HUELLA_HOST_PRODUCCION`). Tras el corte a Cloud SQL, la base de producción se alcanza por el conector o por `cloud-sql-proxy` en `127.0.0.1`, y ni la guardia de EP-11 ni la de EP-03 la detectarían.

## Entrega
1. Reconocer la instancia de producción `evydentia:us-central1:evydentia-production` en el parámetro `host` de las URL del conector (por ejemplo `host=/cloudsql/<instancia>`).
2. Con una conexión abierta, comprobar además un marcador en la base: `SELECT current_database(), inet_server_addr()` o una fila de una tabla de configuración que solo existe en producción.
3. **Fallar cerrado:** si la comprobación no puede hacerse (error, tiempo agotado), se trata como producción y se detiene.
4. Va **antes del corte** (paso D del brief del propietario).

## Pruebas (`tests/test_sec20_huella_cloudsql.py`)
1. Una URL simulada con `host=/cloudsql/evydentia:us-central1:evydentia-production` se reconoce como producción.
2. Una URL de `127.0.0.1` con el marcador de producción en la base (simulado) se reconoce como producción.
3. Si la consulta del marcador falla, el resultado es «producción» (falla cerrado).
4. Una base de prueba sin marcador no se reconoce como producción.
5. La guardia de EP-11 corta el arranque con los casos 1 y 2.

**Mutación:** quitar el reconocimiento de la instancia hace fallar la prueba 1.

## No hagas
- No te conectes a producción ni a Cloud SQL: solo URLs y resultados simulados.
- No escribas el marcador en ninguna base real: crearlo en producción es tarea del propietario, por brief.
