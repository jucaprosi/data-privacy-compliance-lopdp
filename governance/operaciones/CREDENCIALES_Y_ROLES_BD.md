# Inventario de Credenciales y Roles de Base de Datos (SEC-10)

> **Documento Operativo y Doctrina de Seguridad**  
> **Ámbito:** Plataforma LOPDP 360  
> **Fecha:** 21 de Octubre de 2026  
> **Rastros:** `¤seguridad`, `¤rbac-tenant`  
> **Base Legal:** LOPDP Art. 47 (Seguridad de datos personales y principio de responsabilidad proactiva); RGPD Art. 32 (Seguridad del tratamiento y control de accesos); PRD §5.3.1.

---

## 1. Inventario Real de Roles y Atributos (PostgreSQL / Neon)

Medición empírica realizada en modo solo lectura (`SET TRANSACTION READ ONLY`) contra el catálogo `pg_roles` y `pg_auth_members`:

| Rol | rolsuper | rolinherit | rolcreaterole | rolcreatedb | rolcanlogin | rolbypassrls | Grupos / Membresías |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `lopdp_beta_owner` | `False` | `True` | `True` | `True` | `True` | **`True`** | `neon_superuser`, `neon_service`, `lopdp_app` |
| `lopdp_app` | `False` | `True` | `False` | `False` | `True` | **`False`** | *(ninguno)* |
| `neon_superuser` | `False` | `True` | `True` | `True` | `False` | **`True`** | `pg_read_all_data`, `pg_write_all_data`, `pg_monitor`, `pg_signal_backend`, `pg_create_subscription` |

### Implicaciones de Seguridad de la Llave Maestra
1. **El peligro de `BYPASSRLS`:**  
   El rol `lopdp_beta_owner` pertenece a `neon_superuser` y posee explícitamente `rolbypassrls = True`. Esto significa que **ignora completamente todas las políticas de aislamiento multi-inquilino (`tenant_isolation_*`)** de PostgreSQL, aun cuando se declare `FORCE ROW LEVEL SECURITY`. Cualquier conexión que use esta credencial tiene visibilidad global irrestricta sobre los datos de todos los inquilinos.
2. **Rol de Producción (`lopdp_app`):**  
   El rol `lopdp_app` carece de superusuario, no posee `BYPASSRLS` y no hereda privilegios de administración. Es el único rol autorizado doctrinalmente para la conexión de la API en producción y entornos de ejecución ordinaria.

---

## 2. Mapa de Asignación de Credenciales

Mapeo de variables de entorno y componentes según el análisis estático del código (`session.py`, `env.py`, `.env.example`, `.github/workflows/zero-regression-pipeline.yml`):

| Componente / Entorno | Variable de Entorno | Rol Asignado | Tipo de Endpoint | Propósito y Privilegios Requeridos |
| :--- | :--- | :--- | :--- | :--- |
| **API Producción / Preview** | `DATABASE_URL` | `lopdp_app` | Pooler (PgBouncer) | DML mínimo de negocio (`SELECT`, `INSERT`, `UPDATE`). RLS forzado y efectivo. Sin `BYPASSRLS`. Sin `DELETE` en tablas globales. |
| **Migraciones Alembic (Deploy)** | `MIGRATION_DATABASE_URL` | `lopdp_beta_owner` | Directo (sin pooler) | DDL completo (`CREATE`, `ALTER`, `DROP`, `GRANT`). Requiere conexión directa para transacciones de catálogo. |
| **CI (GitHub Actions)** | `TEST_DATABASE_URL` | `lopdp_beta_owner` | Pooler (Rama `test`) | Ejecución de suite de pruebas backend. Los tests que validan RLS ejecutan `SET ROLE lopdp_app` dentro de transacciones aisladas. |
| **Entorno Local / Agentes** | `TEST_DATABASE_URL` | `lopdp_beta_owner` | Pooler (Rama propia) | Entorno transaccional de pruebas de cada agente o desarrollador. |
| **Entorno Local / Migraciones** | `TEST_MIGRATION_DATABASE_URL` | `lopdp_beta_owner` | Directo (Rama propia) | Ejecución de `alembic upgrade head` en ramas de prueba efímeras. |

---

## 3. Análisis de Aislamiento en Tablas Globales (`tenants` y `users`)

### 3.1. Estado Actual de Privilegios
En la migración `20261008_app_role_rls.py`, las tablas `tenants` y `users` fueron incluidas originalmente en la lista `DML_TABLES`, otorgándoles `SELECT, INSERT, UPDATE, DELETE`.
Sin embargo, el análisis del código en `api/`, `features/` y `app_core/` demuestra que:
- **`tenants`:** El código productivo únicamente ejecuta `SELECT` (consulta de tamaño/configuración) y `UPDATE` (actualización de configuración organizativa). **Ningún archivo de código productivo ejecuta `DELETE FROM tenants`**.
- **`users`:** El código ejecuta `SELECT` (identificación, listado de usuarios del tenant), `INSERT` (creación de usuarios) y `UPDATE` (vinculación de `google_sub`). **Ningún archivo de código productivo ejecuta `DELETE FROM users`** (la baja es lógica mediante `deleted_at`).
- **Endurecimiento aplicado:** Se revocó `DELETE` a `lopdp_app` en ambas tablas, garantizando el principio de mínimo privilegio.

### 3.2. ¿Por qué `tenants` y `users` NO deben tener RLS estricto por `tenant_id`?
Un análisis detallado de los flujos de autenticación y arquitectura revela por qué aplicar una política RLS estándar (`tenant_id = current_setting('app.current_tenant_id')`) en estas dos tablas causaría una rotura total del sistema:

1. **Flujo de Autenticación OIDC / Google (`app_core/security.py`):**
   ```python
   # app_core/security.py (Líneas 131 y 137)
   # Se ejecuta ANTES de conocer el tenant del usuario:
   SELECT id FROM users WHERE google_sub = :sub AND activo AND deleted_at IS NULL
   SELECT id, google_sub FROM users WHERE lower(email) = :email AND activo AND deleted_at IS NULL
   UPDATE users SET google_sub = :sub WHERE id = :id AND google_sub IS NULL
   ```
   Cuando un usuario inicia sesión con Google, la aplicación únicamente recibe el token JWT de Google (`google_sub`, `email`). En ese instante, **la aplicación desconoce a qué organización(es) pertenece el usuario**. Por tanto, la variable de sesión `app.current_tenant_id` aún no está establecida.
   Si `users` tuviera RLS condicionado a `tenant_id`, la consulta devolvería cero registros, impidiendo el login de todos los usuarios.

2. **Modelo Multi-Tenant Muchos a Muchos:**
   Los usuarios no tienen una columna `tenant_id` fija en la tabla `users`. La pertenencia a una o varias organizaciones reside en la tabla intermedia `user_tenant_roles(user_id, tenant_id, role)`, la cual **sí tiene RLS forzado** por `tenant_id`.
   Proteger la tabla `users` mediante RLS rompería a aquellos usuarios legítimos que colaboran en múltiples tenants (por ejemplo, auditores externos, DPOs externos o consultores multi-cliente).

3. **Resolución Inicial de Organización (`tenants`):**
   Durante la resolución del contexto del tenant (`api/context.py` y carga de configuración), el sistema consulta `tenants` por su identificador primario o dominio. Si `tenants` tuviera RLS que exige conocer el tenant antes de poder leer el tenant, se crearía una dependencia circular irresoluble.

### 3.3. Recomendación Arquitectónica Futura
- **No aplicar RLS tradicional a `tenants` ni a `users`** (se mantiene conforme a la doctrina actual).
- **Vistas o funciones con filtro de tenant para listados:** Para listar miembros dentro del panel de administración de una organización, el código ya utiliza correctamente un `JOIN` con la tabla `user_tenant_roles` (`features/organizacion/services/usuarios_engine.py:list_tenant_users`), lo cual garantiza el aislamiento contextual sin requerir RLS en la tabla global `users`.

---

## 4. Procedimiento para el Propietario (PowerShell)

> [!IMPORTANT]
> **Instrucciones para el Propietario del Proyecto:**  
> Este procedimiento está diseñado para ejecutarse en PowerShell sin exponer secretos en pantalla ni en logs de terminal. Permite verificar el rol de producción, rotar la contraseña del dueño `lopdp_beta_owner` y sincronizar los entornos sin disrupción del servicio.

### Paso 1: Comprobar el Usuario de Conexión en Vercel (Producción)
Comprueba qué usuario está configurado en `DATABASE_URL` en producción **sin revelar la contraseña ni la URL completa**:

```powershell
# Requiere Vercel CLI (vercel link previo al proyecto)
$dbUrlProd = vercel env pull .env.prod.tmp --environment=production --yes | Out-Null; `
$line = (Get-Content .env.prod.tmp | Where-Object { $_ -match "^DATABASE_URL=" }) -replace "^DATABASE_URL=", ""; `
Remove-Item .env.prod.tmp -Force; `
if ($line) {
    $uri = [System.Uri]$line
    $user = $uri.UserInfo.Split(':')[0]
    $host = $uri.Host
    Write-Host "✅ Producción DATABASE_URL configurada con:"
    Write-Host "   Usuario : $user"
    Write-Host "   Host    : $host"
    if ($user -eq "lopdp_app") {
        Write-Host "   ESTADO: CORRECTO (Producción conecta como lopdp_app sin BYPASSRLS)" -ForegroundColor Green
    } else {
        Write-Host "   ADVERTENCIA: Producción NO está usando lopdp_app. Debe actualizarse." -ForegroundColor Yellow
    }
} else {
    Write-Host "❌ No se encontró la variable DATABASE_URL en producción." -ForegroundColor Red
}
```

### Paso 2: Rotar la Contraseña de `lopdp_beta_owner` en Neon Console
1. Inicie sesión en la consola web de [Neon](https://console.neon.tech).
2. Seleccione el proyecto de la Plataforma LOPDP 360 y diríjase a la sección **Project Settings > Roles**.
3. Localice el rol `lopdp_beta_owner` y haga clic en **Reset Password**.
4. Copie la nueva contraseña generada de forma segura (gestor de contraseñas).

### Paso 3: Actualizar los Secretos y Archivos de Configuración A LA VEZ
Ejecute el siguiente bloque en PowerShell reemplazando `<NUEVA_CONTRASENA>` por el secreto obtenido en el Paso 2:

```powershell
$nuevaClave = Read-Host -Prompt "Ingrese la nueva contraseña de lopdp_beta_owner" -AsSecureString
$BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($nuevaClave)
$plainPass = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)

# 1. Actualizar MIGRATION_DATABASE_URL en Vercel (producción)
# (La aplicación de producción usa DATABASE_URL con lopdp_app, por lo que NO se cae)
vercel env add MIGRATION_DATABASE_URL production --value "postgresql+psycopg://lopdp_beta_owner:$plainPass@ep-dry-cloud-b51wa0h5.c-7.us-east-2.aws.neon.tech/lopdp_beta?channel_binding=require&sslmode=require" --force

# 2. Actualizar secreto en GitHub Actions (TEST_DATABASE_URL para el pipeline de CI)
gh secret set TEST_DATABASE_URL --body "postgresql+psycopg://lopdp_beta_owner:$plainPass@ep-dry-cloud-b51wa0h5-pooler.c-7.us-east-2.aws.neon.tech/lopdp_beta?channel_binding=require&sslmode=require"

# 3. Limpiar memoria del script
[System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
$plainPass = $null
Write-Host "✅ Credenciales actualizadas en Vercel y GitHub Secrets sin exponer secretos." -ForegroundColor Green
```

### Paso 4: Verificación Posterior a la Rotación
Verificar que la nueva credencial funcione correctamente y que la aplicación de producción continúe operando:

```powershell
# 1. Comprobar conectividad directa de migración con la nueva credencial
# (Debe responder con código 0 y la cabeza de Alembic)
$env:MIGRATION_DATABASE_URL = vercel env pull .env.mig.tmp --environment=production --yes | Out-Null; `
$murl = (Get-Content .env.mig.tmp | Where-Object { $_ -match "^MIGRATION_DATABASE_URL=" }) -replace "^MIGRATION_DATABASE_URL=", ""; `
Remove-Item .env.mig.tmp -Force; `
python -m alembic -x url="$murl" current

# 2. Verificar que el endpoint de salud de producción responda 200 OK
$resp = Invoke-RestMethod -Uri "https://plataforma-lopdp-360.vercel.app/api/health" -Method Get
Write-Host "Estado de la API en producción: $($resp.status)" -ForegroundColor Green
```

---

## 5. Trazabilidad y Cumplimiento
- **Invariante Cero Regresión:** Las tablas de negocio conservan RLS forzado; `tenants` y `users` cuentan con privilegios DML acotados (sin `DELETE`).
- **Doctrina ADPA:** Todas las verificaciones se realizaron contra la compuerta y las entidades vivas de la base de datos sin interpolación dinámica de SQL.
