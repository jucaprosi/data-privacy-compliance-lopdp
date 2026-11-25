# DEMO-11 · Backend y migración de la demo
`¤sdd` `¤demo` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones propias. Hechos medidos en `origin/main` dfc82838 y con `gcloud` de lectura del Tech Lead (2026-11-24):
- **Solo la web.** `governance/operaciones/DEMO_COMERCIAL.md` describe la web (§5, DEMO-09 y DEMO-10), pero no el backend ni la migración. `PROPIETARIO_DESPLIEGUE_IA13_IA14.v2.md` D2 remite a él para migrar.
- **Sin job de migración.** En `evydentia-demo` solo existe el job `purga-demo` (`entornos/demo/job_purga.yaml`). Producción migra con `evydentia-migrate` (`entornos/produccion/MIGRAR_PRODUCCION.md`).
- **Secreto sin declarar.** `DATABASE_URL` existe en Secret Manager de `evydentia-demo`, pero `entornos/demo/secretos.yaml` no lo declara. El backend lee `DATABASE_URL_APP` (`cloudrun_backend.yaml`).
- **Membresía sin documentar.** Las migraciones conceden a `lopdp_app`, y la demo conecta como `evydentia_demo_app` (`cloud_sql.yaml:28`). Ningún documento dice que este sea miembro de `lopdp_app`.
- **Cabezas a mano.** `cloud_sql.yaml:3` lista 12 cabezas de Alembic escritas a mano, que ya no corresponden al grafo (CI-28: una rama por sala).
- **Imagen del backend.** `gcloud` de lectura del CTO (2026-11-24): el repositorio `us-central1-docker.pkg.dev/evydentia-demo/evydentia-demo-containers` tiene `backend`, `purga-demo` y `web`. El servicio `evydentia-backend-demo` (revisión 00015-lsn) corre `…/backend:b56f39c3`. `cloudrun_backend.yaml:26` declara `evydentia-backend-demo`, un paquete que no existe.
- **Cómo llegó esa imagen.** `gcloud builds list` y `describe` de lectura en `evydentia-demo` (2026-11-24): un `gcloud builds submit --tag …/backend:b56f39c3` desde la raíz del repositorio (paso `docker build -t … .`, sin `COMMIT_SHA`), el 2026-11-24 a las 00:15Z; antes, `backend:v1`, el 2026-11-16. La construcción de producción publica en otro repositorio (`evydentia/evydentia-containers/backend`).
- **Sin registro de la demo.** `REGISTRO_MIGRACIONES_MANUALES.md` no tiene filas de `evydentia-demo-db`; su regla 4 lo limita a bases de pruebas.

## 2. API

Sin API.

## 3. Reglas

- **R1 · Job de migración declarado.** `entornos/demo/job_migracion.yaml` declara el Cloud Run Job `migrar-demo` del proyecto `evydentia-demo`, región `us-central1`:
  - imagen `us-central1-docker.pkg.dev/evydentia-demo/evydentia-demo-containers/backend`, la misma que el servicio, fijada por digest en cada migración;
  - comando `alembic upgrade heads`;
  - `maxRetries: 0`, `taskCount: 1`, `timeoutSeconds: 600`;
  - cuenta de servicio propia del job, distinta de la del backend y de la de la purga;
  - Cloud SQL `evydentia-demo:us-central1:evydentia-demo-db`;
  - `DATABASE_URL` desde Secret Manager, nunca literal;
  - `APP_ENV=demo`.
- **R2 · Secreto declarado.** `secretos.yaml` declara `DATABASE_URL`: URL de `evydentia-demo-db` con el usuario que migra (con DDL), y solo la lee la cuenta del job de R1. El backend sigue con `DATABASE_URL_APP`.
- **R3 · Membresía del rol.** `cloud_sql.yaml` declara, en `roles_y_politicas`, que `evydentia_demo_app` es miembro de `lopdp_app` (`miembro_de: [lopdp_app]`), sin ADMIN y sin SET a otros roles. La línea de las 12 cabezas se sustituye por «Migraciones: las del grafo de Alembic, aplicadas con `migrar-demo` (DEMO_COMERCIAL.md §6)».
- **R4 · §6 de DEMO_COMERCIAL.md, «Backend y migración de la demo».** Bloques de PowerShell completos y pegables, con `gcloud` y sin valores de secretos:
  - **6.1 Imagen:** la del mismo commit que la web de §5.2, con el commit corto como etiqueta. Si `gcloud artifacts docker images describe …/backend:<commit>` no la encuentra, se construye una sola vez en `evydentia-demo` desde ese commit, como se construyó `backend:b56f39c3`: `git switch --detach <commit>` y, desde la raíz, `gcloud builds submit --tag us-central1-docker.pkg.dev/evydentia-demo/evydentia-demo-containers/backend:<commit> --project=evydentia-demo .` (usa el `Dockerfile` raíz). Después se toma su digest, que usan 6.2 y 6.3.
  - **6.2 Migración, antes de publicar el backend:**
    - copia previa de `evydentia-demo-db` (`gcloud sql backups create`);
    - comprobación de solo lectura de la membresía de R3 (`pg_has_role('evydentia_demo_app','lopdp_app','MEMBER')`); si da falso, se para y se avisa al propietario;
    - `gcloud run jobs update migrar-demo --image=<imagen>@<digest>` y `gcloud run jobs execute migrar-demo --wait`;
    - comprobación de que `alembic heads` y la revisión aplicada coinciden: el número de cabezas aplicadas es el número de ramas del grafo.
  - **6.3 Publicación del backend:** revisión sin tráfico con etiqueta, comprobación de `/health` en la URL de la etiqueta y paso del tráfico, como en §5.2.
  - **6.4 Vuelta atrás:** el tráfico vuelve a la etiqueta «anterior». La base no se baja de versión: si hace falta, se restaura la copia de 6.2, y eso lo decide el propietario.
  - **6.5 Registro:** una tabla con fecha, commit, digest, revisiones antes y después, quién aplicó y confirmación. Sin credenciales.
- **R7 · Imagen declarada del servicio.** `cloudrun_backend.yaml` declara `image: us-central1-docker.pkg.dev/evydentia-demo/evydentia-demo-containers/backend`, el mismo nombre que R1 y 6.1. Su ficha anterior, IA-16, está hecha, y ninguna ficha abierta lo tiene en propiedad.
- **R5 · Quién.** Lo ejecuta el propietario, desde `main` y tras fusionar. Ninguna sesión de IA migra ni publica la demo.
- **R6 · Sin prohibiciones** (GEN-01 R3).
- **R-ADPA · Ortogonalidad ZERAG (`DEMO-11`).** Solo los archivos de la propiedad. La prueba lee YAML con `tests/_lector_yaml.py`, sin `import yaml`.

## 4. Interfaz

Sin interfaz.

## 5. Aceptación

| Caso | Árbitro |
| :--- | :--- |
| **Dado** `job_migracion.yaml`, **entonces** cumple R1: comando, `maxRetries: 0`, imagen del repositorio de la demo, cuenta propia distinta de la del backend y de la purga, y `DATABASE_URL` por `secretKeyRef`. Mutación m1: una URL literal en `env` da rojo. | `tests/test_demo11_backend_y_migracion.py` |
| **Dado** `secretos.yaml`, **entonces** `DATABASE_URL` está declarado y solo lo lee la cuenta del job. Mutación m2: añadir la cuenta del backend da rojo. | ídem |
| **Dado** `cloud_sql.yaml`, **entonces** `evydentia_demo_app` declara `miembro_de: [lopdp_app]` y no lista cabezas a mano. Mutación m3: quitar la membresía da rojo. | ídem |
| **Dado** la §6 de `DEMO_COMERCIAL.md`, **entonces** tiene 6.1 a 6.5, la copia previa va antes de `jobs execute`, usa el mismo commit que §5.2 y no contiene `postgresql://` ni contraseñas. Mutación m4: mover la copia después de la ejecución da rojo. | ídem |
| **Dado** `cloudrun_backend.yaml`, `job_migracion.yaml` y el bloque 6.1, **entonces** nombran el mismo paquete `evydentia-demo-containers/backend`. Mutación m5: volver a `evydentia-backend-demo` en cualquiera de los tres da rojo. | `tests/test_demo11_backend_y_migracion.py` |
| **Dado** la §5, **entonces** DEMO-09 y DEMO-10 siguen en verde. | `tests/test_demo09_web_demo.py` |

## 6. Trazabilidad

- **PRD:** §5.6, demo comercial con base propia (decisión de bases por entorno del 2026-11-09).
- Hallazgo del Tech Lead con autorización del propietario (2026-11-24), base `origin/main` dfc82838. Modelo de producción: `MIGRAR_PRODUCCION.md`.
