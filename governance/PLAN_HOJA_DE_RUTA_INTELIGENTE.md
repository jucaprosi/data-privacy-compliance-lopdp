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
4. **Hueco de despliegue.** La generación con IA encola en Redis y la consume un worker de larga duración, que las funciones serverless de Vercel no pueden alojar; además, en Vercel solo están cargadas `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS` y las de IA, sin las de R2 ni Redis. → OPS-01 y OPS-02.

## 3. Ejecución por olas

Cada tarea tiene archivos de propiedad exclusiva, contrato congelado y árbitro propio (ver `TASKS.md`, Fase 7), por lo que las tareas de una misma ola se pueden asignar a agentes distintos sin coordinarse.

| Ola | Tareas | Agentes en paralelo | Depende de | Orden de magnitud |
| :--- | :--- | :--- | :--- | :--- |
| **0** Contrato | RM-00 | 1 | — | ~1 h |
| **1** Fundamentos | RM-01, RM-02, RM-03, FE-01 | 4 | RM-00 (RM-01 y FE-01) | RM-01 2–3 h · RM-02 2–3 h · RM-03 ~2 h · FE-01 ~2 h |
| **2** Salas y vistas | RM-05, FE-02, FE-03, FE-04, FE-05 | 5 | RM-01 (RM-05) · FE-01 (las FE) | RM-05 3–4 h · cada FE 2–3 h |
| **3** Brechas del backend | RM-07, RM-08, RM-09 (RM-10 bloqueada) | 3 | RM-05 | ~2 h cada una |
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

## 6. Decisiones que necesito del usuario

| ID | Decisión | Bloquea | Opciones |
| :--- | :--- | :--- | :--- |
| **D-1** | Dónde corre el worker de generación | OPS-02 | (a) servicio propio de larga duración; (b) cola con entrega HTTP a una función serverless; (c) generación en línea sin cola para el MVP. Antes de elegir hay que comprobar los límites de duración de función del plan de Vercel, porque una llamada al modelo puede superarlos. |
| **D-2** | Cargar en Vercel las variables de R2, Redis e IA | OPS-01 | Las carga el usuario; el repositorio no guarda valores. |
| **D-3** | Flujo de alta de responsables (encargado solicita, implementador ejecuta) | RM-10 | Define si hay solicitud con estado, quién aprueba y qué tabla la guarda. |
| **D-4** | Proveedor de firma electrónica (entidad acreditada por la ARCOTEL) | FIRMA-01 | A elegir antes de diseñar la sala. |
| **D-5** | Alcance y responsable de la integración ZERAG ↔ agente de código | ZERAG-01 | Hoy es una tarea externa al repositorio. |
| **D-6** | Mecanismo de autenticación | SEC-03 | Token firmado propio (ya existe `JWT_SECRET`) o SSO (Entra ID, Google Workspace). |

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

## 8. Definición de terminado de la Fase 7

Los cuatro criterios nuevos del PRD (§9, puntos 10 a 13) se cumplen y sus árbitros están en verde: `tests/test_matriz_permisos.py` sin filas pendientes, `tests/test_rls_app_role.py`, el flujo de punta a punta de QA-01 y `scripts/verificar_despliegue.py` con código 0 contra producción.
