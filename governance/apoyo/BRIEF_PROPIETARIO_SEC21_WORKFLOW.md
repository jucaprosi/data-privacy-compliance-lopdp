# Brief para el propietario · SEC-21 · Variable `PROXIES_CONFIABLES` en el despliegue de Cloud Run
`¤seguridad` `¤entorno-pruebas`

> **Gobernanza reservada.** Este brief lo aplica el propietario: el sub chat de Seguridad no escribe en `.github/`. Ficha `governance/tareas/SEC-21.md`. Va **antes** de fusionar el PR de SEC-21.

## Por qué
SEC-21 limita por IP la ruta pública `GET /api/v1/entorno` y corrige cómo se calcula la IP del cliente. Esa IP sale de `X-Forwarded-For`, pero solo de las entradas que añaden los proxies de confianza. La variable `PROXIES_CONFIABLES` (un entero `n ≥ 0`) dice cuántos hay delante de la aplicación. Es **obligatoria en Cloud Run** (`K_SERVICE`): si falta o no es un entero, el servicio no arranca, a propósito (falla cerrado).

**Estado a 2026-11-12.** El cambio de workflow ya está en `main`: `deploy-gcp.yml` define `PROXIES_CONFIABLES=1` en `--set-env-vars` (commit `8b2422e0`). Lo que queda es comprobarlo y confirmar el ingress, antes de fusionar el PR de SEC-21. Si SEC-21 se fusionara sin esa variable, la revisión nueva de Cloud Run no arrancaría y el despliegue quedaría en rojo (Cloud Run seguiría sirviendo la revisión anterior).

## Qué hacer (PowerShell, solo lectura)

1. **Comprueba que el workflow trae la variable.** Debe imprimir una línea con `PROXIES_CONFIABLES=1`:

   ```powershell
   $RAIZ = "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"; Set-Location $RAIZ; git fetch origin; git show origin/main:.github/workflows/deploy-gcp.yml | Select-String "PROXIES_CONFIABLES"
   ```

   - **`1` es el valor de hoy:** Cloud Run sin balanceador delante. La infraestructura de Google añade la IP real del cliente como última entrada de `X-Forwarded-For`, y eso es lo que el servicio lee.
   - **Con balanceador externo** el valor cambia. No se supone: se fija con el `X-Forwarded-For` real que se vea en los logs de Cloud Run, y se anota aquí la fecha, el valor visto y el valor elegido.

2. **Confirma que el servicio de Cloud Run ya tiene la variable. Es la compuerta del PR de SEC-21: no se fusiona hasta que esto salga bien.** El arranque en la nube exige `PROXIES_CONFIABLES`; si el servicio no la tiene, el primer despliegue con SEC-21 deja `evydentia-backend` sin arrancar. Comprobación (solo lectura): debe imprimir una línea con `PROXIES_CONFIABLES` y el valor `1` (un salto: el frente de Cloud Run, sin balanceador).

   ```powershell
   $PROYECTO = "evydentia"; $REGION = "us-central1"; $SERVICIO = "evydentia-backend"; gcloud run services describe $SERVICIO --region $REGION --project $PROYECTO --format="json(spec.template.spec.containers[0].env)" | Select-String -Context 0,1 "PROXIES_CONFIABLES"
   ```

   Si no imprime nada, la variable no está puesta. Ponla tú con Antigravity (esto escribe en Google Cloud; no lo hace ninguna sesión de IA) y repite la comprobación:

   ```powershell
   $PROYECTO = "evydentia"; $REGION = "us-central1"; $SERVICIO = "evydentia-backend"; gcloud run services update $SERVICIO --region $REGION --project $PROYECTO --update-env-vars "PROXIES_CONFIABLES=1"
   ```

   Cuando salga bien, avisa al Tech Lead para que el CTO pueda fusionar el PR.

3. **Confirma el ingress del servicio.** Debe imprimir `all` mientras no haya balanceador (el despliegue no fija `--ingress`):

   ```powershell
   $PROYECTO = "evydentia"; $REGION = "us-central1"; $SERVICIO = "evydentia-backend"; gcloud run services describe $SERVICIO --region $REGION --project $PROYECTO --format="value(metadata.annotations['run.googleapis.com/ingress'])"
   ```

4. **Anota una IP real de cliente** (evidencia, no árbitro). Tras abrir una vez `GET /api/v1/entorno` en la URL `run.app` del servicio, lee un registro reciente; no copies la consulta ni datos personales:

   ```powershell
   $PROYECTO = "evydentia"; $SERVICIO = "evydentia-backend"; gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$SERVICIO AND httpRequest.requestUrl:/api/v1/entorno" --project $PROYECTO --limit 3 --format="value(httpRequest.remoteIp)"
   ```

## Requisito cuando exista el balanceador externo (no bloquea este PR)
- El ingress debe pasar a `internal-and-cloud-load-balancing`. Con ingress `all` y el balanceador delante, un atacante entra directo por la URL `run.app`, antepone una IP falsa a `X-Forwarded-For`, y el valor que cuenta el balanceador es **falsificable**: el límite por IP deja de servir.
- Se fija en el comando de despliegue (`--ingress internal-and-cloud-load-balancing`) o con `gcloud run services update`, y lo aplica el propietario con Antigravity. Si hace falta un árbitro para esto, será una ficha de nube aparte sobre `deploy-gcp.yml` o la plantilla del servicio.
- **Evidencia, no árbitro:** el propietario anota un `X-Forwarded-For` real visto en los logs y el ingress, y fija `PROXIES_CONFIABLES`.

## Complemento recomendado (no bloqueante)
Una regla de rate limit en Cloud Armor del balanceador para `/api/v1/entorno`, como segunda barrera delante de la aplicación.

## Local, CI y arnés
No hacen falta cambios: fuera de la nube la variable vale 0 si falta, y `X-Forwarded-For` se ignora (cada conexión tiene su cubeta). Un valor que no sea un entero ≥ 0 falla también fuera de la nube.
