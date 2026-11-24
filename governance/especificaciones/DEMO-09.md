# DEMO-09 · La web de demo se publica desde main con la imagen web de producción del mismo commit
`¤sdd` `¤demo` `¤arbitro`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `governance/operaciones/DEMO_COMERCIAL.md` | nueva §5 «Publicar la web de demo (DEMO-09)» con el procedimiento de §3 R3 en un bloque `powershell` que define `$IMAGEN` |
| `governance/operaciones/entornos/demo/cloudrun_frontend.yaml` | `image: us-central1-docker.pkg.dev/evydentia/evydentia-containers/web`; el resto no cambia |
| `tests/test_demo09_web_demo.py` (nuevo) | las comprobaciones de §5, sin `import yaml` (`tests/_lector_yaml.py`) |

Hecho medido en `origin/main` 572b1127. El CTO aportó las lecturas de gcloud del 2026-11-23 y el Arquitecto las repitió ese mismo día, solo con gcloud de lectura:
- **Lo desplegado.**
  - La web de demo corre `evydentia-web-demo-00005-8f5`, con `us-central1-docker.pkg.dev/evydentia-demo/evydentia-demo-containers/web:v1`, del 2026-11-16. Le faltan FE-29, GCP-08c y lo que entre después.
  - El backend de demo corre `backend:b56f39c3`.
  - El repositorio web de producción tiene `web:01530613` (`sha256:aa7772f0…`) y `web:b56f39c3` (`sha256:3e39b19a…`).
- **El manifiesto no coincide.** `cloudrun_frontend.yaml` (DEMO-07) declara `…/evydentia-demo-containers/evydentia-web-demo`, una imagen que ningún servicio usa.
- **Solo una variable se incrusta al compilar.**
  - `frontend/Dockerfile.cloudrun` declara un único `ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID`, y `frontend/cloudbuild.yaml` pasa un único `--build-arg`, con el id `943042355099-…`.
  - Las demás `NEXT_PUBLIC_*` que lee `frontend/src` no se pasan al compilar en Cloud Run, así que valen igual en todos los entornos: `AUTH_MODE`, `API_URL`, `OPERADOR_PLATAFORMA`, `USER_ID`, `USER_ROLE`, `USER_EMAIL`, `TENANT_ID` y `EVIDENCIA_FISICA`.
  - `next.config.cloudrun.ts` no fija el entorno y quita los rewrites. `APP_ENV`, `BACKEND_URL` y `PROXY_AUTH_CLOUD_RUN` se leen al ejecutar: `src/lib/entorno.ts`, `layout.tsx`, `robots.ts` y `app/api/v1/[...ruta]/route.ts` (EP-02, GCP-08).
- **El client id de la demo es el de producción** (`NEXT_PUBLIC_GOOGLE_CLIENT_ID` del servicio). En la demo, esa variable de ejecución no tiene efecto, porque Next ya la incrustó al compilar.
- **Permisos entre proyectos.**
  - `gcloud artifacts repositories get-iam-policy evydentia-containers --project=evydentia` devuelve una política vacía (`etag ACAB`).
  - La política del proyecto `evydentia` no nombra ninguna cuenta del proyecto `evydentia-demo` (número `517105327086`).
  - Hoy la demo **no puede** leer la imagen de producción.

## 2. API

Sin rutas.

## 3. Reglas

- **R1 · Opción (a): el mismo binario en los dos entornos.**
  - La web de demo corre la imagen web de producción del mismo commit, por digest, leída del repositorio `evydentia/evydentia-containers`.
  - Razones:
    1. Nada del bundle depende del entorno al compilar, salvo el client id, que es el mismo (§1).
    2. Hay una sola construcción, y la demo enseña exactamente lo que producción ejecuta.
    3. Sin una segunda construcción no hay un segundo `cloudbuild` que mantener ni un client id que pueda divergir.
  - Se descarta la (b) porque duplica la construcción sin que cambie ningún byte del bundle.
  - Dentro de la (a), se elige el permiso de lectura y no la copia. La copia pide una herramienta más (`gcrane` o `docker pull/push`) y un repositorio que mantener en la demo, y su digest podría no ser el de producción.
- **R2 · Prerrequisito único del propietario.**
  - El propietario concede `roles/artifactregistry.reader` **solo sobre el repositorio** `evydentia-containers`, nunca sobre el proyecto `evydentia`, al agente de servicio de Cloud Run de la demo, `service-517105327086@serverless-robot-prod.iam.gserviceaccount.com`. Cloud Run descarga las imágenes con esa cuenta, no con la de ejecución.
  - Mínimo privilegio: es lectura de imágenes y nada más. La demo no puede escribir en producción ni leer nada fuera de ese repositorio.
  - El procedimiento empieza comprobando el permiso con gcloud de lectura.
  - **Supuesto que anoto:** la cuenta del agente de servicio sigue el formato documentado por Google para desplegar imágenes de otros proyectos. El propietario la confirma con `gcloud projects get-iam-policy evydentia-demo` antes de concederle el permiso.
- **R3 · Procedimiento en `DEMO_COMERCIAL.md` §5.** Comandos completos y pegables en PowerShell, con `cd` y variables:
  1. **Imagen del commit.**
     - Se fija `$COMMIT` como el commit corto de `origin/main` y `$IMAGEN = "us-central1-docker.pkg.dev/evydentia/evydentia-containers/web"`.
     - Si `gcloud artifacts docker images describe "$IMAGEN:$COMMIT"` no la encuentra, se construye una sola vez desde `frontend/` con `gcloud builds submit --config cloudbuild.yaml --substitutions=_ETIQUETA=$COMMIT .` (GCP-03b), la misma construcción de producción.
     - Se anota el digest.
  2. **Revisión sin tráfico:** `gcloud run deploy evydentia-web-demo --project=evydentia-demo --region=us-central1 --image="$IMAGEN@$DIGEST" --no-traffic --tag="c$COMMIT"`. Las variables y la cuenta del servicio no cambian.
  3. **Verificar en la URL de la etiqueta.**
     - `/login` responde 200 y ofrece el acceso con Google.
     - El aviso de entorno dice «demo» y una fecha sale en es-EC (GCP-08c).
     - Con IA-15 fusionada, el consentimiento del preanálisis nombra «Estados Unidos (región us)».
  4. **Tráfico:** `gcloud run services update-traffic evydentia-web-demo --to-latest`, y se repite la comprobación en la URL pública.
  5. **Volver atrás:** `update-traffic --to-revisions=<revisión anterior>=100`, anotada antes del paso 2. Hoy es `evydentia-web-demo-00005-8f5`.
  - **Nunca compila aparte:** el procedimiento no contiene `docker build` ni `--build-arg`, y solo llama a `gcloud builds submit` con `--config cloudbuild.yaml`.
- **R4 · Manifiesto alineado.**
  - `cloudrun_frontend.yaml` declara el repositorio de R1 sin etiqueta ni digest. El digest es del despliegue y lo fija el paso 2.
  - `NEXT_PUBLIC_GOOGLE_CLIENT_ID` sigue en el manifiesto, con un comentario: es informativa y debe ser igual al `--build-arg` de `frontend/cloudbuild.yaml`.
- **R5 · Prueba exógena.** `tests/test_demo09_web_demo.py` lee los tres archivos del repositorio y no toca la red (§5).
- **R6 · Límites.**
  - Nada en `.github/workflows/` ni en la nube.
  - No cambian `frontend/cloudbuild.yaml` ni `frontend/Dockerfile.cloudrun`: la prueba los lee, no los posee.
  - El brief para el propietario vive en `C:\Users\Juan Carlos\compartido\evydentia\briefs\DEMO-09-propietario.md`, fuera del repositorio (GOB-06). Su nombre no es el id de la ficha, así que `verificar_briefs_locales.py` no lo confunde con el brief de la ficha.
- **R-ADPA · Ortogonalidad ZERAG (`DEMO-09`).** Solo los tres archivos de la propiedad. Sin `import yaml`.

## 4. Interfaz

No aplica. La interfaz no cambia, así que no pasa por UX/UI.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** el manifiesto de la demo, `DEMO_COMERCIAL.md` §5 y `frontend/cloudbuild.yaml`, **entonces** la `image` del manifiesto, el `$IMAGEN` del procedimiento y la imagen de `images:` de cloudbuild sin `:${_ETIQUETA}` son la misma cadena. Mutación m1: volver a `evydentia-demo-containers/evydentia-web-demo` en el manifiesto da rojo. | `test_la_imagen_del_manifiesto_es_la_del_procedimiento` |
| **Dado** el `NEXT_PUBLIC_GOOGLE_CLIENT_ID` del manifiesto, **entonces** es igual al `--build-arg` de cloudbuild, y todo client id (`\d+-[a-z0-9]+\.apps\.googleusercontent\.com`) de §5 es ese mismo. Mutación m2: otro id en el manifiesto o en §5 da rojo. | `test_el_client_id_es_uno_solo` |
| **Dado** §5, **entonces** no contiene `docker build` ni `--build-arg`, y todo `gcloud builds submit` lleva `--config cloudbuild.yaml`. Mutación m3: añadir `--build-arg NEXT_PUBLIC_GOOGLE_CLIENT_ID=…` da rojo. | `test_el_procedimiento_no_compila_aparte` |
| **Dado** `frontend/Dockerfile.cloudrun` y cloudbuild, **entonces** hay exactamente un `ARG NEXT_PUBLIC_` y un `--build-arg`, los dos de `NEXT_PUBLIC_GOOGLE_CLIENT_ID`; si aparece otro, el supuesto de R1 cae. Mutación m4: un segundo `ARG NEXT_PUBLIC_X` da rojo. | `test_solo_el_client_id_entra_al_compilar` |
| **Dado** el procedimiento, **cuando** el propietario lo sigue, **entonces** la revisión nueva de `evydentia-web-demo` sirve `/login` con `$IMAGEN@<digest del commit>`. | lo corre el propietario |

## 6. Trazabilidad

- Ficha: `governance/tareas/DEMO-09.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Pedido del CTO (2026-11-23), que prefería la (a) si el bundle no dependía del entorno: lo comprueba §1.
- Protocolo de Google Cloud: el Arquitecto solo usa gcloud de lectura y el propietario hace los cambios con Antigravity (R4).
- Depende de las fichas hechas que comparten estos archivos o fijan lo que se lee: DEMO-07 (el manifiesto y la guía), GCP-03 y GCP-03b (la imagen y `cloudbuild.yaml`), GCP-08 (el entorno al ejecutar) y GCP-08c (ICU en la imagen).
