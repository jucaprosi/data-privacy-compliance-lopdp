# Brief del propietario · Secreto de cifrado de la cédula del inventario (ORG-17)

Fecha: 2026-11-10. Redactado por el Tech Lead por decisión del CTO. Lo ejecuta el propietario (con Antigravity o desde PowerShell). Los ingenieros no ejecutan nada de esto.

## Qué se hace y por qué
El inventario de activos (ORG-17) guarda, solo si la firma la exige, la cédula de una persona. Se guarda cifrada con Fernet y nunca se devuelve. La clave sale del secreto `INVENTARIO_CLAVE_CIFRADO`, que vive en Secret Manager y llega al servicio como variable de entorno. Mientras el secreto no exista, la función falla cerrada: la cédula se rechaza con 503 y el resto de la persona se guarda sin ella. Nada más del inventario depende del secreto.

Qué no hace este brief: no escribe la clave en ningún archivo, en el chat ni en el repositorio, y no toca la base de datos ni otros secretos.

## Valores
- Proyecto: `evydentia`
- Secreto: `INVENTARIO_CLAVE_CIFRADO`
- Cuenta de servicio del backend: `sa-evydentia-backend@evydentia.iam.gserviceaccount.com`

## Pasos (PowerShell, copiar y pegar completos)

### 1. Comprobar el estado actual (solo lectura)
```powershell
$PROYECTO = "evydentia"
gcloud secrets list --project=$PROYECTO --filter="name~INVENTARIO_CLAVE_CIFRADO" --format="value(name)"
```
Resultado esperado hoy: no imprime nada.

### 2. Crear el secreto con una clave nueva, sin mostrarla
La clave es una clave Fernet (32 bytes en base64 seguro para URL). Se genera y se envía a Secret Manager sin pasar por un archivo ni por la pantalla.
```powershell
$PROYECTO = "evydentia"
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$clave = [Convert]::ToBase64String($bytes).Replace("+", "-").Replace("/", "_")
gcloud secrets create INVENTARIO_CLAVE_CIFRADO --project=$PROYECTO --replication-policy=automatic
$clave | gcloud secrets versions add INVENTARIO_CLAVE_CIFRADO --project=$PROYECTO --data-file=-
Remove-Variable clave, bytes
```
No copies la clave a otro lugar. Si se pierde, las cédulas ya guardadas dejan de poder leerse: no hay copia en el repositorio. Antes de rotarla en el futuro, pide un brief nuevo.

### 3. Dar acceso de lectura solo a la cuenta de servicio del backend
```powershell
$PROYECTO = "evydentia"
$SA = "sa-evydentia-backend@evydentia.iam.gserviceaccount.com"
gcloud secrets add-iam-policy-binding INVENTARIO_CLAVE_CIFRADO --project=$PROYECTO --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
```
No des `roles/secretmanager.admin` ni acceso a otras cuentas.

### 4. Conectar el secreto al servicio
El despliegue actual (`.github/workflows/deploy-gcp.yml`) fija los secretos con `--set-secrets`, así que en el próximo despliegue un secreto añadido a mano desaparecería. Por eso la conexión se hace en el flujo de despliegue, sin escribir ningún valor, solo la referencia `INVENTARIO_CLAVE_CIFRADO=INVENTARIO_CLAVE_CIFRADO:latest` junto a los dos secretos que ya lista. Ese archivo lo cambia el propietario o el CTO por su cuenta (los ingenieros no tocan `.github/workflows/`). Hasta entonces la función sigue cerrada.

### 5. Comprobar que quedó (solo lectura)
```powershell
$PROYECTO = "evydentia"
gcloud secrets describe INVENTARIO_CLAVE_CIFRADO --project=$PROYECTO --format="value(name)"
gcloud secrets versions list INVENTARIO_CLAVE_CIFRADO --project=$PROYECTO --format="table(name,state)"
```
Resultado esperado: el secreto aparece y una versión está en estado `ENABLED`. No uses `gcloud secrets versions access`: mostraría la clave.

## Cuándo se considera hecho
El secreto existe, solo la cuenta de servicio del backend puede leerlo y el flujo de despliegue lo referencia. Con eso la organización puede guardar una cédula opcional en Inventario › Activos y personas; sin esto, la pantalla ofrece «Guardar sin cédula».
