# ¤entorno-pruebas ¤ci-cd
<#
.SYNOPSIS
  Reinicia el entorno de pruebas de EVYDENTIA (EP-06): base nueva, migrada, buckets vacios y siembra.

.DESCRIPTION
  Contrato: PRD.md 5.5 e invariante 55. Lo ejecuta una persona; ninguna sesion
  de IA actua en Google Cloud. Solo actua sobre -Proyecto: todo comando de gcloud lleva --project.
  Orden:
    1. Aborta si el proyecto coincide con HUELLA_PROYECTO_PRODUCCION.
    2. Pide confirmacion escrita: hay que teclear el id del proyecto (o pasarlo en -Confirmacion).
    3. Comprueba que cada bucket pertenece a -Proyecto (project_number del bucket = projectNumber del
       proyecto). --project no limita una URL gs://, asi que sin esta comprobacion se podria vaciar un
       bucket ajeno. Si alguno no coincide, se detiene antes de borrar la base o cualquier bucket.
    4. Recrea la base de pruebas en la instancia de Cloud SQL.
    5. Migra (alembic upgrade head) por el conector de Cloud SQL, con la URL de un archivo local.
    6. Vacia los buckets del proyecto de pruebas (su retencion no esta bloqueada).
    7. Llama a la siembra de EP-03: scripts/sembrar_entorno_pruebas.py.
  Nunca imprime la URL de conexion. Con -SoloMostrar imprime los pasos sin ejecutar ninguno.

.EXAMPLE
  .\scripts\reiniciar_entorno_pruebas.ps1 -Proyecto <id> -InstanciaCloudSql <id>:<region>:<instancia> -BaseDeDatos <base> -Buckets <bucket-evidencias>,<bucket-video> -SoloMostrar
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Proyecto,
    [Parameter(Mandatory = $true)][string]$InstanciaCloudSql,
    [Parameter(Mandatory = $true)][string]$BaseDeDatos,
    [Parameter(Mandatory = $true)][string[]]$Buckets,
    [string]$ArchivoUrl = "herramientas\url-base-pruebas.txt",
    [string]$ArchivoTesters = "herramientas\testers-entorno-pruebas.txt",
    [string]$Confirmacion,
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

# -File entrega "a,b" como un solo texto: se parte por comas.
$Buckets = @($Buckets | ForEach-Object { $_ -split ',' } | ForEach-Object { $_.Trim() } | Where-Object { $_ })
$instanciaCorta = ($InstanciaCloudSql -split ':')[-1]
$proxy = $null

try {
    Paso 1 "guardia de la huella de produccion"
    Muestra "comparar -Proyecto, -Buckets y -InstanciaCloudSql con HUELLA_PROYECTO_PRODUCCION"
    $huella = "$env:HUELLA_PROYECTO_PRODUCCION".Trim().ToLower()
    if (-not $huella) { Falla "falta HUELLA_PROYECTO_PRODUCCION; sin ella no se puede descartar produccion." }
    foreach ($valor in @($Proyecto, $InstanciaCloudSql) + $Buckets) {
        if ($valor.ToLower().Contains($huella)) { Falla "el destino es de produccion. No se reinicia nada." }
    }

    Paso 2 "confirmacion escrita"
    Muestra "teclear el id del proyecto: $Proyecto"
    if (-not $SoloMostrar) {
        if (-not $PSBoundParameters.ContainsKey("Confirmacion")) {
            $Confirmacion = Read-Host "Esto borra la base y los buckets de $Proyecto. Escriba el id del proyecto para seguir"
        }
        if ($Confirmacion -cne $Proyecto) { Falla "la confirmacion no coincide con el proyecto. No se reinicia nada." }
    }

    Paso 3 "pertenencia de los buckets al proyecto"
    Muestra "gcloud projects describe $Proyecto --format=value(projectNumber) --project $Proyecto"
    foreach ($bucket in $Buckets) {
        Muestra "gcloud storage buckets describe gs://$bucket --format=value(project_number) --project $Proyecto"
    }
    if (-not $SoloMostrar) {
        $numeroProyecto = "$(gcloud projects describe $Proyecto --format='value(projectNumber)' --project $Proyecto)".Trim()
        if ($LASTEXITCODE -ne 0 -or -not $numeroProyecto) { Falla "no se pudo leer el numero del proyecto. No se borra nada." }
        foreach ($bucket in $Buckets) {
            $numeroBucket = "$(gcloud storage buckets describe "gs://$bucket" --format='value(project_number)' --project $Proyecto)".Trim()
            if ($LASTEXITCODE -ne 0 -or $numeroBucket -ne $numeroProyecto) {
                Falla "el bucket $bucket no pertenece al proyecto $Proyecto. No se borra nada."
            }
        }
    }

    Paso 4 "recrear la base de pruebas"
    Muestra "gcloud sql databases delete $BaseDeDatos --instance $instanciaCorta --project $Proyecto --quiet"
    Muestra "gcloud sql databases create $BaseDeDatos --instance $instanciaCorta --project $Proyecto"
    if (-not $SoloMostrar) {
        Corre { gcloud sql databases delete $BaseDeDatos --instance $instanciaCorta --project $Proyecto --quiet } "no se pudo borrar la base de pruebas."
        Corre { gcloud sql databases create $BaseDeDatos --instance $instanciaCorta --project $Proyecto } "no se pudo crear la base de pruebas."
    }

    Paso 5 "migrar por el conector de Cloud SQL"
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

    Paso 6 "vaciar los buckets del proyecto de pruebas"
    foreach ($bucket in $Buckets) {
        Muestra "gcloud storage rm --recursive gs://$bucket/** --project $Proyecto --quiet"
        if (-not $SoloMostrar) {
            gcloud storage rm --recursive "gs://$bucket/**" --project $Proyecto --quiet
            # Un bucket ya vacio devuelve error al no encontrar objetos; se comprueba que quede vacio.
            $resto = @(gcloud storage ls "gs://$bucket/**" --project $Proyecto 2>$null)
            if ($resto.Count -gt 0) { Falla "el bucket $bucket no quedo vacio." }
        }
    }

    Paso 7 "siembra de EP-03"
    Muestra "python scripts/sembrar_entorno_pruebas.py --testers $ArchivoTesters --bucket $($Buckets[0])"
    if (-not $SoloMostrar) {
        Corre { python scripts/sembrar_entorno_pruebas.py --testers $ArchivoTesters --bucket $Buckets[0] } "fallo la siembra."
    }
    if ($SoloMostrar) { Write-Output "SOLO MOSTRAR: no se ejecuto ningun paso." }
} finally {
    Remove-Item Env:MIGRATION_DATABASE_URL -ErrorAction SilentlyContinue
    if ($proxy) { Stop-Process -Id $proxy.Id -Force -ErrorAction SilentlyContinue }
}
exit 0
