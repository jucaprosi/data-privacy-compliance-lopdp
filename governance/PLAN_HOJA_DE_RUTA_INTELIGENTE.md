# Plan de Ejecución — Módulo Hoja de Ruta Inteligente
`¤roadmap` `¤rbac-tenant` `¤adpa`

> **Documentos que lo sostienen:** especificación en `governance/artefactos/PRD.md` (Módulo 5), leyes en `governance/artefactos/INVARIANTS.md` y tareas en `governance/artefactos/TASKS.md` (Fase 7). Este plan no repite su contenido: ordena la ejecución.
> **Fecha de corte:** 2026-10-10, sobre `main`.

---

## 1. Qué cambió desde el informe ejecutivo

El informe describe el estado a mediados de la fase 2. Varias partes ya se superaron; otras no estaban en el informe.

| Punto del informe | Estado real en `main` |
| :--- | :--- |
| Fase 2.2.5 y 2.2.6 «pendientes de commit» | Hechas (`5c32258`). |
| Fase 2.4 «Codex ejecutando» (RBAC completo) | Hecha (`0ab37e7`): usuarios, áreas, roles, `/me/roles`, SoD del DPO, cuatro ojos, alcance por área. |
| RLS «activo» en 7 tablas | **Era inerte**: la app se conectaba con el rol dueño, que tiene `BYPASSRLS`. Corregido con el rol `lopdp_app` y `FORCE ROW LEVEL SECURITY`; aplicado en TEST y producción. |
| Pilar 3 del arnés «falla por falso positivo en `.venv`» | Resuelto (`de204e3`). |
| 38 tests, 85 % de cobertura | 265 tests en verde. |
| Fase 2.3: `database.py` con SQL interpolado | **Sigue abierta** (`app_core/database.py:38`). Es la tarea RM-02. |
| Fase 3: frontend | **No existe ninguna pantalla de la hoja de ruta.** Es la mayor parte del trabajo restante. |

## 2. Hallazgos nuevos que el plan incorpora

1. **Autenticación inexistente (riesgo alto).** La identidad llega en las cabeceras `X-User-ID`, `X-Tenant-ID` y `X-Role`, que envía el propio cliente; el servidor solo comprueba que esa combinación exista en la base. Quien conozca un identificador válido puede suplantarlo. → SEC-03, bloqueante para producción con clientes reales.
2. **Brechas entre la matriz del informe y los endpoints.** No existen: editar tareas (solo se cambia el estado), distribuir tareas, consultar el audit log y alta de responsables por el implementador. → RM-07, RM-08, RM-09 y RM-10.
3. **El módulo está fuera de las salas ADPA.** Vive en `app_core/` (servicios, esquemas, worker, IA) y no en `features/<sala>/` con su compuerta `_service.py`. → RM-01 y RM-05.
4. **La generación con IA no es fiable hoy (medido).** El prompt no incluye el esquema que exige el validador: 3 de 3 respuestas de prueba fueron inválidas, y con el esquema la salida se corta en el tope de 4096 tokens. Es independiente del hosting. → RM-12 y Anexo A.
5. **Hueco de despliegue.** La generación con IA encola en Redis y la consume un worker de larga duración, que las funciones serverless de Vercel no pueden alojar; además, en Vercel solo están cargadas `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS` y las de IA, sin las de R2 ni Redis. → OPS-01 y OPS-02.

## 3. Ejecución por olas

Cada tarea tiene archivos de propiedad exclusiva, contrato congelado y árbitro propio (ver `TASKS.md`, Fase 7), por lo que las tareas de una misma ola se pueden asignar a agentes distintos sin coordinarse.

| Ola | Tareas | Agentes en paralelo | Depende de | Orden de magnitud |
| :--- | :--- | :--- | :--- | :--- |
| **0** Contrato | RM-00 | 1 | — | ~1 h |
| **1** Fundamentos | RM-01, RM-02, RM-03, FE-01 | 4 | RM-00 (RM-01 y FE-01) | RM-01 2–3 h · RM-02 2–3 h · RM-03 ~2 h · FE-01 ~2 h |
| **2** Salas y vistas | RM-05, FE-02, FE-03, FE-04, FE-05 | 5 | RM-01 (RM-05) · FE-01 (las FE) | RM-05 3–4 h · cada FE 2–3 h |
| **3** Brechas del backend | RM-07, RM-08, RM-09, RM-12 y RM-10 (esta solo depende de RM-01) | 5 | RM-05 (RM-10: RM-01) | ~2 h cada una; RM-10 ~4 h; RM-12 ~3 h |
| **4** Integración | RM-11, FE-06, QA-01, SEC-03, SEC-02 | 2–3 | olas 2 y 3 | RM-11 ~1 h · FE-06 ~2 h · QA-01 ~3 h · SEC-03 por decidir · SEC-02 ~2 h |
| **5** Despliegue | OPS-01 a OPS-04 | 1 + usuario | ola 4 | ~1–2 h |
| Independientes | GOB-01, SEC-01, ZERAG-01, FIRMA-01, TEST-01 | según decisión | — | ZERAG 3–5 h · firma 8–12 h (estimaciones del informe) |

**Camino crítico:** RM-00 → RM-01 → RM-05 → RM-07/08/09 → RM-11 → FE-06 → QA-01 → OPS. En tiempo de reloj ronda las 17 h con agentes en paralelo, frente a unas 40 h en serie. Son órdenes de magnitud, no compromisos.

**Recomendación de prioridad (la del informe, adoptada):** cerrar la deuda de SQL interpolado (RM-02) antes de multiplicar endpoints con el frontend. Como RM-02 no depende de nada ni toca archivos de otras tareas, corre en la ola 1 sin retrasar a las demás.

## 4. Protocolo para trabajar con varios agentes

1. **Un agente, una tarea, una rama, un PR.** Cada agente trabaja en su propio árbol de trabajo (`git worktree add <ruta corta> <rama>`): varias sesiones sobre una misma carpeta cambian de rama bajo los pies de las demás (Aporte 90). En Windows, la ruta del árbol debe ser corta por el nombre largo del PDF de la SPSP en la raíz (`core.longpaths`).
2. **No tocar archivos ajenos.** Si una tarea necesita un cambio fuera de su lista, lo declara y espera a la tarea de integración de su ola.
3. **Contrato primero.** Los agentes del frontend trabajan contra `hoja_de_ruta.openapi.json` y un *mock*, nunca contra el backend en curso.
4. **Árbitro exógeno.** El agente no certifica su propio trabajo: lo certifica su árbitro (prueba, AST o arnés) y el check `Arnés Físico Determinista` del PR.
5. **Fusión.** Solo cuando el check esté en verde, en el orden de las olas. `main` ya exige ese check.
6. **Roles de gobernanza:** backend `¤¤developer-architect`; pruebas y matriz `¤¤qa-engineer`; frontend `¤¤frontend-architect`; seguridad `¤¤security-engineer`; el cierre de cada tarea con `mcp_close_session`.

## 5. Reconstrucción de Vercel (Ola 5)

**Estado verificado el 2026-10-10:**
- Production y Preview ya usan `DATABASE_URL` con el rol `lopdp_app` (Production creada hace 8 h; Preview hace 6 h).
- Las 10 vistas previas más recientes (5 h o menos) se construyeron **después** del cambio, así que ya incluyen el valor nuevo. Las anteriores corresponden a ramas ya fusionadas y borradas; no requieren reconstrucción.
- El último despliegue de Production sirve `GET /api/v1/health` ⟹ 200, `OPERATIONAL`, 16/16 routers.
- **Diferencia entre entornos:** Preview no tiene `CORS_ORIGINS` ni `DEEPSEEK_MODEL`, que Production sí tiene; sin `CORS_ORIGINS` la aplicación cae en el valor por defecto `*`. OPS-01 las alinea.

**Procedimiento tras cada cambio de variables o fusión relevante (OPS-01 a OPS-04):**
1. **Variables.** Cargar en Vercel, para Production y Preview, las de R2 y Redis y las del proveedor de IA que falten (las pone el usuario; nunca se escriben en el repositorio). Usar `vercel env add <NOMBRE> <entorno> --sensitive`, leyendo el valor desde el `.env` sin mostrarlo y sin BOM (en PowerShell 5.1: `$OutputEncoding = New-Object System.Text.UTF8Encoding $false`).
2. **Producción.** Fusionar a `main` (la CI debe estar en verde); Vercel despliega solo. Si solo cambiaron variables, `vercel redeploy <url del último despliegue de main> --target production`.
3. **Vistas previas.** Las que sean anteriores al último cambio de variables se reconstruyen con `vercel redeploy <url de la vista previa>`; las nuevas ya nacen con el valor vigente.
4. **Verificación (OPS-03).** `python scripts/verificar_despliegue.py <dominio>` debe devolver 0: `/api/v1/health` 200 con `OPERATIONAL`, todos los routers cargados y las rutas esperadas en `/openapi.json`.
5. **Reversión.** Si falla, *Promote to Production* del despliegue anterior. No usar *Redeploy* sobre filas «Redeploy of …»: repiten código antiguo y sustituyen al despliegue correcto.
6. **Worker de generación (OPS-02).** Hasta resolver la decisión D-1, la generación con IA no funciona en Vercel: el trabajo se encola y nadie lo consume.

## 6. Decisiones

| ID | Decisión | Estado | Efecto |
| :--- | :--- | :--- | :--- |
| **D-1** | Dónde corre la generación con IA | **Abierta** (contexto en el Anexo A) | OPS-02 |
| **D-2** | Variables de R2, Redis e IA en Vercel | **Aceptada:** las carga el usuario; el repositorio no guarda valores | OPS-01 |
| **D-3** | Flujo de alta de responsables | **Resuelta** con la especificación del usuario, incorporada al PRD §5.3.1; quedan dos puntos por confirmar (tabla de eventos propia y `tenants.tamano` nulo ⟹ organización grande) | RM-10 desbloqueada |
| **D-4** | Proveedor de firma electrónica | **Resuelta: ANF** | FIRMA-01 |
| **D-5** | Alcance de la integración ZERAG ↔ agente de código | **Abierta** (información en el Anexo B) | ZERAG-01 |
| **D-6** | Mecanismo de autenticación | **Resuelta: SSO (OIDC)**; falta elegir el proveedor de identidad | SEC-03 |

## 7. Riesgos

| # | Riesgo | Impacto | Mitigación |
| :--- | :--- | :--- | :--- |
| R1 | Identidad suplantable por cabeceras | **Alto** | SEC-03 antes de abrir a clientes reales. |
| R2 | SQL interpolado en `app_core/database.py` | Alto | RM-02 en la ola 1 con árbitro AST. |
| R3 | Generación con IA inoperante en Vercel (sin worker ni variables) | Medio | D-1 y OPS-01/02 antes de anunciar la función. |
| R4 | Mover código entre salas rompe imports | Medio | RM-01 y RM-05 sin cambio de comportamiento, con la suite completa y `test_adpa_bulkhead.py` como árbitros; sin *shims*. |
| R5 | Colisiones entre agentes en archivos compartidos | Medio | Propiedad exclusiva por tarea; integración solo en RM-11 y FE-06; un árbol de trabajo por agente. |
| R6 | La matriz de permisos y el código divergen | Medio | RM-03 la convierte en prueba; el `xfail` estricto obliga a retirarlo al implementar. |
| R7 | Clave de acceso del MCP expuesta en un chat anterior | Medio | SEC-01, antes del primer cliente. |
| R8 | La generación con IA devuelve JSON inválido o cortado | Alto | RM-12: esquema en el prompt, tope de tokens suficiente o generación por olas, reintento con el error de validación. |

## 8. Definición de terminado de la Fase 7

Los cuatro criterios nuevos del PRD (§9, puntos 10 a 13) se cumplen y sus árbitros están en verde: `tests/test_matriz_permisos.py` sin filas pendientes, `tests/test_rls_app_role.py`, el flujo de punta a punta de QA-01 y `scripts/verificar_despliegue.py` con código 0 contra producción.


---

## Anexo A. Evidencia para decidir D-1 (dónde corre la generación)

### A.1 Qué hace hoy la generación
Una llamada al modelo (dos si la primera no valida), `max_tokens = 4096`, cliente síncrono sin tiempo límite propio; después, la persistencia de olas y tareas en la base. Los textos de entrada son diminutos (menos de 1 000 caracteres de prompt); lo que pesa es la **salida**.

### A.2 Medición real (2026-10-10, entrada sintética de 20 controles, modelo `deepseek-flash`)

| Prueba | Tokens de salida | Tiempo | Resultado |
| :--- | :--- | :--- | :--- |
| Sin esquema, intento 1 | 3 310 | 12,6 s | **Inválido** (JSON envuelto en otra clave; faltan campos obligatorios) |
| Sin esquema, intento 2 | 3 460 | 12,9 s | **Inválido** (2 errores de validación) |
| Sin esquema, intento 3 | 3 152 | 12,4 s | **Inválido** (3 errores de validación) |
| Con esquema, tope 4096 | 4 096 | 14,6 s | **Cortado** (`finish_reason = length`) |
| Con esquema, tope 8000 | 5 281 | 18,5 s | **Válido:** 2 olas, 20 tareas |

Velocidad sostenida: unos 255 a 285 tokens por segundo. Cada tarea ocupa unos 264 tokens de salida; **extrapolando** (estimación, no medición) a las 73 tareas posibles, una sola llamada rondaría los 19 000 tokens y unos 70 s, si el modelo admitiera esa salida; generando por olas serían varias llamadas de 15 a 25 s.

**Conclusión de la medición:** la duración de una llamada es de segundos, no de minutos, y el defecto serio no es el tiempo sino la fiabilidad del resultado (RM-12).

### A.3 Límites vigentes de Vercel (documentación oficial, actualizada el 2026-08-24)
Con *Fluid compute* (activo por defecto):

| Plan | Duración por defecto | Máxima | Máxima ampliada |
| :--- | :--- | :--- | :--- |
| Hobby | 300 s | 300 s | — |
| Pro | 300 s | 800 s | 1 800 s (beta; Python 3.12 a 3.14) |

* Para una aplicación FastAPI la duración se fija en `vercel.json` (`functions`), con la clave del archivo de entrada (aquí `api/index.py`). Hoy no existe `vercel.json`.
* Cron Jobs: en Hobby solo una vez al día; en Pro, por minuto. No sirven para consumir una cola con baja latencia.
* **Vercel Queues** (beta, todos los planes): entrega por llamada a una función consumidora (con la misma duración máxima) o consumo propio en modo *poll*; hay SDK de Python.
* **QStash de Upstash** (ya usas Upstash para Redis): plan gratuito de 1 000 mensajes al día y respuesta de hasta 15 minutos; cada reintento cuenta como mensaje.
* No conozco el plan de Vercel de tu equipo; con cualquiera de los dos, 300 s multiplican por más de 4 el peor caso medido (dos intentos de unos 70 s).

### A.4 Opciones

| | (a) Servicio propio de larga duración | (b) Cola con entrega HTTP a una función | (c) En línea, sin cola |
| :--- | :--- | :--- | :--- |
| **Cambio de código** | Ninguno: el worker actual funciona tal cual | El worker pasa a ser un manejador HTTP idempotente que verifica la firma de la cola | Mínimo: la solicitud ejecuta la generación y responde |
| **Infraestructura nueva** | Un servicio 24 h (pago, o gratuito con suspensión por inactividad) y sus secretos | Cola gestionada (QStash o Vercel Queues) | Ninguna; Redis deja de ser necesario para los trabajos |
| **Espera del usuario** | Sondeo del estado (contrato actual) | Sondeo del estado (contrato actual) | Conexión abierta de 20 a 90 s; hace falta indicador de progreso |
| **Fallo a mitad** | Reintento del worker | Reintentos automáticos de la cola | Se pierde el trabajo; hay que marcar el roadmap como fallido y pedir reintento |
| **Riesgo principal** | Operar y pagar otro servicio para tareas de segundos | Complejidad, dependencia de un producto en beta (Queues) o del límite diario gratuito (QStash) | Una instancia ocupada durante la espera; exige llamada no bloqueante al modelo |
| **Encaje con la medición** | Sobredimensionado | Correcto, pero prematuro | Suficiente mientras la generación dure menos de 300 s |

### A.5 Recomendación
**(c) para el MVP, con (b) como evolución.** Con llamadas de 15 a 25 s y un límite de 300 s, el servicio propio no se justifica. Condiciones para (c): RM-12 resuelta primero (no sirve esperar 20 s para recibir un JSON inválido); `maxDuration` fijado en `vercel.json`; llamada al modelo en un hilo aparte (`asyncio.to_thread`) o con el cliente asíncrono, porque hoy bloquea el bucle de eventos; el estado del roadmap se marca `failed` si algo falla. Pasar a (b) cuando haya volumen, reintentos automáticos o generaciones por olas que se acerquen a los 300 s.

**Dato que necesito de ti:** el plan de Vercel (Hobby o Pro) y si prefieres conservar el contrato actual de «202 y sondeo» o aceptar una respuesta directa.

---

## Anexo B. Información para decidir D-5 (integración ZERAG ↔ agente de código)

### B.1 Cómo está hoy (verificado en tu equipo)
* El agente de código (Codex) registra el servidor `zero_regression_bios` mediante `npx mcp-remote https://mcp.jubyz.com/sse`: un **puente local** que habla `stdio` con Codex y abre una conexión de red hacia el servidor **alojado** (transporte SSE).
* El repositorio de ZERAG ya incluye **dos formas de ejecución:** `python -m mcp_server.server` (proceso local por `stdio`, con su `mcp_config.json`) y `mcp_server/sse_server.py` (la versión alojada). También hay instaladores por cliente, entre ellos uno para Codex.
* El servidor tiene **medición de créditos** (`credit_metering.py`): el uso alojado se contabiliza y se cobra.

### B.2 El problema que describe el informe (no verificado por mí)
El entorno aislado de Codex no tiene resolución de nombres de red, de modo que el puente `mcp-remote` no podría llegar a `mcp.jubyz.com`. Además, el servidor alojado «no ve tu disco», por lo que sus verificaciones no pueden operar directamente sobre el repositorio.

### B.3 Qué significaría «integrar por stdio»
Que Codex arranque el servidor de ZERAG como proceso local (la entrada `python -m mcp_server.server`) en lugar del puente a la red. Ganancias: funciona sin red y el servidor **puede leer el espacio de trabajo**. Costes y dudas:
1. **Modelo de negocio:** una copia local del servidor lleva el código al equipo del cliente y podría saltarse la medición de créditos. Hay que decidir si el modo local mide, no mide, o solo expone las herramientas que no consumen créditos.
2. **Intérprete:** la configuración local apunta a Python 3.14 en una ruta concreta; el informe ya señala que el arnés usa ese mismo intérprete.
3. **Actualizaciones:** una instalación local se desactualiza; la alojada no.
4. **Alcance:** si es una tarea de este repositorio o de ZERAG (el código vive en `Desktop\ZERAG`, otro proyecto).

### B.4 Opciones
* **A. Solo stdio local** en Codex: lo más simple y sin red; implica decidir la medición y la distribución del servidor.
* **B. Mantener el servidor alojado** y permitir red al entorno aislado de Codex: no toca ZERAG, pero depende de una configuración de seguridad de Codex.
* **C. Híbrido:** `stdio` local para las verificaciones que necesitan ver el disco y el servidor alojado para las medidas y el triaje.

**Datos que necesito de ti:** quién es el responsable de esta integración, si el modo local debe medir créditos y si hoy el bloqueo de red de Codex te impide algo concreto.
