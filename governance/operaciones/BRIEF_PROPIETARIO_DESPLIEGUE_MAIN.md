# Brief para el propietario · Desplegar `main` en producción (backend y frontend)

Lo ejecuta Juan Carlos, o Aleczandra o José, desde PowerShell. Ninguna IA publica en producción: el CTO prepara el brief, comprueba con lecturas y da el visto bueno de cada paso.

Sustituye al procedimiento que se dio en el chat el 2026-11-21. Recoge lo que salió mal aquella vez:
- la imagen web `188d207c` se publicó sin el client id de Google, y se volvió a `web:v2` (GCP-03b);
- el WAF bloqueaba el login, con la firma 942421 (GCP-04b y `BRIEF_PROPIETARIO_WAF_403_LOGIN.md`).

## 0. Antes de empezar

| Comprobación | Cómo | Si falla |
|---|---|---|
| ¿Trae migraciones? | `git diff --stat <commit publicado>..origin/main -- alembic`. El commit publicado es el de la imagen del backend del paso 1. | Si hay cambios, primero `BRIEF_PROPIETARIO_MIGRACION_COMPLETA.md`: respaldo, Job `evydentia-migrate` por digest, verificación y fila en `REGISTRO_MIGRACIONES_MANUALES.md`. |
| ¿GCP-03b está en `main`? | `governance/tareas/GCP-03b.md` con `estado = "hecha"`, o el Dockerfile con `ARG NEXT_PUBLIC_GOOGLE_CLIENT_ID` en la etapa builder | **No publiques el frontend.** Sin GCP-03b la imagen sale sin client id y el login muestra «Falta configurar NEXT_PUBLIC_GOOGLE_CLIENT_ID». Publica solo el backend. |
| ¿Se lanza una sola vez? | Antes de aprobar, `gh run list --workflow deploy-gcp.yml --limit 3` | Si hay dos corridas esperando aprobación del mismo commit, cancela una (`gh run cancel <id>`) y aprueba la otra. |

## 1. Estado actual (solo lectura)

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"; git fetch origin main; foreach ($S in @("evydentia-backend", "evydentia-web")) { gcloud run services describe $S --region us-central1 --project evydentia --format="value(status.traffic[0].revisionName,status.traffic[0].percent,spec.template.spec.containers[0].image)" }
```

Anota las dos revisiones que sirven el 100 %. Son las de vuelta atrás.

## 2. Backend

### 2.1 Publicar

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"; gh workflow run deploy-gcp.yml --ref main; Start-Sleep -Seconds 5; $RUN = gh run list --workflow deploy-gcp.yml --limit 1 --json databaseId --jq ".[0].databaseId"; gh run watch $RUN --exit-status
```

El entorno `gcp-produccion` pide aprobación: en la página de la corrida, «Review pending deployments», marca `gcp-produccion` y pulsa «Approve and deploy».

### 2.2 Verificar

```powershell
gcloud run services describe evydentia-backend --region us-central1 --project evydentia --format="value(status.traffic[0].revisionName,status.traffic[0].percent,spec.template.spec.containers[0].image)"; (Invoke-WebRequest "https://app.evydentia.com/api/v1/health" -UseBasicParsing).Content
```

Debe salir una revisión nueva con el 100 % y la imagen `backend:<commit de main>`. El health debe dar `OPERATIONAL` con `"fallidos":[]`. El total de routers no siempre sube: una sala puede montar routers nuevos dentro del suyo, como hizo BOV-02b.

### 2.3 Vuelta atrás

```powershell
gcloud run services update-traffic evydentia-backend --region us-central1 --project evydentia --to-revisions "<revisión del paso 1>=100"
```

Este comando vuelve a fijar el tráfico a esa revisión. En el siguiente despliegue, comprueba que la revisión nueva recibe el 100 %. Si no lo recibe, ejecuta `gcloud run services update-traffic evydentia-backend --to-latest --region us-central1 --project evydentia`.

## 3. Frontend (solo con GCP-03b en `main`)

### 3.1 Construir la imagen con la etiqueta del commit

Tarda entre 5 y 8 minutos.

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"; git switch main; git pull --ff-only origin main; $SHA = git rev-parse --short=8 HEAD; gcloud builds submit frontend --config frontend/cloudbuild.yaml --substitutions "_ETIQUETA=$SHA" --project evydentia
```

- Desde GCP-03b, `frontend/cloudbuild.yaml` etiqueta la imagen como `web:${_ETIQUETA}` y falla si no se le pasa. Ya no existe la etiqueta fija `v2`.
- Los avisos `npm warn EBADENGINE` (paquetes que piden Node 22) no detienen la construcción. Desaparecen con CI-36.

### 3.2 Publicar

```powershell
gcloud run services update evydentia-web --image "us-central1-docker.pkg.dev/evydentia/evydentia-containers/web:$SHA" --region us-central1 --project evydentia
```

`services update` solo cambia la imagen. Las variables (`APP_ENV`, `BACKEND_URL`, `NEXT_PUBLIC_GOOGLE_CLIENT_ID`), la cuenta de servicio y el ingress siguen como estaban.

Después lleva el tráfico a la revisión nueva:

```powershell
gcloud run services update-traffic evydentia-web --to-latest --region us-central1 --project evydentia
```

- La salida debe decir `100% LATEST (currently evydentia-web-000NN-xxx)`, con la revisión que acaba de crear `services update`.
- Hace falta porque una vuelta atrás (3.4) fija el tráfico a una revisión. Desde ese momento, cada `services update` crea revisiones nuevas que no reciben tráfico. Así pasó el 2026-11-22: la revisión 00005 quedó lista, pero el tráfico seguía en la 00003.
- Si el tráfico ya seguía a la más reciente, el comando no cambia nada.

### 3.3 Verificar que el client id llegó al navegador

```powershell
$x = Invoke-WebRequest "https://app.evydentia.com/login" -UseBasicParsing; $js = [regex]::Matches($x.Content, '/_next/static/chunks/[^"]+\.js') | ForEach-Object { $_.Value } | Select-Object -Unique; $ok = $false; foreach ($j in $js) { if ((Invoke-WebRequest ("https://app.evydentia.com" + $j) -UseBasicParsing).Content -match "apps\.googleusercontent\.com") { $ok = $true; break } }; if ($ok) { "OK: el client id está en el bundle" } else { "FALTA el client id: vuelve atrás (3.4)" }
```

Después, en el navegador, entra con tu cuenta y comprueba tres cosas:
- el login pasa y llega al panel;
- al cerrar y volver a abrir la aplicación no sale «403 Forbidden», porque el WAF ya no bloquea la cookie de Google Identity (GCP-04b);
- las pantallas nuevas del despliegue se ven.

### 3.4 Vuelta atrás

Solo si 3.3 dice «FALTA» o si el login falla en el navegador. Con «OK» y el login bien, no se ejecuta.

```powershell
gcloud run services update-traffic evydentia-web --region us-central1 --project evydentia --to-revisions "<revisión del paso 1>=100"
```

Este comando vuelve a fijar el tráfico a esa revisión. En la siguiente publicación, el `update-traffic --to-latest` de 3.2 es obligatorio.

## 4. Si aparece un 403

- **Página en blanco «403 Forbidden»:** la responde Cloud Armor, no la aplicación. Lee el bloqueo; el registro del balanceador está activado desde el 2026-11-22:

```powershell
gcloud logging read 'resource.type="http_load_balancer" AND jsonPayload.enforcedSecurityPolicy.outcome="DENY"' --project evydentia --freshness=30m --limit 5 --format="value(timestamp,httpRequest.requestUrl,jsonPayload.enforcedSecurityPolicy.priority,jsonPayload.enforcedSecurityPolicy.preconfiguredExprIds)"
```

  Pasa la firma al CTO. Cada exclusión nueva necesita su evidencia en `governance/especificaciones/GCP-04b.md`, §1.
- **«No se pudieron consultar tus organizaciones: el servidor respondió 403» sin DENY en el registro:** el 403 lo da el backend. La cuenta no está en `users` ni en `operadores_plataforma`. Ve al §5.

## 5. Dar de alta un correo

- **Operador de la plataforma** (entra en `/plataforma`, da de alta organizaciones y emite invitaciones). Necesitas `$env:MIGRATION_DATABASE_URL` cargada solo en la sesión, por el Cloud SQL Auth Proxy, nunca en un archivo.

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"; python -m features.plataforma.administrar_operadores listar
```

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"; python -m features.plataforma.administrar_operadores alta <correo> "<nombre>"
```

- **Miembro de una organización:** desde la aplicación. Un operador emite la invitación desde `/plataforma`, o un administrador de la organización la da de alta en Organización → Usuarios.

## 6. Confirmar en el chat del CTO

Pega:

> Backend `<revisión>` (`<commit>`) y web `<revisión>` (`web:<commit>`) publicados; health OPERATIONAL sin fallidos; client id OK; login y reapertura sin 403.

Si el despliegue trajo migraciones, añade la fila de `REGISTRO_MIGRACIONES_MANUALES.md`.
