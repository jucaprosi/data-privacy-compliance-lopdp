# Procedimiento de despliegue y reconstrucción en Vercel
`¤ci-cd` `¤seguridad`

> Procedimiento operativo del backend (`data-privacy-compliance-lopdp`, plan **Hobby**). Los valores de las variables **nunca** se escriben en el repositorio; las carga el usuario.

## 1. Entornos y variables

| Entorno | Base de datos | Notas |
| :--- | :--- | :--- |
| **Production** | rama principal de Neon, usuario `lopdp_app` | Despliega solo al fusionar a `main`. |
| **Preview** | rama `test` de Neon, usuario `lopdp_app` | Una vista previa por rama o PR. |

La lista de variables por entorno, sin valores, está en `governance/operaciones/VARIABLES_VERCEL.md` (tarea OPS-01). Para cargar una variable sin mostrar su valor y sin BOM (PowerShell 5.1):

```bash
$OutputEncoding = New-Object System.Text.UTF8Encoding $false; ((Get-Content .env | Select-String '^NOMBRE=' | Select-Object -Last 1).Line -replace '^NOMBRE=','').Trim() | vercel env add NOMBRE preview --sensitive --yes
```

## 2. Cuándo reconstruir

* Cambiaste una variable: las vistas previas **anteriores** al cambio conservan el valor viejo. Las que se crean después ya nacen con el valor nuevo.
* Production: se despliega al fusionar a `main`; si solo cambió una variable, se reconstruye el último despliegue.

## 3. Pasos

1. **Comprobar el estado:** `vercel env ls` (qué variable está en qué entorno y desde cuándo) y `vercel ls` (qué despliegues existen y su antigüedad). Una vista previa más reciente que el último cambio de variables **no** necesita reconstruirse.
2. **Production:** fusionar a `main` con la CI en verde. Para solo reaplicar variables: `vercel redeploy <url del último despliegue de main> --target production`.
3. **Vistas previas anteriores al cambio:** `vercel redeploy <url de la vista previa>`.
4. **Verificar** con `python scripts/verificar_despliegue.py <dominio>` (tarea OPS-03): debe devolver 0 (`/api/v1/health` 200 con `OPERATIONAL`, todos los routers cargados y las rutas esperadas en `/openapi.json`).
5. **Si falla:** *Promote to Production* del despliegue anterior y mirar `vercel logs <url>` (el detalle del error está en el log, no en la respuesta). **No** usar *Redeploy* sobre filas «Redeploy of …»: repiten código antiguo y sustituyen al despliegue correcto.

## 4. Límites del plan gratuito (documentación de Vercel, 2026-08-24)

* Duración de una función: 300 s (por defecto y máximo); se fija con `maxDuration` en `vercel.json`.
* Cron Jobs: solo uno al día. No sirven para consumir una cola.
* El inicio de sesión con Google no se puede probar en las vistas previas: sus direcciones cambian y no se pueden registrar una a una como orígenes autorizados.

## 5. Estado verificado el 2026-10-10

* `DATABASE_URL` de Production y de Preview usan `lopdp_app`; las 10 vistas previas más recientes se construyeron después del cambio.
* Production responde `/api/v1/health` con 200, `OPERATIONAL` y 16 de 16 routers.
* Preview no tiene `CORS_ORIGINS` ni `DEEPSEEK_MODEL`, que Production sí tiene (se corrige en OPS-01).
