# Brief para el propietario · EP-07 · Flujo de GitHub del verificador del entorno de pruebas
`¤entorno-pruebas` `¤arbitro`

> **Gobernanza reservada.** Este brief lo aplica el propietario: el sub chat no escribe en `.github/`. Decisión del CTO del 2026-11-08 (ficha `governance/tareas/EP-07.md`). Contrato: `PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5 e invariante 57.

## Qué hace
Crea `.github/workflows/entorno-pruebas.yml`, con un job, `verificar-entorno-pruebas`, que corre `scripts/verificar_entorno_pruebas.py` contra el entorno de pruebas y registra su resultado con `scripts/digest_verificado.py` (EP-06).

- **Cuándo corre:** a mano (`workflow_dispatch`) o cuando termina un despliegue en pruebas. El despliegue lo hace una persona con `scripts/desplegar_entorno_pruebas.ps1`, que no es un workflow, así que al terminar avisa con un `repository_dispatch` del tipo `despliegue-pruebas-terminado`. El comando está abajo.
- **Cómo se autentica:** por *Workload Identity Federation*, sin claves de cuenta de servicio en GitHub. La cuenta de servicio del verificador, del proyecto de pruebas, necesita solo:
  - `roles/run.viewer`, para leer el digest;
  - permiso para invocar el backend (`roles/run.invoker`);
  - acceso por IAP al frontend (`roles/iap.httpsResourceAccessor`);
  - `roles/iam.serviceAccountTokenCreator` sobre sí misma, para emitir tokens de identidad.

  No tiene ningún permiso en el proyecto de producción.
- **Direcciones:** salen de variables del repositorio, no del archivo. Ninguna es un secreto.
- **No es un check obligatorio** del PR ni de `main`. No se agrega a la protección de ramas (`PROTECCION_MAIN.md`) ni cambia los checks de `zero-regression-pipeline.yml` (CI-17). Si falla, ese digest queda rechazado para la promoción a producción (§5.5), pero no bloquea ninguna fusión.

## Variables del repositorio (Settings → Secrets and variables → Actions → Variables)

| Variable | Contenido |
|---|---|
| `PRUEBAS_PROYECTO` | id del proyecto de Google Cloud de pruebas |
| `PRUEBAS_REGION` | región de Cloud Run (`us-central1`) |
| `PRUEBAS_FRONTEND_URL` | URL `run.app` del frontend de pruebas |
| `PRUEBAS_BACKEND_URL` | URL `run.app` del backend de pruebas |
| `PRUEBAS_IAP_AUDIENCIA` | id del cliente OAuth de IAP del frontend |
| `PRUEBAS_WIF_PROVIDER` | proveedor de Workload Identity del proyecto de pruebas |
| `PRUEBAS_VERIFICADOR_SA` | cuenta de servicio del verificador (proyecto de pruebas) |
| `HUELLA_PROYECTO_PRODUCCION` | huella del proyecto de producción (identificador, no secreto) |

El job usa el entorno de GitHub `gcp-pruebas` (Settings → Environments). Se crea vacío, sin revisores, y sirve para separar sus permisos de los de `gcp-produccion`.

## Contenido de `.github/workflows/entorno-pruebas.yml`

```yaml
name: Verificador del entorno de pruebas

on:
  workflow_dispatch:
  repository_dispatch:
    types: [despliegue-pruebas-terminado]

permissions:
  contents: read
  id-token: write

concurrency:
  group: entorno-pruebas
  cancel-in-progress: false

jobs:
  verificar-entorno-pruebas:
    name: Verificar el entorno de pruebas
    runs-on: ubuntu-latest
    timeout-minutes: 10
    environment: gcp-pruebas
    env:
      PROYECTO_PRUEBAS: ${{ vars.PRUEBAS_PROYECTO }}
      REGION_PRUEBAS: ${{ vars.PRUEBAS_REGION }}
      IAP_AUDIENCIA: ${{ vars.PRUEBAS_IAP_AUDIENCIA }}
      VERIFICADOR_CUENTA_SERVICIO: ${{ vars.PRUEBAS_VERIFICADOR_SA }}
      HUELLA_PROYECTO_PRODUCCION: ${{ vars.HUELLA_PROYECTO_PRODUCCION }}
    steps:
      - name: Obtener el código
        uses: actions/checkout@v4

      - name: Autenticarse en Google Cloud (Workload Identity Federation)
        uses: google-github-actions/auth@v2
        with:
          workload_identity_provider: ${{ vars.PRUEBAS_WIF_PROVIDER }}
          service_account: ${{ vars.PRUEBAS_VERIFICADOR_SA }}

      - name: Preparar gcloud
        uses: google-github-actions/setup-gcloud@v2

      - name: Preparar Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Verificar el entorno de pruebas
        id: verificar
        run: |
          set -o pipefail
          python scripts/verificar_entorno_pruebas.py "${{ vars.PRUEBAS_FRONTEND_URL }}" "${{ vars.PRUEBAS_BACKEND_URL }}" | tee verificacion.txt

      - name: Resumen
        if: always()
        run: |
          echo "## Verificador del entorno de pruebas" >> "$GITHUB_STEP_SUMMARY"
          sed 's/^/    /' verificacion.txt >> "$GITHUB_STEP_SUMMARY" || true
```

El verificador nunca imprime tokens ni URL, así que `verificacion.txt` y el resumen se pueden leer sin riesgo. El registro del digest para la promoción (`digest_verificado.py guardar`) lo sigue haciendo la persona que despliega, en su máquina, con el digest que aparece en la línea `DIGEST`. El registro vive en `%USERPROFILE%\.evydentia\`, fuera del runner.

## Cómo lo aplica el propietario (PowerShell)

```powershell
cd "C:\Users\<usuario>\Desktop\Plataforma LOPDP 360\.claude\worktrees\<worktree-del-propietario>"
git fetch origin
git switch -c tarea/<persona>/ep07-workflow origin/main
# Copiar el bloque yaml de arriba en .github/workflows/entorno-pruebas.yml
git add .github/workflows/entorno-pruebas.yml
git commit -m "ci: EP-07 verificador del entorno de pruebas (no es un check obligatorio)"
git push -u origin tarea/<persona>/ep07-workflow
gh pr create --base main --title "ci: EP-07 verificador del entorno de pruebas" --body "Brief: governance/apoyo/BRIEF_PROPIETARIO_EP07_WORKFLOW.md"
```

Al terminar un despliegue en pruebas (después de `desplegar_entorno_pruebas.ps1`):

```powershell
gh api repos/jucaprosi/data-privacy-compliance-lopdp/dispatches -f event_type=despliegue-pruebas-terminado
```

## Comprobación
- `tests/test_ep07_verificar_entorno.py` lee el bloque yaml de este brief y comprueba que:
  - trae el job `verificar-entorno-pruebas` con la llamada a `scripts/verificar_entorno_pruebas.py`;
  - se autentica por Workload Identity, con `id-token: write` y sin `credentials_json`;
  - no tiene ninguna URL escrita en el archivo.
- Después de fusionarlo, ninguna regla de protección de `main` debe mencionar `verificar-entorno-pruebas`.
