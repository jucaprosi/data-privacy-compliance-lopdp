# Brief del propietario · Revisión 00006 de evydentia-backend (GCP-11)

Para el propietario, con Antigravity. Ninguna IA ejecuta estos comandos. Los de **lectura** van primero; cualquier **cambio** es un paso aparte, al final, y lo ejecuta solo el propietario. Ningún bloque imprime el valor de un secreto.

## Lectura

### 1. Estado de las dos revisiones (sin variables sensibles)

```powershell
$Proyecto = "evydentia"
$Region = "us-central1"
Set-Location "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
gcloud run revisions describe evydentia-backend-00006-7ks --project $Proyecto --region $Region --format="yaml(metadata.creationTimestamp,status.conditions)"
gcloud run revisions describe evydentia-backend-00007-g7q --project $Proyecto --region $Region --format="yaml(metadata.creationTimestamp,status.conditions)"
```

### 2. Versiones de los secretos (solo metadatos: estado y fecha, sin valor)

```powershell
$Proyecto = "evydentia"
foreach ($Secreto in "DATABASE_URL_APP", "JWT_SECRET", "SESSION_SECRET", "INVENTARIO_CLAVE_CIFRADO") {
  Write-Output "== $Secreto"
  gcloud secrets versions list $Secreto --project $Proyecto --format="table(name.basename(),state,createTime)"
}
```

### 3. Error de arranque de la 00006 (registros de error)

```powershell
$Proyecto = "evydentia"
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.revision_name="evydentia-backend-00006-7ks" AND severity>=ERROR' --project $Proyecto --limit 8 --format="value(timestamp,textPayload)"
```

### 4. Árbitro de secretos sin BOM (lee solo tres bytes de cada secreto y no imprime valores)

Primero la versión 1, la que usó la 00006; después `latest`, la que usa la 00007. Cada línea dice el nombre del secreto y «sin BOM», «CON BOM», «vacío» o «no se pudo leer».

```powershell
Set-Location "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
python scripts/verificar_secretos_sin_bom.py --proyecto evydentia --version 1
python scripts/verificar_secretos_sin_bom.py --proyecto evydentia --version latest
```

### 5. Comprobación previa al despliegue: el esquema de DATABASE_URL (imprime solo True o False)

Exige `True`. Si da `False`, no se despliega.

```powershell
$Proyecto = "evydentia"
$Valor = gcloud secrets versions access latest --secret=DATABASE_URL_APP --project $Proyecto
($Valor -match '^postgresql') -and ($Valor -notmatch '^\uFEFF')
Remove-Variable Valor
```

## Cambio (solo el propietario, solo si el paso 4 muestra CON BOM)

### 6. Crear una versión nueva del secreto sin BOM

Escribe los bytes en UTF-8 sin BOM. No uses una redirección de PowerShell (`>` o `Out-File` sin cuidado): en Windows PowerShell 5.1 añaden el BOM. Pega el valor en la terminal cuando lo pida, sin guardarlo en un archivo con nombre.

```powershell
$Proyecto = "evydentia"
$Secreto = "DATABASE_URL_APP"
$Valor = Read-Host "Pega el valor del secreto (no se muestra el eco de salida)" -AsSecureString
$Texto = [System.Net.NetworkCredential]::new("", $Valor).Password
$Ruta = Join-Path $env:TEMP "secreto-sin-bom.tmp"
[System.IO.File]::WriteAllBytes($Ruta, (New-Object System.Text.UTF8Encoding($false)).GetBytes($Texto))
gcloud secrets versions add $Secreto --project $Proyecto --data-file=$Ruta
Remove-Item $Ruta -Force
Remove-Variable Texto, Valor
```

Después, repite los pasos 4 y 5 antes de cualquier despliegue.
