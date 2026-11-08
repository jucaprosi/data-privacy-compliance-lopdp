+++
id = "SEC-16"
titulo = "Secretos obligatorios en la nube: el backend no arranca con JWT_SECRET o SESSION_SECRET por defecto"
ola = "D"
estado = "en_curso"
sala = "pasillo_central, biblioteca"
depende_de = ["SEC-15", "FIRMA-06", "BIB-104", "SEC-06", "RM-13"]
propiedad = ["app_core/config.py#SEC-16", "api/index.py", "features/biblioteca/services/archivos.py#SEC-16", "tests/test_sec16_secretos_obligatorios.py"]
arbitro = "pytest tests/test_sec16_secretos_obligatorios.py + suite completa + vigilantes; prueba de mutación documentada"
rastros = ["¤seguridad", "¤arbitro"]
+++

# SEC-16 · Secretos obligatorios en la nube

**Cambio 2026-11-07 (todo en Google Cloud, decisión del propietario):** la nube es Cloud Run. La detección de nube es solo `K_SERVICE`, que Cloud Run define siempre; donde esta ficha dice `VERCEL=1` o `VERCEL_ENV=production`, se lee `K_SERVICE` definida. La sección «Antes de fusionar» sobre Vercel queda para el PMV congelado: en EVYDENTIA, `JWT_SECRET` y `SESSION_SECRET` van en Secret Manager, montadas en el servicio de Cloud Run (las carga el propietario con Antigravity).

**Hallazgo (2026-11-05, preparación del guion de publicación, PR #422).** Tres sitios del backend ponen una clave escrita en el código cuando falta la variable. El repositorio es público, así que esas claves son conocidas:
- `api/index.py:12`, el punto de entrada de Vercel: `os.environ.setdefault("JWT_SECRET", ...)`.
- `app_core/config.py:48`: la misma clave por defecto para `JWT_SECRET`.
- `features/biblioteca/services/archivos.py:24`: los enlaces de descarga de la Biblioteca se firman con `SESSION_SECRET`, y si falta, con `SECRET_KEY` o una clave fija.

Si en producción falta la variable, o se carga con otro nombre (en Google Cloud se creó `JWT_SECRET_KEY` en lugar de `JWT_SECRET`), el backend arranca sin aviso. Entonces cualquiera puede firmar sesiones o enlaces de descarga válidos.

**Contrato:** `INV_LOPDP_NO_DEFAULT_SECRETS_IN_CLOUD` (`governance/artefactos/INVARIANTS.md`). Principio: Saltzer y Schroeder (1975), «Fail-safe defaults».

## Entrega
- **`app_core/config.py#SEC-16`:** la función `exigir_secretos_en_la_nube()` se llama al cargar la configuración. Si `corre_en_la_nube()` (de `app_core/huellas_produccion.py`, `SEC-15`) es verdadero, lanza `RuntimeError` con el nombre de la variable y la regla, sin el valor, cuando `JWT_SECRET` o `SESSION_SECRET`:
  - falta o está vacía;
  - vale una de las claves por defecto que hoy están en el código; se comparan contra una lista en este módulo;
  - mide menos de 32 caracteres;
  - o las dos son iguales.

  Fuera de la nube no hace nada y se conservan los valores de desarrollo.
- **`api/index.py`:** se retira `setdefault("JWT_SECRET", ...)`. Si la importación falla, la API de emergencia ya responde 503 `STARTUP_ERROR` sin detalles. Así el fallo se ve en `/health` y en `verificar_despliegue.py`, y no se sirve nada con una clave conocida.
- **`features/biblioteca/services/archivos.py#SEC-16`:** la clave de firma sale de `SESSION_SECRET` en una sola función, leída al usarla, no al importar. El alias `SECRET_KEY` y la clave fija quedan solo fuera de la nube.

## Pruebas
- `tests/test_sec16_secretos_obligatorios.py`:
  - en la nube (`VERCEL=1`), cada uno de estos casos lanza el error:
    - sin `JWT_SECRET`;
    - con la clave por defecto;
    - con una de 20 caracteres;
    - sin `SESSION_SECRET`;
    - con las dos iguales.

    El mensaje nunca contiene el valor;
  - en la nube, con dos secretos válidos: arranca;
  - fuera de la nube, sin ninguna de las dos: arranca, como hoy;
  - importar `api.index` en un subproceso con `VERCEL=1` y sin `JWT_SECRET`: `/health` responde 503 con `STARTUP_ERROR`;
  - `archivos.py`, en la nube y sin `SESSION_SECRET`, no firma enlaces.
- Las pruebas usan valores generados en la propia prueba, nunca secretos reales.
- Mutación documentada: quitar la comprobación de la clave por defecto; el caso «con la clave por defecto» debe fallar.

## Antes de fusionar
- `JWT_SECRET` y `SESSION_SECRET` deben estar cargadas en Vercel, en **Production y Preview**. Si no, el despliegue siguiente responde 503. Ver `governance/operaciones/PUBLICACION_PMV.md`, paso 2.1, y `VARIABLES_VERCEL.md`.
- En Google Cloud, el secreto se llama `JWT_SECRET`, no `JWT_SECRET_KEY`.

## Límites
- No cambia el algoritmo ni la duración de los tokens.
- No rota claves: rotar lo hacen las personas.
- No toca `DEEPSEEK_API_KEY` (`features/roadmap/ai/client.py`, con `dummy_key` por defecto). Una clave falsa ahí solo hace fallar la llamada a la IA y no abre acceso.

## Notas para el propietario
- `api/index.py` también pone por defecto `DATABASE_URL` (SQLite en `/tmp`) y `CORS_ORIGINS="*"`. En la nube, los dos fallan abiertos: el primero esconde una base mal configurada y el segundo admite cualquier origen. Merecen la misma guarda, pero es una decisión aparte.
