# Operaciones: Variables de Entorno, Ramas Neon, Protección de `main` y Despliegue
`¤ci-cd` `¤seguridad`

> **SSOT Operativa:** Documento unificado de variables de entorno por servicio, ciclo de vida de ramas Neon, gobernanza de ramas protegidas y protocolo notarial de verificación de despliegues.  
> **Cumplimiento de Seguridad:** Los secretos, contraseñas y llaves API se referencian **estrictamente por nombre**, nunca por valor.  
> **Invariante ADPA:** Los procedimientos técnicos aquí descritos garantizan el aislamiento determinista entre entornos de producción, preview y ramas de pruebas por agente.

---

## 1. Variables de Entorno por Servicio y Entorno

El sistema se compone de dos capas de despliegue principales en Vercel:
1. **Backend API Gateway (FastAPI):** Servicio Python serverless bajo `api/index.py` y `app_core/`.
2. **Frontend IDE (Next.js):** Aplicación interactiva React 19 / Next.js 15.5+ bajo `frontend/`.

### Matriz Exhaustiva de Variables de Entorno

| Variable | Servicio | Entornos | Fuente del Secreto / Configuración | Notas de Seguridad e Integración |
| :--- | :--- | :--- | :--- | :--- |
| `DATABASE_URL` | Backend | Production, Preview, Local | Neon Console (Endpoint con Connection Pooling) | Cadena de conexión transaccional con rol restrictivo `lopdp_app` (sin `BYPASSRLS` y con `FORCE RLS`). En modo pooled utiliza el puerto `6543` / PgBouncer. Formato driver: `postgresql+psycopg://`. |
| `MIGRATION_DATABASE_URL` | Backend / Migraciones | Local, Runner CI (secreto) | Neon Console (Endpoint Directo) | Cadena de conexión directa (sin pooler, puerto `5432`) para Alembic con usuario DDL `lopdp_beta_owner`. **Prohibido cargar en runtime de Vercel**. |
| `TEST_DATABASE_URL` | Backend (Tests) | Local (Agentes), Runner CI | Neon Console (`test` o `test-<agente>`) | Cadena de conexión de la rama efímera del agente. Usada por `pytest_rama.ps1` y `tests/conftest.py`. Conexión directa como `lopdp_beta_owner`; los tests de RLS ejecutan `SET ROLE lopdp_app`. |
| `APP_ENV` | Backend | Production, Preview, Local | Configuración de servicio | Identificador de entorno: `production`, `preview`, `test`, `development`. Leído por `app_core/config.py`. |
| `CORS_ORIGINS` | Backend | Production, Preview, Local | Configuración de dominio | Lista separada por comas de orígenes HTTP/HTTPS permitidos. En producción: dominio del frontend Vercel y dominios corporativos autorizados. En Preview: debe configurarse explícitamente (alineación obligatoria para evitar fallback abierto `*`). |
| `JWT_SECRET` | Backend | Production, Preview, Local | Gestor de secretos / Generador criptográfico | Llave simétrica (mínimo 256 bits) para firma y verificación de tokens de sesión (`HS256`). Requisito de rotación periódica. |
| `JWT_ALGORITHM` | Backend | Production, Preview, Local | Configuración de seguridad | Algoritmo de firma JWT; por defecto `HS256`. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Backend | Production, Preview, Local | Parámetro de sesión | Ventana de caducidad de tokens de acceso (por defecto `60`). |
| `DEEPSEEK_API_KEY` | Backend | Production, Preview, Local | Proveedor DeepSeek (Dashboard) | Token de autenticación para inferencia de modelos LLM (`deepseek-chat`, `deepseek-reasoner`). Usado por `features/roadmap/ai/client.py` y `app_core/ai/deepseek_client.py`. |
| `DEEPSEEK_BASE_URL` | Backend | Production, Preview, Local | Configuración de proveedor | URL base del API de DeepSeek (por defecto `https://api.deepseek.com/v1`). |
| `DEEPSEEK_MODEL` | Backend | Production, Preview, Local | Configuración de inferencia | Modelo de lenguaje asignado (ej. `deepseek-chat`). Preview debe contar con el valor explícito alineado con Production. |
| `OPENAI_API_KEY` | Backend | Production, Preview, Local | Proveedor OpenAI (Dashboard) | Token para servicios de vectorización/embeddings y copiloto RAG (`features/ai_copilot/`). |
| `PREANALISIS_API_KEY` | Backend | Production, Preview, Local | Proveedor IA / Gateway | Token dedicado opcional para preanálisis de brechas; fallback a `OPENAI_API_KEY`. |
| `PREANALISIS_BASE_URL` | Backend | Production, Preview, Local | Configuración de proveedor | Endpoint base para preanálisis si se utiliza proxy corporativo o Azure OpenAI. |
| `PREANALISIS_MODEL` | Backend | Production, Preview, Local | Configuración de inferencia | Modelo designado para extracción de entidades y anonimización en preanálisis. |
| `R2_ENDPOINT_URL` | Backend | Production, Preview, Local | Cloudflare R2 Console | URL S3-compatible del bucket de evidencias documentales (`https://<account-id>.r2.cloudflarestorage.com`). |
| `R2_BUCKET_NAME` | Backend | Production, Preview, Local | Cloudflare R2 Console | Nombre del bucket de almacenamiento WORM de evidencias auditables. |
| `R2_ACCESS_KEY_ID` | Backend | Production, Preview, Local | Cloudflare R2 API Tokens | ID de credencial de acceso S3 con permisos restringidos de lectura/escritura en el bucket de evidencias. |
| `R2_SECRET_ACCESS_KEY` | Backend | Production, Preview, Local | Cloudflare R2 API Tokens | Clave secreta asociada al token de Cloudflare R2. |
| `UPSTASH_REDIS_URL` | Backend | Production, Preview, Local | Upstash Console | Cadena de conexión TLS (`rediss://default:<token>@<endpoint>:6379`) para colas de tareas asíncronas y rate limiting distribuido. |
| `GOOGLE_CLIENT_ID` | Backend / Frontend | Production, Local (SEC-03) | Google Cloud Console (OAuth 2.0) | Identificador de cliente para verificación OIDC de identidad. En Preview no se habilita debido a que las URLs aleatorias de Vercel no pueden precargarse en Google Cloud Console. |
| `GOOGLE_CLIENT_SECRET` | Backend | Production, Local (SEC-03) | Google Cloud Console (OAuth 2.0) | Clave secreta del cliente OAuth de Google para canje de tokens en backend. |
| `RESEND_API_KEY` | Backend | Production, Preview, Local (NOTIF-01)| Resend Console | Llave API para envío de notificaciones transaccionales de tareas por correo (máx. 100 correos/día en plan gratuito). |
| `RESEND_FROM_EMAIL` | Backend | Production, Preview, Local (NOTIF-01)| Resend Console | Dirección de correo verificada bajo dominio corporativo validado en DNS (SPF, DKIM, DMARC). |
| `NEXT_PUBLIC_API_URL` | Frontend | Production, Preview, Local | Vercel Project Settings / `.env.local` | URL pública base del Backend REST Gateway hacia donde el cliente Next.js despacha las solicitudes `/api/v1/*`. |
| `NEXT_PUBLIC_TENANT_ID`| Frontend | Local, Preview (Demo) | Configuración de desarrollo | Identificador de tenant por defecto para pruebas de interfaz (ej. `tenant-corp-demo`). |
| `BACKEND_URL` | Frontend (SSR/Proxy) | Production, Preview, Local | Vercel Internal Routing | URL interna para proxy de peticiones del copiloto en rutas server-side (`copilotProxy.ts`). |
| `PLAYWRIGHT_BASE_URL` | Frontend (Tests) | CI / Local | Configuración de pruebas E2E | URL destino para la suite de pruebas Playwright. |

### Protocolo de Inyección de Variables en Vercel (CLI PowerShell)
Para provisionar o actualizar variables en Vercel sin exponer sus valores en consola ni generar archivos con marca de orden de bytes (BOM):

```powershell
$OutputEncoding = New-Object System.Text.UTF8Encoding $false
((Get-Content .env | Select-String '^NOMBRE_VARIABLE=' | Select-Object -Last 1).Line -replace '^NOMBRE_VARIABLE=','').Trim() | vercel env add NOMBRE_VARIABLE preview --sensitive --yes
```

---

## 2. Gestión y Ciclo de Vida de Ramas en Neon Postgres

El proyecto opera sobre un clúster serverless PostgreSQL 16 administrado en **Neon** (Proyecto: `square-violet-52579154`, Base de datos: `lopdp_beta`).

### Jerarquía de Ramas
```
production (Rama Raíz / SSOT de Datos Reales)
  └── test (Rama Compartida de Integración y CI)
        ├── test-rm07 (Rama Efímera Agente RM-07)
        ├── test-rm08 (Rama Efímera Agente RM-08)
        ├── test-rm09 (Rama Efímera Agente RM-09)
        └── test-<agente> (Rama Efímera por Sesión de Desarrollo)
```

1. **Rama `production`:**
   - Asociada de forma exclusiva al despliegue de **Production** en Vercel.
   - Accedida en runtime mediante el rol `lopdp_app` (con RLS obligatorio).
   - Las migraciones estructurales se aplican únicamente mediante pipeline autorizado con `lopdp_beta_owner`.
2. **Rama `test`:**
   - Rama compartida de integración previa y pruebas automáticas de GitHub Actions.
   - Refleja el esquema base verificado para pull requests concurrentes.
3. **Ramas Efímeras por Agente (`test-<agente>`):**
   - Creadas a partir de `production` o `test` para aislar completamente las pruebas de integración y migraciones de cada tarea.
   - Garantizan que las mutaciones de datos, pruebas de RLS destructivas o bloqueos transaccionales no interfieran entre agentes simultáneos.

### Procedimiento de Creación y Configuración Automatizada
El aprovisionamiento de una rama de desarrollo se realiza mediante el script local `crear_rama_neon.ps1`:

1. **Carga de Credenciales de Gestión:**
   Ejecutar `C:\Users\Juan Carlos\Desktop\herramientas\config_neon.ps1` para inicializar el token de API de Neon (`NEON_API_KEY`) y variables maestras de proyecto.
2. **Disparo de Creación:**
   ```powershell
   powershell -File "C:\Users\Juan Carlos\Desktop\herramientas\crear_rama_neon.ps1" -Agente rm07
   ```
3. **Salida Notarial Generada:**
   El script genera un archivo local desacoplado `C:\Users\Juan Carlos\Desktop\herramientas\rama-<agente>.txt` con:
   - `DATABASE_URL` (conexión pooled con rol `lopdp_app`).
   - `MIGRATION_DATABASE_URL` (conexión directa con rol `lopdp_beta_owner`).
4. **Ejecución Aislada de Pruebas:**
   El desarrollador ejecuta sus pruebas sin alterar el `.env` del repositorio:
   ```powershell
   .\pytest_rama.ps1 -Rama test-rm07 tests/test_roadmap_tarea_edicion.py -v
   ```

### Límites del Plan y Política Estricta de Limpieza
- **Cuota del Plan Gratuito Neon:** Máximo **10 ramas concurrentes** por proyecto y **100 horas de cómputo mensuales acumuladas**.
- **Regla de Purgado Obligatorio:**
  - Toda rama efímera `test-<agente>` debe eliminarse inmediatamente una vez que la tarea ha sido verificada y fusionada a `main`.
  - Comando de limpieza vía API REST de Neon:
    ```bash
    curl -X DELETE "https://console.neon.tech/api/v2/projects/$PROJECT_ID/branches/$BRANCH_ID" \
         -H "Authorization: Bearer $NEON_API_KEY" \
         -H "Accept: application/json"
    ```
  - Si el número de ramas activas alcanza 8, se prohíbe la creación de nuevas ramas efímeras hasta purgar las tareas concluidas.

---

## 3. Política de Protección de Rama `main` y Control de Regresiones

La rama `main` es la línea base de producción y estabilidad del repositorio.

### Reglas de Protección Vigentes en GitHub
- **Patrón de Rama:** `main`.
- **Exigencia de Pull Request:** Todos los cambios requieren un Pull Request aprobado; los commits directos a `main` remoto están bloqueados.
- **Check Obligatorio Mandatorio:**
  - Nombre del check: **`Arnés Físico Determinista`** (Job: `zero-regression` en `.github/workflows/zero-regression-pipeline.yml`).
  - El merge queda completamente bloqueado si este check falla o no reporta estado verde.
- **Alcance del Arnés Físico en CI:**
  1. *Pilar 1 (Backend & Gobernanza):* Ejecución completa de suite `pytest tests/`, verificación de codificación UTF-8 estricta sin BOM y comprobación de cero huellas abiertas `¦` en archivos `.py`.
  2. *Pilar 2 (Frontend Tipado):* Verificación estricta de TypeScript mediante `tsc --noEmit`.
  3. *Pilar 3 (Frontend Build):* Compilación de producción Next.js mediante `next build --turbopack`.

### Estado Real y Deuda Técnica Identificada
- **Estado de Ejecución:** El pipeline se ejecuta de forma determinista ante cada `push` y `pull_request` contra `main`.
- **Deuda Técnica (`required_status_checks.strict` - Tarea CI-01):**
  - Actualmente la regla de branch protection permite fusionar ramas que no estén estrictamente al día con la última cabeza de `main` (`strict = false`).
  - **Plan de Reserva (CI-01):** Si se detectasen colisiones de migraciones Alembic (múltiples cabezas) o inconsistencias cruzadas entre bloques paralelos, se activará `required_status_checks.strict = true` mediante:
    ```bash
    gh api repos/:owner/:repo/branches/main/protection/required_status_checks -X PATCH -F strict=true
    ```
  - *Condición de activación:* Decisión expresa del Tech Lead cuando la tasa de concurrencia de PRs lo justifique, mitigando la sobrecarga de rebase continuo.

### Procedimiento de Bypass Justificado (Solo Propietario / Coordinador)
- **Criterio Restrictivo:** Únicamente admisible ante incidentes de producción críticos (hotfix de seguridad, bloqueo de disponibilidad 503) o resolución de desincronización de metadatos de gobernanza (`TASKS.md`, `.test_verdict.json`).
- **Condiciones Sine Qua Non para Bypass:**
  1. Validación local determinista previa con `.\ejecutar_arnes_tres_pilares.bat` certificando que los tres pilares pasan exitosamente.
  2. Aprobación expresa del Tech Lead documentada en la bitácora de auditoría.
  3. Ejecución obligatoria de `scripts/verificar_despliegue.py` contra el entorno desplegado inmediatamente después de la integración.

---

## 4. Checklist Notarial de Verificación de Despliegue

Todo despliegue a **Production** o reconstrucción en **Preview** debe ser validado con el árbitro exógeno determinista desarrollado en la tarea **OPS-03**:

### Script de Verificación (`scripts/verificar_despliegue.py`)
El script actúa como árbitro exógeno sin estado:
```bash
python scripts/verificar_despliegue.py <dominio_o_url> [--timeout 15.0]
```

### Criterios de Aceptación Automáticos Evaluados (Exit Code 0)
1. **Disponibilidad y Mamparos (`GET /api/v1/health`):**
   - Código HTTP de respuesta: estrictamente `200 OK`.
   - Estado del payload: `status == "OPERATIONAL"`.
   - Cero routers fallidos: `routers.fallidos` debe ser una lista vacía `[]`.
   - Carga íntegra: `routers.total == len(routers.cargados) > 0` (todos los routers de las salas ADPA activos).
2. **Contrato de API (`GET /openapi.json`):**
   - Código HTTP de respuesta: `200 OK`.
   - Presencia confirmada de todas las rutas raíz y prefijos de salas fundamentales (`/`, `/health`, `/api/v1/health`, `/api/v1/diagnostico/*`, `/api/v1/rat/*`, `/api/v1/riesgos/mtge/*`, `/api/v1/dpo/*`, `/api/v1/capa/*`, `/api/v1/evidencias/*`, `/api/v1/rag/*`, `/api/v1/arco/*`, `/api/v1/terceros/*`, `/api/v1/ai/*`, `/api/v1/niif18/*`, `/api/v1/preanalisis/*`, `/api/v1/organizacion/*`).

### Protocolo de Contingencia (Rollback Inmediato si Exit Code == 1)
Si `verificar_despliegue.py` reporta código de salida `1`:
1. **Ejecutar Rollback en Vercel:** Aplicar *Promote to Production* sobre el despliegue anterior sano desde el dashboard de Vercel.
2. **Inspección de Logs:** Analizar logs de ejecución mediante `vercel logs <url-despliegue-fallido>`.
3. **Prohibición:** **No** ejecutar *Redeploy* sobre registros "Redeploy of...", ya que reutilizan artefactos compilados previos en lugar del código fuente corregido.
