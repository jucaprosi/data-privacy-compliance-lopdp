# Procedimiento de despliegue y reconstrucción en Vercel

> **Histórico · PMV congelado; vigente solo para la rama `produccion`.** Movido desde su ruta anterior por NEON-04 (2026-11-12) con `git mv`; `main` es solo EVYDENTIA.
>
> **Nota sobre el PMV (2026-11-09):** la rama `pmv/consolidacion` se creó a partir de `produccion` (6cf7131d). El trabajo de Aleczandra sobre el PMV va en ramas `pmv/aleczandra/<tema>` con PR hacia `pmv/consolidacion`, probado contra la base de pruebas del PMV `test-aleczandra`; `main` queda solo para EVYDENTIA. Publicar al PMV es un PR de `pmv/consolidacion` hacia `produccion` con aprobación de otra persona, decisión del propietario.

`¤ci-cd` `¤seguridad`

> Procedimiento operativo del backend (`data-privacy-compliance-lopdp`, plan **Hobby**). Los valores de las variables **nunca** se escriben en el repositorio; las carga el usuario.

## 1. Entornos y variables

| Entorno | Base de datos | Notas |
| :--- | :--- | :--- |
| **Production** | rama principal de Neon, usuario `lopdp_app` | Despliega solo al fusionar un PR de `main` hacia `produccion`, una vez por noche y con la aprobación de otra persona (apartado 6). Fusionar en `main` no despliega. |
| **Preview** | rama `test` de Neon, usuario `lopdp_app` | Solo las ramas `preview/**`, empujadas a propósito. |

La lista de variables por entorno, sin valores, está en `governance/historico/pmv/VARIABLES_VERCEL.md` (tarea OPS-01). Para cargar una variable sin mostrar su valor y sin BOM (PowerShell 5.1):

```bash
$OutputEncoding = New-Object System.Text.UTF8Encoding $false; ((Get-Content .env | Select-String '^NOMBRE=' | Select-Object -Last 1).Line -replace '^NOMBRE=','').Trim() | vercel env add NOMBRE preview --sensitive --yes
```

## 2. Cuándo reconstruir

* Cambiaste una variable: las vistas previas **anteriores** al cambio conservan el valor viejo. Las que se crean después ya nacen con el valor nuevo.
* Production: se despliega al fusionar el PR a `produccion` (apartado 6); si solo cambió una variable, se reconstruye el último despliegue.

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

## 6. Despliegue nocturno de producción (OPS-06, 2026-10-29; con aprobación desde 2026-11-02)

El plan gratuito permite **100 despliegues al día** y cada cambio cuenta dos veces (backend y frontend). El 2026-10-29 hubo 28 despliegues de producción con 14 fusiones a `main`. Desde OPS-06, Vercel despliega solo la rama `produccion` y las `preview/**` (`git.deploymentEnabled` en `vercel.json` y `frontend/vercel.json`, comprobado por `tests/test_vercel_despliegue.py`).

**Configuración, una sola vez, en los dos proyectos** (`data-privacy-compliance-lopdp` y `data-privacy-compliance-lopdp-frontend`): *Settings* → *Environments* → *Production* → *Branch Tracking*: rama `produccion`.

**Regla de GitHub para `produccion` (2026-11-02).** En *Settings* → *Rules* → *Rulesets* → `produccion`, sin lista de excepciones: borrar la rama y reescribir su historia están prohibidos, y toda actualización exige un PR con 1 aprobación. La aprobación debe venir de alguien distinto de quien empujó el último commit, se descarta si después se empujan commits nuevos y el único método de fusión permitido es *Merge*. No se exige estado de CI en ese PR, porque esos commits ya pasaron el CI en `main`. La configuración se comprueba en el panel de GitHub.

**Cada noche,** quien cerró la ventana de fusiones (regla 10 de `governance/tareas/README.md`) primero migra producción y después publica:

1. Abre el PR de `main` hacia `produccion`:

```bash
gh pr create --repo jucaprosi/data-privacy-compliance-lopdp --base produccion --head main --title "Publicación AAAA-MM-DD" --body "Publica main en producción, ya migrada."
```

2. Otra persona del equipo lo aprueba en GitHub. Quien abrió el PR no puede aprobarlo.
3. Se fusiona con *Merge pull request*. Eso crea dos despliegues de producción, uno por proyecto, con el `main` de esa noche.
4. Verifica con `python scripts/verificar_despliegue.py data-privacy-compliance-lopdp.vercel.app` (apartado 3, paso 4). Usa el dominio del backend: el del frontend no sirve `/openapi.json` y el verificador falla ahí aunque el despliegue esté sano.

Si GitHub no deja fusionar el PR, falta una aprobación o se empujaron commits después de aprobarlo: pide una aprobación nueva. La rama `produccion` solo recibe fusiones de `main`. Cada publicación añade un commit de fusión, así que ya no coincide con `main` commit a commit; para saber qué falta publicar compara con `git diff origin/produccion origin/main`.

**Ninguna IA publica por su cuenta.** El empuje directo a `produccion` lo rechaza la regla de GitHub. Las sesiones de Claude Code de la máquina del propietario llevan además reglas de denegación en `~/.claude/settings.json` para empujar a `produccion`, usar el CLI `vercel`, llamar con `curl` a `vercel.com` y usar `gh api` sobre rulesets y protecciones. Esas reglas valen por máquina y no se versionan: las sesiones de Aleczandra y José necesitan las suyas. Una IA puede abrir el PR, pero lo aprueba una persona. Cualquiera con permiso de escritura puede aprobar, así que la solicitud expresa del propietario es un acuerdo del equipo y no una restricción técnica. El riesgo que queda es una IA que use el token de una cuenta administradora, que podría editar la propia regla.

**Emergencia.** Si hay que publicar sin otra persona disponible, el propietario puede desactivar la regla un momento en *Settings* → *Rules* → *Rulesets*, publicar y reactivarla. Anota el motivo y la hora en el PR. Para volver atrás no hace falta tocar la rama: *Promote to Production* del despliegue anterior (apartado 3, paso 5).
