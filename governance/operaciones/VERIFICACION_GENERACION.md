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
   - En [`api/routers/roadmaps.py`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/api/routers/roadmaps.py#L40-L51), el endpoint `POST /api/v1/roadmaps/generate` recibe el payload de diagnóstico (`GenerateRoadmapRequest`), valida el rol autorizado (`implementador`), inyecta el contexto de tenant (`ctx["tenant_id"]`) y despacha la invocación hacia el servicio de dominio.
2. **Motor de Generación en Línea:**
   - En [`features/roadmap/services/generacion_en_linea.py`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/features/roadmap/services/generacion_en_linea.py#L33-L96), la función `generate_roadmap_inline` orquesta el flujo:
     - Crea el registro inicial en estado `draft` en la base de datos PostgreSQL ([L50-L63](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/features/roadmap/services/generacion_en_linea.py#L50-L63)).
     - Ejecuta la inferencia del modelo LLM mediante `asyncio.to_thread(generate_roadmap_document, ...)` ([L84-L92](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/features/roadmap/services/generacion_en_linea.py#L84-L92)) para evitar el bloqueo del bucle de eventos asyncio en Windows y Linux.
     - Valida el esquema estructurado `RoadmapDocument` (Pydantic), calcula los KPIs globales y persiste las olas y tareas en Neon PostgreSQL ([L133-L245](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/features/roadmap/services/generacion_en_linea.py#L133-L245)).
     - Retorna `{job_id, status: "generated", roadmap_id}` o `{job_id, status: "failed", roadmap_id}` si ocurre un fallo no recuperable.
3. **Configuración de Límite Serverless en Vercel:**
   - En [`vercel.json`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/vercel.json#L1-L7), se fija explícitamente:
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
   - Consultar [`governance/operaciones/PROCEDIMIENTO_VERCEL.md`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/governance/operaciones/PROCEDIMIENTO_VERCEL.md) y [`governance/operaciones/VARIABLES_VERCEL.md`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/governance/operaciones/VARIABLES_VERCEL.md).
   - Verificar que `DEEPSEEK_API_KEY`, `DEEPSEEK_MODEL` (`deepseek-chat`) y `DATABASE_URL` estén provisionadas en Production (`vercel env ls`).
2. **Árbitro Exógeno de Salud:**
   - Antes de lanzar la generación, comprobar la estabilidad del despliegue ejecutando [`scripts/verificar_despliegue.py`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/scripts/verificar_despliegue.py):
     ```bash
     python scripts/verificar_despliegue.py <dominio_produccion>
     ```
   - El script debe retornar **código 0** confirmando `status == "OPERATIONAL"` y todas las rutas activas en `/openapi.json`.

### B. Identidad y Tenant de Prueba
- **Tenant Aislado:** Emplear exclusivamente un tenant de pruebas designado, por ejemplo `tenant-benchmark-ops02` o el tenant de demostración corporativa preexistente (`demo-corp-lopdp`).
- **Identidad Autenticada:** Generar un token JWT firmado con `JWT_SECRET` conteniendo:
  - `sub`: `benchmark-runner-ops02`
  - `tenant_id`: `<TENANT_ID_PRUEBA>`
  - `role`: `implementador` (rol requerido por la compuerta de `POST /generate`).
- **Regla Anti-Exposición:** El token y los endpoints se referencian por variables de entorno de shell local (`$TOKEN`, `$PROD_URL`), nunca impresos en texto plano en bitácoras compartidas.

### C. Ejecución de la Medición (Cronometrada)
Realizar la petición midiendo el tiempo transcurrido desde el despacho del payload hasta la respuesta HTTP 200:
```bash
curl -X POST "$PROD_URL/api/v1/roadmaps/generate" \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d @fixtures/payload_assessment_benchmark.json \
     -w "\nTiempo Total: %{time_total}s | Codigo HTTP: %{http_code}\n"
```

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

| Fecha (AAAA-MM-DD HH:MM) | Duración (s) | Intentos del Modelo (Retries) | Resultado (generated / failed) | Notas Técnicas y Contexto |
| :--- | :--- | :--- | :--- | :--- |
| *Ej. 2026-10-18 10:30* | *48.5 s* | *1 intento (0 retries)* | *generated* | *Payload estándar: 12 dimensiones, 38 preguntas LOPDP.* |
| | | | | |
| | | | | |

---

## 4. Criterio de Decisión y Umbral para Apertura de Evaluación de Colas (PROPUESTA)

> **ESTADO DE LA SECCIÓN:** **PROPUESTA** (Sujeta a validación empírica y ratificación del Tech Lead).

La decisión D-1 asume que una función serverless en Vercel puede completar la inferencia y persistencia en una ventana confortable. No obstante, variaciones en la latencia de red, tiempo de respuesta de la API del LLM o reintentos correctivos por errores de validación sintáctica pueden aproximar la solicitud al límite de tiempo.

### Criterio de Umbral Propuesto (Alerta al 70%)
- **Umbral Crítico de Advertencia:** **210 segundos (70% del límite de 300 s)**.
- **Justificación Técnica:**
  - El motor `generate_roadmap_document` ([`features/roadmap/services/generacion_engine.py`](file:///c:/Users/Juan%20Carlos/Desktop/Plataforma%20LOPDP%20360/features/roadmap/services/generacion_engine.py#L52)) incluye hasta `max_retries = 2` en caso de salida truncada o fallo en el schema Pydantic.
  - Cada reintento completo del LLM puede tomar entre 30 y 60 segundos adicionales.
  - Si una generación base sobrepasa los **210 segundos**, un único reintento correctivo provocaría un timeout 504 (*GATEWAY_TIMEOUT*) ineludible por parte de la infraestructura de Vercel.

### Plan de Acción si se Cruza el Umbral
Si cualquier medición real supera los **210 segundos** o si se registran fallos por timeout en producción:
1. Abrir formalmente la tarea de evaluación de arquitectura de **Colas Asíncronas** (apoyada en el cliente Redis `app_core/queue/redis_client.py` y worker externo o tarea serverless delegada).
2. Modificar el endpoint `POST /generate` para retornar de inmediato `202 Accepted` con `job_id`, delegando el procesamiento de fondo a un worker desacoplado.

---

## 5. Verificación de Límites Oficiales de Vercel (Estado del Proveedor)

- **Fuente Oficial Consultada:** Documentación de Plataforma Vercel ([vercel.com/docs/functions/limitations](https://vercel.com/docs/functions/limitations)).
- **Fecha de Verificación:** **16 de octubre de 2026**.
- **Límites Confirmados para el Plan Hobby (Gratuito):**
  - **Duración Máxima de Función (`maxDuration`):** **300 segundos** (5 minutos) máximo configurable.
  - **Configuración:** Soportada mediante la directiva `functions.api/index.py.maxDuration` en `vercel.json` (aplicada en el proyecto).
  - **Memoria Máxima:** 1024 MB (por defecto en Fluid compute).
  - **Payload de Solicitud:** 4.5 MB máximo para el cuerpo de la petición HTTP.
- **Aspectos No Verificados:**
  - Variaciones temporales de cuota por región de despliegue o degradación de cuotas bajo picos de concurrencia global en la infraestructura compartida de Vercel quedan clasificadas como **no verificado**.
