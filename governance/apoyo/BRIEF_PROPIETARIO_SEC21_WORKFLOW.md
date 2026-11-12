# Brief para el propietario · SEC-21 · Variable `PROXIES_CONFIABLES` en el despliegue de Cloud Run
`¤seguridad` `¤entorno-pruebas`

> **Gobernanza reservada.** Este brief lo aplica el propietario: el sub chat de Seguridad no escribe en `.github/`. Ficha `governance/tareas/SEC-21.md`. Va **antes** de fusionar el PR de SEC-21.

## Por qué
SEC-21 limita por IP la ruta pública `GET /api/v1/entorno` y corrige cómo se calcula la IP del cliente. Esa IP sale de `X-Forwarded-For`, pero solo de las entradas que añaden los proxies de confianza. La variable `PROXIES_CONFIABLES` (un entero `n ≥ 0`) dice cuántos hay delante de la aplicación. Es **obligatoria en Cloud Run** (`K_SERVICE`): si falta o no es un entero, el servicio no arranca, a propósito (falla cerrado).

**Consecuencia del orden.** `deploy-gcp.yml` despliega en cada push a `main`. Si SEC-21 se fusiona sin la variable en el comando de despliegue, la revisión nueva no arranca y el despliegue falla; Cloud Run sigue sirviendo la revisión anterior, pero `main` queda con el despliegue en rojo. Por eso el cambio de workflow va primero.

## Qué hacer

1. **Añade la variable a `--set-env-vars`** del paso «Deploy to Cloud Run» de `.github/workflows/deploy-gcp.yml`:

   ```text
   --set-env-vars "APP_ENV=production,ENVIRONMENT=production,PROJECT_ID=${{ env.PROJECT_ID }},GCP_STORAGE_BUCKET=${{ env.PROJECT_ID }},PROXIES_CONFIABLES=1"
   ```

   - **`1` es el valor de hoy:** Cloud Run sin balanceador delante. La infraestructura de Google añade la IP real del cliente como última entrada de `X-Forwarded-For`, y eso es lo que el servicio lee hoy.
   - **Con balanceador externo** el valor cambia. No se supone: se fija con el `X-Forwarded-For` real que se vea en los logs de Cloud Run (`gcloud logging read`, solo lectura) y se anota aquí la fecha, el valor visto y el valor elegido.

2. **Confirma el ingress de Cloud Run** (solo lectura):

   ```bash
   gcloud run services describe NOMBRE_DEL_SERVICIO --region us-central1 --project ID_DEL_PROYECTO --format="value(metadata.annotations['run.googleapis.com/ingress'])"
   ```

   Hoy el despliegue no fija `--ingress`, así que el valor es `all`. Eso es correcto **mientras no haya balanceador**.

## Requisito cuando exista el balanceador externo (no bloquea este PR)
- El ingress debe pasar a `internal-and-cloud-load-balancing`. Con ingress `all` y el balanceador delante, un atacante entra directo por la URL `run.app`, antepone una IP falsa a `X-Forwarded-For`, y el valor que cuenta el balanceador es **falsificable**: el límite por IP deja de servir.
- Se fija en el comando de despliegue (`--ingress internal-and-cloud-load-balancing`) o con `gcloud run services update`, y lo aplica el propietario con Antigravity. Si hace falta un árbitro para esto, será una ficha de nube aparte sobre `deploy-gcp.yml` o la plantilla del servicio.
- **Evidencia, no árbitro:** el propietario anota un `X-Forwarded-For` real visto en los logs y el ingress, y fija `PROXIES_CONFIABLES`.

## Complemento recomendado (no bloqueante)
Una regla de rate limit en Cloud Armor del balanceador para `/api/v1/entorno`, como segunda barrera delante de la aplicación.

## Local, CI y arnés
No hacen falta cambios: fuera de la nube la variable vale 0 si falta, y `X-Forwarded-For` se ignora (cada conexión tiene su cubeta). Un valor que no sea un entero ≥ 0 falla también fuera de la nube.
