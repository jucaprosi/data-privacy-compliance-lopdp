# Tablero de Tareas y Control de Avance (`TASKS.md`)
`¤bbap`

> **MEMORIA OPERATIVA Y CONTROL DE EJECUCIÓN:**
> Este archivo registra las tareas pendientes, activas y completadas de **JUBYS Plataforma LOPDP 360**. Cada hito está anclado a su rastro estigmérgico (`¤`) y garantiza la trazabilidad del roadmap desde la Fase 0 (Discovery y Diseño) hasta el despliegue del MVP y módulos avanzados.

---

## Estado General del Proyecto
* **Fase Actual:** `Fases 0–5 completadas; Fase 6 (NIIF 18) y Fase 7 (Hoja de Ruta Inteligente) en progreso`
* **Metodología de Desarrollo:** BBAP (Boceto ➔ Sellado) con Confinamiento en Salas ADPA.
* **Diseño Frontend:** Estilo Antigravity / Cursor (Clean IDE, Command Palette, Dark/Light mode).

---

## 🎯 Plan de Trabajo por Fases

### 🟢 FASE 0: Discovery, Nido de Artefactos y Arquitectura (EN PROGRESO - 85%)
- [x] **Ingesta y Análisis Epistémico:** Lectura de la Guía de Diseño JUBYS v1.1 y resoluciones SPDP 2024–2026. `¤fuentes`
- [x] **Product Requirements Document (PRD):** Creación del PRD con benchmark de mercado (Global Suite, Novoser, Pirani, Isotools) y lineamientos frontend. `¤artefactos-prd`
- [x] **Núcleo Neuronal VPA_MAP:** Definición del mapa estigmérgico y catálogo de rastros del sistema. `¤vpa`
- [x] **Catálogo Central de Invariantes:** Registro de leyes inmutables del negocio (Independencia DPO, evidencias, MTGE). `¤invariantes`
- [x] **Mapa Epistémico y Bibliografía:** Anclaje formal de resoluciones oficiales SPDP (F01–F17). `¤fuentes`
- [x] **Tratado de Aportes Inéditos:** Documentación de las 8 innovaciones arquitectónicas del Compliance Graph y evaluación 60 min. `¤aportes`
- [x] **Metodologías de Ejecución y Ergonomía:** Marco de trabajo basado en DMAT, Odoo, Antigravity/Cursor, Global Suite, Novoser, Pirani e Isotools. `¤metodologias`
- [x] **Doctrinas Constitucionales:** Principios rectores no negociables basados en el Blueprint JUBYS v1.1. `¤doctrinas`
- [x] **Arquitectura de Software (SAD):** Diseño técnico multi-tenant, salas ADPA herméticas, RLS, pipeline DLP y frontend IDE-grade. `¤arquitectura`
- [x] **Data Model Inicial y Salas ADPA:** Especificación de modelos Pydantic/Dataclasses, compuertas `_service.py` y suite de tests con Exit Code 0. `¤rat` `¤adpa`
- [x] **Institución del Rol Tech Lead (`¤¤tech-lead`):** Formalización de la custodia agéntica de artefactos maestros (`PRD.md`, `TASKS.md`, `INVARIANTS.md`, doctrinas, metodologías, tratados científicos y arneses físicos). `¤vpa` `¤bbap`


---

### 🔵 FASE 1: MVP - Diagnóstico Rápido y Cockpit DPO Básico (EN PROGRESO - 60%)
- [x] **Motor de Diagnóstico Adaptativo (60 min):**
  - [x] Implementación de la Ficha Organizacional Inteligente (`DIA-01`). `¤diagnostico`
  - [x] Árbol de preguntas condicionales con límite técnico de 80 preguntas visibles (`DIA-05`). `¤diagnostico-motor`
  - [x] Motor de scoring multidimensional (Madurez 0-3 SPDP vs Conformidad vs Riesgo) (`DIA-07`). `¤diagnostico-scoring`
  - [x] Generador de informe ejecutivo preliminar en Markdown y HTML (`DIA-10`). `¤diagnostico-reporte`
- [x] **RAT Maestro y Compliance Graph Inicial:**
  - [x] Sala ADPA `features/rat/` con compuerta estanca `rat_service.py`. `¤rat` `¤adpa`
  - [x] CRUD y versionado de actividades de tratamiento (`IMP-02`). `¤rat`
- [x] **Cockpit del DPD/DPO (Independencia & Supervisión):**
  - [x] Sala ADPA `features/dpo_cockpit/` con permisos de solo lectura operativa y barrera SoD. `¤dpo-cockpit`
  - [x] Bandeja de asesorías y registro cronológico de dictámenes (`DPO-01`, `DPO-04`). `¤dpo-asesoria`
- [x] **Motor MTGE y Tratamientos a Gran Escala:**
  - [x] Sala ADPA `features/riesgos_mtge/` con cálculo determinista bajo Res. SPDP-SPD-2026-0005-R. `¤mtge-granescala`
- [x] **Pasarela REST API Gateway Unificada (FastAPI):**
  - [x] Enrutadores REST para las 7 salas ADPA con resolución multi-tenant y middleware CORS (`main.py` y `api/`).
  - [x] Suite de integración determinista `tests/test_api_gateway.py` (21/21 pruebas en verde). `¤adpa`
- [x] **Frontend IDE Base (Estilo Antigravity / Cursor / Render.com):**
  - [x] Shell de navegación con layout split pane y soporte dark/light nativo. `¤frontend-ide`
  - [x] Command Palette (`Ctrl + K`) para navegación rápida y búsqueda de controles/artículos. `¤frontend-ide`
  - [x] Módulos interactivos para las 7 salas ADPA con conexión API REST y Turbopack. `¤frontend-ide`
  - [x] Pestaña de Configuración del Proyecto / Ficha Organizacional antecedente (`ProjectConfig.tsx`). `¤frontend-ide` `¤diagnostico`
  - [x] Store global Zustand (`useAuditStore.ts`) con sincronización reactiva de empresa y evidencias. `¤frontend-ide`
  - [x] Whitelist de evidencias dinámica Poka-Yoke con purga automática al cambiar de normativa. `¤evidencias`
  - [x] Purificación de paleta Render.com (grises/negros acromáticos, jerarquía tonal invertida y dock plegable). `¤frontend-ide`



---

### 🟣 FASE 2: Implementación Avanzada y Motor MTGE (COMPLETADA)
- [x] **Motor de Riesgos y EIPD:**
  - [x] Matriz de riesgos sobre derechos y libertades (`IMP-06`). `¤riesgos-eipd`
  - [x] Calculadora algorítmica de Tratamiento a Gran Escala MTGE (`IMP-13`). `¤mtge-granescala`
- [x] **Derechos de Titulares e Incidentes:**
  - [x] Workflow de solicitudes ARCO+ con cronómetro de vencimiento (`IMP-05`). `¤derechos`
  - [x] Playbook de gestión de brechas y reloj de notificación SPDP/CSIRT (`IMP-12`). `¤incidentes`
- [x] **Terceros y Transferencias:**
  - [x] Inventario de encargados, debida diligencia y cláusulas obligatorias (`IMP-08`). `¤transferencias`

---

### 🟡 FASE 3: Auditoría y Copiloto IA (COMPLETADA)
- [x] **Módulo de Auditoría y CAPA:**
  - [x] Generación de checklists normativos desde snapshot histórico (`AUD-02`). `¤auditoria-programa`
  - [x] Workflow de hallazgos, planes de acción y verificación de cierre independiente (`AUD-06`, `AUD-07`). `¤auditoria-capa`
- [x] **Copiloto RAG Legal con Guardrails:**
  - [x] Indexación vectorial del corpus normativo cerrado de la SPDP. `¤regulation-code`
  - [x] Filtro DLP pre-inferencia y obligación de citación exacta de artículos. `¤copiloto-ia`

---

### 🟢 FASE 4: Producción, CI/CD y Despliegue (COMPLETADA)
- [x] **Containerización Multi-Capa (Docker):**
  - [x] `Dockerfile` para FastAPI y `Dockerfile` para Next.js (Multi-stage). `¤docker`
  - [x] `docker-compose.yml` integrando PostgreSQL con RLS y volúmenes locales. `¤docker-compose`
- [x] **Gobernanza CI/CD Automatizada:**
  - [x] Pipeline de GitHub Actions para disparar el Arnés Físico Zero-Regression en cada PR. `¤ci-cd`
- [x] **Reportes y Artefactos Inmutables:**
  - [x] Motor de exportación a PDF (WORM) para Diagnósticos y Auditorías. `¤reportes-pdf`
- [x] **Hardening de Producción:**
  - [x] Sanitización de variables de entorno, CORS estricto y rotación de logs. `¤seguridad`

---

### 🟢 FASE 5: Seguridad Avanzada y Optimización Cognitiva (COMPLETADA)
- [x] **Árbol de Merkle para No-Repudio (Aporte 27):**
  - [x] Integración de `merkle_tree.py` y anclaje asíncrono RFC 3161 para Snapshots de Auditoría.
- [x] **K-Anonimato en Indexación RAG (Aporte 28):**
  - [x] Motor NER Heurístico para evitar ataques de inversión de embeddings vectoriales.
- [x] **Sensor de Deriva de Riesgo EIPD (Aporte 29):**
  - [x] Reglas reactivas sobre volumen (+25%) y datos biométricos en MTGE.
  - [x] Inyección de heurísticas de contexto usando `usePathname` en `cmdk` de Next.js.

---

### 🟠 FASE 6: Integración Profunda NIIF 18 (EN PROGRESO)
- [x] **Diagnóstico y Trazabilidad Estigmérgica (`¤niif18`)**: Inserción del Módulo 4 en `PRD_Plataforma_LOPDP_360.md` y estructura en `TASKS.md` para asimilar el modelo NIIF 18 al Core Multi-Tenant.
- [x] **Desacople e Ingesta ADPA Backend (`¤niif18-backend`)**:
  - [x] Agente 1 (Backend Data): Trasladar lógica `app.py` heredada hacia `features/niif18/engines/parser_engine.py` (inferencia) y `classifier_engine.py`.
  - [x] Agente 2 (Backend Math): Trasladar lógica de P&L, MPMs y Excel hacia `financials_engine.py`, `mpm_engine.py` y `export_engine.py`.
  - [x] Ensamblar `niif18_service.py` como compuerta principal que consume los engines.
  - [x] Configurar las rutas en `api/routers/niif18.py`.
- [x] **Copiloto de IA Contextual (`¤niif18-ai`)**:
  - [x] Migrar volúmenes de `NIIF 18/docs/biblioteca_doctrinal/` a JUBYS.
  - [x] Agente 3 (Cognitive AI): Actualizar el backend de IA (`inference_engine.py`) para consumir contexto y asumir rol NIIF 18 experto en base a los subtotales pasados.
- [x] **Reactividad Frontend (`¤niif18-frontend`)**:
  - [x] Conectar los endpoints de `features/niif18` a `useAuditStore` y los componentes creados (`NiifReclasificacionView`, `NiifMpmView`, etc.).
  - [x] Garantizar recálculo de subtotales NIIF en caliente ante edición del usuario en la UI.


---

### 🔴 FASE 7: Hoja de Ruta Inteligente (EN PROGRESO)
`¤roadmap` `¤rbac-tenant`

> **Especificación:** `PRD.md`, Módulo 5 (salas, matriz de permisos, SoD, RLS, contrato de API, despliegue). **Plan de ejecución:** `governance/PLAN_HOJA_DE_RUTA_INTELIGENTE.md`.
>
> **Reglas de ejecución multiagente (aplican a todas las tareas de esta fase):**
> 1. **Independencia:** cada tarea declara su *propiedad exclusiva* de archivos (no se tocan fuera de esa lista), su contrato de entrada congelado (`RM-00`) y su propio árbitro exógeno.
> 2. **Una tarea = un agente = una rama = un PR**, en su propio árbol de trabajo (`git worktree add`): varias sesiones sobre una misma carpeta cambian de rama bajo los pies (Aporte 90).
> 3. **Salas ADPA:** entre salas solo existen compuertas `_service.py`; el código de negocio vive en `features/<sala>/`, no en `app_core/`.
> 4. **Archivos compartidos** (compuertas, `ROUTERS_MAP` de `main.py`, `dashboard/page.tsx`, tipos de navegación) los edita **solo** la tarea de integración de su ola.
> 5. **Terminado =** árbitro de la tarea en verde + suite completa + check `Arnés Físico Determinista` en el PR. Sin parches ni *shims* de compatibilidad.

#### 7.0 Base ya entregada (verificada en `main`)
- [x] **Contrato, persistencia y RLS inicial:** modelos Pydantic, prompts, router base, persistencia async, R2 y cola (commits `0501eb6`, `6e3b3e9`). `¤roadmap`
- [x] **Tests y limpieza:** suite de la hoja de ruta, limpieza de BOM y *skipif* del arnés (commits `4000f99`, `5c32258`). `¤arbitro`
- [x] **RBAC por tenant completo (antes «Fase 2.4»):** usuarios, áreas, roles, `/me/roles`, trigger de SoD del DPO, cuatro ojos y alcance por área (commit `0ab37e7`). `¤rbac-tenant`
- [x] **RLS efectivo:** rol `lopdp_app` sin `BYPASSRLS` y `FORCE ROW LEVEL SECURITY` en 7 tablas (migración `20261008_app_role_rls`, PR #15); aplicado en TEST y producción; `DATABASE_URL` de la app y de Preview usan `lopdp_app`. `¤seguridad-tenant`
- [x] **Contexto de sesión correcto:** `get_session` lee las cabeceras (PR #16), `config.py` carga `.env` antes de los valores por defecto (PR #18) y `DATABASE_URL` tolera restos de pegado (PR #19). `¤seguridad`
- [x] **`/health` honesto:** informa routers cargados y fallidos, responde 503 si hay fallos y el modo de emergencia ya no publica el traceback (PR #27, #29, #30). `¤adpa`
- [x] **Arnés:** el Pilar 3 ya no marca falsos positivos en `.venv` (commit `de204e3`). `¤arbitro`
- [x] **Protección de `main`:** el check `Arnés Físico Determinista` es obligatorio para fusionar. `¤ci-cd`

#### 7.1 Ola 0 — Contrato (1 agente; bloquea las olas 1 y 2)
- [ ] **RM-00 · Congelar el contrato de la hoja de ruta.** `¤roadmap` `¤adpa`
  - **Entrega:** (a) script `scripts/exportar_contrato_hoja_ruta.py` que exporta el OpenAPI de `/roadmaps` y `/organizacion` a `governance/contratos/hoja_de_ruta.openapi.json`, incluyendo como *propuestos* los endpoints pendientes del PRD §5.6; (b) `governance/contratos/hoja_de_ruta_compuertas.md` con las firmas públicas de `organizacion_service` y `roadmap_service`.
  - **Propiedad exclusiva:** `scripts/exportar_contrato_hoja_ruta.py`, `governance/contratos/**`, `tests/test_contrato_hoja_ruta.py`.
  - **Depende de:** nada.
  - **Árbitro:** `pytest tests/test_contrato_hoja_ruta.py` (el OpenAPI generado debe coincidir con el archivo congelado; falla si cambia sin actualizarlo).

#### 7.2 Ola 1 — Fundamentos (paralelo; archivos disjuntos)
- [ ] **RM-01 · Sala `features/organizacion/` (RBAC por tenant).** `¤rbac-tenant` `¤adpa`
  - **Entrega:** mover `app_core/services/rbac_service.py` y `app_core/schemas/rbac_schema.py` a la sala (`domain/`, `services/`, compuerta `organizacion_service.py`); `api/rbac.py` y `api/routers/organizacion.py` importan solo la compuerta; sustituir el SQL dinámico de `rbac_service` (`f"UPDATE areas SET {sets}…"`, `f"…{where}…"`) por listas blancas explícitas de columnas; crear `tests/test_adpa_bulkhead.py` (AST: ningún módulo fuera de una sala importa sus `services/` ni cruza salas sin compuerta). **Sin cambio de comportamiento y sin *shims*:** se editan además, solo en sus líneas de `import`, `app_core/services/roadmap_service.py` y `api/routers/roadmaps.py`.
  - **Propiedad exclusiva:** `features/organizacion/**`, `api/rbac.py`, `api/routers/organizacion.py`, `tests/test_organizacion_*.py`, `tests/test_adpa_bulkhead.py`; elimina los dos archivos de `app_core` indicados.
  - **Depende de:** RM-00.
  - **Árbitro:** suite de organización y roadmaps existente en verde + `tests/test_adpa_bulkhead.py`.
- [ ] **RM-02 · Sesión de BD única y cero SQL interpolado (antes «Fase 2.3»).** `¤seguridad` `¤adpa`
  - **Entrega:** eliminar `app_core/database.py` (contiene `SET LOCAL app.current_tenant_id = '{tenant_id}'` interpolado) y dejar `app_core/db/session.py` como única fuente de sesión con `set_config(…, true)`; migrar sus consumidores: `api/routers/{ai_copilot,arco_router,terceros_router}.py`, `app_core/models_base.py`, `features/derechos_arco/domain/models.py`, `features/terceros/domain/models.py`, `features/transferencias/services/encargados_service.py`, `scripts/seed_database.py`, `tests/test_database_rls.py`, `tests/test_ai_copilot.py`, `tests/test_api_integracion.py`.
  - **Propiedad exclusiva:** los archivos listados y `tests/test_sin_sql_interpolado.py`.
  - **Depende de:** nada.
  - **Árbitro:** `tests/test_sin_sql_interpolado.py` (AST: ningún `text(f"…")` con variables no constantes) + suite completa; habilita `INV_LOPDP_SESSION_SINGLE_SOURCE`.
- [ ] **RM-03 · Matriz de permisos como prueba (QA; solo prueba, no corrige).** `¤rbac-tenant` `¤arbitro`
  - **Entrega:** `tests/test_matriz_permisos.py` parametrizado (rol × endpoint) contra PRD §5.2 y §5.6. Las filas que el backend aún no implementa (RM-07, RM-08, RM-09, RM-10) se marcan `xfail(strict=True)` con el ID de su tarea, de modo que al implementarse el `xfail` estricto falle y obligue a retirarlo. Todo desvío distinto de esos se reporta como defecto.
  - **Propiedad exclusiva:** `tests/test_matriz_permisos.py`.
  - **Depende de:** nada.
  - **Árbitro:** el propio test; sustenta `INV_LOPDP_ROADMAP_RBAC_MATRIX`.
- [ ] **FE-01 · Cliente de API y store del frontend.** `¤frontend-ide` `¤roadmap`
  - **Entrega:** tipos generados desde `hoja_de_ruta.openapi.json`, cliente con las cabeceras `X-User-ID`, `X-Tenant-ID` y `X-Role`, *mock* del contrato para desarrollar sin backend y `useRoadmapStore`.
  - **Propiedad exclusiva:** `frontend/src/lib/roadmap/**`, `frontend/src/store/useRoadmapStore.ts`, `frontend/src/types/roadmap.ts`.
  - **Depende de:** RM-00.
  - **Árbitro:** `tsc --noEmit` y `next build` (Pilares 2 y 3 del arnés) + prueba unitaria del cliente contra el *mock*.

#### 7.3 Ola 2 — Sala Hoja de Ruta y vistas (paralelo)
- [ ] **RM-05 · Sala `features/roadmap/`.** `¤roadmap` `¤adpa`
  - **Entrega:** mover `app_core/services/roadmap_service.py`, `app_core/schemas/roadmap_schema.py`, `app_core/workers/roadmap_worker.py` y `app_core/ai/roadmap_prompts.py` a la sala (`domain/`, `services/` por motor: generación, evidencia, KPIs, auditoría; compuerta `roadmap_service.py`); consumir SoD y cuatro ojos **solo** vía `organizacion_service`; `api/routers/roadmaps.py` importa solo la compuerta. `app_core/` conserva `queue/`, `storage/` y `ai/deepseek_client.py` como núcleo compartido.
  - **Propiedad exclusiva:** `features/roadmap/**`, `api/routers/roadmaps.py`, `tests/test_roadmap_service.py`, `tests/test_roadmaps_api.py`.
  - **Depende de:** RM-01.
  - **Árbitro:** suite de roadmaps en verde + `tests/test_adpa_bulkhead.py`.
- [ ] **FE-02 · Formulario de variables de planeación y generación.** `¤frontend-ide` `¤roadmap`
  - **Entrega:** `PlaneacionForm.tsx` (variables, validación, disparo de `POST /roadmaps/generate` y seguimiento del *job* con sondeo).
  - **Propiedad exclusiva:** `frontend/src/components/modules/roadmap/planeacion/**`.
  - **Depende de:** FE-01.
  - **Árbitro:** Pilares 2 y 3 del arnés + `frontend/tests/roadmap/planeacion.spec.ts` (Playwright contra el *mock*).
- [ ] **FE-03 · Vista de olas y tareas.** `¤frontend-ide` `¤roadmap`
  - **Entrega:** `OlasView`, `TareaCard`, `KpiBar`: estado, filtros por área y rol, KPIs, acciones visibles según la matriz del PRD §5.2.
  - **Propiedad exclusiva:** `frontend/src/components/modules/roadmap/olas/**`.
  - **Depende de:** FE-01.
  - **Árbitro:** Pilares 2 y 3 + `frontend/tests/roadmap/olas.spec.ts`.
- [ ] **FE-04 · Panel de evidencia.** `¤evidencias` `¤frontend-ide`
  - **Entrega:** subida con URL prefirmada y `react-dropzone` (lista blanca de extensiones), listado, validar o rechazar con comentario, y bloqueo visible de la regla de cuatro ojos.
  - **Propiedad exclusiva:** `frontend/src/components/modules/roadmap/evidencia/**`.
  - **Depende de:** FE-01.
  - **Árbitro:** Pilares 2 y 3 + `frontend/tests/roadmap/evidencia.spec.ts`.
- [ ] **FE-05 · Administración de la organización.** `¤rbac-tenant` `¤frontend-ide`
  - **Entrega:** usuarios, áreas jerárquicas y asignación o revocación de roles; los 409 de SoD se muestran como mensajes claros.
  - **Propiedad exclusiva:** `frontend/src/components/modules/roadmap/admin/**`.
  - **Depende de:** FE-01.
  - **Árbitro:** Pilares 2 y 3 + `frontend/tests/roadmap/admin.spec.ts`.

#### 7.4 Ola 3 — Brechas del backend respecto a la matriz (paralelo; cada una en su motor)
Cada tarea entrega su motor en `features/roadmap/services/`, su prueba y un router parcial `api/routers/roadmaps_<x>.py`; el registro en la compuerta y en `ROUTERS_MAP` lo hace RM-11.
- [ ] **RM-07 · Editar tareas** (título, fechas, responsable, KPI, entregable). `PATCH /roadmaps/tasks/{id}`, rol `implementador`, evento `task_edited` en el audit log.
  - **Propiedad exclusiva:** `features/roadmap/services/tarea_edicion_engine.py`, `api/routers/roadmaps_edicion.py`, `tests/test_roadmap_tarea_edicion.py`.
  - **Depende de:** RM-05 · **Árbitro:** su test + retiro del `xfail` en RM-03.
- [ ] **RM-08 · Distribuir tareas.** `POST /roadmaps/tasks/{id}/assign`, rol `encargado`; solo a responsables activos del mismo tenant y área; evento `task_assigned`.
  - **Propiedad exclusiva:** `features/roadmap/services/tarea_asignacion_engine.py`, `api/routers/roadmaps_asignacion.py`, `tests/test_roadmap_tarea_asignacion.py`.
  - **Depende de:** RM-05 · **Árbitro:** su test + retiro del `xfail` en RM-03.
- [ ] **RM-09 · Consultar el audit log.** `GET /roadmaps/{id}/audit-log`, roles `encargado`, `dpo`, `implementador` y `admin_organizacion`; paginado y de solo lectura.
  - **Propiedad exclusiva:** `features/roadmap/services/auditoria_consulta_engine.py`, `api/routers/roadmaps_auditoria.py`, `tests/test_roadmap_auditoria_consulta.py`.
  - **Depende de:** RM-05 · **Árbitro:** su test + retiro del `xfail` en RM-03.
- [ ] **RM-10 · Flujo de alta de responsables de área** (PRD §5.3.1). `¤rbac-tenant` `¤dpo-independencia`
  - **Entrega:** migración Alembic con la tabla `area_responsable_requests` (RLS por `tenant_id` y `GRANT` explícito a `lopdp_app`), tabla de eventos append-only con RLS (propuesta; a confirmar) y la columna `user_tenant_roles.request_id`; motor `solicitud_responsable_engine` en la sala; los siete endpoints de `/areas/responsable-requests`; ejecución atómica (rol + evento + estado) y reglas de validación del usuario destino, con `tenants.tamano` nulo tratado como organización grande.
  - **Propiedad exclusiva:** `alembic/versions/*_responsable_requests.py`, `features/organizacion/services/solicitud_responsable_engine.py`, `api/routers/areas_responsable_requests.py`, `tests/test_responsable_requests.py`.
  - **Depende de:** RM-01 (vive en la sala Organización; no depende de RM-05).
  - **Árbitro:** `tests/test_responsable_requests.py` (habilita `INV_LOPDP_RESPONSABLE_ALTA_FLOW`) + `tests/test_rls_app_role.py` ampliado a la tabla nueva + retiro del `xfail` en RM-03.
  - **Fuera de esta tarea:** notificaciones por correo y expiración a 30 días (fase posterior).
- [ ] **RM-12 · Generación fiable con IA.** `¤roadmap` `¤copiloto-ia`
  - **Motivo (medido el 2026-10-10):** el prompt pide un JSON «conforme al esquema `RoadmapDocument`» pero **no incluye el esquema**; 3 de 3 respuestas sin esquema fueron inválidas, y con el esquema la salida de 20 tareas ocupa unos 5 300 tokens, por encima del tope actual de 4096 (se corta). Ver Anexo A del plan.
  - **Entrega:** incluir el esquema en el prompt; subir el tope de tokens o generar por olas (varias llamadas más pequeñas); reintento correctivo que reenvíe el esquema y el error de validación; llamada al modelo sin bloquear el bucle de eventos; tiempo límite explícito en el cliente.
  - **Propiedad exclusiva:** `features/roadmap/ai/**`, `features/roadmap/services/generacion_engine.py`, `tests/test_roadmap_generacion.py`.
  - **Depende de:** RM-05 · **Árbitro:** `tests/test_roadmap_generacion.py` con un modelo simulado (esquema presente en el prompt, reintento con el error, truncado detectado) y una verificación manual opcional contra el modelo real.
- [ ] **RM-13 · Generación en línea (decisión D-1).** `¤roadmap` `¤adpa`
  - **Entrega:** `POST /roadmaps/generate` ejecuta la generación dentro de la solicitud y responde con `{job_id, status, roadmap_id}` ya terminado (los endpoints de estado siguen existiendo); llamada al modelo en un hilo aparte (`asyncio.to_thread`); `vercel.json` con `maxDuration` de 300 s para `api/index.py`; si algo falla, el roadmap queda `failed` con el motivo y el cliente puede reintentar.
  - **Propiedad exclusiva:** `vercel.json`, `features/roadmap/services/generacion_en_linea.py`, la función de `POST /generate` en `api/routers/roadmaps.py`, `tests/test_roadmap_generacion_en_linea.py`.
  - **Depende de:** RM-05 y RM-12 · **Árbitro:** su test (éxito; fallo del modelo ⟹ `failed`; el bucle de eventos no se bloquea durante la llamada) + `tests/test_matriz_permisos.py`.

#### 7.5 Ola 4 — Integración (secuencial; archivos compartidos)
- [ ] **RM-11 · Integración del backend.** Registrar en las compuertas y en `ROUTERS_MAP` los routers de RM-07 a RM-10; confirmar `/health` con todos los routers cargados.
  - **Propiedad exclusiva:** `features/roadmap/roadmap_service.py`, `features/organizacion/organizacion_service.py`, `main.py` (solo `ROUTERS_MAP`).
  - **Depende de:** RM-07, RM-08, RM-09 y RM-10 · **Árbitro:** suite completa + `tests/test_matriz_permisos.py` sin `xfail` + `/health` 200.
- [ ] **FE-06 · Integración del frontend.** Pestaña «Hoja de Ruta» en `dashboard/page.tsx`, tipos de navegación (`VistaActiva`, `ActiveView`), visibilidad por rol con `/organizacion/me/roles`, textos de interfaz sin tokens de gobernanza (`¦interfaz`).
  - **Propiedad exclusiva:** `frontend/src/app/dashboard/page.tsx`, `frontend/src/types/index.ts`.
  - **Depende de:** FE-02, FE-03, FE-04, FE-05, RM-11 · **Árbitro:** Pilares 2 y 3.
- [ ] **QA-01 · Pruebas de punta a punta por rol.** Flujo del criterio de aceptación 12 del PRD con Playwright.
  - **Propiedad exclusiva:** `frontend/tests/roadmap/e2e/**`.
  - **Depende de:** FE-06 · **Árbitro:** el propio *spec*.
- [ ] **SEC-03 · Autenticación verificable con Google (bloqueante para producción con clientes).** Sustituir la identidad por cabeceras declaradas por el cliente: el servidor valida el token de identidad de **Google (OIDC)** (emisor, audiencia, vigencia y correo verificado) y obtiene de él solo el usuario; el tenant y el rol declarados se autorizan contra `user_tenant_roles` del usuario verificado. Migración que añade `users.google_sub` (único, opcional) y vincula la cuenta por correo verificado. **Acción manual del usuario:** crear el cliente OAuth en Google Cloud y registrar los orígenes autorizados (las vistas previas de Vercel cambian de dirección y no se pueden registrar una a una). `¤seguridad` `¤rbac-tenant`
  - **Propiedad exclusiva:** `api/rbac.py`, `api/dependencies.py` (solo la parte de identidad), `alembic/versions/*_users_google_sub.py`, `tests/test_autenticacion.py`.
  - **Depende de:** RM-01 · decisión D-6 resuelta (Google) · **Árbitro:** `tests/test_autenticacion.py` con tokens simulados (sin token ⟹ 401; emisor o audiencia ajenos ⟹ 401; correo no verificado ⟹ 401; `X-User-ID` suplantado ⟹ ignorado; tenant sin membresía ⟹ 403) + suite completa.
- [ ] **SEC-02 · Auditoría de seguridad previa a producción.** RLS, SoD, cabeceras de identidad (hoy autenticación por cabeceras, sin JWT firmado en la hoja de ruta), carga de evidencia y secretos.
  - **Depende de:** RM-11 · **Árbitro:** informe `governance/AUDITORIA_SEGURIDAD_HOJA_DE_RUTA.md` sin hallazgos críticos abiertos.

#### 7.6 Ola 5 — Despliegue y reconstrucción de Vercel
- [ ] **OPS-01 · Variables de entorno completas en Vercel (Production y Preview).** `DATABASE_URL` ya usa `lopdp_app`; faltan las de R2 y Redis y las del proveedor de IA según el entorno, y Preview no tiene `CORS_ORIGINS` ni `DEEPSEEK_MODEL` (caería en `*`). Los valores los carga el usuario; no se escriben en el repositorio. `¤seguridad`
- [ ] **OPS-02 · Verificar la generación en el entorno gratuito (decisión D-1: en línea).** Confirmar en Vercel que `vercel.json` aplica `maxDuration` de 300 s a `api/index.py` y que una generación completa termina dentro del límite; sin worker ni cola.
- [ ] **OPS-03 · Script de verificación de despliegue** `scripts/verificar_despliegue.py`: `GET /api/v1/health` ⟹ 200, `OPERATIONAL`, todos los routers cargados y rutas esperadas presentes en `/openapi.json`. Árbitro exógeno de OPS-04.
- [ ] **OPS-04 · Reconstrucción y verificación.** Tras fusionar a `main`: confirmar el despliegue de Production; reconstruir con `vercel redeploy <url>` las vistas previas anteriores al último cambio de variables; ejecutar OPS-03; si falla, *Promote to Production* del despliegue anterior. No usar *Redeploy* sobre filas «Redeploy of …».

#### 7.7 Tareas independientes (en cualquier momento)
- [ ] **GOB-01 · Promover los rastros nuevos** `¤roadmap` y `¤rbac-tenant` al VPA (`mcp_promote_vpa_candidate`; el `VPA_MAP` lo sirve el MCP y no se edita a mano). `¤vpa`
- [ ] **SEC-01 · Rotar la clave de acceso del MCP de gobernanza** (acción del usuario, antes del primer cliente real). `¤seguridad`
- [ ] **ZERAG-01 · Integración ZERAG ↔ agente de código por transporte `stdio`.** Alcance: este repositorio (`Plataforma LOPDP 360`), decisión D-5. Faltan por decidir la opción (`stdio` local, red permitida o híbrido) y si el modo local mide créditos (Anexo B del plan).
- [ ] **FIRMA-01 · Boceto (BBAP, paso 1) de la sala `features/firma_electronica/`:** firma electrónica de evidencia y actas con una entidad de certificación acreditada por la ARCOTEL. **Proveedor definido (D-4): ANF.** Falta diseñar la sala. `¤firma-electronica`
- [ ] **NOTIF-01 · Boceto (BBAP, paso 1) de la sala `features/notificaciones/`:** avisos al usuario sobre sus tareas asignadas (PRD §5.8). Por definir con el usuario: canal (en la aplicación, por correo o ambos), eventos además de la asignación y proveedor de correo. Depende de RM-08 para el primer evento. `¤roadmap`
- [ ] **TEST-01 · Cobertura pendiente:** pruebas HTTP de los endpoints de evidencia y pruebas de `redis_client` con *mock*.
