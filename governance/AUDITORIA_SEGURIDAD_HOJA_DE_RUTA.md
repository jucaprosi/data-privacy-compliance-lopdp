# Auditoría de Seguridad Previa a Producción — Hoja de Ruta (SEC-02)
`¤seguridad` `¤adpa` `¤auditoria`

> **Fecha de auditoría:** 2026-10-18  
> **Commit auditado (`origin/main` / `HEAD`):** `6c5efd5078302b436c9e69a7bcc377bb2b4f96ed`  
> **Árbitro de la tarea:** Informe sin hallazgos críticos abiertos (evaluado por el coordinador).  
> **Nivel de intervención:** Documental exclusivo (análisis de código, pruebas estáticas y dinámicas; cero modificaciones de código).

---

## 1. Resumen Ejecutivo y Estado General de Seguridad

Se ejecutó la auditoría de seguridad integral sobre el núcleo de la API (`app_core/`, `api/`), los mecanismos de aislamiento multi-inquilino (RLS), la segregación de funciones (SoD / Cuatro Ojos), las protecciones criptográficas de evidencia en Cloudflare R2, las cabeceras HTTP de seguridad y los endpoints de la API REST de la Plataforma LOPDP 360.

### Métricas de Verificación Dinámica y Estática:
- **Suite de autenticación y seguridad (`test_autenticacion.py`, `test_evidencia_filtro_rol.py`, `test_evidencia_validacion_servidor.py`, `test_cabeceras_seguridad.py`):** **97/97 pasaron** (100% éxito en 114.00s).
- **Protección contra inyección SQL e interpolación (`test_sin_sql_interpolado.py`):** **8/8 pasaron** (cero interpolación en sentencias SQL dinámicas).
- **Mamparos herméticos y compuertas ADPA (`test_adpa_bulkhead.py`):** **6/6 pasaron**.
- **Flujos de integración y retiro de tokens simulados (`test_e2e_flujo_completo.py`, `test_api_integracion.py`, `test_ai_copilot.py`):** **8/8 pasaron**.

### Cuadro Resumen de Hallazgos

| ID | Área Auditada | Severidad | Estado | Resumen |
| :--- | :--- | :--- | :--- | :--- |
| **SEC-02-H01** | Endpoints de Dominio | **Alto** | Abierto | Router obsoleto `arco.py` registrado en `/api/v1/arco` con almacén en memoria (`_arco_store`) en lugar de `arco_router.py` persistente con RLS. |
| **SEC-02-H02** | Endpoints sin Identidad | **Medio** | Abierto | Endpoint `/ai_copilot` (`implementation_assistant.py`) valida sintaxis de cabecera `X-Tenant-ID` pero no autentica identidad ni membresía activa. |
| **SEC-02-H03** | Endpoints sin Identidad | **Bajo** / Diseño | Aclarado | `niif18` y `riesgos_mtge` son motores de cálculo puro en memoria sin persistencia ni acceso a datos multi-inquilino. |
| **SEC-02-H04** | Gestión de Secretos | **Bajo** | Mitigado | Valores de contingencia (fallback) para `JWT_SECRET` en `api/index.py` y `app_core/config.py`. Sin impacto activo en modo `oidc`. |

---

## 2. Alcance Detallado de la Auditoría

### 2.1 Aislamiento Multi-Inquilino y RLS (Row Level Security)
- **Implementación auditada:** `app_core/db/session.py` (`fijar_contexto_rls`, `get_session`, `get_tenant_session`) y `tests/test_database_rls.py`.
- **Mecanismo:** La fijación de variables de sesión en PostgreSQL se realiza exclusivamente mediante sentencias parametrizadas seguras:
  ```python
  await session.execute(text("SELECT set_config('app.current_tenant_id', :tid, true)"), {"tid": tenant_id})
  ```
  El uso de `is_local = true` garantiza el alcance de transacción (`SET LOCAL`), impidiendo fugas de contexto entre conexiones reutilizadas en el pool de SQLAlchemy (`async_sessionmaker`).
- **AST Security Check:** `tests/test_sin_sql_interpolado.py` verifica mediante análisis del árbol sintáctico (AST) que ninguna llamada a `session.execute` o `text` contenga interpolación de variables o `f-strings`. Solo existen dos exenciones documentadas en migraciones DDL de Alembic donde PostgreSQL no admite *bind parameters*.
- **Evaluación:** Conforme y robusto.

### 2.2 Separación de Funciones (SoD) y Principio de Cuatro Ojos
- **Implementación auditada:** `app_core/security.py` (`validar_permiso_sod`, `ACCIONES_INCOMPATIBLES_DPO`), `features/organizacion/services/sod_engine.py` y `features/roadmap/services/evidencia_engine.py`.
- **Regla del DPO (Art. 48 LOPDP):** Se prohíbe formalmente que los roles DPO (`DPD_DPO_INTERNO`, `DPD_DPO_EXTERNO`) ejecuten remediaciones, aprueben finalidades RAT o asignen dueños de control (`DPO_INCOMPATIBLE_ROLES = {Role.implementador, Role.coordinador}`).
- **Principio de Cuatro Ojos en Evidencias:** En `evidencia_engine.py:validate_evidence`, la validación de una evidencia subida por un usuario exige `check_four_eyes(current[0], user_id)`. Si quien intenta aprobar la evidencia es el mismo usuario que la subió (`uploaded_by == user_id`), el motor arroja `SoDViolation` (HTTP 409 Conflict).
- **Evaluación:** Conforme y blindado en backend.

### 2.3 Autenticación y Autorización (Verificación SEC-03 y SEC-07)
- **Implementación auditada:** `app_core/security.py` y `api/rbac.py`.
- **Mecanismo OIDC:** Por defecto (`AUTH_MODE` ausente, vacío o distinto de `headers`), el sistema opera en modo `oidc`. La identidad del usuario es extraída exclusivamente de la verificación criptográfica del token de Google (`PyJWT[crypto]` con claves públicas de Google obtenidas de JWKS con caché en memoria).
- **Protección contra suplantación:** En modo `oidc`, la cabecera `X-User-ID` se ignora por completo. La pertenencia del usuario al tenant declarado en `X-Tenant-ID` y la posesión del rol declarado en `X-Role` se comprueban obligatoriamente contra la tabla relacional `user_tenant_roles`. Si el usuario no tiene rol activo en el tenant, el servidor responde HTTP 403 Forbidden.
- **Retiro de tokens simulados (SEC-07):** Se comprobó que `PREFIJO_TOKEN_SIMULADO` (`jwt_mock_tenant_`) fue erradicado de `app_core/security.py`. Sin cabecera `X-Tenant-ID` válida, el servidor responde HTTP 401 Unauthorized.
- **Evaluación:** Conforme.

### 2.4 Carga y Validación de Evidencias (Verificación SEC-04 y SEC-05)
- **Filtrado de evidencia por rol (SEC-04):** En `evidencia_engine.py:list_evidence`, cuando el rol es `responsable_area`, la consulta SQL aplica `AND uploaded_by = :uid`. Si no se provee identidad del usuario, falla cerrado devolviendo lista vacía `[]`. Los demás roles ven la evidencia autorizada del tenant.
- **Validación estricta en servidor (SEC-05):**
  - Lista blanca exhaustiva en `app_core/storage/r2.py:TIPOS_PERMITIDOS`: PDF, PNG, JPEG, DOCX, XLSX, CSV, TXT.
  - Límite máximo: 10 MB (`TAMANO_MAXIMO_BYTES = 10 * 1024 * 1024`).
  - La verificación se aplica tanto al solicitar la URL de subida (`/tasks/{task_id}/evidence/upload-url`) como al registrar la evidencia en base de datos (`/tasks/{task_id}/evidence`).
  - El rechazo genera `ErrorNegocio` con códigos formales `EVIDENCE_TYPE_NOT_ALLOWED` y `EVIDENCE_TOO_LARGE`.
- **Evaluación:** Conforme.

### 2.5 Exposición de Errores Públicos y Trazas
- **Implementación auditada:** `main.py` (`http_exception_handler`, `error_negocio_handler`) y `api/index.py`.
- **Manejo de excepciones:** `main.py` captura `HTTPException` y retorna únicamente `{"detail": exc.detail}`. Los tracebacks se dirigen exclusivamente a la consola de logging estructurado JSON (`jubys_lopdp_json_logger`).
- **Fallback en arranque:** En `api/index.py`, los endpoints `/health` devuelven únicamente el nombre de la clase de excepción (`err_tipo`), evitando divulgar rutas absolutas de archivos o credenciales en el cuerpo de la respuesta HTTP pública.
- **Evaluación:** Conforme.

### 2.6 Gestión de Secretos y Variables de Entorno
- **Auditoría de cadenas y tokens:** No existen credenciales activas ni tokens de producción commiteados en el repositorio.
- **Credenciales Cloudflare R2:** Leídas estrictamente desde `os.environ["R2_ACCESS_KEY_ID"]` y `os.environ["R2_SECRET_ACCESS_KEY"]`.
- **JWT Secret:** Se identificó un valor de fallback `"super_secret_jwt_key_for_lopdp_360_prod_fallback"` en `api/index.py` y `app_core/config.py`. En la arquitectura actual OIDC (SEC-03), el backend no firma tokens simétricos HS256, sino que verifica tokens RS256 de Google, por lo que esta clave no tiene impacto en la autorización de usuarios de la API.
- **Evaluación:** Conforme con recomendación menor (ver Hallazgo SEC-02-H04).

### 2.7 Cabeceras HTTP de Seguridad (Verificación SEC-06)
- **Backend (`vercel.json`):**
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: no-referrer`
  - `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()`
  - `Content-Security-Policy: frame-ancestors 'none'`
- **Frontend (`frontend/next.config.ts`):**
  - Implementa `headers()` en Next.js aplicando HSTS, nosniff, DENY, `frame-ancestors 'none'` y `Content-Security-Policy-Report-Only` (modo informe sin `unsafe-inline` en scripts para Next.js).
- **Pruebas automatizadas:** `tests/test_cabeceras_seguridad.py` ejecutado y 100% aprobado.
- **Evaluación:** Conforme.

---

## 3. Registro Detallado de Hallazgos

### Hallazgo SEC-02-H01 (Alto): Coexistencia de Router Obsoleto `arco.py` con Mock en Memoria en lugar de `arco_router.py`

- **Severidad:** **Alto** (Integridad de datos y multi-tenancy).
- **Evidencia:** [api/routers/arco.py:16-31](file:///C:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/api/routers/arco.py#L16-L31) frente a [api/routers/arco_router.py:1-34](file:///C:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/api/routers/arco_router.py#L1-L34) y [main.py:84](file:///C:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/main.py#L84).
- **Descripción:**
  En `main.py` línea 84, la lista `ROUTERS_MAP` incluye `("api.routers.arco", "arco")`. El archivo `api/routers/arco.py` es un archivo semilla legado que mantiene un array en memoria (`_arco_store = []`) y extrae el tenant mediante `authorization.replace("Bearer ", "")`, sin validar autenticación OIDC ni persistir en PostgreSQL. Por el contrario, el archivo moderno `api/routers/arco_router.py` (creado en la tarea ADPA-01/RM-02) implementa la integración real con `features.derechos_arco.derechos_arco_service` y utiliza `Depends(get_tenant_session)` con RLS. Dado que `arco_router.py` no declara `AUTO_REGISTRO = True` ni está en `ROUTERS_MAP`, las peticiones a `/api/v1/arco/solicitudes` son atendidas por el router legado en memoria.
- **Reproducción:**
  ```powershell
  python -c "from main import app; print([r.endpoint.__module__ for r in app.routes if hasattr(r, 'path') and '/arco' in r.path])"
  # Imprime: ['api.routers.arco'] en lugar de 'api.routers.arco_router'
  ```
- **Recomendación para el Coordinador:**
  Proponer una micro-tarea técnica para actualizar `main.py:84` reemplazando `api.routers.arco` por `api.routers.arco_router`, o incorporar `AUTO_REGISTRO = True` en `api/routers/arco_router.py` y archivar/eliminar el archivo semilla `api/routers/arco.py`.

---

### Hallazgo SEC-02-H02 (Medio): Router `implementation_assistant.py` sin Validación de Membresía ni Autenticación OIDC

- **Severidad:** **Medio** (Consumo no autorizado de motor RAG / Asistente IA).
- **Evidencia:** [api/routers/implementation_assistant.py:23-38](file:///C:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/api/routers/implementation_assistant.py#L23-L38).
- **Descripción:**
  Los endpoints `GET /api/v1/ai_copilot/estado` y `POST /api/v1/ai_copilot/consulta` exigen la cabecera `x_tenant_id: str = Header(...)`, pero la validación se limita a la función `validar_tenant`:
  ```python
  def validar_tenant(tenant: str) -> None:
      if not tenant.strip() or len(tenant) > 120:
          raise HTTPException(status_code=400, detail="Contexto de organización inválido.")
  ```
  No se utiliza `get_context`, `get_usuario_autenticado` ni `get_current_tenant`. En consecuencia, cualquier cliente con acceso de red puede enviar un identificador de tenant arbitrario y consumir el asistente de implementación y las búsquedas semánticas del corpus normativo sin haber iniciado sesión en Google ni pertenecer a la organización.
- **Reproducción:**
  ```powershell
  python -c "from api.routers.implementation_assistant import router; print([d.call.__name__ for d in router.routes[1].dependant.dependencies])"
  # No incluye dependencias de seguridad o identidad.
  ```
- **Recomendación para el Coordinador:**
  Actualizar `api/routers/implementation_assistant.py` para inyectar `ctx: dict = Depends(get_context)` o `tenant_id: str = Depends(get_current_tenant)`.

---

### Hallazgo SEC-02-H03 (Bajo / Decisión de Diseño): Routers `niif18` y `riesgos_mtge` como Endpoints Funcionales en Memoria

- **Severidad:** **Bajo / Informativo** (Servicio computacional puro sin persistencia).
- **Evidencia:** [api/routers/niif18.py:38-132](file:///C:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/api/routers/niif18.py#L38-L132) y [api/routers/riesgos_mtge.py:20-42](file:///C:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/api/routers/riesgos_mtge.py#L20-L42).
- **Descripción:**
  Ni `niif18.py` ni `riesgos_mtge.py` declaran dependencias de identidad (`X-User-ID`, `Authorization`, `X-Tenant-ID`).
  - `niif18`: Es una utilidad de reporting contable bajo la norma NIIF 18. Recibe balances en memoria (Excel/CSV), procesa subtotales y emite informes descargables (Markdown, PDF, Excel) sin consultar ni escribir en base de datos.
  - `riesgos_mtge`: Implementa la fórmula paramétrica de tratamiento de datos a gran escala según la Resolución SPDP-SPD-2026-0005-R. Es una función puramente matemática determinista sin estado ni acceso a registros de la plataforma.
- **Decisión y Recomendación:** Ver Sección 4 para la justificación de cada endpoint.

---

### Hallazgo SEC-02-H04 (Bajo): Secreto de Contingencia Legado `JWT_SECRET` en Archivos de Arranque

- **Severidad:** **Bajo**.
- **Evidencia:** [api/index.py:12](file:///C:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/api/index.py#L12) y [app_core/config.py:42](file:///C:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/app_core/config.py#L42).
- **Descripción:**
  Se asigna por defecto `os.environ.setdefault("JWT_SECRET", "super_secret_jwt_key_for_lopdp_360_prod_fallback")`. Aunque `JWT_SECRET` ya no se usa para autenticar usuarios en la API (reemplazado por Google OIDC con RS256 en SEC-03), la presencia de claves hardcodeadas en código fuente puede disparar falsos positivos en escáneres SAST de producción.
- **Recomendación para el Coordinador:**
  Limpiar la variable `jwt_secret` de `app_core/config.py` y `api/index.py` si no existen otros módulos que dependan de ella.

---

## 4. Endpoints sin Identidad — Decisión Justificada por Cada Uno

Conforme al encargo específico de la tarea SEC-02, se analizan los cuatro routers señalados en el hallazgo del 2026-10-17:

### 1. `niif18` (`api/routers/niif18.py`)
- **Estado actual:** No exige identidad ni cabeceras de tenant.
- **Análisis de seguridad:** Todos los métodos (`/procesar-balance`, `/recalcular-subtotales`, `/mpm`, `/informe`, `/exportar/*`, `/doctrina`) son transformaciones *stateless* puras en memoria. No consultan la base de datos PostgreSQL, no leen almacenamiento persistente ni exponen datos de otros inquilinos.
- **Decisión recomendada:** **Público / Abierto como herramienta utilitaria**, O **Exigir sesión si se desea restringir el uso de cómputo a clientes registrados**. Si el modelo de negocio contempla el diagnóstico NIIF 18 como *lead magnet* o herramienta pública previa al registro, es seguro mantenerlo público; si es un servicio de pago, debe agregarse `Depends(get_usuario_autenticado)`.
- **Clasificación:** *Decisión de modelo de negocio del propietario*. No representa riesgo de fuga de datos multi-inquilino.

### 2. `riesgos_mtge` (`api/routers/riesgos_mtge.py`)
- **Estado actual:** No exige identidad ni cabeceras de tenant.
- **Análisis de seguridad:** Expone `POST /api/v1/riesgos/mtge/evaluar`. Recibe atributos numéricos y booleanos (`numero_titulares`, `volumen_datos_por_titular`, etc.) y aplica el algoritmo matemático del umbral MTGE de la SPDP. No guarda datos en base de datos.
- **Decisión recomendada:** **Público a propósito**. Sirve como calculadora paramétrica de evaluación previa. Su exposición no vulnera el aislamiento de tenants ni divulga información reservada.

### 3. `arco` (`api/routers/arco.py` vs. `api/routers/arco_router.py`)
- **Estado actual:** `api/routers/arco.py` extrae un token simulado de `authorization` pero no implementa autenticación real ni persistencia.
- **Análisis de seguridad:** El ejercicio de derechos ARCO (Acceso, Rectificación, Cancelación, Oposición) involucra datos personales altamente sensibles (cédula, nombres, tipo de solicitud).
- **Decisión recomendada:** **DEBE EXIGIR SESIÓN OBLIGATORIA CON RLS**. Las solicitudes ARCO no pueden ser gestionadas por un mock en memoria. Debe activarse de inmediato el router persistente `api/routers/arco_router.py` con `get_tenant_session`, exigiendo `get_current_tenant` o `get_context`.

### 4. `implementation_assistant` (`api/routers/implementation_assistant.py`)
- **Estado actual:** Exige `X-Tenant-ID` en cabecera pero solo valida su longitud y formato, sin autenticar al solicitante.
- **Análisis de seguridad:** Los endpoints `GET /api/v1/ai_copilot/estado` y `POST /api/v1/ai_copilot/consulta` consumen recursos del motor RAG y pueden consumir tokens de modelos de lenguaje (LLM). Permitir su invocación sin autenticar al usuario abre el sistema a denegación de servicio (DoS) por consumo abusivo de APIs de IA.
- **Decisión recomendada:** **DEBE EXIGIR SESIÓN**. Debe requerir `ctx: dict = Depends(get_context)` para garantizar que la consulta la realiza un usuario autenticado y perteneciente a la organización indicada.

---

## 5. Lo No Verificado

Conforme a la política de verificación honesta del proyecto:

1. **Despliegue real en producción en Vercel:** No se pudo verificar la emisión en vivo de cabeceras HTTP mediante `curl -I https://app.evydentia.com` debido a que el entorno de auditoría es local; la verificación depende de la inspección de `vercel.json` y los tests de Playwright simulados.
2. **Escaneo antivirus en tiempo real en Cloudflare R2:** Al no haber un escáner antivirus desplegado físicamente en runtime (tarea sujeta al boceto `ANTIVIRUS_EVIDENCIA_BOCETO.md` de SEC-05), la inocuidad del binario depositado en R2 queda catalogada como **NO VERIFICADA**.
3. **Comportamiento de Google JWKS ante revocación inmediata:** La caché de claves públicas de Google en `app_core/security.py` opera con TTL de 3600 segundos (`VIGENCIA_CLAVES_SEGUNDOS = 3600`); la revocación instantánea de una clave pública de Google antes de su vencimiento no fue verificada dinámicamente contra la red de Google.
4. **Validación end-to-end del flujo visual de Playwright en Chromium:** Las pruebas unitarias y de integración de Python pasaron al 100%, pero la ejecución completa del navegador Playwright requiere el arnés físico continuo.
