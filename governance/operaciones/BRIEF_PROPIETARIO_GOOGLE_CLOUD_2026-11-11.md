# Brief para el propietario · Google Cloud de EVYDENTIA con Antigravity (orden de ejecución)

Lo ejecuta Juan Carlos con Antigravity. Proyecto de Google Cloud: `evydentia`, región `us-central1`. Ninguna IA del repositorio crea recursos en la nube: esto lo ejecuta Antigravity bajo la cuenta del propietario, paso a paso.

## Reglas para Antigravity (valen para todos los bloques)
1. Antes de empezar: `cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"; git checkout main; git pull`, y `gcloud config set project evydentia`. Confirma con `gcloud config get-value project` que dice `evydentia`.
2. Un bloque por vez. Al terminar cada uno, ejecuta sus comprobaciones de solo lectura y pega la salida al propietario. No pases al siguiente si alguna falla.
3. Si un comando falla: NO borres nada, NO reintentes con variantes, NO uses `--force`. Detente y pega el error completo.
4. Nunca muestres ni guardes valores de secretos, claves ni URL de conexión en el chat, en archivos ni en el repositorio. Nada contra la base de producción. No uses el `.env` de la carpeta principal.
5. No lances ningún despliegue (`deploy-gcp.yml` es manual y no se ejecuta en este brief).
6. Los comandos exactos están en los briefs del repositorio (carpeta `governance/operaciones/`). Usa esos archivos tal cual; sustituye solo los valores que cada uno marca como parámetros.

## Bloque 0 · Lectura (no cambia nada)
- Estado de los recursos: `gcloud run services list --region us-central1`, `gcloud secrets list`, `gcloud storage buckets list`, `gcloud services list --enabled --filter="name:aiplatform.googleapis.com"`.
- Presupuesto de conexiones de Cloud SQL (lo necesita GCP-05): `gcloud sql instances list` y `gcloud sql instances describe <instancia> --format="yaml(settings.tier,settings.databaseFlags,settings.dataDiskSizeGb)"`. Pega el resultado al propietario; no lo guardes en el repositorio.

## Bloque 1 · Workflow de despliegue: hecho
`.github/workflows/deploy-gcp.yml` ya lleva `PROXIES_CONFIABLES=1`, `CORS_ORIGINS=https://app.evydentia.com` y el secreto `INVENTARIO_CLAVE_CIFRADO=INVENTARIO_CLAVE_CIFRADO:latest` (PR #619, fusionado el 2026-11-12). Como el workflow ya referencia el secreto, **no se lanza ningún despliegue hasta terminar el bloque 2**. El ingress del backend no se cierra hasta el bloque 6.

## Bloque 2 · Secreto del inventario
Brief: `governance/operaciones/BRIEF_PROPIETARIO_SECRETO_INVENTARIO.md` (pasos 1 a 5). Crea el secreto con una clave nueva sin mostrarla y dale lectura solo a la cuenta de servicio del backend.

## Bloque 3 · Bucket de evidencias
Brief: `governance/operaciones/BRIEF_PROPIETARIO_BUCKET_EVIDENCIAS.md`. Al terminar, comprueba si fijar la retención por objeto exige además el permiso `storage.objects.update` y dile al propietario el resultado: si lo exige, el rol personalizado del brief hay que ajustarlo antes de seguir. La retención NO se bloquea (sin Object Lock / WORM) hasta que el abogado confirme los plazos.

## Bloque 4 · Demo
Briefs: `BRIEF_PROPIETARIO_BUCKET_DEMO.md` (bucket sin retención y comprobación de que no la tiene) y después `BRIEF_PROPIETARIO_DEMO05.md` (Job de purga nocturna y su Scheduler). La demo no se activa hasta que el propietario lo decida.

## Bloque 5 · Vertex AI
Brief: `governance/operaciones/BRIEF_PROPIETARIO_VERTEX.md`: habilitar la API y dar el rol mínimo a la cuenta de servicio del backend. Es la condición para la «Evidencia de humo» de IA-03.

## Bloque 6 · Balanceador HTTPS de `app.evydentia.com`
Brief: `governance/operaciones/BRIEF_PROPIETARIO_BALANCEADOR.md` (pasos 0 a 8). Importante: el paso 7 (cerrar el ingress del backend) solo cuando `https://app.evydentia.com/api/v1/entorno` responda por el balanceador. Después del paso 6, mira en los registros de Cloud Run cuántas direcciones trae `X-Forwarded-For` en una petición real y dile al propietario el resultado (de eso depende si `PROXIES_CONFIABLES` pasa de 1 a 2).

## Lo que NO es de este brief
Aplicar migraciones a producción, reglas de GitHub, el workflow de EP-07 y la rotación de las credenciales de la base remota del PMV.

## Al terminar cada bloque
Una línea al propietario: bloque, qué se creó o cambió, resultado de las comprobaciones. El propietario se la pasa al CTO.
