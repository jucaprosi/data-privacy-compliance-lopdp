# Plan de Ejecución — Módulo Hoja de Ruta Inteligente
`¤roadmap` `¤rbac-tenant` `¤adpa`

> **Documentos que lo sostienen:** qué se exige, en `governance/artefactos/PRD.md` (Módulo 5); cómo está construido, en `governance/arquitectura/HOJA_DE_RUTA_ADPA.md`; quién hace qué, en `governance/tareas/` (índice en `TASKS.md`, Fase 7); el despliegue, en `governance/operaciones/PROCEDIMIENTO_VERCEL.md`. Este plan solo ordena la ejecución y recoge las decisiones.
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
6. **Hueco de despliegue.** Faltan en Vercel las variables de R2 y Redis y un `vercel.json` con la duración máxima; Preview tampoco tiene `CORS_ORIGINS` ni `DEEPSEEK_MODEL`. → OPS-01, OPS-02 y RM-13.

## 3. Revisión del Tech Lead: qué se rehízo y por qué

La primera versión de estos documentos afirmaba que las tareas eran «totalmente independientes» sin poder comprobarlo. Al revisarla se vio que **no lo eran** y que además dañaba la salud de la documentación:

| Problema detectado | Corrección |
| :--- | :--- |
| `ROUTERS_MAP`, las compuertas y dos archivos de pruebas los tocaban varias tareas a la vez. | Autoregistro de routers (RM-00), **secciones reservadas** en las compuertas (RM-01), `xfail` dinámico en la matriz (RM-03) y pruebas propias en cada tarea. |
| Cinco tareas crearían una migración en paralelo: dos cabezas de Alembic al fusionar. | Prueba de una sola cabeza (RM-00) y `main` exige la rama al día. |
| Todos los agentes probarían contra la misma rama de Neon, pisándose al migrar y limpiar. | Una rama hija de Neon por agente (el plan gratuito admite 10 y hay 2 en uso). |
| Hacían falta dos tareas en cadena para mover el mismo código (RBAC y roadmap). | Una sola tarea de reestructuración (RM-01): menos olas y sin edición cruzada de imports. |
| El PRD llevaba rutas de archivos y columnas «pendiente/implementado» que caducan; `TASKS.md` (que el servidor también modifica) llevaba 30 tareas. | PRD solo de producto; arquitectura aparte; **una especificación por tarea** con cabecera legible por máquina y estado propio. |
| La independencia solo estaba afirmada. | `scripts/generar_indice_tareas.py` y `tests/test_indice_tareas.py` la **comprueban**: dos tareas que pueden ejecutarse a la vez no pueden poseer el mismo archivo. Probado con conflictos forzados. |
| Notificaciones, firma electrónica e integración ZERAG mezcladas con el núcleo. | Las dos primeras quedan como bocetos en el *backlog*; ZERAG sale del proyecto. |

## 4. Ejecución por olas

Las tareas de una misma ola se asignan a agentes distintos sin coordinarse. El detalle de cada una (entrega, propiedad de archivos, árbitro) está en su especificación.

| Ola | Tareas | Depende de |
| :--- | :--- | :--- |
| **A** Fundamentos | RM-00, RM-01, RM-02, RM-03, RM-14 y, tras RM-00, FE-01 | — |
| **B** Funciones y vistas | RM-07, RM-08, RM-09, RM-12, RM-15, RM-16, SEC-03, FE-02, FE-03, FE-04, FE-05 | RM-01 (las de backend), FE-01 (las de frontend) |
| **C** Flujos que encadenan | RM-10 (tras RM-14 y RM-16), RM-13 (tras RM-12) | ola B |
| **D** Integración | FE-06, QA-01, SEC-02 | olas B y C |
| **E** Despliegue | OPS-01, OPS-02 | RM-13 |
| Independientes | OPS-03, GOB-01, GOB-02 (hecha) | — |
| *Backlog* | NOTIF-01, FIRMA-01, TEST-01 | según la tarea |

**Camino crítico:** RM-01 → RM-12 → RM-13 → QA-01 → OPS-02 (o RM-01 → RM-16 → RM-10 → QA-01). Tras RM-01 se abre la mayor paralelización: hasta once tareas a la vez. No se dan horas: ninguna estimación se ha medido.

**Prioridad:** RM-02 (SQL interpolado) va en la ola A y no depende de nada ni toca archivos de otras tareas, así que no retrasa a las demás.

## 5. Protocolo para varios agentes

1. **Un agente, una tarea, una rama, un PR**, en su propio árbol de trabajo (`git worktree add <ruta corta>`; en Windows, ruta corta por el nombre largo de un PDF en la raíz).
2. **Una rama hija de Neon por agente** (`test-<agente>`), nunca la rama `test` compartida. Sin Docker en el equipo, es la vía; el plan gratuito admite 10 ramas por proyecto y 100 horas de cómputo al mes en total.
3. **Propiedad exclusiva.** Si una tarea necesita un cambio fuera de su lista, lo declara y espera; no lo hace.
4. **Contrato primero.** Los agentes del frontend trabajan contra `governance/contratos/hoja_de_ruta.openapi.json` y un *mock*.
5. **Árbitro exógeno.** Cada tarea lo declara; además, el check `Arnés Físico Determinista`. El agente no certifica su propio trabajo.
6. **Fusión** solo con el check en verde y la rama al día con `main`.
7. **Roles de gobernanza:** backend `¤¤developer-architect`; pruebas `¤¤qa-engineer`; frontend `¤¤frontend-architect`; seguridad `¤¤security-engineer`.

## 6. Reconstrucción de Vercel

El procedimiento completo está en `governance/operaciones/PROCEDIMIENTO_VERCEL.md`. Resumen:

* **Estado verificado hoy:** Production y Preview usan `lopdp_app`; las 10 vistas previas más recientes se construyeron **después** del cambio de variable y no necesitan reconstrucción; Production responde 200, `OPERATIONAL`, 16 de 16 routers.
* **Cuándo reconstruir:** tras cambiar variables, las vistas previas anteriores al cambio (`vercel redeploy <url>`) y, en Production, el último despliegue de `main`.
* **Verificar:** `scripts/verificar_despliegue.py` (OPS-03) debe devolver 0.
* **Si falla:** *Promote to Production* del despliegue anterior; nunca *Redeploy* sobre filas «Redeploy of …».
* **Pendiente:** cargar en Vercel las variables de R2 y Redis (OPS-01), alinear Preview con Production y añadir `vercel.json` (RM-13).

## 7. Decisiones

| ID | Decisión | Resultado |
| :--- | :--- | :--- |
| D-1 | Dónde corre la generación | **En línea** (plan gratuito, 300 s; medición de 13 a 19 s). Resuelta por defecto; revertible. Anexo A. |
| D-2 | Variables en Vercel | **Aceptada:** las carga el usuario. |
| D-3 | Flujo de alta de responsables | **Resuelta** (PRD §5.3.1). Eventos en `audit_events`; tamaño nulo ⟹ bloqueo con error guiado y sin valor por defecto. |
| D-4 | Firma electrónica | **ANF**. Boceto en el *backlog*. |
| D-5 | Integración ZERAG ↔ agente de código | **Fuera de este proyecto** (pertenece a ZERAG). |
| D-6 | Autenticación | **SSO con Google (OIDC)**; la cuenta solo prueba la identidad. |
| D-7 | Notificaciones | **Solo correo; proveedor Resend** (Anexo B). |
| D-8 | Base de pruebas por agente | **Propuesta:** una rama hija de Neon por agente. Pendiente de confirmar. |

## 8. Acciones que solo puede hacer el usuario

1. Confirmar D-8 (ramas hijas de Neon por agente).
2. Crear el cliente OAuth en Google Cloud (SEC-03).
3. Cargar las variables en Vercel (OPS-01).
4. Verificar un dominio remitente en Resend (NOTIF-01).
5. En GitHub, exigir que las ramas estén al día antes de fusionar en `main` (hoy no se exige): evita dos cabezas de migración y un `main` roto al fusionar en paralelo.
6. Rotar la clave de acceso del MCP de gobernanza, expuesta en un chat anterior, antes del primer cliente.

## 9. Riesgos

| # | Riesgo | Impacto | Mitigación |
| :--- | :--- | :--- | :--- |
| R1 | Identidad suplantable por cabeceras | **Alto** | SEC-03 antes de abrir a clientes. |
| R2 | SQL interpolado en `app_core/database.py` | Alto | RM-02, con árbitro AST. |
| R3 | La generación devuelve JSON inválido o cortado | Alto | RM-12. |
| R4 | Mover código entre salas rompe imports | Medio | RM-01 sin cambio de comportamiento, con la suite y `test_adpa_bulkhead.py` como árbitros; sin *shims*. |
| R5 | Colisiones entre agentes | Medio | Propiedad exclusiva **verificada** por prueba; secciones reservadas; árbol de trabajo y rama de Neon por agente. |
| R6 | La matriz de permisos y el código divergen | Medio | RM-03 la convierte en prueba. |
| R7 | Clave del MCP expuesta | Medio | Acción 6 del usuario. |
| R8 | Dos cabezas de Alembic al fusionar en paralelo | Medio | Prueba de una cabeza (RM-00) y rama al día (acción 5). |
| R9 | El SSO no funciona en las vistas previas | Medio | Probarlo en local y en producción. |
| R10 | `task_audit_log` borra registros en cascada con la tarea | Bajo (latente) | Los eventos nuevos van a `audit_events`; evaluar `RESTRICT`. |
| R11 | Tres vocabularios de tamaño y dos fuentes (ficha del navegador y base) | Medio | RM-15. |
| R12 | Límites del plan gratuito (Resend: 100 correos al día; Neon: 100 h de cómputo al mes) | Bajo | Correo agrupado por usuario y lote; ramas de Neon con suspensión por inactividad. |

## 10. Definición de terminado de la Fase 7

Los criterios de aceptación 10 a 13 del PRD se cumplen y sus árbitros están en verde: `tests/test_matriz_permisos.py` sin filas pendientes, `tests/test_rls_app_role.py`, el flujo de punta a punta de QA-01 y `scripts/verificar_despliegue.py` con código 0 contra producción.

---

## Anexo A. Evidencia para D-1 (medida el 2026-10-10)

Entrada sintética de 20 controles, modelo `deepseek-flash`; una sola llamada por prueba.

| Prueba | Tokens de salida | Tiempo | Resultado |
| :--- | :--- | :--- | :--- |
| Sin esquema (3 veces) | 3 152 a 3 460 | 12,4 a 12,9 s | **Inválido las 3 veces** |
| Con esquema, tope 4096 | 4 096 | 14,6 s | **Cortado** (`finish_reason = length`) |
| Con esquema, tope 8000 | 5 281 | 18,5 s | **Válido:** 2 olas, 20 tareas |

Unos 255 a 285 tokens por segundo; unos 264 tokens por tarea. **Extrapolación** (no medida): 73 tareas serían unos 19 000 tokens y unos 70 s en una sola llamada, o de 15 a 25 s por ola si se genera por olas. Dos intentos serían unos 140 s, por debajo de los 300 s del plan Hobby (documentación de Vercel, 2026-08-24; Pro llega a 800 s).

**Opciones consideradas.** (a) Servicio propio: sobredimensionado para tareas de segundos y añade un servicio que pagar y operar. (b) Cola con entrega HTTP (QStash: 1 000 mensajes al día gratis; Vercel Queues, en beta): correcta pero prematura. **(c) En línea: elegida**; sin infraestructura nueva. Condiciones: RM-12 primero, `maxDuration` en `vercel.json`, y llamada al modelo en un hilo aparte porque hoy bloquea el bucle de eventos. Se pasa a (b) cuando haya volumen o la generación se acerque a los 300 s. El contrato se conserva en lo esencial: `POST /roadmaps/generate` responde con `job_id`, estado y `roadmap_id` ya terminados, y cambia de 202 a 200.

## Anexo B. Correo para las notificaciones (D-7; fuentes oficiales, 2026-10-10)

| | Resend (plan gratuito) | Google Workspace |
| :--- | :--- | :--- |
| Límites | 3 000 correos al mes y 100 al día; 3 dominios; retención de 30 días | 2 000 mensajes al día por usuario; 500 en cuentas de prueba |
| Integración | API HTTP, apta para funciones serverless | SMTP o API de Gmail, con la cuenta de una persona |

**Elegido: Resend.** Con 100 correos al día, asignar 70 tareas de golpe agotaría la cuota si saliera un correo por tarea; por eso el diseño agrupa por usuario y lote. El correo lleva el mínimo de datos personales y un enlace a la tarea, sin el contenido de la evidencia.
