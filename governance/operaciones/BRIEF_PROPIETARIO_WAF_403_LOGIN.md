# Brief para el propietario · 403 al consultar las organizaciones tras el login (2026-11-22)

Lo ejecuta Juan Carlos con Antigravity. Ninguna IA cambia Google Cloud ni consulta la base de producción.

**Síntoma.** Google autentica, pero la pantalla dice «No se pudieron consultar tus organizaciones: el servidor respondió 403». Ocurrió hacia las 15:04 UTC del 2026-11-22, con la cuenta `juancarlosproanio@gmail.com`, en evydentia-web-00003-m7w y evydentia-backend-00013-d4t.

## Lo medido (solo lectura)

| Hecho | Fuente |
|---|---|
| `evydentia-backend` no registra nada desde las 03:28 UTC; la llamada a `/api/v1/organizacion/mis-organizaciones` no llegó | CTO, gcloud logging |
| Los dos servicios de backend tienen `evydentia-waf` y el registro del balanceador desactivado | CTO, gcloud compute |
| Las reglas 1000 (`sqli-v33-stable`) y 1001 (`xss-v33-stable`) son `deny(403)`, sin `sensitivity` | `governance/operaciones/cloud_load_balancer.yaml:11-16` |
| Una cuenta no registrada recibe un 403 del **backend** («Usuario no registrado en la plataforma.»), y ese 403 sí quedaría en el registro de Cloud Run | `app_core/security.py:167-190` |

**Hipótesis principal [I]:** falso positivo de Cloud Armor sobre la cabecera `Authorization: Bearer <token de Google>`.

`evaluatePreconfiguredWaf('…-v33-stable')` sin `sensitivity` evalúa todas las firmas, hasta el nivel 4 de paranoia. A ese nivel, un JWT largo en base64url dispara firmas de SQLi con facilidad. Que el backend no registre nada es coherente con esta hipótesis.

**Segunda causa posible.** La cuenta sin «s» puede no estar en `users`. El correo del propietario en el repositorio lleva «s». El paso 3 lo comprueba.

## Paso 0 · Variables (PowerShell)

```powershell
$PROYECTO = "evydentia"; $POLITICA = "evydentia-waf"; $BS = "evydentia-backend-bs"
```

## Paso 1 · Diagnóstico: activar el registro y reintentar

```powershell
gcloud compute backend-services update $BS --global --enable-logging --logging-sample-rate=1 --project $PROYECTO
```

Vuelve a entrar en https://app.evydentia.com con la misma cuenta y espera un minuto. Luego lee el bloqueo:

```powershell
gcloud logging read 'resource.type="http_load_balancer" AND jsonPayload.enforcedSecurityPolicy.outcome="DENY"' --project $PROYECTO --freshness=30m --limit 5 --format="json(timestamp,httpRequest.requestUrl,jsonPayload.enforcedSecurityPolicy)"
```

Anota `priority`, `name` y `preconfiguredExprIds`, por ejemplo `owasp-crs-v030301-id942432-sqli`, y pásaselos al Arquitecto.

- Si no sale ningún DENY y la petición llega al backend, la causa no es el WAF: sigue en el paso 3.
- Si no llega ni al balanceador, pasa la salida de los registros de `evydentia-web` al CTO.

## Paso 2 · Corrección, según el resultado del paso 1

Hay dos opciones. Ninguna apaga la regla.

**2a · Exclusión de campo (preferida si es una o dos firmas).** Excluye solo la cabecera `Authorization` de las firmas que salieron en el paso 1. Repite el comando por cada regla (1000 o 1001) y conjunto (`sqli-v33-stable` o `xss-v33-stable`) que aparezca:

```powershell
gcloud compute security-policies rules add-preconfig-waf-exclusion 1000 --security-policy $POLITICA --target-rule-set "sqli-v33-stable" --target-rule-ids "<id_del_paso_1>" --request-header-to-exclude "op=EQUALS,val=authorization" --project $PROYECTO
```

**2b · Sensibilidad 1 (si salen muchas firmas distintas).** Deja la regla con las firmas de nivel 1, que son las de menos falsos positivos:

```powershell
gcloud compute security-policies rules update 1000 --security-policy $POLITICA --expression "evaluatePreconfiguredWaf('sqli-v33-stable', {'sensitivity': 1})" --project $PROYECTO
```

Si también bloqueó la 1001, repite el comando con `1001` y `xss-v33-stable`.

Vuelve a entrar con la cuenta. Si el login pasa, repite la lectura del paso 1 para confirmar que no hay DENY nuevos. Después avisa al Arquitecto qué opción aplicaste, para reflejarla en `cloud_load_balancer.yaml`.

## Paso 3 · ¿La cuenta está registrada? (solo lectura, en la base de producción)

```sql
SELECT id, email, google_sub IS NOT NULL AS vinculada, activo, deleted_at FROM users WHERE lower(email) IN ('juancarlosproanio@gmail.com', 'juancarlosproanios@gmail.com');
SELECT email, google_sub IS NOT NULL AS vinculada FROM operadores_plataforma WHERE lower(email) IN ('juancarlosproanio@gmail.com', 'juancarlosproanios@gmail.com');
```

- Si la cuenta sin «s» no aparece en `users`, el backend responderá 403 «Usuario no registrado» incluso con el WAF corregido. Entra con la cuenta registrada o da de alta la otra.
- Si aparece vinculada a otro `google_sub`, el 403 es «La cuenta está vinculada a otra identidad de Google».

## Paso 4 · Dejar el registro activado

No lo desactives al terminar. Así, el próximo bloqueo de Cloud Armor deja rastro. Activa también el del frontend:

```powershell
gcloud compute backend-services update evydentia-web-bs --global --enable-logging --logging-sample-rate=1 --project $PROYECTO
```

El Arquitecto propone al Tech Lead una ficha que lo fije en `cloud_load_balancer.yaml` con su árbitro.
