# ¤entorno-pruebas ¤ci-cd
<#
.SYNOPSIS
  Ciclo de una version en el entorno de pruebas de EVYDENTIA (EP-06): migra y despliega un digest.

.DESCRIPTION
  Contrato: PRD_EVYDENTIA_REVENTA_NUBE.md 5.5 (Ciclo de una version) e invariante 55. Lo ejecuta una
  persona (Juan Carlos, Aleczandra o Jose); ninguna sesion de IA despliega en Google Cloud.
  Se detiene en el primer fallo y sigue este orden:
    1. origin/main tiene una sola cabeza de Alembic.
    2. Aborta si el proyecto coincide con HUELLA_PROYECTO_PRODUCCION.
    3. Migra la base de pruebas (alembic upgrade head) por el conector de Cloud SQL, con la URL
       leida de un archivo local de herramientas.
    4. Despliega el digest en los tres servicios (gcloud run deploy --image ...@sha256:...).
    5. Muestra el comando del verificador (EP-07).
  Nunca imprime la URL de conexion. Con -SoloMostrar imprime los pasos sin ejecutar ninguno.

.EXAMPLE
  .\scripts\desplegar_entorno_pruebas.ps1 -Proyecto <id> -Digest sha256:<64 hex> -Imagen <region>-docker.pkg.dev/<id>/<repo>/evydentia -Servicios api,web,worker -InstanciaCloudSql <id>:<region>:<instancia> -SoloMostrar
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Proyecto,
    [Parameter(Mandatory = $true)][string]$Digest,
    [Parameter(Mandatory = $true)][string]$Imagen,
    [Parameter(Mandatory = $true)][string[]]$Servicios,
    [Parameter(Mandatory = $true)][string]$InstanciaCloudSql,
    [string]$Region = "us-central1",
    [string]$ArchivoUrl = "herramientas\url-base-pruebas.txt",
    [int]$PuertoConector = 5434,
    [switch]$SoloMostrar
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Paso([int]$Numero, [string]$Nombre) { Write-Output "PASO $Numero ${Nombre}" }
function Muestra([string]$Comando) { Write-Output "  > $Comando" }
function Falla([string]$Motivo) { Write-Output "DETENIDO: $Motivo"; exit 1 }
function Corre([scriptblock]$Bloque, [string]$Motivo) {
    & $Bloque
    if ($LASTEXITCODE -ne 0) { Falla $Motivo }
}

# -File entrega "a,b,c" como un solo texto: se parte por comas.
$Servicios = @($Servicios | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })

# Precondiciones: se comprueban siempre, tambien con -SoloMostrar, porque no actuan sobre nada.
$digestNormal = $Digest.Trim().ToLower()
if ($digestNormal -notmatch '^sha256:[0-9a-f]{64}$') { $digestNormal = "sha256:$digestNormal" }
if ($digestNormal -notmatch '^sha256:[0-9a-f]{64}$') { Falla "el digest debe ser sha256:<64 hexadecimales>." }
if ($Imagen -match '[@]' -or ($Imagen -split '/')[-1] -match ':') { Falla "la imagen va sin etiqueta ni digest; el digest se pasa en -Digest." }
if ($Servicios.Count -ne 3) { Falla "se esperan los tres servicios de Cloud Run." }
$huella = "$env:HUELLA_PROYECTO_PRODUCCION".Trim().ToLower()
if (-not $huella) { Falla "falta HUELLA_PROYECTO_PRODUCCION; sin ella no se puede descartar produccion." }
$referencia = "$Imagen@$digestNormal"
$proxy = $null

try {
    Paso 1 "una sola cabeza de Alembic en origin/main"
    Muestra "git fetch origin main ; git worktree add <temporal> origin/main ; python -m alembic heads"
    if (-not $SoloMostrar) {
        Corre { git fetch --quiet origin main } "no se pudo traer origin/main."
        $temporal = Join-Path ([IO.Path]::GetTempPath()) ("ep06-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
        Corre { git worktree add --quiet --detach $temporal origin/main } "no se pudo preparar origin/main."
        try {
            Push-Location $temporal
            $cabezas = @(python -m alembic heads 2>$null | Where-Object { $_ -match '\(head\)' })
            Pop-Location
        } finally { git worktree remove --force $temporal | Out-Null }
        if ($cabezas.Count -ne 1) { Falla "origin/main tiene $($cabezas.Count) cabezas de Alembic; se espera una." }
    }

    Paso 2 "guardia de la huella de produccion"
    Muestra "comparar -Proyecto con HUELLA_PROYECTO_PRODUCCION"
    if ($Proyecto.Trim().ToLower().Contains($huella)) { Falla "el proyecto es el de produccion. No se despliega nada." }

    Paso 3 "migrar la base de pruebas por el conector de Cloud SQL"
    Muestra "cloud-sql-proxy $InstanciaCloudSql --port $PuertoConector"
    Muestra "MIGRATION_DATABASE_URL <- $ArchivoUrl (no se imprime) ; python -m alembic upgrade head"
    if (-not $SoloMostrar) {
        if (-not (Test-Path $ArchivoUrl)) { Falla "no existe el archivo local con la URL de la base de pruebas." }
        $proxy = Start-Process -FilePath "cloud-sql-proxy" -ArgumentList @($InstanciaCloudSql, "--port", "$PuertoConector") -PassThru -WindowStyle Hidden
        Start-Sleep -Seconds 5
        $env:MIGRATION_DATABASE_URL = (Get-Content $ArchivoUrl -Raw).Trim()
        if ($env:MIGRATION_DATABASE_URL.ToLower().Contains($huella)) { Falla "la URL del archivo es de produccion." }
        Corre { python -m alembic upgrade head *> $null } "fallo la migracion de la base de pruebas."
    }

    Paso 4 "desplegar el digest en los tres servicios"
    foreach ($servicio in $Servicios) {
        Muestra "gcloud run deploy $servicio --image $referencia --project $Proyecto --region $Region --quiet"
        if (-not $SoloMostrar) {
            Corre { gcloud run deploy $servicio --image $referencia --project $Proyecto --region $Region --quiet } "fallo el despliegue de $servicio."
        }
    }

    Paso 5 "verificador del entorno de pruebas (EP-07)"
    Muestra "python scripts/verificar_entorno_pruebas.py --proyecto $Proyecto"
    Muestra "python scripts/digest_verificado.py guardar --digest $digestNormal --codigo <codigo de salida del verificador>"
    if ($SoloMostrar) { Write-Output "SOLO MOSTRAR: no se ejecuto ningun paso." }
} finally {
    Remove-Item Env:MIGRATION_DATABASE_URL -ErrorAction SilentlyContinue
    if ($proxy) { Stop-Process -Id $proxy.Id -Force -ErrorAction SilentlyContinue }
}
exit 0
