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

### 🟢 FASE 0: Discovery, Nido de Artefactos y Arquitectura (COMPLETADA)
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

### 🔵 FASE 1: MVP - Diagnóstico Rápido y Cockpit DPO Básico (COMPLETADA)
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
- [x] **Diagnóstico y Trazabilidad Estigmérgica (`¤niif18`)**: Módulo 6 en `PRD.md` y estructura en `TASKS.md` para asimilar el modelo NIIF 18 al Core Multi-Tenant.
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

> **Especificación:** `PRD.md`, Módulo 5 · **Arquitectura:** `governance/arquitectura/HOJA_DE_RUTA_ADPA.md` · **Plan y decisiones:** `governance/PLAN_HOJA_DE_RUTA_INTELIGENTE.md` · **Despliegue:** `governance/operaciones/PROCEDIMIENTO_VERCEL.md`.
>
> **Las tareas viven en `governance/tareas/<ID>.md`**, una especificación por tarea con su propiedad exclusiva de archivos, sus dependencias y su árbitro (ver el `README` de esa carpeta). El índice siguiente se **genera** con `scripts/generar_indice_tareas.py` y la independencia entre tareas se **comprueba** en `tests/test_indice_tareas.py`: este archivo no se edita a mano para esta fase. La **sala** de cada tarea sale del catálogo del PRD (apartado 7.1) y el mismo verificador comprueba que existe; las tareas de salas distintas, o sin dependencia entre sí, se ejecutan en paralelo por agentes distintos.

#### 7.0 Base ya entregada (verificada en `main`)
- [x] **Contrato, persistencia y RLS inicial:** modelos Pydantic, prompts, router base, persistencia async, R2 y cola (commits `0501eb6`, `6e3b3e9`). `¤roadmap`
- [x] **Tests y limpieza:** suite de la hoja de ruta, limpieza de BOM y *skipif* del arnés (commits `4000f99`, `5c32258`). `¤arbitro`
- [x] **RBAC por tenant completo (antes «Fase 2.4»):** usuarios, áreas, roles, `/me/roles`, trigger de SoD del DPO, cuatro ojos y alcance por área (commit `0ab37e7`). `¤rbac-tenant`
- [x] **RLS efectivo:** rol `lopdp_app` sin `BYPASSRLS` y `FORCE ROW LEVEL SECURITY` en 7 tablas (migración `20261008_app_role_rls`, PR #15); aplicado en TEST y producción; `DATABASE_URL` de la app y de Preview usan `lopdp_app`. `¤seguridad-tenant`
- [x] **Contexto de sesión correcto:** `get_session` lee las cabeceras (PR #16), `config.py` carga `.env` antes de los valores por defecto (PR #18) y `DATABASE_URL` tolera restos de pegado (PR #19). `¤seguridad`
- [x] **`/health` honesto:** informa routers cargados y fallidos, responde 503 si hay fallos y el modo de emergencia ya no publica el traceback (PR #27, #29, #30). `¤adpa`
- [x] **Arnés:** el Pilar 3 ya no marca falsos positivos en `.venv` (commit `de204e3`). `¤arbitro`
- [x] **Protección de `main`:** el check `Arnés Físico Determinista` es obligatorio para fusionar. `¤ci-cd`

#### 7.1 Índice de tareas

<!-- INDICE-TAREAS:INICIO (generado por scripts/generar_indice_tareas.py; no editar a mano) -->
**76 tareas.** El estado de cada una está en su especificación (`python scripts/generar_indice_tareas.py --estado`).

| ID | Tarea | Ola | Sala | Depende de |
| :--- | :--- | :--- | :--- | :--- |
| [FE-01](../tareas/FE-01.md) | Cliente de API y store del frontend | A | `frontend` | RM-00 |
| [RM-00](../tareas/RM-00.md) | Andamiaje compartido: contrato, autoregistro de routers, errores y una sola cabeza de migraciones | A | `pasillo_central` | — |
| [RM-01](../tareas/RM-01.md) | Reestructuración ADPA: salas Organización y Hoja de Ruta | A | `organizacion, roadmap` | — |
| [RM-02](../tareas/RM-02.md) | Sesión de BD única y cero SQL interpolado | A | `pasillo_central` | — |
| [RM-03](../tareas/RM-03.md) | Matriz de permisos como prueba | A | `pruebas` | — |
| [RM-14](../tareas/RM-14.md) | Tabla audit_events y registro de eventos | A | `pasillo_central` | — |
| [FE-02](../tareas/FE-02.md) | Formulario de variables de planeación y generación | B | `frontend` | FE-01 |
| [FE-03](../tareas/FE-03.md) | Vista de olas y tareas | B | `frontend` | FE-01 |
| [FE-04](../tareas/FE-04.md) | Panel de evidencia | B | `frontend` | FE-01 |
| [FE-05](../tareas/FE-05.md) | Administración de la organización | B | `frontend` | FE-01 |
| [RM-07](../tareas/RM-07.md) | Editar tareas de la hoja de ruta | B | `roadmap` | RM-00, RM-01 |
| [RM-08](../tareas/RM-08.md) | Distribuir tareas a los responsables | B | `roadmap` | RM-00, RM-01 |
| [RM-09](../tareas/RM-09.md) | Consultar el audit log | B | `roadmap` | RM-00, RM-01 |
| [RM-12](../tareas/RM-12.md) | Generación fiable con IA | B | `roadmap` | RM-01 |
| [RM-15](../tareas/RM-15.md) | Configuración de la organización y vocabulario de tamaños | B | `organizacion` | RM-01, RM-02, RM-14 |
| [RM-16](../tareas/RM-16.md) | Regla del encargado con rol de responsable según el tamaño | B | `organizacion` | RM-01, RM-00 |
| [SEC-03](../tareas/SEC-03.md) | Autenticación verificable con Google (OIDC) | B | `pasillo_central` | RM-01, RM-00, ENT-01, RM-02 |
| [ADPA-01](../tareas/ADPA-01.md) | Compuertas de las salas Derechos ARCO, Terceros y Transferencias | C | `derechos_arco, terceros, transferencias` | RM-02 |
| [RM-10](../tareas/RM-10.md) | Flujo de alta de responsables de área | C | `organizacion` | RM-01, RM-14, RM-16 |
| [RM-13](../tareas/RM-13.md) | Generación en línea (decisión D-1) | C | `roadmap` | RM-00, RM-12 |
| [DEV-01](../tareas/DEV-01.md) | Modo desarrollador para pruebas en físico: organización de demostración con un usuario por rol en una rama de desarrollo | D | `operaciones` | ORG-02, ORG-06, ORG-07, SEC-07 |
| [FE-06](../tareas/FE-06.md) | Integración del frontend | D | `frontend` | FE-02, FE-03, FE-04, FE-05 |
| [FE-07](../tareas/FE-07.md) | Inicio de sesión con Google en el frontend | D | `frontend` | SEC-03, FE-06 |
| [FE-08](../tareas/FE-08.md) | Una sola fuente del tamaño de la organización: ficha y backend | D | `frontend` | FE-07, FE-05, RM-15 |
| [FE-09](../tareas/FE-09.md) | Pestaña «Estructura» de la administración: unidades, cargos, jefaturas y vacantes | D | `frontend` | ORG-07, ORG-00, FE-05 |
| [FE-10](../tareas/FE-10.md) | Pantallas del operador de la plataforma y aceptación de invitaciones | D | `frontend` | ORG-09, FE-07 |
| [FE-11](../tareas/FE-11.md) | Pantallas de las designaciones formales del DPD y del coordinador | D | `frontend` | ORG-06, FE-09, LEG-01 |
| [FE-12](../tareas/FE-12.md) | Tarjeta de tarea legible en los dos temas y con el color de su dimensión | D | `frontend` | FE-03, ORG-00 |
| [LEG-01](../tareas/LEG-01.md) | Citas normativas de la interfaz coherentes con la LOPDP | D | `frontend` | — |
| [LEG-02](../tareas/LEG-02.md) | Norma técnica de notificación de vulneraciones: lectura del texto vinculante | D | `gobernanza` | — |
| [OPS-05](../tareas/OPS-05.md) | Guía de configuración del inicio de sesión con Google (local y producción) | D | `operaciones` | FE-07, SEC-03 |
| [ORG-00](../tareas/ORG-00.md) | Renombrar el rol «encargado» a «coordinador» (clave, datos, API e interfaz) | D | `organizacion` | RM-00, RM-01, RM-03, RM-07, RM-08, RM-09, RM-10, RM-13, RM-16, SEC-04, SEC-05, TEST-01, FE-01, FE-02, FE-03, FE-04, FE-05, FE-06, FE-07, FE-08 |
| [ORG-01](../tareas/ORG-01.md) | Una sola matriz de incompatibilidades de roles, con su base legal; el DPO sin roles operativos | D | `organizacion` | ORG-00, RM-01, RM-10, RM-16 |
| [ORG-02](../tareas/ORG-02.md) | Excepciones de separación de funciones, explícitas y con fin, en lugar de «permitido por tamaño» | D | `organizacion` | ORG-01, ORG-07, RM-10, RM-16 |
| [ORG-05](../tareas/ORG-05.md) | Un único camino de altas de roles; sin concesión a uno mismo | D | `organizacion` | ORG-02, RM-01, RM-10, SEC-03 |
| [ORG-06](../tareas/ORG-06.md) | Designaciones formales: delegado de protección de datos (con inscripción y declaración) y mandato de la alta dirección al coordinador | D | `organizacion` | ORG-01, ORG-07, RM-10 |
| [ORG-07](../tareas/ORG-07.md) | Estructura orgánica: unidades, cargos y jefaturas como base de los responsables de área | D | `organizacion` | ORG-00, RM-01, RM-10 |
| [ORG-08](../tareas/ORG-08.md) | Retirar el alias y los restos del rol «encargado»: el código como si «coordinador» siempre hubiera sido el nombre | D | `organizacion` | ORG-00, ORG-02, ORG-05, ORG-06, FE-05, SEC-03 |
| [ORG-09](../tareas/ORG-09.md) | Operador de la plataforma: alta de organizaciones e invitación del administrador inicial, sin acceso a los datos de los clientes | D | `plataforma` | DEV-01, SEC-03, SEC-07, ORG-00 |
| [ORG-10](../tareas/ORG-10.md) | El operador revoca cualquier invitación pendiente desde el listado y ve las caducadas como caducadas | D | `plataforma` | ORG-09, FE-10 |
| [ORG-11](../tareas/ORG-11.md) | Reemitir la invitación del administrador inicial mientras la organización no tenga administrador | D | `plataforma` | ORG-10 |
| [ORG-12](../tareas/ORG-12.md) | El coordinador fija el área de una tarea al distribuirla (las tareas generadas no la traen) | D | `roadmap` | RM-08, ORG-00, ORG-08, QA-06, FE-01, FE-03, FE-07, QA-01 |
| [QA-01](../tareas/QA-01.md) | Pruebas de punta a punta por rol | D | `frontend` | FE-06, RM-07, RM-08, RM-09, RM-10, RM-13, SEC-03, ORG-00 |
| [QA-02](../tareas/QA-02.md) | El entorno del arnés resuelve el intérprete del proyecto también dentro de un worktree | D | `operaciones` | QA-01 |
| [QA-03](../tareas/QA-03.md) | Auditoría de los criterios de aceptación del MVP frente a sus árbitros | D | `gobernanza` | — |
| [QA-04](../tareas/QA-04.md) | RLS demostrado en todas las tablas con datos de organización (criterio 11 del MVP) | D | `gobernanza` | QA-03 |
| [QA-05](../tareas/QA-05.md) | La matriz de permisos falla si queda una fila pendiente (criterio 10 del MVP) | D | `gobernanza` | QA-03, RM-03, ORG-00, ORG-02, ORG-07 |
| [QA-06](../tareas/QA-06.md) | Recorrido de la hoja de ruta por roles contra el backend y la base reales (criterio 12 del MVP) | D | `gobernanza` | QA-03 |
| [QA-07](../tareas/QA-07.md) | Árbitros de la ergonomía del dashboard y de la ficha organizacional previa (criterios 6 y 7 del MVP) | D | `frontend` | QA-03 |
| [QA-08](../tareas/QA-08.md) | Árbitro de la purga de evidencias al cambiar de normativa (criterio 8 del MVP) | D | `frontend` | QA-03 |
| [RM-17](../tareas/RM-17.md) | La generación de la hoja de ruta no falla porque la IA escriba «P01» en lugar de «P1» | D | `roadmap` | RM-01, RM-12, RM-13, RM-07, RM-08, RM-09 |
| [RM-18](../tareas/RM-18.md) | El proxy del frontend espera a la generación de la hoja de ruta (Next cortaba a los 30 s) | D | `roadmap, frontend` | RM-17, SEC-06 |
| [SEC-02](../tareas/SEC-02.md) | Auditoría de seguridad previa a producción | D | `gobernanza` | SEC-03, RM-10, RM-13, SEC-04, SEC-05, SEC-06 |
| [SEC-04](../tareas/SEC-04.md) | Evidencia filtrada por rol en la API | D | `roadmap` | RM-13 |
| [SEC-05](../tareas/SEC-05.md) | Validación de evidencia en el servidor y diseño del antivirus | D | `pasillo_central` | SEC-04, RM-00 |
| [SEC-06](../tareas/SEC-06.md) | Cabeceras HTTP de seguridad | D | `pasillo_central, frontend` | RM-13 |
| [SEC-07](../tareas/SEC-07.md) | Retirar la compatibilidad del token simulado en el modo headers | D | `pasillo_central` | SEC-03, FE-07, RM-02 |
| [SEC-08](../tareas/SEC-08.md) | ARCO+: reemplazar el router en memoria por el persistente, con identidad y aislamiento por tenant | D | `pasillo_central` | SEC-02, SEC-07, FE-07, ADPA-01, SEC-09 |
| [SEC-09](../tareas/SEC-09.md) | Recrear la tabla derechos_arco_solicitudes con RLS: el modelo ARCO+ no tiene tabla en la base | D | `derechos_arco` | SEC-02, ORG-07 |
| [SEC-10](../tareas/SEC-10.md) | Cerrar la llave maestra: credencial del dueño solo para migraciones, producción como lopdp_app y permisos mínimos en users y tenants | D | `gobernanza` | SEC-02, SEC-03 |
| [SEC-11](../tareas/SEC-11.md) | Comprobar desde fuera que producción exige el acceso con Google (AUTH_MODE) | D | `gobernanza` | SEC-03, OPS-03, ORG-09 |
| [TEST-03](../tareas/TEST-03.md) | Arnés de integración: el frontend contra el backend real | D | `frontend` | TEST-02, FE-07, SEC-07 |
| [TEST-04](../tareas/TEST-04.md) | Prueba de que cada ruta que llama el frontend existe en el backend | D | `pasillo_central` | FE-07 |
| [OPS-01](../tareas/OPS-01.md) | Variables de entorno en Vercel | E | `operaciones` | — |
| [OPS-02](../tareas/OPS-02.md) | Verificar la generación en el entorno gratuito | E | `operaciones` | RM-13, OPS-01 |
| [ENT-01](../tareas/ENT-01.md) | Un intérprete sin las dependencias detiene la suite con un solo mensaje | indep | `pruebas` | — |
| [GOB-01](../tareas/GOB-01.md) | Promover los rastros nuevos al VPA | indep | `gobernanza` | — |
| [GOB-02](../tareas/GOB-02.md) | Verificador de especificaciones de tareas | indep | `gobernanza` | — |
| [OPS-03](../tareas/OPS-03.md) | Script de verificación de despliegue | indep | `operaciones` | — |
| [OPS-04](../tareas/OPS-04.md) | Rama de Neon por agente de desarrollo | indep | `operaciones` | — |
| [TEST-02](../tareas/TEST-02.md) | Reparar el arnés de Playwright de la raíz y valorar ejecutarlo en el CI | indep | `pruebas` | — |
| [CI-01](../tareas/CI-01.md) | Exigir ramas al día en main (solo cuando haga falta) | backlog | `operaciones` | — |
| [ENT-02](../tareas/ENT-02.md) | Un solo punto de entrada fija el bucle de eventos compatible con psycopg en Windows | backlog | `operaciones` | RM-00, RM-02 |
| [FIRMA-01](../tareas/FIRMA-01.md) | Firma electrónica con ANF (boceto) | backlog | `firma_electronica` | — |
| [NOTIF-01](../tareas/NOTIF-01.md) | Notificaciones por correo (boceto) | backlog | `notificaciones` | RM-08 |
| [TEST-01](../tareas/TEST-01.md) | Cobertura pendiente de evidencia y Redis | backlog | `pruebas` | RM-01 |
<!-- INDICE-TAREAS:FIN -->
