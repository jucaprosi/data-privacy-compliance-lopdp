# Brief del propietario · Migrar Cloud SQL con la imagen de `main` y publicar

Fecha: 2026-11-15. Redactado por el CTO de EVYDENTIA. Lo ejecuta el propietario con Antigravity, que tiene acceso a `gcloud` y a `gh`. Ninguna sesión de IA escribe en Google Cloud ni en la base.

## Por qué

Las migraciones de CON-01, BOV-02, NORM-03 y DER-01 están en `main` (6d63f402) y no en Cloud SQL. El job `evydentia-migrate` migra con una imagen fijada por su digest, pero la imagen más reciente del repositorio de contenedores es del 2026-11-13 y no las contiene. `deploy-gcp.yml` construye la imagen y publica la revisión en un solo paso, así que hoy no hay forma de obtener el digest de una imagen de `main` sin publicar antes, y nunca se publica antes de migrar.

Este brief añade al workflow una entrada `publicar` y ejecuta la secuencia completa: construir, copia de respaldo, migrar, verificar, publicar.

## Reglas para quien ejecute

- No escribas contraseñas, URL de conexión ni secretos en ningún archivo, comando de ejemplo, salida pegada ni mensaje. Se leen desde Secret Manager dentro de Google Cloud, nunca se copian.
- Si un paso falla, **detente** y avisa al CTO con la salida del error. No reintentes, no sigas al paso siguiente y no publiques.
- No uses `latest` para migrar: se fija siempre el digest.
- Los pasos 1 y 8 cambian archivos del repositorio y van por PR desde una rama `tarea/juan-carlos/<id>` creada desde `origin/main`. Nunca se empuja a `main`.

## Paso 1 · Añadir la entrada `publicar` a `deploy-gcp.yml` (PR)

```powershell
cd "$env:USERPROFILE\Desktop\Plataforma LOPDP 360"
git fetch origin main
git switch -c tarea/juan-carlos/deploy-solo-construir origin/main
```

Edita `.github/workflows/deploy-gcp.yml` con tres cambios y ninguno más.

**a)** El disparador pasa a:

```yaml
on:
  workflow_dispatch:
    inputs:
      publicar:
        description: "true publica la revisión en Cloud Run; false solo construye la imagen y muestra su digest"
        type: boolean
        default: true
```

**b)** El paso «Build and Push Docker Image» pasa a tener un `id` y a mostrar el digest al terminar:

```yaml
      - name: Build and Push Docker Image
        id: imagen
        run: |
          IMAGE_TAG="${{ env.IMAGE_NAME }}:${{ github.sha }}"
          IMAGE_LATEST="${{ env.IMAGE_NAME }}:latest"

          docker build -t "$IMAGE_TAG" -t "$IMAGE_LATEST" .
          docker push "$IMAGE_TAG"
          docker push "$IMAGE_LATEST"

          DIGEST="$(docker inspect --format='{{index .RepoDigests 0}}' "$IMAGE_TAG" | cut -d@ -f2)"
          echo "digest=$DIGEST" >> "$GITHUB_OUTPUT"
          echo "### Imagen construida" >> "$GITHUB_STEP_SUMMARY"
          echo "- Commit: ${{ github.sha }}" >> "$GITHUB_STEP_SUMMARY"
          echo "- Digest: $DIGEST" >> "$GITHUB_STEP_SUMMARY"
```

**c)** El paso «Deploy to Cloud Run» lleva, justo debajo de su `name:`, esta línea y nada más:

```yaml
        if: ${{ inputs.publicar }}
```

Comprueba antes de abrir el PR que ninguna prueba depende del texto del workflow:

```powershell
cd "$env:USERPROFILE\Desktop\Plataforma LOPDP 360"
git grep -l "deploy-gcp" -- tests
python -m pytest -q $(git grep -l "deploy-gcp" -- tests)
```

Abre el PR, espera el CI en verde y avisa al CTO para que lo revise y lo fusione. No sigas hasta que esté en `main`.

## Paso 2 · Construir la imagen de `main` sin publicar

```powershell
cd "$env:USERPROFILE\Desktop\Plataforma LOPDP 360"
git switch main
git pull --ff-only
git log --oneline -1
gh workflow run deploy-gcp.yml --ref main -f publicar=false
Start-Sleep -Seconds 5
$RUN = gh run list --workflow deploy-gcp.yml --limit 1 --json databaseId --jq ".[0].databaseId"
gh run watch $RUN --exit-status
```

Si el entorno `gcp-produccion` pide aprobación, apruébala en la página de la corrida. Al terminar, lee el digest del resumen de la corrida y compruébalo en el repositorio de contenedores:

```powershell
gh run view $RUN --log | Select-String "Digest:"
gcloud artifacts docker images list us-central1-docker.pkg.dev/evydentia/evydentia-containers/backend --include-tags --sort-by=~UPDATE_TIME --limit=3 --project=evydentia
```

La imagen nueva debe llevar como etiqueta el hash del commit que mostró `git log` y una fecha de hoy. Si no, detente.

## Paso 3 · Copia de respaldo a demanda

```powershell
gcloud sql backups create --instance evydentia-production --project evydentia
gcloud sql backups list --instance evydentia-production --project evydentia --limit 2
```

La copia debe aparecer en estado `SUCCESSFUL` antes de seguir.

## Paso 4 · Migrar con el digest

Pega aquí el digest completo del paso 2, con el prefijo `sha256:` y sin los signos `<` `>`:

```powershell
$DIGEST = "sha256:PEGA_AQUI_EL_DIGEST_DE_64_CARACTERES"
if ($DIGEST -notmatch '^sha256:[0-9a-f]{64}$') { throw "El digest no es válido: pega el valor real." }
gcloud run jobs update evydentia-migrate --image="us-central1-docker.pkg.dev/evydentia/evydentia-containers/backend@$DIGEST" --region=us-central1 --project=evydentia
gcloud run jobs describe evydentia-migrate --region=us-central1 --project=evydentia --format="value(spec.template.spec.template.spec.containers[0].image)"
```

La última línea debe mostrar la imagen con `@sha256:` y el digest elegido. Si es así, ejecuta:

```powershell
gcloud run jobs execute evydentia-migrate --region=us-central1 --project=evydentia --wait
```

## Paso 5 · Verificar la migración

```powershell
gcloud run jobs executions list --job evydentia-migrate --region us-central1 --project evydentia --limit 1
gcloud logging read "resource.type=cloud_run_job AND resource.labels.job_name=evydentia-migrate" --project evydentia --limit 80 --freshness 1h --format="value(textPayload)" | Select-String "Running upgrade"
cd "$env:USERPROFILE\Desktop\Plataforma LOPDP 360"
python -m alembic heads
```

La ejecución debe figurar como completada con éxito. Las revisiones de las líneas `Running upgrade … -> <revisión>` deben cubrir las cabezas que da `alembic heads` (una por sala). Con `main` en 6d63f402 son:

- `con01_politicas_conservacion`
- `20261101_diag_objeciones`
- `norm03_analisis_impacto`
- `bov02_boveda_objetos_custodia`
- `der01_derechos_respuestas`

Si una de esas cabezas no aparece en el registro y tampoco la aplicó una ejecución anterior, **no publiques** y avisa al CTO. Si el registro no muestra ninguna línea `Running upgrade`, la base ya estaba al día: también avisa antes de publicar.

Si la ejecución falla:

- **DER-01** cuenta antes las solicitudes contestadas sin evidencia y, si hay alguna, aborta dando el recuento, sin modificar datos. Pega ese número al CTO: la corrección de esas filas es decisión del propietario.
- Para cualquier otro fallo, pega al CTO las últimas 50 líneas del registro. No intentes reparar la base a mano.

## Paso 6 · Publicar

Solo con el paso 5 completo. La migración y la publicación van seguidas: entre ellas, la revisión antigua corre contra el esquema nuevo. Si `ret02_clave_objeto` (renombra `r2_key` a `clave_objeto`) estaba entre las pendientes, esa revisión antigua falla en las pantallas de evidencia hasta que se publique; no dejes pasar tiempo.

```powershell
cd "$env:USERPROFILE\Desktop\Plataforma LOPDP 360"
gh workflow run deploy-gcp.yml --ref main -f publicar=true
Start-Sleep -Seconds 5
$RUN = gh run list --workflow deploy-gcp.yml --limit 1 --json databaseId --jq ".[0].databaseId"
gh run watch $RUN --exit-status
```

## Paso 7 · Comprobar la revisión nueva (solo lectura)

```powershell
gcloud run revisions list --service evydentia-backend --region us-central1 --project evydentia --limit 2 --format="table(metadata.name,metadata.creationTimestamp,spec.containers[0].image.basename())"
gcloud run services describe evydentia-backend --region us-central1 --project evydentia --format="value(status.latestReadyRevisionName,status.url)"
```

Con la URL del dominio público, comprueba `/api/v1/health`. Debe responder 200.

## Paso 8 · Anotarlo (PR)

Añade una entrada en `governance/operaciones/REGISTRO_MIGRACIONES_MANUALES.md`: fecha, commit de `main`, digest, ejecución del job, revisiones aplicadas y revisión de Cloud Run publicada. Va por PR, igual que el paso 1.

## Qué no hace este brief

- No toca secretos, `lopdp_app`, buckets, ni la facturación.
- No cambia `--min-instances`.
- No migra CCTV-01 (#825): cuando se fusione, su migración se aplica repitiendo los pasos 2 a 7.
