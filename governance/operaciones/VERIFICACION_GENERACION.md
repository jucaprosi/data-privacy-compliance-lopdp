# Verificación de la Generación de Hoja de Ruta en Vercel (Plan Hobby)
`¤roadmap` `¤ci-cd` `¤arbitro`

> **SSOT Operativa para la Verificación en Entorno Gratuito (Decisión D-1, Tarea OPS-02).**  
> Guía normativa y protocolo de medición determinista para verificar que la generación en línea de hojas de ruta de cumplimiento LOPDP culmina exitosamente dentro del umbral de ejecución serverless de Vercel.  
> **Nota de Gobernanza:** Este documento establece el procedimiento. La medición física en producción es potestad exclusiva del propietario del entorno.

---

## 1. Qué se Mide y Cómo

La arquitectura de la Plataforma LOPDP 360 adoptó la **Decisión D-1**: en el plan gratuito de Vercel (Hobby), la generación completa de la Hoja de Ruta Inteligente se ejecuta de manera síncrona dentro del ciclo de vida de la propia solicitud HTTP, prescindiendo de workers desacoplados persistentes.

### Componentes Técnicos Auditables
1. **Punto de Entrada API Gateway:**
   - En [`api/routers/roadmaps.py`](../../api/routers/roadmaps.py#L40-L51), el endpoint `POST /api/v1/roadmaps/generate` recibe el payload de diagnóstico (`GenerateRoadmapRequest`), valida el rol autorizado (`implementador`), inyecta el contexto de tenant (`ctx["tenant_id"]`) y despacha la invocación hacia el servicio de dominio.
2. **Motor de Generación en Línea:**
   - En [`features/roadmap/services/generacion_en_linea.py`](../../features/roadmap/services/generacion_en_linea.py#L33-L259), la función `generate_roadmap_inline` orquesta el flujo:
     - Crea el registro inicial en estado `draft` en la base de datos PostgreSQL ([L50-L63](../../features/roadmap/services/generacion_en_linea.py#L50-L63)).
     - Ejecuta la inferencia del modelo LLM mediante `asyncio.to_thread(generate_roadmap_document, ...)` ([L84-L92](../../features/roadmap/services/generacion_en_linea.py#L84-L92)) para evitar el bloqueo del bucle de eventos asyncio en Windows y Linux.
     - Valida el esquema estructurado `RoadmapDocument` (Pydantic), calcula los KPIs globales y persiste las olas y tareas en Neon PostgreSQL ([L133-L245](../../features/roadmap/services/generacion_en_linea.py#L133-L245)).
     - Retorna `{job_id, status: "completed", roadmap_id}` o `{job_id, status: "failed", roadmap_id}` si ocurre un fallo no recuperable.
3. **Configuración de Límite Serverless en Vercel:**
   - En [`vercel.json`](../../vercel.json#L1-L7), se fija explícitamente:
     ```json
     {
       "functions": {
         "api/index.py": {
           "maxDuration": 300
         }
       }
     }
     ```
     permitiendo un tiempo máximo de ejecución de **300 segundos** para la función serverless de backend.

---

## 2. Procedimiento de Ejecución en Producción sin Exponer Secretos

Para llevar a cabo la medición notarial sin comprometer credenciales ni alterar datos reales:

### A. Precondiciones y Verificación Previa del Despliegue
1. **Consulta de Variables y Despliegues:**
   - Consultar [`governance/operaciones/PROCEDIMIENTO_VERCEL.md`](../../governance/operaciones/PROCEDIMIENTO_VERCEL.md) y [`governance/operaciones/VARIABLES_VERCEL.md`](../../governance/operaciones/VARIABLES_VERCEL.md).
   - Verificar que `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL` (`deepseek-chat`) y `DATABASE_URL` estén provisionadas en Production (`vercel env ls`).
2. **Árbitro Exógeno de Salud:**
   - Antes de lanzar la generación, comprobar la estabilidad del despliegue ejecutando [`scripts/verificar_despliegue.py`](../../scripts/verificar_despliegue.py):
     ```bash
     python scripts/verificar_despliegue.py <dominio_produccion>
     ```
   - El script debe retornar **código 0** confirmando `status == "OPERATIONAL"` y todas las rutas activas en `/openapi.json`.

### B. Identidad y Tenant de Prueba
La plataforma **no valida tokens JWT**: hoy la identidad llega en las cabeceras `X-User-ID`, `X-Tenant-ID` y `X-Role` (la autenticación verificable con Google es la tarea SEC-03, pendiente). Pero `get_context` (`api/rbac.py`) exige además que el usuario tenga ese rol **activo** en `user_tenant_roles` del tenant, así que la identidad de prueba tiene que existir en la base de datos.

- **Tenant aislado de pruebas:** un tenant creado solo para esta medición, al que este documento llama `<TENANT_ID_PRUEBA>`. No existe ninguno todavía: lo crea el propietario (acción sobre datos de producción). No uses el de ningún cliente.
- **Usuario de prueba:** un usuario `<USER_ID_PRUEBA>` con el rol `implementador` activo en ese tenant (rol exigido por `POST /generate`).
- **Regla anti-exposición:** el dominio y los identificadores se referencian por variables de la terminal local (`$PROD_URL`, `$TENANT_ID`, `$USER_ID`) y no se pegan en bitácoras compartidas. Este documento no contiene ningún valor real.
- **Aviso:** si SEC-03 llega a producción con `AUTH_MODE=oidc`, las cabeceras dejarán de bastar y este procedimiento habrá que rehacerlo con un token de Google.

---

### C. Ejecución de la Medición (Cronometrada)
Realizar la petición midiendo el tiempo transcurrido desde el envío hasta la respuesta HTTP 200. El cuerpo sigue `GenerateRoadmapRequest` (`features/roadmap/domain/models.py`); el servidor sustituye `tenant_id` y `user_id` por los de las cabeceras, pero el esquema los exige. Los límites de `variables` son los de `PlanningVariables`: plazo de 3 a 12 meses, presupuesto no negativo, moneda de tres letras, al menos un miembro del equipo y un DPO.

```bash
curl -X POST "$PROD_URL/api/v1/roadmaps/generate"      -H "X-User-ID: $USER_ID" -H "X-Tenant-ID: $TENANT_ID" -H "X-Role: implementador"      -H "Content-Type: application/json"      -d '{"tenant_id": "<TENANT_ID_PRUEBA>", "user_id": "<USER_ID_PRUEBA>",
          "variables": {"plazo_meses": 6, "presupuesto": 15000, "moneda": "USD",
                        "equipo": ["DPO", "Implementador"], "dpo": "<NOMBRE_DPO>", "idioma": "ES"},
          "assessment": {}}'      -w "
Tiempo total: %{time_total}s | Codigo HTTP: %{http_code}
"
```

Un `assessment` vacío es el caso más ligero; con un diagnóstico real, más largo, la duración puede ser mayor. Mide también con uno real y anota en la plantilla cuál usaste.

La respuesta correcta es HTTP 200 con `{"job_id": "...", "status": "completed", "roadmap_id": "..."}`. Si el servidor responde `"status": "failed"`, la generación no terminó: anótalo como fallo.

### D. Procedimiento de Limpieza Post-Prueba
Al terminar la medición, purgar los registros de prueba generados para no alterar métricas ni ocupar cuota innecesaria de base de datos:
1. Conectarse a la base de datos de producción con el rol autorizado mediante conexión administrativa.
2. Ejecutar la sentencia de limpieza acotada estrictamente al tenant de pruebas:
   ```sql
   DELETE FROM roadmaps WHERE tenant_id = '<TENANT_ID_PRUEBA>';
   ```
   *(Las tareas y olas asociadas se eliminan en cascada gracias a las claves foráneas `ON DELETE CASCADE` de PostgreSQL)*.
3. Si Redis está configurado (`UPSTASH_REDIS_URL`), expirar o limpiar las llaves de estado asociadas al `job_id` retornado.

---

## 3. Plantilla Notarial de Registro del Resultado

El propietario o coordinador que ejecute la prueba completará la siguiente tabla notarial de benchmarking:

| Fecha (AAAA-MM-DD HH:MM) | Duración (s) | Intentos del Modelo (Retries) | Resultado (completed / failed) | Notas Técnicas y Contexto |
| :--- | :--- | :--- | :--- | :--- |
| *Ej. 2026-10-18 10:30* | *48.5 s* | *1 intento (0 retries)* | *completed* | *Payload estándar: 12 dimensiones, 38 preguntas LOPDP.* |
| | | | | |
| | | | | |

---

## 4. Criterio de Decisión y Umbral para Apertura de Evaluación de Colas (PROPUESTA)

> **ESTADO DE LA SECCIÓN:** **PROPUESTA** (Sujeta a validación empírica y ratificación del Tech Lead).

La decisión D-1 asume que una función serverless en Vercel puede completar la inferencia y persistencia en una ventana confortable. No obstante, variaciones en la latencia de red, tiempo de respuesta de la API del LLM o reintentos correctivos por errores de validación sintáctica pueden aproximar la solicitud al límite de tiempo.

### Criterio de Umbral Propuesto (Alerta al 70%)
- **Umbral Crítico de Advertencia:** **210 segundos (70% del límite de 300 s)**.
- **Justificación Técnica:**
  - El motor `generate_roadmap_document` ([`features/roadmap/services/generacion_engine.py`](../../features/roadmap/services/generacion_engine.py#L52)) incluye hasta `max_retries = 2` en caso de salida truncada o fallo en el schema Pydantic.
  - Cada reintento completo del LLM añade el tiempo de una llamada más. **No hay una medición de cuánto tarda**: la medición de este procedimiento es la que lo dirá (no verificado).
  - Si una generación base sobrepasa los **210 segundos**, un único reintento correctivo provocaría un timeout 504 (*GATEWAY_TIMEOUT*) ineludible por parte de la infraestructura de Vercel.

### Plan de Acción si se Cruza el Umbral
Si cualquier medición real supera los **210 segundos** o si se registran fallos por timeout en producción:
1. Abrir formalmente la tarea de evaluación de arquitectura de **Colas Asíncronas** (apoyada en el cliente Redis `app_core/queue/redis_client.py` y worker externo o tarea serverless delegada).
2. Modificar el endpoint `POST /generate` para retornar de inmediato `202 Accepted` con `job_id`, delegando el procesamiento de fondo a un worker desacoplado.

---

## 5. Verificación de Límites Oficiales de Vercel (Estado del Proveedor)

- **Fuente oficial consultada:** [vercel.com/docs/functions/limitations](https://vercel.com/docs/functions/limitations). La página declara su última actualización el 2026-08-24; la consulta se hizo el 2026-10-16.
- **Límites confirmados para el plan Hobby:**
  - **Duración de función:** 300 s por defecto y como máximo (con Fluid compute). Al superarla, Vercel responde 504 (`FUNCTION_INVOCATION_TIMEOUT`).
  - **Memoria:** 2 GB y 1 vCPU, por defecto y como máximo.
  - **Cuerpo de la petición o de la respuesta:** 4,5 MB como máximo (si se supera, error 413).
- **Configuración aplicada en el proyecto:** `vercel.json` fija `functions."api/index.py".maxDuration = 300`.
- **No verificado:** las variaciones de cuota por región o bajo picos de concurrencia; y si el proyecto concreto tiene Fluid compute activado (la página fija esos límites para Fluid compute; el estado de esta cuenta se ve en el panel de Vercel).
