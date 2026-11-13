# Brief del propietario · IA-11 · Corrida de evaluación contra Vertex real

Correr `scripts/evaluar_ia.py` es una compuerta humana: gasta Vertex y usa tus credenciales de GCP. El CI nunca lo ejecuta. Solo contra el proyecto de pruebas (`evydentia-pruebas`), nunca producción, y con tu `.env` propio (no el de la carpeta principal).

**Condición previa.** `IA-05` o `IA-06` ya declararon un prompt `VIGENTE` en `features/<sala>/ai/prompts.py` y existe `evaluacion/ia/casos/<prompt_id>.json`. Sin eso no hay nada que evaluar.

**Organización de evaluación.** El script consume el tope de generaciones de la organización que indiques en `--org-id`; usa una organización de pruebas.

```powershell
$raiz = "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.claude\worktrees\<tu-worktree>"
$proyectoPruebas = "evydentia-pruebas"
$promptId = "<sala>.<nombre>"
$version = 1
$modelo = "gemini-2.5-flash"
$orgEval = "<id-de-la-organizacion-de-evaluacion>"
Set-Location $raiz

# Guarda: solo el proyecto de pruebas
if ($proyectoPruebas -match "produccion|prod$" -or $proyectoPruebas -ne "evydentia-pruebas") { throw "Solo el proyecto de pruebas." }
$env:GOOGLE_CLOUD_PROJECT = $proyectoPruebas
$env:VERTEX_LOCATION = "us-central1"
$activo = gcloud config get-value project 2>$null
Write-Host "Proyecto gcloud activo: $activo ; proyecto de la corrida: $env:GOOGLE_CLOUD_PROJECT"
gcloud auth application-default login

# 1) Solo anuncia cuántas generaciones gastará (no llama a Vertex)
python scripts/evaluar_ia.py $promptId $version $modelo --org-id $orgEval

# 2) Corrida real (acepta el gasto anunciado)
python scripts/evaluar_ia.py $promptId $version $modelo --org-id $orgEval --confirmar

# 3) Árbitro y commit del resultado
python -m pytest --noconftest -q tests/test_ia11_evaluacion.py
git add evaluacion/ia/resultados
git commit -m "IA-11: resultado de evaluación $promptId v$version $modelo"
```

Repite el paso 2 para cada modelo de `MODELOS_PERMITIDOS` que uses (`gemini-2.5-flash`, `gemini-2.5-pro`). Si subes la versión de un prompt, el árbitro exige un resultado nuevo con puntaje no menor al anterior. Sin secretos en el repositorio: las credenciales son las de tu sesión de gcloud.
