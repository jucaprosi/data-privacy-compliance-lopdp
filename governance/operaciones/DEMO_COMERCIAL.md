# Guía y Operación de la Demostración Comercial (DEMO-07)

**Entorno:** `evydentia-demo` (Google Cloud).  
**Sala responsable:** `operaciones`.  
**Contrato y Arquitectura:** `PRD.md` §5.6, `INVARIANTS.md` (60–63) y ficha `governance/tareas/DEMO-07.md`.

---

## 1. Arquitectura y Componentes Desplegados

El entorno comercial de demostración opera de manera estrictamente aislada del entorno de producción (`evydentia`):

| Componente | Recurso en Google Cloud | Configuración / Rol |
| :--- | :--- | :--- |
| **Proyecto** | `evydentia-demo` (`517105327086`) | Región `us-central1`. `APP_ENV=demo`. |
| **Base de Datos** | `evydentia-demo-db` (Cloud SQL) | PostgreSQL 16, tier `db-f1-micro`, `activationPolicy=ALWAYS`. Migrada a las 12 cabezas Alembic. |
| **Rol de Aplicación** | `evydentia_demo_app` | `NOSUPERUSER NOBYPASSRLS NOCREATEDB NOCREATEROLE`. RLS activo en todas las tablas. |
| **Rol de Purga** | `purga_demo` | Solo permisos de DELETE definidos en `jobs/purga_demo/politicas_purga.sql` y función `purga_demo_borrar_inmutables`. |
| **Bucket de Evidencias** | `gs://lopdp360-demo-evidencias` | Acceso uniforme, sin prevención de borrado, sin política de retención ni bloqueo WORM, OLM a 3 días. |
| **Backend API** | `evydentia-backend-demo` | Cloud Run gen2, Ingress `all` protegido por IAM. Invocable únicamente por la cuenta del frontend. |
| **Frontend Web** | `evydentia-web-demo` | Cloud Run, Ingress `all`, acceso público. Proxy autenticado con token de servicio (`PROXY_AUTH_CLOUD_RUN=token_servicio`). |
| **Job de Purga** | `purga-demo` (Cloud Run Job) | Contenedor `purga-demo:v1` con guardias de seguridad activas (`APP_ENV=demo`, `HUELLA_PROYECTO_PRODUCCION=evydentia-production`). |
| **Scheduler Nocturno** | `purga-demo-nocturna` (Cloud Scheduler) | Disparo automático diario a las `03:00` America/Guayaquil (`0 3 * * *`). |

---

## 2. Gestión de Vendedores (Altas y Bajas)

Para garantizar que únicamente el personal comercial autorizado pueda clonar y operar instancias de demostración, el acceso se controla a través de dos mecanismos:

### 2.1 Lista de Vendedores Autorizados (`DEMO_VENDEDORES`)
El backend valida que el correo autenticado pertenezca a la lista del secreto `DEMO_VENDEDORES` en Secret Manager antes de permitir la creación de un nuevo tenant demo.

- **Para consultar los vendedores actuales:**
  ```powershell
  gcloud secrets versions access latest --secret=DEMO_VENDEDORES --project=evydentia-demo
  ```

- **Para dar de alta a un vendedor:**
  1. Descarga o prepara la lista actualizada separada por comas (sin espacios):
     ```powershell
     $VENDEDORES = "juancarlosproanios@gmail.com,evydentia@gmail.com,nuevo_vendedor@empresa.com"
     $ARCHIVO = Join-Path $env:TEMP "demo_vendedores.txt"
     Set-Content -Path $ARCHIVO -Value $VENDEDORES -NoNewline -Encoding ascii
     gcloud secrets versions add DEMO_VENDEDORES --data-file=$ARCHIVO --project=evydentia-demo
     Remove-Item $ARCHIVO
     ```
  2. Reinicia o actualiza el backend para tomar la nueva versión si fuera necesario:
     ```powershell
     gcloud run services update evydentia-backend-demo --project=evydentia-demo --region=us-central1 --update-env-vars="TIMESTAMP=$(Get-Date -Format s)"
     ```

- **Para dar de baja a un vendedor:**
  Genera una nueva versión del secreto `DEMO_VENDEDORES` excluyendo el correo del vendedor revocado. La siguiente petición del usuario será rechazada con `403 Prohibido`.

### 2.2 Control de Acceso al Servicio Web (IAP / IAM)
- Cuando IAP está habilitado en Cloud Run, se añade al vendedor mediante:
  ```powershell
  gcloud iap web add-iam-policy-binding --resource-type=cloud-run --service=evydentia-web-demo --region=us-central1 --project=evydentia-demo --member="user:vendedor@empresa.com" --role="roles/iap.httpsResourceAccessor"
  ```
- Para revocar acceso:
  ```powershell
  gcloud iap web remove-iam-policy-binding --resource-type=cloud-run --service=evydentia-web-demo --region=us-central1 --project=evydentia-demo --member="user:vendedor@empresa.com" --role="roles/iap.httpsResourceAccessor"
  ```

---

## 3. Registro del Recorrido de Aceptación (Árbitro DEMO-07)

**Fecha:** 2026-11-21  
**Ejecutores:** Juan Carlos Proaño (verificación técnica y despliegue), Aleczandra Proaño / José (recorrido de negocio).  
**URL Demo:** `https://evydentia-web-demo-517105327086.us-central1.run.app`

### 3.1 Puntos de Comprobación
1. **Entrada y Autenticación:**
   - La pantalla de login muestra el banner contextual: `Demostración · datos ficticios` (`aviso-entorno`).
   - El inicio de sesión se realiza mediante Google OAuth (`943042355099-um6ieu8s1s8kettg253g9v5ms8ag7k4l.apps.googleusercontent.com`).
   - La consulta a `/api/v1/entorno` devuelve `{ "entorno": "demo", "datos_ficticios": true }`.
2. **Siembra y Clonación:**
   - Creación de sesión demo a partir de la plantilla cooperativa (`demo-plantilla-cooperativa`).
   - Se crean las personas ficticias vinculadas al tenant efímero del vendedor.
3. **Selector «Ver como»:**
   - El vendedor puede alternar entre perfiles ficticios (DPO, Oficial de Seguridad, Responsable de Tratamiento) verificando la vista de cada rol sin alterar la persistencia de producción.
4. **Finalización («Terminar demo»):**
   - El vendedor presiona el botón «Terminar demo», marcando la sesión como finalizada y dejando el tenant listo para su recolección.
5. **Purga Nocturna:**
   - El Job `purga-demo` ejecutado en Cloud Run (`purga-demo-9trtv`) procesa los tenants vencidos y limpia físicamente:
     - Objetos en `gs://lopdp360-demo-evidencias` con prefijo del tenant.
     - Filas en tablas inmutables mediante `purga_demo_borrar_inmutables`.
     - Filas en tablas con RLS mediante las políticas de `politicas_purga.sql`.
   - Se preserva intacta la plantilla base `demo-plantilla-cooperativa` y cualquier demo activa no vencida.

---

## 4. Evidencia de Ejecución de la Purga

Ejecución auditada del Job `purga-demo`:

```text
[PURGA_DEMO] Iniciando purga determinista en entorno demo (evydentia-demo)
[PURGA_DEMO] Conectando a evydentia-demo-db con rol purga_demo...
[PURGA_DEMO] Guardias superadas: entorno=demo, huella_prod=evydentia-production
[PURGA_DEMO] Bucket verificado: lopdp360-demo-evidencias (sin retencion, sin bloqueo)
[PURGA_DEMO] Tenants procesados: 14 vencidos
[PURGA_DEMO] Filas eliminadas: 1474
[PURGA_DEMO] Objetos eliminados de GCS: 0
[PURGA_DEMO] Plantilla 'demo-plantilla-cooperativa' preservada con exito.
[PURGA_DEMO] Purga completada con codigo de salida 0.
```

El Cloud Scheduler `purga-demo-nocturna` queda habilitado con la expresión `0 3 * * *` para mantener el almacenamiento y la base de datos limpios diariamente.
