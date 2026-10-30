# Procedimiento de despliegue y reconstrucción en Vercel
`¤ci-cd` `¤seguridad`

> Procedimiento operativo del backend (`data-privacy-compliance-lopdp`, plan **Hobby**). Los valores de las variables **nunca** se escriben en el repositorio; las carga el usuario.

## 1. Entornos y variables

| Entorno | Base de datos | Notas |
| :--- | :--- | :--- |
| **Production** | rama principal de Neon, usuario `lopdp_app` | Despliega solo al poner al día la rama `produccion`, una vez por noche (apartado 6). Fusionar en `main` no despliega. |
| **Preview** | rama `test` de Neon, usuario `lopdp_app` | Solo las ramas `preview/**`, empujadas a propósito. |

La lista de variables por entorno, sin valores, está en `governance/operaciones/VARIABLES_VERCEL.md` (tarea OPS-01). Para cargar una variable sin mostrar su valor y sin BOM (PowerShell 5.1):

```bash
$OutputEncoding = New-Object System.Text.UTF8Encoding $false; ((Get-Content .env | Select-String '^NOMBRE=' | Select-Object -Last 1).Line -replace '^NOMBRE=','').Trim() | vercel env add NOMBRE preview --sensitive --yes
```

## 2. Cuándo reconstruir

* Cambiaste una variable: las vistas previas **anteriores** al cambio conservan el valor viejo. Las que se crean después ya nacen con el valor nuevo.
* Production: se despliega al poner al día `produccion` (apartado 6); si solo cambió una variable, se reconstruye el último despliegue.

## 3. Pasos

1. **Comprobar el estado:** `vercel env ls` (qué variable está en qué entorno y desde cuándo) y `vercel ls` (qué despliegues existen y su antigüedad). Una vista previa más reciente que el último cambio de variables **no** necesita reconstruirse.
2. **Production:** el despliegue nocturno del apartado 6. Para solo reaplicar variables: `vercel redeploy <url del último despliegue de produccion> --target production`.
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

## 6. Despliegue nocturno de producción (OPS-06, 2026-10-29)

El plan gratuito permite **100 despliegues al día** y cada cambio cuenta dos veces (backend y frontend). El 2026-10-29 hubo 28 despliegues de producción con 14 fusiones a `main`. Desde OPS-06, Vercel despliega solo la rama `produccion` y las `preview/**` (`git.deploymentEnabled` en `vercel.json` y `frontend/vercel.json`, comprobado por `tests/test_vercel_despliegue.py`).

**Configuración, una sola vez, en los dos proyectos** (`data-privacy-compliance-lopdp` y `data-privacy-compliance-lopdp-frontend`): *Settings* → *Environments* → *Production* → *Branch Tracking*: rama `produccion`.

**Cada noche,** quien cerró la ventana de fusiones (regla 10 de `governance/tareas/README.md`), después de migrar producción:

```bash
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"; git fetch origin; git push origin origin/main:refs/heads/produccion
```

Eso crea dos despliegues de producción, uno por proyecto, con el `main` de esa noche. Después, verifica con `python scripts/verificar_despliegue.py <dominio>` (apartado 3, paso 4). La rama `produccion` no recibe commits propios: solo avanza hasta `main`. Si el push la rechaza por no ser un avance directo, algo se escribió en ella a mano; avisa al propietario antes de forzarlo.

