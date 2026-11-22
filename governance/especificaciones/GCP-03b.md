# GCP-03b · Client id de Google incrustado al compilar la imagen web y etiqueta por commit
`¤sdd` `¤arbitro` `¤seguridad`

## 1. Datos

Sin tablas ni migraciones. Estado final:

| Archivo | Estado final |
| :--- | :--- |
| `frontend/Dockerfile.cloudrun` | la etapa `builder` declara `ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID` y `ENV NEXT_PUBLIC_GOOGLE_CLIENT_ID=${NEXT_PUBLIC_GOOGLE_CLIENT_ID}` antes de `npm run build` |
| `frontend/cloudbuild.yaml` | etiqueta `web:${_ETIQUETA}` en `-t` y en `images`, sin valor por defecto; conserva el `--build-arg` del client id |
| `tests/test_gcp03_frontend_cloudrun.py` | casos de §5 |

Hecho medido en `origin/main` 188d207c:
- El commit 5cd05062 (2026-11-17) quitó esas dos líneas de la etapa `builder`. Next incrusta `NEXT_PUBLIC_*` en el bundle al compilar, y `frontend/src/lib/auth/modo.ts:49` lo lee en el navegador. Por eso la variable de Cloud Run no llega a la pantalla de login, y `frontend/cloudbuild.yaml` pasa un `--build-arg` que nadie declara.
- `tests/test_gcp03_frontend_cloudrun.py:176` solo prohíbe `ARG APP_ENV`. El CI no construye la imagen de producción.
- `frontend/src` lee nueve variables `NEXT_PUBLIC_*`. Se clasifican en tres grupos:
  - **de compilación:** `NEXT_PUBLIC_GOOGLE_CLIENT_ID`;
  - **de servidor**, que se leen en tiempo de ejecución desde `route.ts` y `copilotProxy.ts`: `NEXT_PUBLIC_API_URL`;
  - **solo de desarrollo**, del modo «headers» o de pruebas: `NEXT_PUBLIC_AUTH_MODE`, `NEXT_PUBLIC_USER_ID`, `NEXT_PUBLIC_USER_ROLE`, `NEXT_PUBLIC_USER_EMAIL`, `NEXT_PUBLIC_TENANT_ID`, `NEXT_PUBLIC_OPERADOR_PLATAFORMA` y `NEXT_PUBLIC_EVIDENCIA_FISICA`.
- Entornos:
  - Demo y pruebas usan la misma imagen por digest, así que el arreglo les llega igual.
  - `entornos/demo/cloudrun_frontend.yaml:34` fija el client id en tiempo de ejecución. No hace daño, pero no tiene efecto en el navegador.
  - `entornos/pruebas/cloudrun_frontend.yaml:42` fija `NEXT_PUBLIC_APP_ENV`, que `frontend/src` no lee.
  - Ninguno de los dos tiene un Dockerfile propio. La limpieza de esas dos entradas la decide el propietario, que es dueño de esos YAML.

## 2. API

No aplica.

## 3. Reglas

- **R1 · El client id entra al compilar.** La etapa `builder` declara el `ARG` y el `ENV`, y `frontend/cloudbuild.yaml` lo pasa como `--build-arg`. El client id de OAuth es público por diseño. «Una imagen por digest» sigue rigiendo para `APP_ENV` y `BACKEND_URL`, que no entran al compilar.
- **R2 · Toda variable del cliente está clasificada.** Cada `NEXT_PUBLIC_*` que lee `frontend/src` está en uno de los tres grupos de §1, declarados en la prueba.
  - Las de compilación tienen `ARG` en `builder` y `--build-arg` en `frontend/cloudbuild.yaml`.
  - Las solo de desarrollo no tienen `ARG` ni `--build-arg`, para que una identidad de prueba nunca entre al bundle de producción.
  - Una variable nueva sin clasificar da rojo.
- **R3 · Etiqueta por commit.** `frontend/cloudbuild.yaml` etiqueta `web:${_ETIQUETA}`, y el propietario la construye con `--substitutions=_ETIQUETA=$(git rev-parse --short HEAD)`. Sin `_ETIQUETA`, Cloud Build rechaza la construcción. Ya no hay etiqueta `v2`.
- **R-ADPA · Ortogonalidad ZERAG (`GCP-03b`).** Solo los tres archivos. Sin `import yaml`: `frontend/cloudbuild.yaml` se lee como texto.

## 4. Interfaz

No aplica: el login vuelve a mostrar el botón de Google sin cambiar textos.

## 5. Aceptación

| Escenario | Prueba |
| :--- | :--- |
| **Dado** `frontend/Dockerfile.cloudrun`, **entonces** `builder` declara `ARG` y `ENV` del client id antes de `RUN npm run build`. Mutación m1: quitar el `ARG` da rojo. | `test_client_id_entra_al_compilar` |
| **Dado** `frontend/cloudbuild.yaml`, **entonces** pasa `--build-arg NEXT_PUBLIC_GOOGLE_CLIENT_ID=…`. Mutación m2: quitarlo da rojo. | `test_cloudbuild_pasa_el_client_id` |
| **Dado** `frontend/src`, **entonces** cada `NEXT_PUBLIC_*` está clasificada. Las de compilación tienen `ARG`, y las solo de desarrollo no lo tienen. Mutación m3: una variable nueva sin clasificar, o un `ARG NEXT_PUBLIC_USER_ID`, da rojo. | `test_variables_del_cliente_clasificadas` |
| **Dado** `frontend/cloudbuild.yaml`, **entonces** `-t` e `images` usan `${_ETIQUETA}` y no aparece `:v2`. Mutación m4: volver a `v2` da rojo. | `test_imagen_etiquetada_por_commit` |

Tras la fusión, el propietario construye y publica la imagen. En la revisión nueva, el login muestra «Continuar con Google» y no el aviso de configuración.

## 6. Trazabilidad

- Ficha: `governance/tareas/GCP-03b.md`. Especificación de referencia: `governance/especificaciones/README.md`.
- Incidente del 2026-11-21 (revisión evydentia-web-00004-xkg), pedido del CTO. Regresión de 5cd05062.
- Depende de las fichas hechas que comparten estos archivos: EP-02, GCP-01, GCP-03, GCP-08, GCP-09, GCP-10, QA-12 y RET-05. CI-36 pasa a depender de esta.
