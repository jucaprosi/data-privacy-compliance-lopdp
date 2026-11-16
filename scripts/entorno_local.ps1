<#
.SYNOPSIS
    Fija en la ventana actual de PowerShell las variables de entorno locales para LOPDP 360.
.DESCRIPTION
    El proyecto lee únicamente variables de entorno del proceso (`os.environ`); cualquier archivo `.env`
    se ignora. Este script configura las variables de conexión contra el PostgreSQL 16 local del arnés
    (`127.0.0.1:55432`) o una URL local explícita validada con `app_core.huellas_produccion.es_base_local`.
    No contiene secretos ni URLs reales de la nube.
.EXAMPLE
    .\scripts\entorno_local.ps1
.EXAMPLE
    .\scripts\entorno_local.ps1 -AppEnv demo -AuthMode oidc -HuellaProyectoProduccion "<huella>"
#>
[CmdletBinding()]
param(
    [string]$DatabaseUrl = "",
    [string]$MigrationDatabaseUrl = "",
    [string]$TestDatabaseUrl = "",
    [ValidateSet("headers", "oidc")]
    [string]$AuthMode = "headers",
    [ValidateSet("development", "test", "pruebas", "demo")]
    [string]$AppEnv = "development",
    [string]$CorsOrigins = "http://localhost:3000,http://127.0.0.1:3000",
    [string]$JwtSecret = "",
    [string]$SessionSecret = "",
    [string]$HuellaProyectoProduccion = ""
)

$ErrorActionPreference = "Stop"

$Raiz = Split-Path -Parent $PSScriptRoot
$Python = $env:PYTHON_BIN
if (-not $Python) {
    $VenvPython = Join-Path $Raiz ".venv\Scripts\python.exe"
    $Python = if (Test-Path $VenvPython) { $VenvPython } else { "python" }
}

if (-not $DatabaseUrl) {
    $UrlArnes = & $Python -c "import sys; sys.path.insert(0, r'$Raiz\verificadores'); import arnes_local as a; print(a.URL_LOCAL)" 2>$null
    if ($LASTEXITCODE -eq 0 -and $UrlArnes) {
        $DatabaseUrl = $UrlArnes.Trim()
    } else {
        $DatabaseUrl = "postgresql://lopdp_beta_owner@127.0.0.1:55432/lopdp"
    }
}
if (-not $MigrationDatabaseUrl) { $MigrationDatabaseUrl = $DatabaseUrl }
if (-not $TestDatabaseUrl) { $TestDatabaseUrl = $DatabaseUrl }

# Validar cada URL proporcionada antes de exportarlas a la sesión.
$env:DATABASE_URL = $DatabaseUrl
$env:MIGRATION_DATABASE_URL = $MigrationDatabaseUrl
$env:TEST_DATABASE_URL = $TestDatabaseUrl

& $Python -c "import sys; sys.path.insert(0, r'$Raiz'); from app_core.huellas_produccion import exigir_base_local; exigir_base_local()"
if ($LASTEXITCODE -ne 0) {
    Remove-Item Env:DATABASE_URL, Env:MIGRATION_DATABASE_URL, Env:TEST_DATABASE_URL -ErrorAction SilentlyContinue
    throw "[ENTORNO] Alguna URL indicada no apunta a una base local permitida (localhost, 127.0.0.1, ::1)."
}

$env:APP_ENV = $AppEnv
$env:AUTH_MODE = $AuthMode
$env:CORS_ORIGINS = $CorsOrigins
if ($JwtSecret) { $env:JWT_SECRET = $JwtSecret }
if ($SessionSecret) { $env:SESSION_SECRET = $SessionSecret }
if ($HuellaProyectoProduccion) { $env:HUELLA_PROYECTO_PRODUCCION = $HuellaProyectoProduccion }

Write-Host "[ENTORNO] Variables fijadas en esta ventana (sin .env): APP_ENV=$($env:APP_ENV), AUTH_MODE=$($env:AUTH_MODE), CORS_ORIGINS, DATABASE_URL, MIGRATION_DATABASE_URL, TEST_DATABASE_URL."
