# Rama de Neon por Agente de Desarrollo (Decisión D-8)
`¤ci-cd` `¤seguridad`

> **SSOT Operativa para Aislamiento de Base de Datos en Desarrollo y Pruebas.**  
> Procedimiento normativo y técnico para que cada agente de desarrollo (sesión de Claude, Codex u otra herramienta que implementa una tarea; no el asistente de IA Copiloto de la plataforma) pruebe y migre en su propia rama hija de Neon, **NUNCA en la rama `test` compartida**.

---

## 1. Propósito y Doctrina de Aislamiento (Decisión D-8)

En entornos de desarrollo concurrentes regidos por ADPA (Aislamiento Determinista por Propiedad de Archivos), múltiples sesiones de agentes trabajan simultáneamente. La propiedad exclusiva aísla el árbol de código, pero si los agentes compartieran la base de datos de pruebas (`test`), ocurrirían colisiones destructivas:
- Mutaciones concurrentes sobre fixtures o tablas maestras (`tenants`, `usuarios`, `roles`).
- Ejecución desordenada o conflictiva de migraciones DDL con Alembic.
- Pruebas de políticas Row Level Security (RLS) que ejecutan comandos con aislamiento de tenant (`set_config('app.current_tenant_id', ...)` o `SET LOCAL ROLE lopdp_app`).

**Regla de Oro (Decisión D-8):**
Cada agente de desarrollo debe trabajar y migrar sobre su **propia rama efímera hija de Neon** (`test-<agente>`). La rama `test` compartida queda reservada exclusivamente para el runner de CI de GitHub Actions y como base común de bifurcación.

---

## 2. Procedimiento Operativo Paso a Paso

### Paso a: Crear la rama hija desde `test`
1. Ingresar a la consola web de Neon ([console.neon.tech](https://console.neon.tech)), navegar al proyecto `square-violet-52579154` (base de datos `lopdp_beta`).
2. Ir a la sección **Branches**.
3. Crear una nueva rama:
   - **Parent branch:** Seleccionar `test`.
   - **Branch name:** `test-<agente>` (por ejemplo: `test-rm14`, `test-ops04`, `test-sec02`).
4. Alternativamente, si el usuario provee el script de aprovisionamiento automatizado:
   ```powershell
   powershell -File "C:\Users\Juan Carlos\Desktop\herramientas\crear_rama_neon.ps1" -Agente <agente>
   ```

### Paso b: Configuración de cadenas en el `.env` LOCAL del agente
Copiar las cadenas de conexión generadas para la rama `test-<agente>` a las variables del archivo `.env` **LOCAL** en la máquina del agente.  
> **ADVERTENCIA CRÍTICA DE SEGURIDAD:**  
> **NUNCA** commitear ni escribir credenciales reales en el repositorio (`.env` está en `.gitignore`). A continuación se nombran las variables usando placeholders:

- `TEST_DATABASE_URL`: Conexión de aplicación para ejecutar la suite de pruebas Pytest.  
  Usa el rol dueño (`lopdp_beta_owner`) con host transaccional con connection pooling (`-pooler`).  
  *Patrón:* `postgresql+psycopg://lopdp_beta_owner:<PASSWORD>@ep-<endpoint-id>-pooler.<region>.neon.tech/lopdp_beta?sslmode=require`
- `TEST_MIGRATION_DATABASE_URL`: Conexión directa DDL para Alembic.  
  Usa el rol dueño (`lopdp_beta_owner`) **SIN `-pooler`** (puerto estándar 5432 o endpoint directo, necesario para DDL y transacciones de migración no soportadas por PgBouncer).  
  *Patrón:* `postgresql://lopdp_beta_owner:<PASSWORD>@ep-<endpoint-id>.<region>.neon.tech/lopdp_beta?sslmode=require`

### Paso c: Aplicar migraciones y comprobar el rol `lopdp_app`
1. Ejecutar las migraciones pendientes sobre la rama efímera usando la cadena directa de migración:
   ```bash
   alembic upgrade head
   ```
2. Comprobar que la migración base `20261008_app_role_rls` está aplicada y que el rol de aplicación sin privilegios `lopdp_app` existe en la base de datos de la rama:
   ```sql
   SELECT rolname, rolbypassrls, rolsuper FROM pg_roles WHERE rolname = 'lopdp_app';
   ```
   *Resultado esperado:* Debe devolver 1 fila con `rolbypassrls = false` y `rolsuper = false`. Si el rol no existe, los tests de RLS (`tests/test_rls_app_role.py`) harán `pytest.skip`.

### Paso d: Borrar la rama efímera al terminar
Una vez que la tarea ha sido validada, commiteada y fusionada en `main`:
1. Ir a la consola de Neon, sección **Branches**.
2. Seleccionar la rama `test-<agente>` y eliminarla (**Delete Branch**).
3. O mediante la API REST de Neon:
   ```bash
   curl -X DELETE "https://console.neon.tech/api/v2/projects/<PROJECT_ID>/branches/<BRANCH_ID>" \
        -H "Authorization: Bearer <NEON_API_KEY>" \
        -H "Accept: application/json"
   ```

---

## 3. Límites del Plan Gratuito de Neon

Datos oficiales extraídos de la documentación de Neon ([neon.com/docs/introduction/plans](https://neon.com/docs/introduction/plans), verificado a octubre de 2026):

1. **Ramas por proyecto:**
   - **Máximo 10 ramas** por proyecto en el plan gratuito (Free Tier).
   - En el proyecto actual se mantienen activas de forma permanente 2 ramas base (`production` y `test`). Quedan **hasta 8 ramas simultáneas** para agentes de desarrollo concurrentes.
2. **Cómputo mensual acumulado:**
   - **100 horas de cómputo (CU-hours)** por proyecto al mes en el plan gratuito.
   - Las instancias de cómputo escalan a cero automáticamente tras 5 minutos de inactividad, conservando las horas.
3. **Almacenamiento y Transferencia:**
   - **1 GB de almacenamiento** PostgreSQL por proyecto (con un límite global de 20 GB por cuenta).
   - **5 GB de transferencia de datos** pública mensual (egress).
4. **Política de Purgado Preventivo:**
   - Si se alcanza el umbral de 8 ramas activas, se prohíbe crear nuevas ramas hasta que se purguen las ramas de tareas concluidas.
   - *Nota de verificación:* Todo límite de cuota o escalado automático se monitoriza directamente desde el dashboard de Neon. Parámetros de facturación o ampliación de plan fuera de lo indicado aquí quedan marcados como **no verificado**.

---

## 4. Hallazgos Verificables en el Repositorio (SSOT de Código)

A continuación se detallan los puntos contractuales de la arquitectura verificables en el árbol de código:

### (a) Configuración de roles y pooler en URLs de prueba
- En [`tests/conftest.py`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/tests/conftest.py#L55-L56):
  ```python
  if "TEST_DATABASE_URL" in os.environ:
      os.environ["DATABASE_URL"] = os.environ["TEST_DATABASE_URL"]
  ```
  `TEST_DATABASE_URL` se conecta con el rol dueño `lopdp_beta_owner` (con host `-pooler`), y las pruebas que evalúan RLS ([`tests/test_rls_app_role.py`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/tests/test_rls_app_role.py#L3-L5)) ejecutan explícitamente `SET LOCAL ROLE lopdp_app` para auditar el comportamiento no privilegiado.
- En [`alembic/env.py`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/alembic/env.py#L15-L20):
  ```python
  url = os.environ.get("MIGRATION_DATABASE_URL") or os.environ.get("DATABASE_URL")
  ```
  Para migraciones locales, `TEST_MIGRATION_DATABASE_URL` utiliza el rol dueño `lopdp_beta_owner` **sin `-pooler`**, asegurando que operaciones DDL transaccionales no fallen por limitaciones del PgBouncer de Neon.

### (b) El arnés exige la rama `test` migrada
- Conforme al **Aporte 112 (Aprendizaje A4)** en [`governance/artefactos/APORTES_INEDITOS.md`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/governance/artefactos/APORTES_INEDITOS.md#L2312):
  > *«A4. El arnés requiere la rama test migrada (no solo test-<agente>).»*
- Aunque el agente pruebe su migración en `test-<agente>` (por ejemplo, en [`governance/tareas/RM-14.md`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/governance/tareas/RM-14.md) para la tabla `audit_events`), antes de la fusión o ejecución del arnés sobre la rama `test` compartida, dicha rama debe tener aplicadas las migraciones hasta la cabeza común para que las pruebas de integración no fallen.

### (c) El secreto `TEST_DATABASE_URL` de GitHub Actions
- En [`.github/workflows/zero-regression-pipeline.yml`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/.github/workflows/zero-regression-pipeline.yml#L61-L64):
  ```yaml
  env:
    # Rama test de Neon (rol dueño); los tests de RLS hacen SET ROLE lopdp_app.
    TEST_DATABASE_URL: ${{ secrets.TEST_DATABASE_URL }}
  run: pytest tests/ -v
  ```
  El secreto `TEST_DATABASE_URL` en GitHub Actions apunta fija y exclusivamente a la rama compartida **`test`**. Un agente de desarrollo en local **NO tiene acceso ni debe modificar** este secreto en GitHub; únicamente configura sus variables en su propio `.env` local.

### (d) Rotación de contraseñas y fallo en CI
- Si en Neon se rota o regenera la contraseña del rol `lopdp_beta_owner` para la rama `test`, es mandatorio actualizar de inmediato el secreto `TEST_DATABASE_URL` en los Settings del repositorio en GitHub (`Settings -> Secrets and variables -> Actions`).
- Si no se actualiza, el pipeline de CI fallará inmediatamente durante el paso `Backend Pytest (E2E y Unitarias)` con el error:
  ```text
  sqlalchemy.exc.OperationalError: (psycopg.OperationalError) connection failed: password authentication failed for user "lopdp_beta_owner"
  ```
  bloqueando el check obligatorio **Arnés Físico Determinista** en todos los PRs.

---

## 5. El `.env` en cada carpeta de trabajo (regla para todo el equipo)

Aplica a Juan Carlos, Aleczandra, José y a toda sesión de IA, en cualquier sistema operativo. Las ramas de prueba vigentes son `test-main` (CI de `main`), `test-<persona>` y sus hijas temporales; `test` y `revision` ya no existen, aunque secciones anteriores las nombren.

**Por qué existe:** el `.env` de la carpeta principal de quien migra producción apunta a producción. Un worktree no trae `.env` porque está ignorado por git. Si el código o una persona toma en ese caso el `.env` de la carpeta principal, la aplicación queda conectada a producción desde una carpeta de pruebas.

**Reglas:**

1. **Cada worktree tiene su propio `.env`**, escrito a mano con las URL de su rama Neon de prueba. `DATABASE_URL` y `TEST_DATABASE_URL` apuntan a esa rama.
2. **Nunca se copia ni se enlaza el `.env` de la carpeta principal** a un worktree.
3. **El código nunca busca un `.env` fuera de su propia carpeta.** Si falta, el proceso falla con un mensaje claro. Un cambio que añada ese respaldo no se fusiona.
4. **Ningún `.env` de un worktree contiene el host de producción** (`ep-late-hall`), ni siquiera en una variable que no se use.
5. **Antes de correr pruebas, la API o migraciones en un worktree, se ejecuta la comprobación** de abajo. Si falla, se detiene y se corrige; no se sigue sin ella.
6. **Una sesión de IA no recibe ni imprime URL de conexión.** Si encuentra el host de producción, aborta y lo avisa.

**Comprobación en Windows (PowerShell), desde la carpeta del worktree:**

```powershell
if (-not (Test-Path .env)) { throw "Falta el .env de este worktree: créalo con tu rama de prueba." }; if (Select-String -Path .env -Pattern 'ep-late-hall' -Quiet) { throw "Este .env contiene el host de producción: abortado." }; "OK: .env propio y sin producción"
```

**Comprobación en Mac o Linux (terminal), desde la carpeta del worktree:**

```bash
if [ ! -f .env ]; then echo "Falta el .env de este worktree: créalo con tu rama de prueba."; elif grep -q 'ep-late-hall' .env; then echo "Este .env contiene el host de producción: abortado."; else echo "OK: .env propio y sin producción"; fi
```

Esta comprobación mira solo el `.env` de la carpeta. Si una variable de la sesión de la terminal ya apunta a producción, cierra esa terminal y abre otra.
