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

> **Reescrito por el coordinador el 2026-10-22** tras ejecutarlo de verdad. La versión anterior usaba el host de una rama de pruebas (`ep-dry-cloud-b51wa0h5`, la rama `test-rm08`) en lugar de producción y de la rama del CI, situaba los roles en la configuración del proyecto, usaba la variable de solo lectura `$host` y una opción de Alembic que `env.py` no admite.

Ningún paso muestra contraseñas ni URLs completas. Las URLs viven en el `.env` del proyecto y en los archivos `rama-*.txt` de la carpeta local `herramientas`, fuera del repositorio.

### Paso 1: Qué credencial usa cada sitio

| Sitio | Variable | Rol | Rama de Neon (host) |
| :-- | :-- | :-- | :-- |
| Aplicación de producción | `DATABASE_URL` | `lopdp_app` | `production` (`ep-late-hall-b50bpbk5-pooler`) |
| Migraciones de producción | `MIGRATION_DATABASE_URL` | `lopdp_beta_owner` | `production` (`ep-late-hall-b50bpbk5`) |
| CI (secreto de GitHub) | `TEST_DATABASE_URL` | `lopdp_beta_owner` | `test` (`ep-soft-darkness-b5z454vp-pooler`) |
| Desarrollo y agentes | `TEST_DATABASE_URL` en `rama-*.txt` | `lopdp_beta_owner` | una rama propia por agente |

Rotar la contraseña de `lopdp_beta_owner` **no debe afectar a la aplicación de producción**, siempre que esta conecte como `lopdp_app`. **Verificado el 2026-10-22:** el `DATABASE_URL` de producción en Vercel usaba la credencial del dueño; al rotarla, toda consulta a la base daba 500. Se sustituyó por la de `lopdp_app` en el pooler y se redesplegó; `scripts/verificar_despliegue.py` contra producción pasa (incluido `modo_autenticacion`: producción exige Google). Antes de rotar cualquier credencial, compruebe qué sitios la usan, también las variables «Sensitive» de Vercel, que no se pueden leer.

### Paso 2: Rotar en Neon, rama por rama

En Neon cada rama tiene su propia copia del rol: cambiar la contraseña en `production` **no** la cambia en `test` ni en las ramas de desarrollo. Para cada rama:

1. Elija la rama en el selector de arriba a la izquierda.
2. Vaya a **Roles** → `lopdp_beta_owner` → menú **⋮** → **Reset password**, y copie la contraseña nueva.
3. Refresque la página: «Last updated» debe cambiar. Si no cambia, la rotación no se guardó.

Las ramas que ya no se usen se borran en vez de rotarse.

### Paso 3: Actualizar el `.env` y los archivos de las ramas

Con dos utilidades locales de la carpeta `herramientas` (no versionadas):

- `comprobar_credenciales.py`: intenta `SELECT 1` con cada URL y muestra «OK» o «FALLA», el usuario y el host, sin la contraseña.
- `actualizar_contrasena_owner.py <prefijo-del-host>`: pide la contraseña nueva dos veces sin eco y la sustituye solo en las URLs de `lopdp_beta_owner` con ese host. Antes guarda una copia de cada archivo en `herramientas\respaldo_credenciales\`.

```powershell
cd "C:\Users\Juan Carlos\Desktop\herramientas"
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" comprobar_credenciales.py
& "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360\.venv\Scripts\python.exe" actualizar_contrasena_owner.py ep-late-hall-b50bpbk5
```

Repita `actualizar_contrasena_owner.py` con el host de cada rama rotada. No rote una rama mientras una suite esté corriendo contra ella.

### Paso 4: Actualizar el secreto del CI (solo si se rotó la rama `test`)

El valor se pasa con `--body`, no por una tubería: en Windows PowerShell 5.1 `$valor | gh secret set` añade un salto de línea final y el CI no puede leer la URL (pasó el 2026-10-22: 190 pruebas con «Could not parse SQLAlchemy URL»).

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
$linea = Get-Content .env -Encoding UTF8 | Where-Object { $_ -match '^\s*TEST_DATABASE_URL\s*=' } | Select-Object -First 1
$valor = ($linea -replace '^\s*TEST_DATABASE_URL\s*=\s*', '').Trim().Trim('"')
if ($valor -notmatch '^postgresql(\+psycopg)?://[^\s]+$' -or $valor -notmatch 'ep-soft-darkness-b5z454vp') { throw "Valor inesperado: abortado." }
gh secret set TEST_DATABASE_URL --repo jucaprosi/data-privacy-compliance-lopdp --body $valor
Remove-Variable valor, linea
```

### Paso 5: Verificar y limpiar

1. `comprobar_credenciales.py` de nuevo: todas las líneas en «OK».
2. Las migraciones de producción responden con la credencial nueva (solo lectura):

```powershell
cd "C:\Users\Juan Carlos\Desktop\Plataforma LOPDP 360"
$linea = Get-Content .env -Encoding UTF8 | Where-Object { $_ -match '^\s*MIGRATION_DATABASE_URL\s*=' } | Select-Object -First 1
$env:MIGRATION_DATABASE_URL = ($linea -replace '^\s*MIGRATION_DATABASE_URL\s*=\s*', '').Trim().Trim('"')
.\.venv\Scripts\python.exe -m alembic current
Remove-Item Env:MIGRATION_DATABASE_URL
```

3. Un PR cualquiera pasa el check `Arnés Físico Determinista` (prueba el secreto del CI).
4. Borre `herramientas\respaldo_credenciales`: sus copias contienen la contraseña antigua.

---

## 5. Trazabilidad y Cumplimiento
- **Invariante Cero Regresión:** Las tablas de negocio conservan RLS forzado; `tenants` y `users` cuentan con privilegios DML acotados (sin `DELETE`).
- **Doctrina ADPA:** Todas las verificaciones se realizaron contra la compuerta y las entidades vivas de la base de datos sin interpolación dinámica de SQL.
