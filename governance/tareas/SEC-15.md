+++
id = "SEC-15"
titulo = "Guarda de arranque: el backend no arranca en modo de cabeceras contra la base de producción ni en la nube"
ola = "D"
estado = "pendiente"
sala = "pasillo_central"
depende_de = ["SEC-03", "SEC-07", "DEV-01", "RM-00", "ENT-02"]
propiedad = ["app_core/huellas_produccion.py", "app_core/security.py", "main.py#SEC-15", "scripts/crear_organizacion_dev.py", "tests/test_sec15_guarda_arranque.py"]
arbitro = "pytest tests/test_sec15_guarda_arranque.py + suite completa + vigilantes; prueba de mutación documentada"
rastros = ["¤rbac-tenant", "¤arbitro"]
+++

# SEC-15 · Guarda de arranque: modo de cabeceras nunca contra producción

**Hallazgo (2026-11-05, chat «Tareas no fusionadas de José (fork)», consolidado por el coordinador).**
- El lanzador local de pruebas físicas leyó un archivo de credenciales que no existía. `DATABASE_URL` quedó sin definir y el backend arrancó igual («Application startup complete», `AUTH_MODE=headers`).
- Sin esa variable, `app_core/config.py` ejecuta `load_dotenv(<carpeta del código>/.env, override=False)`. Desde la carpeta principal, ese `.env` tiene `DATABASE_URL`, `MIGRATION_DATABASE_URL` y `DATABASE_URL_DIRECT` de **producción**.
- En modo de cabeceras la identidad sale de `X-User-ID` y `X-Role`, que cualquiera puede escribir. Ese arranque deja la base de producción abierta a quien alcance el puerto 5000, porque uvicorn escuchaba en `0.0.0.0`.
- No consta que llegara a conectarse a producción. Pero hoy nada lo impide: la única guarda está en `scripts/crear_organizacion_dev.py` (`HOST_PRODUCCION`) y en el lanzador, fuera del repositorio, y cada una cubre solo su propio camino.

**Contrato:** `INV_LOPDP_HEADERS_NEVER_WITH_PRODUCTION` (`governance/artefactos/INVARIANTS.md`). Principio: Saltzer y Schroeder (1975), «Fail-safe defaults».

## Entrega
- **`app_core/huellas_produccion.py`** (nuevo): la huella del host de producción de Neon (`ep-late-hall-b50bpbk5`) y `apunta_a_produccion(url) -> bool`, que compara solo el host. Es el único sitio donde vive. `scripts/crear_organizacion_dev.py` pasa a importarla en lugar de tener su propia constante. El mismo módulo expone `corre_en_la_nube() -> bool` (`VERCEL` o `K_SERVICE` definidas), que usan esta tarea y `SEC-16`: la detección vive en un solo sitio.
- **`app_core/security.py`:** `exigir_arranque_seguro()`. Si `modo_autenticacion() == "headers"` y se cumple cualquiera de estas condiciones, lanza `RuntimeError`:
  - alguna de `DATABASE_URL`, `MIGRATION_DATABASE_URL` o `DATABASE_URL_DIRECT` apunta a producción;
  - corre en la nube: `VERCEL` o `K_SERVICE` definidas.

  El mensaje nombra la regla y la variable, nunca la URL. Con `oidc` no hace nada.
- **`main.py#SEC-15`:** llama a `exigir_arranque_seguro()` al importar el módulo, después de cargar la configuración y antes de crear la aplicación. Así falla también con `uvicorn main:app` y con cualquier lanzador.
- Al arrancar en modo de cabeceras, el registro muestra una línea con el modo y el host de la base (solo el host, sin usuario ni contraseña), para que quien lo arranca vea a qué se conectó.

## Pruebas
- `tests/test_sec15_guarda_arranque.py`:
  - modo de cabeceras con cada una de las tres URL apuntando a producción: falla, y el mensaje no contiene la URL;
  - modo de cabeceras con `VERCEL` o `K_SERVICE`: falla;
  - modo de cabeceras con un host de prueba: arranca;
  - `oidc` con producción: arranca (es el caso legítimo de Vercel);
  - importar `main` en un subproceso con modo de cabeceras y la huella de producción en `DATABASE_URL`: el proceso sale con error;
  - `scripts/crear_organizacion_dev.py` usa la huella del módulo.
- Las pruebas usan URL ficticias con la huella del host, nunca credenciales reales.
- Mutación documentada: hacer que `exigir_arranque_seguro()` no compruebe `MIGRATION_DATABASE_URL`; su caso debe fallar.

## Límites
- No cambia `app_core/config.py` ni el orden de carga del `.env` (decisión aparte).
- No cambia el lanzador de pruebas físicas, que está fuera del repositorio. Conviene que también falle si no encuentra su archivo de credenciales.
- No toca `app_core/entorno/` (`EP-01`, guardas del entorno de pruebas de Google Cloud), que es complementario.

## Notas para el propietario
- `app_core/config.py` define por defecto un `JWT_SECRET` fijo si falta la variable. No es parte de esta tarea, pero merece una guarda igual: en la nube, sin `JWT_SECRET` propio, no se debería arrancar.
