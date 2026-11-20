# Plan de Ejecución — Módulo Hoja de Ruta Inteligente
`¤roadmap` `¤rbac-tenant` `¤adpa`

> **Documentos que lo sostienen:** qué se exige, en `governance/artefactos/PRD.md` (Módulo 5); cómo está construido, en `governance/arquitectura/HOJA_DE_RUTA_ADPA.md`; quién hace qué, en `governance/tareas/`; el despliegue en Google Cloud, en `governance/operaciones/BRIEF_PROPIETARIO_DESPLIEGUE_GCP.md`. Este plan solo ordena la ejecución y recoge las decisiones.
> **Fecha de corte:** 2026-10-10, sobre `main`.

---

## 1. Qué cambió desde el informe ejecutivo

| Punto del informe | Estado real en `main` |
| :--- | :--- |
| Fases 2.2.5, 2.2.6 y 2.4 (RBAC completo) | Hechas: usuarios, áreas, roles, `/me/roles`, SoD del DPO, cuatro ojos y alcance por área. |
| RLS «activo» en 7 tablas | **Era inerte** (la aplicación usaba el rol dueño, con `BYPASSRLS`). Corregido con el rol `lopdp_app` y `FORCE ROW LEVEL SECURITY`; aplicado en TEST y producción. |
| Pilar 3 del arnés con falso positivo en `.venv` | Resuelto. |
| 38 tests, 85 % de cobertura | 265 tests en verde. |
| Fase 2.3: SQL interpolado en `database.py` | **Sigue abierta** (RM-02). |
| Fase 3: frontend | **No existe ninguna pantalla de la hoja de ruta.** Es la mayor parte del trabajo restante. |

## 2. Hallazgos que el informe no recogía

1. **Autenticación inexistente (riesgo alto).** La identidad llega en cabeceras que envía el propio cliente; quien conozca un identificador válido puede suplantarlo. → SEC-03, bloqueante para producción con clientes.
2. **Cuatro funciones de la matriz sin endpoint:** editar tareas, distribuirlas, consultar el audit log y dar de alta responsables. → RM-07, RM-08, RM-09 y RM-10.
3. **El módulo vive en `app_core/` y no en salas `features/` con compuerta.** → RM-01.
4. **La generación con IA no es fiable hoy (medido).** El prompt no incluye el esquema que exige el validador: 3 de 3 respuestas de prueba fueron inválidas, y con el esquema la salida se corta en el tope de 4096 tokens. → RM-12 (Anexo A).
5. **`tenants.tamano` está vacío en todos los tenants y ningún endpoint lo escribe**, y coexisten tres vocabularios de tamaño. → RM-15 y RM-16.
6. **Configuración de despliegue.** Variables de Cloud Storage (`GCP_STORAGE_BUCKET`), Memorystore/caché, `CORS_ORIGINS` y Vertex AI (`GOOGLE_CLOUD_PROJECT`, `VERTEX_LOCATION`) configuradas por servicio en Cloud Run y Secret Manager. → OPS-01, OPS-02 y RM-13.

## 3. Revisión del Tech Lead: qué se rehízo y por qué

La primera versión de estos documentos afirmaba que las tareas eran «totalmente independientes» sin poder comprobarlo. Al revisarla se vio que **no lo eran** y que además dañaba la salud de la documentación:

| Problema detectado | Corrección |
| :--- | :--- |
| `ROUTERS_MAP`, las compuertas y dos archivos de pruebas los tocaban varias tareas a la vez. | Autoregistro de routers (RM-00), **secciones reservadas** en las compuertas (RM-01), `xfail` dinámico en la matriz (RM-03) y pruebas propias en cada tarea. |
| Cinco tareas crearían una migración en paralelo: dos cabezas de Alembic al fusionar. | Prueba de una cabeza por sala (CI-28). La CI de cada PR prueba su fusión con `main` y la de `main` corre tras cada fusión; el procedimiento está en `governance/operaciones/FUSION_ALEMBIC.md`. Exigir ramas al día queda como plan de reserva (CI-01). |
| Todos los agentes de desarrollo probarían contra la misma base compartida, pisándose al migrar y limpiar. | Una base local de pruebas por agente de desarrollo (contenedor PostgreSQL 16 del arnés). |
| Hacían falta dos tareas en cadena para mover el mismo código (RBAC y roadmap). | Una sola tarea de reestructuración (RM-01): menos olas y sin edición cruzada de imports. |
| El PRD llevaba rutas de archivos y columnas «pendiente/implementado» que caducan; `TASKS.md` (que el servidor también modifica) llevaba 30 tareas. | PRD solo de producto; arquitectura aparte; **una especificación por tarea** con cabecera legible por máquina y estado propio. |
| La independencia solo estaba afirmada. | `scripts/generar_indice_tareas.py` y `tests/test_indice_tareas.py` la **comprueban**: dos tareas que pueden ejecutarse a la vez no pueden poseer el mismo archivo. Probado con conflictos forzados. |
| Notificaciones, firma electrónica e integración ZERAG mezcladas con el núcleo. | Las dos primeras quedan como bocetos en el *backlog*; ZERAG sale del proyecto. |

## 4. Ejecución por olas

Las tareas de una misma ola se asignan a agentes de desarrollo distintos sin coordinarse. El detalle de cada una (entrega, propiedad de archivos, árbitro) está en su especificación.

| Ola | Tareas | Depende de |
| :--- | :--- | :--- |
| **A** Fundamentos | RM-00, RM-01, RM-02, RM-03, RM-14 y, tras RM-00, FE-01 | — |
| **B** Funciones y vistas | RM-07, RM-08, RM-09, RM-12, RM-15, RM-16, SEC-03, FE-02, FE-03, FE-04, FE-05 | RM-01 (las de backend), FE-01 (las de frontend) |
| **C** Flujos que encadenan | RM-10 (tras RM-14 y RM-16), RM-13 (tras RM-12) | ola B |
| **D** Integración | FE-06, QA-01, SEC-02 | olas B y C |
| **E** Despliegue | OPS-01, OPS-02 | RM-13 |
| Independientes | OPS-03, OPS-04, GOB-01, GOB-02 (hecha) | — |
| *Backlog* | CI-01, NOTIF-01, FIRMA-01, TEST-01 | según la tarea |

**Camino crítico:** RM-01 → RM-12 → RM-13 → QA-01 → OPS-02 (o RM-01 → RM-16 → RM-10 → QA-01). Tras RM-01 se abre la mayor paralelización: hasta once tareas a la vez. No se dan horas: ninguna estimación se ha medido.

**Prioridad:** RM-02 (SQL interpolado) va en la ola A y no depende de nada ni toca archivos de otras tareas, así que no retrasa a las demás.

## 5. Protocolo para varios agentes de desarrollo

> **Agente de desarrollo:** sesión de Claude, Codex u otra herramienta que implementa una tarea del plan. **No** es el asistente de IA (Copiloto) de la plataforma, que no usa estas ramas ni este protocolo.

1. **Un agente de desarrollo, una tarea, una rama, un PR**, en su propio árbol de trabajo (`git worktree add <ruta corta>`; en Windows, ruta corta por el nombre largo de un PDF en la raíz).
2. **Una base local de pruebas por agente de desarrollo** (PostgreSQL 16 del arnés), nunca una base compartida.
3. **Propiedad exclusiva.** Si una tarea necesita un cambio fuera de su lista, lo declara y espera; no lo hace.
4. **Contrato primero.** Los agentes de desarrollo del frontend trabajan contra `governance/contratos/hoja_de_ruta.openapi.json` y un *mock*.
5. **Árbitro exógeno.** Cada tarea lo declara; además, el check `Arnés Físico Determinista`. El agente de desarrollo no certifica su propio trabajo.
6. **Fusión** solo con el check en verde. No se exige la rama al día: ADPA evita los choques entre ramas y la CI prueba la fusión con `main`. Si hiciera falta, CI-01 lo activa.
7. **Roles de gobernanza:** backend `¤¤developer-architect`; pruebas `¤¤qa-engineer`; frontend `¤¤frontend-architect`; seguridad `¤¤security-engineer`.

## 6. Despliegue en Cloud Run

El procedimiento completo está en `governance/operaciones/BRIEF_PROPIETARIO_DESPLIEGUE_GCP.md`. Resumen:

* **Estado verificado hoy:** Production y Preview usan `lopdp_app`; las 10 vistas previas más recientes se construyeron **después** del cambio de variable y no necesitan reconstrucción; Production responde 200, `OPERATIONAL`, 16 de 16 routers.
* **Cuándo desplegar:** cada cambio de código o configuración actualiza una nueva revisión de Cloud Run mediante `deploy-gcp.yml`.
* **Verificar:** `scripts/verificar_despliegue.py` (OPS-03) debe devolver 0.
* **Si falla:** *Promote to Production* del despliegue anterior; nunca *Redeploy* sobre filas «Redeploy of …».
* **Variables del servicio:** configurar `GCP_STORAGE_BUCKET`, `REDIS_URL`, `CORS_ORIGINS` y los parámetros de Vertex AI en Cloud Run (`OPS-01`, `RM-13`).

## 7. Decisiones

| ID | Decisión | Resultado |
| :--- | :--- | :--- |
| D-1 | Dónde corre la generación | **En línea** (plan gratuito, 300 s; medición de 13 a 19 s). Resuelta por defecto; revertible. Anexo A. |
| D-2 | Variables y secretos en Cloud Run / Secret Manager | **Aceptada:** las carga el propietario vía consola / `gcloud`. |
| D-3 | Flujo de alta de responsables | **Resuelta** (PRD §5.3.1). Eventos en `audit_events`; tamaño nulo ⟹ bloqueo con error guiado y sin valor por defecto. |
| D-4 | Firma electrónica | **ANF**. Boceto en el *backlog*. |
| D-5 | Integración ZERAG ↔ agente de código | **Fuera de este proyecto** (pertenece a ZERAG). |
| D-6 | Autenticación | **SSO con Google (OIDC)**; la cuenta solo prueba la identidad. |
| D-7 | Notificaciones | **Aviso en aplicación; envío externo de correo desactivado hasta configurar dominio/proveedor** (Anexo B). |
| D-8 | Base de pruebas por agente de desarrollo | **Resuelta:** una base local de pruebas por agente de desarrollo (OPS-04; hoy, el contenedor PostgreSQL 16 del arnés). |

## 8. Acciones que solo puede hacer el usuario

1. Crear el cliente OAuth en Google Cloud (SEC-03).
2. Verificar variables y secretos en Cloud Run y Secret Manager (OPS-01).
3. Delegar correo en el proveedor corporativo elegido cuando se habilite (NOTIF-01).
4. Preparar la base local de pruebas de cada agente de desarrollo (OPS-04); su cadena de conexión es un secreto.
5. Rotar la clave de acceso del MCP de gobernanza, expuesta en un chat anterior, antes del primer cliente.
6. Solo si hiciera falta: exigir ramas al día en `main` (CI-01).

## 9. Riesgos

| # | Riesgo | Impacto | Mitigación |
| :--- | :--- | :--- | :--- |
| R1 | Identidad suplantable por cabeceras | **Alto** | SEC-03 antes de abrir a clientes. |
| R2 | SQL interpolado en `app_core/database.py` | Alto | RM-02, con árbitro AST. |
| R3 | La generación devuelve JSON inválido o cortado | Alto | RM-12. |
| R4 | Mover código entre salas rompe imports | Medio | RM-01 sin cambio de comportamiento, con la suite y `test_adpa_bulkhead.py` como árbitros; sin *shims*. |
| R5 | Colisiones entre agentes de desarrollo | Medio | Propiedad exclusiva **verificada** por prueba; secciones reservadas; árbol de trabajo y base local por agente de desarrollo. |
| R6 | La matriz de permisos y el código divergen | Medio | RM-03 la convierte en prueba. |
| R7 | Clave del MCP expuesta | Medio | Acción 6 del usuario. |
| R8 | Dos cabezas de Alembic al integrar migraciones casi a la vez | Bajo | Prueba de una cabeza por sala (CI-28); la CI prueba la fusión con `main`; una migración de fusión dentro de la sala si ocurre. Plan de reserva: CI-01. |
| R9 | El SSO no funciona en las vistas previas | Medio | Probarlo en local y en producción. |
| R10 | `task_audit_log` borra registros en cascada con la tarea | Bajo (latente) | Los eventos nuevos van a `audit_events`; evaluar `RESTRICT`. |
| R11 | Tres vocabularios de tamaño y dos fuentes (ficha del navegador y base) | Medio | RM-15. |
| R12 | Cuotas y límites de servicio en Google Cloud | Bajo | Agrupación por lote en notificaciones y cuotas configuradas en Vertex AI y Cloud SQL. |

## 10. Definición de terminado de la Fase 7

Los criterios de aceptación 10 a 13 del PRD se cumplen y sus árbitros están en verde: `tests/test_matriz_permisos.py` sin filas pendientes, `tests/test_rls_app_role.py`, el flujo de punta a punta de QA-01 y `scripts/verificar_despliegue.py` con código 0 contra producción.

---

## Anexo A. Evidencia para D-1 (medida el 2026-10-10)

Entrada sintética de 20 controles en pruebas de generación estructurada; una sola llamada por prueba.

| Prueba | Tokens de salida | Tiempo | Resultado |
| :--- | :--- | :--- | :--- |
| Sin esquema (3 veces) | 3 152 a 3 460 | 12,4 a 12,9 s | **Inválido las 3 veces** |
| Con esquema, tope 4096 | 4 096 | 14,6 s | **Cortado** (`finish_reason = length`) |
| Con esquema, tope 8000 | 5 281 | 18,5 s | **Válido:** 2 olas, 20 tareas |

Unos 255 a 285 tokens por segundo; unos 264 tokens por tarea. **Extrapolación** (no medida): 73 tareas serían unos 19 000 tokens y unos 70 s en una sola llamada, o de 15 a 25 s por ola si se genera por olas. Dos intentos serían unos 140 s, dentro del límite de 300 s configurado en Cloud Run (`timeout`).

**Opciones consideradas.** (a) Servicio independiente adicional: sobredimensionado para tareas de segundos. (b) Cola asíncrona en Cloud Tasks: correcta pero reservada para volúmenes superiores a 300 s. **(c) En línea: elegida**; sin infraestructura adicional en Cloud Run (`timeout: 300s`) y con ejecución no bloqueante en el servidor ASGI. El contrato responde en línea con `job_id`, estado y `roadmap_id` terminados (`200 OK`).

## Anexo B. Correo para las notificaciones (D-7; fuentes oficiales, 2026-10-10)

| Opción | Gmail API / Google Workspace | Pasarela HTTP futura |
| :--- | :--- | :--- |
| Límites | 2 000 mensajes al día por usuario en Workspace | Según proveedor corporativo elegido |
| Integración | API oficial de Google Workspace con delegación de dominio | Proveedor inyectable en `features/notificaciones/` |

**Estado vigente:** El diseño agrupa por usuario y lote con el mínimo de datos personales (enlace a la tarea, sin contenido de evidencia), y el envío externo permanece desactivado hasta configurar el proveedor corporativo en Google Workspace.
