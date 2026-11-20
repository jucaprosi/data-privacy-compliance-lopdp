# Brief del propietario · Secreto de cifrado de los webhooks (API-02b)

Fecha: 2026-11-19. Redactado por el Tech Lead para la tarea API-02b. Lo ejecuta el propietario (con Antigravity o desde PowerShell). Los ingenieros no ejecutan nada de esto.

## Qué se hace y por qué
Los webhooks salientes (API-02b) guardan su secreto de firma cifrado con Fernet en `webhooks_suscripciones.secreto_cifrado`, porque el backend necesita descifrarlo cada vez que firma una entrega saliente. La clave sale del secreto `WEBHOOKS_CLAVE_CIFRADO`, que vive en Secret Manager y llega al servicio como variable de entorno. Mientras el secreto no exista o no sea válido, la creación, rotación de secretos y entrega de avisos fallan cerradas con 503 (`WEBHOOKS_CIFRADO_NO_CONFIGURADO`) sin afectar a las claves de acceso ni al resto de la plataforma.

Qué no hace este brief: no escribe la clave en ningún archivo, en el chat ni en el repositorio, y no toca la base de datos ni otros secretos.

## Valores
- Proyecto: `evydentia`
- Secreto: `WEBHOOKS_CLAVE_CIFRADO`
- Cuenta de servicio del backend: `sa-evydentia-backend@evydentia.iam.gserviceaccount.com`

## Pasos (PowerShell, copiar y pegar completos)

### 1. Comprobar el estado actual (solo lectura)
```powershell
$PROYECTO = "evydentia"
gcloud secrets list --project=$PROYECTO --filter="name~WEBHOOKS_CLAVE_CIFRADO" --format="value(name)"
```
Resultado esperado hoy: no imprime nada.

### 2. Crear el secreto con una clave nueva, sin mostrarla
La clave es una clave Fernet (32 bytes en base64 seguro para URL). Se genera y se envía a Secret Manager sin pasar por un archivo ni por la pantalla.
```powershell
$PROYECTO = "evydentia"
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Create().GetBytes($bytes)
$clave = [Convert]::ToBase64String($bytes).Replace("+", "-").Replace("/", "_")
gcloud secrets create WEBHOOKS_CLAVE_CIFRADO --project=$PROYECTO --replication-policy=automatic
$clave | gcloud secrets versions add WEBHOOKS_CLAVE_CIFRADO --project=$PROYECTO --data-file=-
Remove-Variable clave, bytes
```
No copies la clave a otro lugar. Si se pierde, los secretos de webhook ya guardados no podrán descifrarse para firmar entregas y deberán rotarse. Antes de rotar `WEBHOOKS_CLAVE_CIFRADO` en el futuro, pide un brief nuevo.

### 3. Dar acceso de lectura solo a la cuenta de servicio del backend
```powershell
$PROYECTO = "evydentia"
$SA = "sa-evydentia-backend@evydentia.iam.gserviceaccount.com"
gcloud secrets add-iam-policy-binding WEBHOOKS_CLAVE_CIFRADO --project=$PROYECTO --member="serviceAccount:$SA" --role="roles/secretmanager.secretAccessor"
```
No des `roles/secretmanager.admin` ni acceso a otras cuentas.

### 4. Conectar el secreto al servicio
El despliegue actual (`.github/workflows/deploy-gcp.yml`) fija los secretos con `--set-secrets`, así que en el próximo despliegue un secreto añadido a mano desaparecería. Por eso la conexión se hace en el flujo de despliegue, sin escribir ningún valor, añadiendo la referencia `WEBHOOKS_CLAVE_CIFRADO=WEBHOOKS_CLAVE_CIFRADO:latest` junto a los secretos que ya lista. Ese archivo lo cambia el propietario o el CTO por su cuenta (los ingenieros no tocan `.github/workflows/`). Hasta entonces la función sigue cerrada (503).

### 5. Comprobar que quedó (solo lectura)
```powershell
$PROYECTO = "evydentia"
gcloud secrets describe WEBHOOKS_CLAVE_CIFRADO --project=$PROYECTO --format="value(name)"
gcloud secrets versions list WEBHOOKS_CLAVE_CIFRADO --project=$PROYECTO --format="table(name,state)"
```
Resultado esperado: el secreto aparece y una versión está en estado `ENABLED`. No uses `gcloud secrets versions access`: mostraría la clave.

## Cuándo se considera hecho
El secreto existe, solo la cuenta de servicio del backend puede leerlo y el flujo de despliegue lo referencia. Con eso la administración de la organización puede crear, probar y rotar webhooks en Configuración › Claves de integración.
