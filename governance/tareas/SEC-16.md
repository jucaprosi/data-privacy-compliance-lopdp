+++
id = "SEC-16"
titulo = "Secretos obligatorios en la nube: el backend no arranca con JWT_SECRET o SESSION_SECRET por defecto"
ola = "D"
estado = "hecha"
sala = "pasillo_central, biblioteca"
depende_de = ["SEC-15", "FIRMA-06", "BIB-104", "SEC-06", "RM-13"]
propiedad = ["app_core/config.py#SEC-16", "features/biblioteca/services/archivos.py#SEC-16", "tests/test_sec16_secretos_obligatorios.py"]
arbitro = "pytest tests/test_sec16_secretos_obligatorios.py + suite completa + vigilantes; prueba de mutación documentada"
rastros = ["¤seguridad", "¤arbitro"]
+++

# SEC-16 · Secretos obligatorios en la nube

**Arquitectura en Google Cloud:** la detección de nube usa `K_SERVICE`, definida siempre en Cloud Run. En EVYDENTIA, `JWT_SECRET` y `SESSION_SECRET` se gestionan en Secret Manager y se montan por servicio en Cloud Run.

**Hallazgo (2026-11-05, preparación del guion de publicación, PR #422).** Tres sitios del backend ponen una clave escrita en el código cuando falta la variable. El repositorio es público, así que esas claves son conocidas:
- La entrada única `main.app` en Cloud Run falla cerrado cuando faltan secretos obligatorios.
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
  - en la nube (`K_SERVICE` definida), cada uno de estos casos lanza `RuntimeError`:
    - sin `JWT_SECRET`;
    - con la clave por defecto;
    - con una de 20 caracteres;
    - sin `SESSION_SECRET`;
    - con las dos iguales.

    El mensaje nunca contiene el valor;
  - en la nube, con dos secretos válidos: arranca;
  - fuera de la nube, sin ninguna de las dos: arranca, como hoy;
  - importar `main` en un subproceso con `K_SERVICE` definido y sin `JWT_SECRET` falla cerrado en el arranque;
  - `archivos.py`, en la nube y sin `SESSION_SECRET`, no firma enlaces.
- Las pruebas usan valores generados en la propia prueba, nunca secretos reales.
- Mutación documentada: quitar la comprobación de la clave por defecto; el caso «con la clave por defecto» debe fallar.

## Antes de fusionar
- `JWT_SECRET` y `SESSION_SECRET` deben estar declaradas en Secret Manager para los servicios de Cloud Run.
- En Google Cloud, el secreto se llama `JWT_SECRET`, no `JWT_SECRET_KEY`.

## Límites
- No cambia el algoritmo ni la duración de los tokens.
- No rota claves: rotar lo hacen las personas.
- La inferencia en Vertex AI opera mediante credenciales ADC sin claves estáticas.

## Notas para el propietario
- `api/index.py` también pone por defecto `DATABASE_URL` (SQLite en `/tmp`) y `CORS_ORIGINS="*"`. En la nube, los dos fallan abiertos: el primero esconde una base mal configurada y el segundo admite cualquier origen. Merecen la misma guarda, pero es una decisión aparte.
