# Tablero de Tareas y Control de Avance (`TASKS.md`)
`¤bbap`

> **MEMORIA OPERATIVA Y CONTROL DE EJECUCIÓN:**
> Este archivo registra las tareas pendientes, activas y completadas de **JUBYS Plataforma LOPDP 360**. Cada hito está anclado a su rastro estigmérgico (`¤`) y garantiza la trazabilidad del roadmap desde la Fase 0 (Discovery y Diseño) hasta el despliegue del MVP y módulos avanzados.

---

## Estado General del Proyecto
<!-- ¤adpa -->
* **Fase Actual:** `Fases 0–5 completadas; Fase 6 (NIIF 18) y Fase 7 (Hoja de Ruta Inteligente) en progreso`
* **Metodología de Desarrollo:** BBAP (Boceto ➔ Sellado) con Confinamiento en Salas ADPA.
* **Diseño Frontend:** Estilo Antigravity / Cursor (Clean IDE, Command Palette, Dark/Light mode).

---


<!-- ¤adpa/ -->

## 🎯 Plan de Trabajo por Fases
<!-- ¤adpa -->

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
**334 tareas.** El estado de cada una está en su especificación (`python scripts/generar_indice_tareas.py --estado`).

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
| [ADPA-02](../tareas/ADPA-02.md) | Reubicar ErrorNegocio en app_core/errors.py y prohibir imports features -> api | C | `auditoria_capa, biblioteca, dpo_cockpit, organizacion, rat, roadmap` | ADPA-01, BIB-112, CAPA-02, DIAG-08, DPO-02, ORG-13, ORG-14, ORG-16, RAT-06, RM-21, RM-24 |
| [ADPA-03](../tareas/ADPA-03.md) | Retirar deuda lateral ADPA lote 1 (auditoria_capa, plataforma, rat, ai_copilot) vía pasillo | C | `auditoria_capa, plataforma, rat, ai_copilot` | ADPA-02 |
| [ADPA-04](../tareas/ADPA-04.md) | Retirar deuda lateral ADPA lote 2 (riesgos_mtge, roadmap) y sellar DEUDA_LATERAL = 0 | C | `riesgos_mtge, roadmap` | ADPA-03, DIAG-08, DIAG-13, RM-23 |
| [ADPA-05](../tareas/ADPA-05.md) | Andamiar domain/errores.py por sala y secciones #ID en compuertas y routers compartidos | C | `auditoria_capa, derechos_arco, diagnostico, dpo_cockpit, evidencias, firma_electronica, incidentes, notificaciones, organizacion, rat, regulacion_rag, riesgos_mtge, roadmap, terceros, transferencias` | ADPA-04, NOTIF-01, FIRMA-01, INC-01 |
| [ADPA-06](../tareas/ADPA-06.md) | Andamiar módulos y secciones #ID en app_core/pasillo/ para integraciones entre salas pendientes | C | `pasillo_central` | ADPA-04, ADPA-05 |
| [ADPA-07](../tareas/ADPA-07.md) | Sembrar secciones #ID en registros y componentes Frontend compartidos para eliminar contención | C | `plataforma, diagnostico, evidencias, biblioteca` | FE-22, BIB-101, DIAG-09 |
| [ADPA-08](../tareas/ADPA-08.md) | Restaurar migración base de terceros_encargados y transferencias_terceros con RLS y separar salas | C | `terceros, transferencias` | SEC-09, ADPA-01, ADPA-05, ADPA-06, ADPA-10 |
| [ADPA-09](../tareas/ADPA-09.md) | Andamiar las salas faltantes del PRD §7.1 (features/formacion y features/conservacion) y sus pasillos | C | `formacion, conservacion` | ADPA-05, ADPA-06 |
| [ADPA-11](../tareas/ADPA-11.md) | Sembrar la sección #DIAG-14 alrededor de los botones de nivel y de evidencia en DiagnosticCanvas.tsx | C | `diagnostico` | ADPA-07, DIAG-03, DIAG-05, DIAG-09, FE-16, FE-26 |
| [API-02](../tareas/API-02.md) | API de integración versionada: claves por organización con alcance, contrato OpenAPI autenticado y webhooks firmados HMAC-SHA256 | C | `pasillo_central, frontend` | SEC-13, OPS-07 |
| [DER-03](../tareas/DER-03.md) | derechos_arco: crear_solicitud_arco respeta el tenant recibido, sin uuid4 ni commit propio | C | `derechos_arco` | ADPA-01, ADPA-05, RM-02, SEC-09 |
| [DIAG-14](../tareas/DIAG-14.md) | Diagnóstico: con un rol que no es DPO, los controles de nivel y de evidencia se muestran deshabilitados y explican por qué | C | `diagnostico, frontend` | ADPA-11, DIAG-03, DIAG-09, FE-16 |
| [GCP-01](../tareas/GCP-01.md) | Chasis Cloud Run ASGI, sesión RLS en 1 RTT con PgBouncer y Secret Manager ADC | C | `pasillo_central, operaciones` | RM-00, RM-02, ENT-02, ADPA-02 |
| [GCP-03](../tareas/GCP-03.md) | Migración del Frontend a Cloud Run: empaquetado standalone de Next.js, Dockerfile multi-stage y proxy regional | C | `frontend, operaciones` | GCP-01, FE-21, FE-22 |
| [GCP-04](../tareas/GCP-04.md) | Migración de Base de Datos y Enrutamiento Unificado: Cloud SQL PostgreSQL 16 con RLS forzado y Cloud Load Balancing | C | `pasillo_central, operaciones` | GCP-01, SEC-10 |
| [GCP-05](../tareas/GCP-05.md) | Escalado verificable en Cloud Run: límites de instancias, presupuesto de conexiones y prueba de carga | C | `operaciones` | GCP-01, GCP-03, GCP-04, GCP-08, GCP-09 |
| [GCP-06](../tareas/GCP-06.md) | Caché sin fuga entre organizaciones: Cloud CDN solo para activos estáticos y caché de lectura por tenant en Memorystore | C | `pasillo_central, operaciones` | GCP-04, GCP-05 |
| [GCP-07](../tareas/GCP-07.md) | Despliegue progresivo por revisiones de Cloud Run con reversión por SLO y verificador de migraciones compatibles (expand/contract) | C | `operaciones, pruebas` | GCP-03, GCP-04, OPS-07 |
| [OPS-07](../tareas/OPS-07.md) | Observabilidad: registro estructurado sin datos personales, errores, disponibilidad y alertas de gasto | C | `pasillo_central, operaciones` | GCP-01 |
| [RM-10](../tareas/RM-10.md) | Flujo de alta de responsables de área | C | `organizacion` | RM-01, RM-14, RM-16 |
| [RM-13](../tareas/RM-13.md) | Generación en línea (decisión D-1) | C | `roadmap` | RM-00, RM-12 |
| [API-01](../tareas/API-01.md) | Sin datos inventados cuando el servidor falla: el frontend muestra el error | D | `frontend` | MTGE-01, RAT-02, FE-11, LEG-01 |
| [BIB-100](../tareas/BIB-100.md) | PMV de Biblioteca: especificación, seguimiento y notas de entrega | D | `biblioteca, gobernanza` | — |
| [BIB-101](../tareas/BIB-101.md) | Contexto y acceso | D | `biblioteca, frontend, pasillo_central, organizacion` | BIB-105, FE-17, FE-10, FE-19, ORG-09, CAPA-01, FE-22 |
| [BIB-102](../tareas/BIB-102.md) | Catálogo y búsqueda | D | `biblioteca, frontend, pasillo_central` | BIB-101, BIB-109, BIB-111, BIB-112 |
| [BIB-103](../tareas/BIB-103.md) | Ficha de plantilla | D | `biblioteca, frontend, pasillo_central` | BIB-109, BIB-111, BIB-112 |
| [BIB-104](../tareas/BIB-104.md) | Descarga controlada | D | `biblioteca, frontend, pasillo_central` | BIB-105, BIB-111, BIB-112 |
| [BIB-106](../tareas/BIB-106.md) | Documentos externos del cliente | D | `biblioteca, frontend, pasillo_central` | BIB-107, BIB-111, BIB-112, BIB-115, CI-04, CI-16, TEST-03 |
| [BIB-107](../tareas/BIB-107.md) | Documentos por empresa | D | `biblioteca, frontend, pasillo_central` | BIB-101, BIB-109, BIB-112 |
| [BIB-109](../tareas/BIB-109.md) | Plantillas Markdown del PMV en el catálogo | D | `biblioteca, pasillo_central` | BIB-105, BIB-108 |
| [BIB-110](../tareas/BIB-110.md) | Biblioteca al cambiar de organización: caché, cambios pendientes y store de auditoría | D | `biblioteca, frontend` | ADPA-07, BIB-101, BIB-111, EVI-01, EVI-01b, FE-21 |
| [BIB-111](../tareas/BIB-111.md) | Registro de vistas de Biblioteca: un archivo por tarea, sin volver a tocar el workspace | D | `biblioteca, frontend` | BIB-101 |
| [BIB-112](../tareas/BIB-112.md) | Catálogo de errores de Biblioteca en su propia sala y secciones de la compuerta para todas las tareas pendientes | D | `biblioteca` | BIB-105, BIB-108, BIB-109 |
| [BIB-113](../tareas/BIB-113.md) | Pestaña «Documentos de la organización» (frontend) | D | `biblioteca, frontend` | BIB-111 |
| [BIB-114](../tareas/BIB-114.md) | Editor de borrador y captura de las variables de contexto (frontend) | D | `biblioteca, frontend` | BIB-111 |
| [BIB-115](../tareas/BIB-115.md) | Biblioteca envía la identidad completa: el cliente del frontend manda X-Role, y X-User-ID en desarrollo, porque todas sus rutas lo exigen | D | `biblioteca, frontend` | BIB-101, BIB-107, BIB-111, BIB-112, FE-07, BIB-102, BIB-113, BIB-114, BIB-203, BIB-204, BIB-205, BIB-206, BIB-207, BIB-301, BIB-302, BIB-303, BIB-402 |
| [BIB-116](../tareas/BIB-116.md) | El botón Biblioteca avisa cuando no pudo cargar el contador de pendientes | D | `biblioteca` | BIB-101, BIB-115 |
| [BIB-119](../tareas/BIB-119.md) | Administración editorial: sin salto al panel al recargar y capacidades que se reinician al cambiar de persona u organización | D | `biblioteca, frontend` | BIB-118 |
| [BIB-201](../tareas/BIB-201.md) | Formulario por versión | D | `biblioteca, frontend, pasillo_central` | BIB-101, BIB-109, ORG-14, RAT-01, BIB-112 |
| [BIB-202](../tareas/BIB-202.md) | Reutilización y procedencia | D | `biblioteca, frontend, pasillo_central` | BIB-201, DIAG-01, RAT-01, BIB-111, BIB-112 |
| [BIB-203](../tareas/BIB-203.md) | Tablas de captura | D | `biblioteca, frontend, pasillo_central` | BIB-201, BIB-111, BIB-112 |
| [BIB-204](../tareas/BIB-204.md) | Aplicabilidad explicable | D | `biblioteca, frontend, pasillo_central` | MTGE-01, BIB-111, BIB-112, ORG-14, RAT-01 |
| [BIB-205](../tareas/BIB-205.md) | Generación de Word y Excel | D | `biblioteca, frontend, pasillo_central` | BIB-201, BIB-203, BIB-111, BIB-112 |
| [BIB-206](../tareas/BIB-206.md) | Vista previa y fidelidad | D | `biblioteca, frontend, pasillo_central` | BIB-205, BIB-111, BIB-112 |
| [BIB-207](../tareas/BIB-207.md) | Concurrencia y trabajos de generación | D | `biblioteca, frontend, pasillo_central` | BIB-205, BIB-111, BIB-112 |
| [BIB-208](../tareas/BIB-208.md) | Cobertura de ocho fichas | D | `biblioteca, frontend, pasillo_central, rat, roadmap` | BIB-203, BIB-204, BIB-206, BIB-207, RM-19, BIB-111, BIB-112, ADPA-05, ADPA-06 |
| [BIB-301](../tareas/BIB-301.md) | Revisión y aprobación | D | `biblioteca, frontend, pasillo_central` | BIB-107, BIB-111, BIB-112 |
| [BIB-302](../tareas/BIB-302.md) | Integración con acciones | D | `biblioteca, frontend, pasillo_central, roadmap` | RM-19, BIB-107, BIB-111, BIB-112, ADPA-05, ADPA-06 |
| [BIB-303](../tareas/BIB-303.md) | Evidencias y verificación | D | `biblioteca, frontend, pasillo_central, roadmap` | BIB-302, RM-24, BIB-111, BIB-112, ADPA-05, ADPA-06 |
| [BIB-304](../tareas/BIB-304.md) | Actualización normativa y documental | D | `biblioteca, frontend, pasillo_central, notificaciones` | BIB-105, NOTIF-01, BIB-107, BIB-111, BIB-112, ADPA-05, ADPA-06 |
| [BIB-305](../tareas/BIB-305.md) | Indicadores verificables | D | `biblioteca, frontend, pasillo_central` | BIB-303, BIB-111, BIB-112 |
| [BIB-306](../tareas/BIB-306.md) | Historial y conservación | D | `biblioteca, frontend, pasillo_central` | BIB-107, BIB-111, BIB-112 |
| [BIB-307](../tareas/BIB-307.md) | Aceptación de extremo a extremo | D | `biblioteca, pruebas, gobernanza` | BIB-304, BIB-305, BIB-306, TEST-03 |
| [BIB-401](../tareas/BIB-401.md) | Plantillas de la cuenta profesional: tercera capa entre la maestra y la de la organización | D | `biblioteca, frontend` | BIB-103, ORG-15, BIB-111, BIB-112, ADPA-06, BIB-115, BIB-118, BIB-119 |
| [BIB-402](../tareas/BIB-402.md) | Documentos de la organización vinculados a tratamientos, controles y tareas; aviso al cambiar un tratamiento | D | `biblioteca, frontend` | BIB-107, BIB-302, RAT-05, BIB-111, BIB-112, ADPA-06 |
| [BOV-01](../tareas/BOV-01.md) | Sala Bóveda Cloud: paquetes de reventa de almacenamiento, cuotas de GB/Egress y aprovisionamiento Multi-Tenant | D | `boveda_cloud` | ADPA-06, ADPA-07, GCP-01, MARCA-01 |
| [BOV-02](../tareas/BOV-02.md) | Bóveda Dual en Google Cloud Storage (short-ttl Standard vs long-retention Autoclass WORM) e ingesta Direct-to-GCS | D | `boveda_cloud` | BOV-01 |
| [BOV-03](../tareas/BOV-03.md) | Carril Forense Dual: custodia del original intacto SHA-256 y derivados de previsualización WebP/AVIF/WebM | D | `boveda_cloud` | BOV-02 |
| [BOV-04](../tareas/BOV-04.md) | Orquestador Comercial de las 10 Dimensiones y Bóveda Cloud: centro de mando de automatizaciones, retenciones, actas SHA-256 y telemetría de paquete | D | `boveda_cloud` | BOV-03, CCTV-02, GOVW-01, GOCA-01, DLP-01, VTX-01 |
| [CAPA-01](../tareas/CAPA-01.md) | Acciones correctivas (CAPA) guardadas en la base y visibles en la sala de auditoría | D | `auditoria_capa, frontend` | DPO-01, LIM-01, RAT-01 |
| [CAPA-02](../tareas/CAPA-02.md) | Controles periódicos con frecuencia y responsable; el control vencido genera un hallazgo | D | `auditoria_capa, roadmap, frontend` | CAPA-01, RM-21, FE-22 |
| [CAPA-03](../tareas/CAPA-03.md) | La evidencia vencida reabre el control periódico y produce un hallazgo | D | `auditoria_capa` | CAPA-02, EVI-02, RM-21, ADPA-05, ADPA-06 |
| [CAPA-04](../tareas/CAPA-04.md) | Auditoría con grilla de verificación por dominio y acta por área, con hallazgos al plan de acción | D | `auditoria_capa, frontend` | CAPA-02, RM-21, EVI-02, DIAG-03, ADPA-05, ADPA-06, ADPA-07 |
| [CCTV-01](../tareas/CCTV-01.md) | Sala Videovigilancia LOPDP: inventario de cámaras/NVR, auditoría de perfil técnico (H.265, eventos, sin audio, máscaras) y retención de 15 días | D | `videovigilancia` | ADPA-06, ADPA-07, BOV-01, MARCA-01 |
| [CCTV-02](../tareas/CCTV-02.md) | Congelamiento Forense (Hold Legal) de clips de videovigilancia por incidente o derecho ARCOP y actas quincenales de destrucción SHA-256 | D | `videovigilancia` | CCTV-01, BOV-02, CON-01 |
| [CI-16](../tareas/CI-16.md) | Ninguna prueba de interfaz queda fuera de todos los proyectos del CI | D | `pasillo_central` | CI-04, TEST-03, BIB-104 |
| [CI-19](../tareas/CI-19.md) | Árbitro de alcance: ramas con sufijo y retiro de las exenciones propias | D | `gobernanza` | — |
| [CON-01](../tareas/CON-01.md) | Sala Conservación y Bloqueo: políticas de retención, purga/anonimización e integración con RAT y DPO Cockpit | D | `conservacion` | ADPA-07, ADPA-09, RAT-07, MARCA-01 |
| [DEMO-00](../tareas/DEMO-00.md) | Contrato de la sala demo: compuerta, dominio, repositorio, pasillo y migración | D | `demo` | EP-01, GCP-04, SEC-10, CI-11, DEMO-04, FE-26 |
| [DEMO-01](../tareas/DEMO-01.md) | Persona activa y «Ver como»: resolver, 403 si es ajena y auditoría con el vendedor real | D | `demo` | DEMO-00, DEMO-08, EP-01 |
| [DEMO-02](../tareas/DEMO-02.md) | Ciclo de sesión demo: entrar, tope, reemplazo, terminar, vencimiento y orquestador de la copia | D | `demo` | DEMO-00, DEMO-08, DEMO-03, DEMO-03a, DEMO-03b, DEMO-03c, DEMO-03d, GCP-01 |
| [DEMO-03](../tareas/DEMO-03.md) | Siembra de la plantilla «Cooperativa Demo» con cinco personas ficticias (el auditor lo añade ORG-22) | D | `operaciones` | DEMO-00, EP-03, SEC-13a, SEC-13b |
| [DEMO-03a](../tareas/DEMO-03a.md) | Clonar desde plantilla en la sala organizacion | D | `organizacion` | ADPA-06, ADPA-10, DEMO-00 |
| [DEMO-03b](../tareas/DEMO-03b.md) | Clonar desde plantilla en la sala diagnostico | D | `diagnostico` | DEMO-00, ADPA-06 |
| [DEMO-03c](../tareas/DEMO-03c.md) | Clonar desde plantilla en la sala roadmap | D | `roadmap` | ADPA-06, ADPA-10, DEMO-00 |
| [DEMO-03d](../tareas/DEMO-03d.md) | Clonar desde plantilla en la sala biblioteca | D | `biblioteca` | DEMO-00, ADPA-06 |
| [DEMO-03e](../tareas/DEMO-03e.md) | Clonar desde plantilla en la sala evidencias | D | `evidencias` | DEMO-00, ADPA-06, EVI-01 |
| [DEMO-03f](../tareas/DEMO-03f.md) | Clonar desde plantilla en la sala videovigilancia | D | `videovigilancia` | DEMO-00, ADPA-06 |
| [DEMO-04](../tareas/DEMO-04.md) | Interfaz demo: «Ver como» con seis personas, «Terminar demo» y pantallas de error | D | `frontend` | EP-02, FE-10, FE-19, BIB-115 |
| [DEMO-05](../tareas/DEMO-05.md) | Cloud Run Job de purga nocturna: filas y objetos de las demos vencidas | D | `operaciones` | DEMO-00, EP-01 |
| [DEMO-06](../tareas/DEMO-06.md) | Prueba de que con APP_ENV=demo no sale ningún correo | D | `pruebas` | EP-08 |
| [DEMO-07](../tareas/DEMO-07.md) | Infraestructura de la demo en Google Cloud (personas, sin agente) | D | `operaciones` | DEMO-02, DEMO-04, DEMO-05, DEMO-06, GCP-01, GCP-03, GCP-04 |
| [DEMO-08](../tareas/DEMO-08.md) | Gancho de identidad demo en usuario_verificado() | D | `pasillo_central` | DEMO-00, EP-01, SEC-15 |
| [DER-01](../tareas/DER-01.md) | Solicitudes de titulares: verificación de identidad, modelos de respuesta y la respuesta como evidencia | D | `derechos_arco, frontend` | EVI-02, FE-22, ADPA-05, ADPA-06, DER-03, DER-05, DER-06a, DER-06b |
| [DER-02](../tareas/DER-02.md) | Portal público de solicitudes de titulares por organización, con enlace de seguimiento | D | `derechos_arco, frontend` | DER-01, DER-06b, SEC-12, ADPA-05, DER-03 |
| [DEV-01](../tareas/DEV-01.md) | Modo desarrollador para pruebas en físico: organización de demostración con un usuario por rol en una rama de desarrollo | D | `operaciones` | ORG-02, ORG-06, ORG-07, SEC-07 |
| [DIAG-01](../tareas/DIAG-01.md) | El diagnóstico se guarda en el servidor por organización (hoy solo vive en el navegador) | D | `diagnostico, frontend` | QA-04, ENT-02, RM-00 |
| [DIAG-02](../tareas/DIAG-02.md) | El banco de 80 preguntas de la plataforma vive en el servidor (hoy el backend usa 48 preguntas de relleno) | D | `diagnostico` | DIAG-01, MTGE-01, RAT-01 |
| [DIAG-03](../tareas/DIAG-03.md) | El DPO responde y sella el diagnóstico; el resultado sellado se guarda en la base por organización y no se puede editar ni borrar | D | `diagnostico, frontend` | CAPA-01, DIAG-01, DIAG-02, FE-16, FE-17, FE-20, TEST-02, QA-08 |
| [DIAG-04](../tareas/DIAG-04.md) | El administrador asigna los dominios del assessment a encargados del diagnóstico | D | `diagnostico, frontend` | DIAG-03, ORG-07, ORG-14, FE-22, RM-21, DIAG-09, ADPA-05, ADPA-06 |
| [DIAG-05](../tareas/DIAG-05.md) | «No aplica» exige justificación en el assessment | D | `diagnostico, frontend` | DIAG-01, DIAG-03, DIAG-08, DIAG-09, ADPA-05, ADPA-07 |
| [DIAG-06](../tareas/DIAG-06.md) | Comparativo de un assessment con la línea base, por dimensión y dominio | D | `diagnostico, frontend` | DIAG-03, FE-22, FE-24, DIAG-08, ADPA-05, DIAG-11 |
| [DIAG-07](../tareas/DIAG-07.md) | Responden el administrador y los encargados del diagnóstico; el DPO revisa con la grilla declarado/verificado, objeta y sella | D | `diagnostico, frontend` | DIAG-04, DIAG-05, ADPA-05, ADPA-06, ADPA-07, ADPA-11, DIAG-07a, DIAG-07b, DIAG-14, EVI-01b |
| [DIAG-07a](../tareas/DIAG-07a.md) | El administrador puede guardar respuestas del diagnóstico (escritura transitoria) | D | `diagnostico` | ADPA-05, DIAG-01, DIAG-03, DIAG-05, DIAG-08 |
| [DIAG-07b](../tareas/DIAG-07b.md) | Las pruebas de pytest siembran las respuestas del diagnóstico como administrador | D | `pruebas` | DIAG-07a, DIAG-01, DIAG-03, DIAG-05, DIAG-06, DIAG-08, DIAG-11, DIAG-13, EVI-01, RM-21 |
| [DIAG-08](../tareas/DIAG-08.md) | Escala SMARTCIDI en el servidor: nivel asignado 1 a 5 y evidencia 0 a 4 por control, nivel por dimensión y sin cifra global de la organización | D | `diagnostico` | DIAG-03, DIAG-02, DIAG-01, RM-21 |
| [DIAG-09](../tareas/DIAG-09.md) | Escala SMARTCIDI en la pantalla: responder el nivel 1 a 5 con su criterio y la evidencia 0 a 4, y retirar el porcentaje global del panel ejecutivo | D | `frontend` | DIAG-08, DIAG-10, FE-17, FE-22 |
| [DIAG-10](../tareas/DIAG-10.md) | Escala de madurez como fuente única: contrato SMARTCIDI, doctrina alineada y árbitro de consumidores | D | `diagnostico` | RM-00 |
| [DIAG-11](../tareas/DIAG-11.md) | Diagnóstico de prueba y diagnóstico real: el diagnóstico se sella dos veces como máximo y el real es la línea base | D | `diagnostico, frontend` | DIAG-03, DIAG-08, ADPA-05, ADPA-06, ADPA-07, DIAG-13, ADPA-11, ADPA-10 |
| [DIAG-12](../tareas/DIAG-12.md) | Estados: el assessment actual, como cortes sellados que parten del diagnóstico real y suman las tareas cerradas con evidencia validada | D | `diagnostico, frontend` | DIAG-11, DIAG-06, EVI-01, ADPA-05, ADPA-06, ADPA-07 |
| [DIAG-13](../tareas/DIAG-13.md) | PMV: el sello conserva la evidencia declarada por el DPO, marcada como no verificada, en lugar de sellarla como E0 | D | `diagnostico` | DIAG-02, DIAG-03, DIAG-08, DIAG-10, RM-19 |
| [DLP-01](../tareas/DLP-01.md) | Sala Descubrimiento DLP Muestreado: escaneo de archivos y tablas con Cloud DLP Sampling y validador Módulo 10 para poblar el RAT | D | `dlp_discovery` | ADPA-06, ADPA-07, GCP-01, MARCA-01 |
| [DPO-01](../tareas/DPO-01.md) | La bitácora del DPO se guarda en la base, con permisos por rol y cadena de huellas por organización | D | `dpo_cockpit, frontend` | MTGE-02, API-01, ORG-06, FE-17, DIAG-02 |
| [DPO-02](../tareas/DPO-02.md) | Informe anual del DPO generado desde su bitácora y estado de inscripción ante la SPDP | D | `dpo_cockpit, frontend` | DPO-01, FE-17 |
| [DPO-03](../tareas/DPO-03.md) | Consultas de la organización al DPO con historial como evidencia de asesoría | D | `dpo_cockpit, frontend` | DPO-02, EVI-02, ADPA-05, ADPA-06, ADPA-07, ADPA-09 |
| [EVI-02](../tareas/EVI-02.md) | Vigencia y visibilidad de las evidencias y paquete para inspección ordenado por requisito | D | `evidencias, frontend` | ADPA-05, ADPA-07, EVI-01, EVI-01b |
| [FE-06](../tareas/FE-06.md) | Integración del frontend | D | `frontend` | FE-02, FE-03, FE-04, FE-05 |
| [FE-07](../tareas/FE-07.md) | Inicio de sesión con Google en el frontend | D | `frontend` | SEC-03, FE-06 |
| [FE-08](../tareas/FE-08.md) | Una sola fuente del tamaño de la organización: ficha y backend | D | `frontend` | FE-07, FE-05, RM-15 |
| [FE-09](../tareas/FE-09.md) | Pestaña «Estructura» de la administración: unidades, cargos, jefaturas y vacantes | D | `frontend` | ORG-07, ORG-00, FE-05 |
| [FE-10](../tareas/FE-10.md) | Pantallas del operador de la plataforma y aceptación de invitaciones | D | `frontend` | ORG-09, FE-07 |
| [FE-11](../tareas/FE-11.md) | Pantallas de las designaciones formales del DPD y del coordinador | D | `frontend` | ORG-06, FE-09, LEG-01 |
| [FE-12](../tareas/FE-12.md) | Tarjeta de tarea legible en los dos temas y con el color de su dimensión | D | `frontend` | FE-03, ORG-00 |
| [FE-13](../tareas/FE-13.md) | Panel de administración legible en los dos temas, con variables de superficie compartidas | D | `frontend` | FE-05, FE-08, FE-09, FE-11, ORG-00, FE-12 |
| [FE-14](../tareas/FE-14.md) | El tamaño de los paneles y el tema se conservan al recargar | D | `frontend` | DIAG-01, QA-07, FE-06, FE-07, FE-19 |
| [FE-15](../tareas/FE-15.md) | Pantallas de la hoja de ruta legibles en los dos temas | D | `frontend` | RM-20, FE-13 |
| [FE-16](../tareas/FE-16.md) | Diagnóstico, configuración y preanálisis legibles en los dos temas | D | `frontend` | FE-15, QA-07, API-01 |
| [FE-17](../tareas/FE-17.md) | Marco del dashboard y demás módulos legibles en los dos temas | D | `frontend` | FE-15, FE-14, SEC-08, MTGE-01, FE-19, API-01, MTGE-02 |
| [FE-18](../tareas/FE-18.md) | Sin colores fijos del tema oscuro: se retira la lista de excepciones del tema claro y un árbitro lo vigila | D | `frontend` | FE-15, FE-16, FE-17, FE-13 |
| [FE-19](../tareas/FE-19.md) | Marca EVYDENTIA en el encabezado y división del panel en encabezado, navegación y vista de hoja de ruta | D | `frontend` | FE-06, FE-07 |
| [FE-20](../tareas/FE-20.md) | Los datos de trabajo del navegador pertenecen a quien los creó: otra persona entra a un panel vacío y nada ajeno se sube al servidor | D | `frontend` | FE-07, DIAG-01 |
| [FE-21](../tareas/FE-21.md) | Quien pertenece a varias organizaciones elige con cuál trabajar y puede cambiar; la organización deja de fijarse por despliegue | D | `frontend` | ORG-13, FE-20 |
| [FE-22](../tareas/FE-22.md) | Navegación por los nueve menús de la estructura funcional, con submenús, y Ctrl+K sobre todas las pantallas | D | `frontend` | FE-17, FE-19, FE-14, FE-06, FE-07, CAPA-01, TEST-02, FE-21, DIAG-03, TEST-03 |
| [FE-23](../tareas/FE-23.md) | Un solo patrón de asistente (progreso, guardado, saltar pasos) para los flujos guiados | D | `frontend` | FE-17 |
| [FE-24](../tareas/FE-24.md) | Tablero de la organización con las cuatro dimensiones y las brechas críticas, sin cifra única | D | `frontend` | FE-17, DIAG-03, DIAG-08 |
| [FE-25](../tareas/FE-25.md) | Ficha resumen de la organización fija bajo la barra superior, con las cuatro dimensiones y las alertas abiertas | D | `frontend` | FE-22, FE-24, ORG-15, RM-21, ADPA-07 |
| [FE-26](../tareas/FE-26.md) | PMV sin subida de archivos: la pantalla no ofrece adjuntar evidencia al diagnóstico ni la custodia de la hoja de ruta, y el servidor rechaza esas subidas | D | `frontend, roadmap` | DIAG-13, FE-16, FE-22, RM-24, SEC-05, DIAG-09, FE-18, BIB-101, CAPA-02, CI-11, ORG-16 |
| [FIRMA-02](../tareas/FIRMA-02.md) | Aceptación simple con acuse (nombre, correo, fecha, IP y sello hash) y verificación de documentos por hash | D | `firma_electronica, frontend` | ADPA-05, ADPA-06, ADPA-07, BIB-107, EVI-01b, EVI-02, FE-27, FIRMA-01 |
| [FOR-01](../tareas/FOR-01.md) | Formación: contenidos, acciones formativas con examen y seguimiento por persona como evidencia de capacitación | D | `formacion, frontend` | ORG-17, EVI-02, FE-22, ADPA-06, ADPA-07, ADPA-09 |
| [GCP-08](../tareas/GCP-08.md) | Frontend en Cloud Run: proxy de /api/v1 con BACKEND_URL leída en cada petición, /health e imagen de menos de 120 MB | D | `frontend, operaciones` | GCP-03 |
| [GOB-03](../tareas/GOB-03.md) | Kit y documentación de Biblioteca versionados | D | `gobernanza, biblioteca` | ORG-01, ORG-08, SEC-02, BIB-105 |
| [GOB-04](../tareas/GOB-04.md) | Flujo de trabajo en equipo: rama desde la punta remota, ciclo diario, dos carpetas de worktrees y un solo escritor de gobernanza | D | `gobernanza` | — |
| [GOCA-01](../tareas/GOCA-01.md) | Agente Edge en Go (services_go/cctv_agent): conector local de cámaras/NVR con recorte por eventos H.265, supresión de audio y subida directa TLS a GCS | D | `go_cctv_agent` | CCTV-01, BOV-02 |
| [GOVW-01](../tareas/GOVW-01.md) | Microservicio en Go (services_go/vault_worker): receptor Eventarc, hashing SHA-256 en streaming y purga masiva en Cloud Run | D | `go_vault_worker` | GCP-01, BOV-01, CON-01, ADPA-09 |
| [INC-01](../tareas/INC-01.md) | La bitácora de incidentes se guarda en la base por organización, con permisos por rol, y deja de mostrar un plazo legal que no está en la ley | D | `incidentes, frontend` | CAPA-01, DPO-01, FE-17, FE-20, LEG-02 |
| [INC-02](../tareas/INC-02.md) | Asistente de vulneración en ocho secciones con decisión de notificar e informes de la norma técnica | D | `incidentes, frontend` | INC-01, FE-23, RM-21, EVI-02, ADPA-05, ADPA-06, ADPA-07 |
| [LEG-01](../tareas/LEG-01.md) | Citas normativas de la interfaz coherentes con la LOPDP | D | `frontend` | — |
| [LEG-02](../tareas/LEG-02.md) | Norma técnica de notificación de vulneraciones: lectura del texto vinculante | D | `gobernanza` | — |
| [LIM-01](../tareas/LIM-01.md) | Se retiran el módulo de diagnóstico y el panel de copiloto antiguos, que nadie monta | D | `frontend` | API-01, FE-17, FE-16 |
| [MTGE-01](../tareas/MTGE-01.md) | Cálculo de gran escala conforme al texto vinculante de la Res. SPDP-SPD-2026-0005-R | D | `riesgos_mtge, frontend` | FE-06, FE-07, LEG-01, SEC-02, SEC-08, RAT-01 |
| [MTGE-02](../tareas/MTGE-02.md) | Obligaciones del tratamiento a gran escala: auditoría anual, informe anual, política de privacidad y plazo del DPO | D | `riesgos_mtge, frontend` | MTGE-01, RAT-01, ENT-02, RM-00 |
| [MTGE-03](../tareas/MTGE-03.md) | EIPD guiada de ocho pasos con asistente de obligatoriedad, decisión documentada e informe final | D | `riesgos_mtge, frontend` | MTGE-02, FE-23, RM-21, EVI-02, ADPA-05, ADPA-06, ADPA-07 |
| [NORM-01](../tareas/NORM-01.md) | Sala Inteligencia Normativa: modelos, conector resiliente a la SPDP, validación SHA-256 y custodia del original | D | `inteligencia_normativa` | ADPA-05, ADPA-06, GCP-01 |
| [NORM-02](../tareas/NORM-02.md) | Centro de Vigilancia Normativa: catálogo de resoluciones SPDP, filtros, visor PDF, disparo manual, bitácora y avisos | D | `inteligencia_normativa, frontend` | NORM-01, NOTIF-01, FE-22 |
| [NORM-03](../tareas/NORM-03.md) | Análisis de impacto de una resolución con Gemini, validado por persona, y regeneración de la caché de contexto | D | `inteligencia_normativa, ai_copilot` | NORM-01, VTX-01 |
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
| [ORG-13](../tareas/ORG-13.md) | Una persona pertenece a varias organizaciones solo como DPO o implementador, y puede consultar las suyas | D | `organizacion, plataforma` | CAPA-01, ORG-10, ORG-11, ORG-12, ORG-00, ORG-02, ORG-07, QA-05, RM-03, RM-20 |
| [ORG-15](../tareas/ORG-15.md) | Cartera de organizaciones por pertenencia, con semáforos por dimensión y sin abrir la RLS | D | `organizacion, frontend` | ORG-13, ORG-14, FE-21, FE-22, FE-24, RM-21, DIAG-08, ADPA-05, ADPA-06 |
| [ORG-16](../tareas/ORG-16.md) | Alta de la organización en el servidor con el asistente de siete pasos, en lugar de la configuración local | D | `organizacion, frontend` | ORG-14, ORG-07, FE-08, FE-16, FE-22, FE-23, RM-21, CAPA-02 |
| [ORG-17](../tareas/ORG-17.md) | Inventario de activos y sistemas, soportes y personas mínimas de la organización | D | `organizacion, frontend` | ORG-07, FE-22, ORG-16, RM-21, ADPA-05, ADPA-06, CI-04, CI-16, BIB-106, BIB-118, BIB-119, TEST-03 |
| [ORG-18](../tareas/ORG-18.md) | Sedes de la organización y clientes cuando actúa como encargada | D | `organizacion, frontend` | ORG-16, ORG-17, ADPA-05, ADPA-06, ADPA-07, CI-04, CI-16, BIB-106, BIB-118, BIB-119, TEST-03 |
| [ORG-20](../tareas/ORG-20.md) | Papelera (archivar y restaurar) y exportación completa de los datos de la organización | D | `organizacion, plataforma, frontend` | ORG-17, EVI-02, ADPA-05, ADPA-06, ADPA-07 |
| [ORG-21](../tareas/ORG-21.md) | El operador de la plataforma entra aunque no pertenezca a ninguna organización | D | `plataforma` | ORG-09, ORG-11, FE-07, FE-10, FE-20, FE-21, BIB-115 |
| [QA-01](../tareas/QA-01.md) | Pruebas de punta a punta por rol | D | `frontend` | FE-06, RM-07, RM-08, RM-09, RM-10, RM-13, SEC-03, ORG-00 |
| [QA-02](../tareas/QA-02.md) | El entorno del arnés resuelve el intérprete del proyecto también dentro de un worktree | D | `operaciones` | QA-01 |
| [QA-03](../tareas/QA-03.md) | Auditoría de los criterios de aceptación del MVP frente a sus árbitros | D | `gobernanza` | — |
| [QA-04](../tareas/QA-04.md) | RLS demostrado en todas las tablas con datos de organización (criterio 11 del MVP) | D | `gobernanza` | QA-03 |
| [QA-05](../tareas/QA-05.md) | La matriz de permisos falla si queda una fila pendiente (criterio 10 del MVP) | D | `gobernanza` | QA-03, RM-03, ORG-00, ORG-02, ORG-07 |
| [QA-06](../tareas/QA-06.md) | Recorrido de la hoja de ruta por roles contra el backend y la base reales (criterio 12 del MVP) | D | `gobernanza` | QA-03 |
| [QA-07](../tareas/QA-07.md) | Árbitros de la ergonomía del dashboard y de la ficha organizacional previa (criterios 6 y 7 del MVP) | D | `frontend` | QA-03 |
| [QA-08](../tareas/QA-08.md) | Árbitro de la purga de evidencias al cambiar de normativa (criterio 8 del MVP) | D | `frontend` | QA-03 |
| [RAT-01](../tareas/RAT-01.md) | El RAT se guarda en el servidor por organización y con los campos de un RAT completo | D | `rat` | QA-04, ORG-00, RM-00, RM-13 |
| [RAT-02](../tareas/RAT-02.md) | Plantilla sectorial de salud: el RAT arranca de un catálogo de establecimientos de salud | D | `rat, frontend` | RAT-01, DIAG-01, ENT-02, RM-00 |
| [RAT-03](../tareas/RAT-03.md) | EIPD persistida por actividad del RAT, con matriz de probabilidad e impacto 5x5 | D | `rat` | RAT-01, ENT-02, RM-00 |
| [RAT-04](../tareas/RAT-04.md) | Retirar el RAT paralelo guardado en un archivo JSON del frontend | D | `frontend` | RAT-01, MTGE-01 |
| [RAT-05](../tareas/RAT-05.md) | Validaciones del RAT por regla y versionado de cada ficha de tratamiento | D | `rat` | RAT-04, RM-21, RAT-03, CAPA-02, DIAG-08 |
| [RAT-06](../tareas/RAT-06.md) | Exportación completa del RAT a XLSX y PDF con la versión vigente de cada ficha | D | `rat` | RAT-05 |
| [RAT-07](../tareas/RAT-07.md) | Colectivos de titulares y registro de consentimientos por finalidad, sin base de titulares | D | `rat` | RAT-05, EVI-02, ADPA-05, ADPA-06 |
| [REG-02](../tareas/REG-02.md) | Centro de conocimiento: normativa de Ecuador, resúmenes y ayuda contextual que cita la base legal | D | `regulacion_rag, frontend` | FE-22 |
| [RM-17](../tareas/RM-17.md) | La generación de la hoja de ruta no falla porque la IA escriba «P01» en lugar de «P1» | D | `roadmap` | RM-01, RM-12, RM-13, RM-07, RM-08, RM-09 |
| [RM-18](../tareas/RM-18.md) | El proxy del frontend espera a la generación de la hoja de ruta (Next cortaba a los 30 s) | D | `roadmap, frontend` | RM-17, SEC-06 |
| [RM-19](../tareas/RM-19.md) | La IA genera la hoja de ruta con el diagnóstico y el RAT reales; catálogo P1-P80 = las 80 preguntas del banco de la plataforma | D | `roadmap, diagnostico, frontend` | DIAG-01, RAT-01, RM-17, DIAG-02, QA-06, ORG-12 |
| [RM-20](../tareas/RM-20.md) | Informe PDF del estado de la implementación, por rol y para constancia | D | `roadmap, frontend` | ORG-12, FE-03, FE-12, ENT-02, RM-00, QA-05 |
| [RM-21](../tareas/RM-21.md) | Hallazgos con origen y una sola compuerta que convierte hallazgos en tareas del plan de acción | D | `roadmap` | RM-20, RM-19, DIAG-03, ORG-14, BIB-109 |
| [RM-22](../tareas/RM-22.md) | Vistas de lista, tablero y cronograma de las tareas, con su hallazgo de origen y las vencidas | D | `roadmap, frontend` | RM-21, FE-12, FE-15, RM-20, ORG-12, DIAG-08 |
| [RM-23](../tareas/RM-23.md) | Cierre automático de hallazgos y recordatorios de vencimiento de tareas por correo | D | `roadmap, notificaciones` | RM-21, NOTIF-01 |
| [SEC-02](../tareas/SEC-02.md) | Auditoría de seguridad previa a producción | D | `gobernanza` | SEC-03, RM-10, RM-13, SEC-04, SEC-05, SEC-06 |
| [SEC-04](../tareas/SEC-04.md) | Evidencia filtrada por rol en la API | D | `roadmap` | RM-13 |
| [SEC-05](../tareas/SEC-05.md) | Validación de evidencia en el servidor y diseño del antivirus | D | `pasillo_central` | SEC-04, RM-00 |
| [SEC-06](../tareas/SEC-06.md) | Cabeceras HTTP de seguridad | D | `pasillo_central, frontend` | RM-13 |
| [SEC-07](../tareas/SEC-07.md) | Retirar la compatibilidad del token simulado en el modo headers | D | `pasillo_central` | SEC-03, FE-07, RM-02 |
| [SEC-08](../tareas/SEC-08.md) | ARCO+: reemplazar el router en memoria por el persistente, con identidad y aislamiento por tenant | D | `pasillo_central` | SEC-02, SEC-07, FE-07, ADPA-01, SEC-09 |
| [SEC-09](../tareas/SEC-09.md) | Recrear la tabla derechos_arco_solicitudes con RLS: el modelo ARCO+ no tiene tabla en la base | D | `derechos_arco` | SEC-02, ORG-07 |
| [SEC-10](../tareas/SEC-10.md) | Cerrar la llave maestra: credencial del dueño solo para migraciones, producción como lopdp_app y permisos mínimos en users y tenants | D | `gobernanza` | SEC-02, SEC-03 |
| [SEC-11](../tareas/SEC-11.md) | Comprobar desde fuera que producción exige el acceso con Google (AUTH_MODE) | D | `gobernanza` | SEC-03, OPS-03, ORG-09 |
| [SEC-12](../tareas/SEC-12.md) | Diseño de seguridad de los portales externos (titulares y encargados) antes de implementarlos | D | `gobernanza` | — |
| [SEC-13](../tareas/SEC-13.md) | Límite de peticiones en la API por IP, usuario y organización, con tope de gasto de IA | D | `pasillo_central` | ENT-02, SEC-03, SEC-10 |
| [SEC-13a](../tareas/SEC-13a.md) | Tope total de generaciones de IA por organización, configurable por tenant | D | `pasillo_central` | SEC-13 |
| [SEC-13b](../tareas/SEC-13b.md) | Alta idempotente del tope de IA por organización: fijar_tope en la compuerta de límites | D | `pasillo_central` | SEC-13a |
| [SEC-15](../tareas/SEC-15.md) | Guarda de arranque: el backend no arranca en modo de cabeceras contra la base de producción ni en la nube | D | `pasillo_central` | SEC-03, SEC-07, DEV-01, RM-00, ENT-02 |
| [SEC-16](../tareas/SEC-16.md) | Secretos obligatorios en la nube: el backend no arranca con JWT_SECRET o SESSION_SECRET por defecto | D | `pasillo_central, biblioteca` | SEC-15, FIRMA-06, BIB-104, SEC-06, RM-13 |
| [SEC-17](../tareas/SEC-17.md) | Configuración mínima en la nube: DATABASE_URL de PostgreSQL con lopdp_app y CORS_ORIGINS explícito, sin valores por defecto | D | `pasillo_central` | SEC-15, SEC-16, FIRMA-06, SEC-06, RM-13 |
| [SEC-19](../tareas/SEC-19.md) | La descarga con token exige sesión, y el token es de quien la usa | D | `biblioteca, frontend` | BIB-112, CI-16 |
| [TER-01](../tareas/TER-01.md) | Hallazgos automáticos de terceros: encargado sin contrato vigente y transferencia internacional sin garantía | D | `terceros, transferencias` | RM-21, EVI-02, ADPA-05, ADPA-06, ADPA-08, FE-28 |
| [TER-02](../tareas/TER-02.md) | Cuestionario de garantías del encargado por portal externo, con revisión e informe | D | `terceros, frontend` | TER-01, SEC-12, FE-23, ADPA-05, ADPA-06, ADPA-08 |
| [TEST-03](../tareas/TEST-03.md) | Arnés de integración: el frontend contra el backend real | D | `frontend` | TEST-02, FE-07, SEC-07 |
| [TEST-04](../tareas/TEST-04.md) | Prueba de que cada ruta que llama el frontend existe en el backend | D | `pasillo_central` | FE-07 |
| [VTX-01](../tareas/VTX-01.md) | Vertex AI Context Caching sobre el corpus normativo LOPDP/SPDP e inferencia con filtro DLP pre-vuelo | D | `regulacion_rag, ai_copilot` | ADPA-03, ADPA-05, ADPA-06, GCP-01, IA-03, REG-02, RM-02, SEC-03 |
| [OPS-01](../tareas/OPS-01.md) | Variables de entorno en Vercel | E | `operaciones` | — |
| [OPS-02](../tareas/OPS-02.md) | Verificar la generación en el entorno gratuito | E | `operaciones` | RM-13, OPS-01 |
| [ADPA-10](../tareas/ADPA-10.md) | La propiedad de cada ficha se comprueba contra el árbol: existe, la crea ella o la crea y siembra una ancestro | indep | `gobernanza` | GOB-02 |
| [BIB-117](../tareas/BIB-117.md) | Conceder y revocar capacidades de la Biblioteca con un script de desarrollo (sin endpoint) | indep | `biblioteca` | BIB-109, BIB-112, BIB-102, BIB-103, BIB-104, BIB-106, BIB-107, BIB-118, BIB-201, BIB-307, ORG-14, RM-21, SEC-18, SEC-19 |
| [BIB-118](../tareas/BIB-118.md) | Menú «Administración editorial» visible solo con capacidades, y GET de capacidades propias | indep | `biblioteca, frontend` | BIB-109, BIB-105, BIB-112, FE-22, FE-26, BIB-106, CI-04, CI-11, CI-16, TEST-03 |
| [CI-02](../tareas/CI-02.md) | PostgreSQL en contenedor para el humo y los arneses de las ramas; Neon solo hacia main | indep | `operaciones` | DIAG-02 |
| [CI-03](../tareas/CI-03.md) | Playwright respeta la corrida cubierta y no se repite sobre el mismo commit | indep | `operaciones` | CI-10 |
| [CI-04](../tareas/CI-04.md) | Playwright contra la compilación de producción, con más trabajadores | indep | `frontend` | TEST-03, CI-11 |
| [CI-06](../tareas/CI-06.md) | Limpieza del flujo: caché, npm ci y una sola copia del lint | indep | `operaciones` | CI-03 |
| [CI-07](../tareas/CI-07.md) | Hook pre-push versionado que corre el arnés local por alcance | indep | `operaciones` | — |
| [CI-09](../tareas/CI-09.md) | Pytest en paralelo con una base de PostgreSQL por trabajador, clonada de una plantilla | indep | `operaciones` | ENT-01, SEC-03 |
| [CI-10](../tareas/CI-10.md) | Activar Pytest en paralelo en el CI de las ramas | indep | `operaciones` | CI-02, CI-09 |
| [CI-11](../tareas/CI-11.md) | Arreglar las pruebas de Playwright que solo pasan al reintentar | indep | `frontend` | DIAG-03, FE-05, FE-07, FE-08, FE-20, FE-21, ORG-00, ORG-08, QA-08 |
| [CI-12](../tareas/CI-12.md) | Causa de la variación de cinco veces en el Arnés completo contra Neon | indep | `operaciones` | — |
| [CI-13](../tareas/CI-13.md) | Contar las consultas a la base por prueba y estimar cuánto pesa la distancia a Neon | indep | `operaciones` | — |
| [CI-15](../tareas/CI-15.md) | Esperar la condición estable en configurarProyecto en lugar de un aviso de 700 ms | indep | `frontend` | DIAG-09, FE-22, TEST-02 |
| [CI-17](../tareas/CI-17.md) | Sacar el CI de Neon: el arnés del push a main corre contra postgres:16 dentro del job | indep | `operaciones` | CI-03, CI-05, CI-13, CI-07, CI-08, CI-12, OPS-04 |
| [CI-18](../tareas/CI-18.md) | La comprobación de Alembic pasa a verificar_cloudsql_conexion.py y se retira verificar_revision_alembic.py | indep | `operaciones` | CI-17, GCP-04, GCP-09 |
| [CI-20](../tareas/CI-20.md) | El CI ejecuta tsc --noEmit del frontend (brief para el propietario) | indep | `gobernanza` | — |
| [CI-21](../tareas/CI-21.md) | Un único lector YAML para las pruebas de manifiestos y arnés que prohíbe import yaml en tests | indep | `pruebas` | GCP-07, EP-05 |
| [ENT-01](../tareas/ENT-01.md) | Un intérprete sin las dependencias detiene la suite con un solo mensaje | indep | `pruebas` | — |
| [EP-01](../tareas/EP-01.md) | Entorno de pruebas: identidad del entorno y guardias de arranque del backend | indep | `pasillo_central` | RM-00, ENT-02 |
| [EP-02](../tareas/EP-02.md) | Entorno de pruebas: aviso fijo en toda pantalla y robots noindex fuera de producción | indep | `frontend` | FE-19 |
| [EP-03](../tareas/EP-03.md) | Entorno de pruebas: siembra idempotente de organizaciones, evidencias y clips sintéticos, y de las cuentas de quienes prueban | indep | `operaciones` | GOB-04 |
| [EP-04](../tareas/EP-04.md) | Entorno de pruebas: proyecto de Google Cloud propio, servicios de Cloud Run, IAP y presupuesto | indep | `operaciones` | GCP-01, GCP-03 |
| [EP-05](../tareas/EP-05.md) | Entorno de pruebas: Cloud SQL propio, buckets sin bloqueo de retención y secretos | indep | `operaciones` | GCP-04 |
| [EP-06](../tareas/EP-06.md) | Entorno de pruebas: ciclo de una versión, de migrar y desplegar el digest en pruebas a reiniciar el entorno | indep | `operaciones` | — |
| [EP-07](../tareas/EP-07.md) | Entorno de pruebas: verificador del entorno y flujo de GitHub tras cada despliegue en pruebas | indep | `operaciones, pruebas` | — |
| [EP-08](../tareas/EP-08.md) | Entorno de pruebas: el correo sale solo hacia destinatarios permitidos | indep | `notificaciones` | NOTIF-01, RM-23 |
| [EP-09](../tareas/EP-09.md) | Entorno de pruebas: puesta en marcha en Google Cloud y primer verificador en verde | indep | `operaciones` | EP-01, EP-02, EP-03, EP-04, EP-05, EP-06, EP-07, EP-08 |
| [EP-10](../tareas/EP-10.md) | Entorno de pruebas: datos de ejemplo de los demás módulos, por sus compuertas | indep | `operaciones` | EP-03 |
| [EP-11](../tareas/EP-11.md) | Demo y pruebas en local: validar_arranque rechaza una base de producción y la guía de ENTORNO_LOCAL lo explica | indep | `operaciones` | EP-01, SEC-15 |
| [FE-27](../tareas/FE-27.md) | Armazón responsive del tablero: tres paneles en lg, copiloto en cajón en md y solo el centro en móvil | indep | `frontend` | BIB-116, BIB-118, BIB-119, FE-22, FE-28 |
| [FE-28](../tareas/FE-28.md) | Textos de interfaz sin jerga técnica ni arquitectura interna, con árbitro que impide reintroducirla | indep | `frontend` | API-01, BIB-105, BIB-113, BIB-118, FE-24 |
| [GCP-02](../tareas/GCP-02.md) | Acelerador CI/CD con Test Impact Analysis (TIA) determinista por grafo ADPA y sharding | indep | `pruebas, operaciones` | ADPA-06, CI-10 |
| [GCP-09](../tareas/GCP-09.md) | Dominio app.evydentia.com, ingress interno con el balanceador y brief del propietario actualizado | indep | `operaciones` | GCP-01, GCP-03, GCP-04, GCP-08 |
| [GOB-01](../tareas/GOB-01.md) | Promover los rastros nuevos al VPA | indep | `gobernanza` | — |
| [GOB-02](../tareas/GOB-02.md) | Verificador de especificaciones de tareas | indep | `gobernanza` | — |
| [LEG-04](../tareas/LEG-04.md) | Citas legales: cómputo de plazos y términos (COA y Reglamento General) | indep | `gobernanza` | LEG-03 |
| [LEG-05](../tareas/LEG-05.md) | Citas legales: transferencia internacional en el Reglamento General y tratamiento de datos en Vertex AI | indep | `gobernanza` | LEG-03, LEG-04 |
| [OPS-03](../tareas/OPS-03.md) | Script de verificación de despliegue | indep | `operaciones` | — |
| [OPS-04](../tareas/OPS-04.md) | Rama de Neon por agente de desarrollo | indep | `operaciones` | — |
| [OPS-06](../tareas/OPS-06.md) | Producción se despliega una vez por noche desde la rama produccion, no en cada fusión a main | indep | `operaciones` | RM-13, SEC-06 |
| [PLAT-01](../tareas/PLAT-01.md) | Alta idempotente de organizaciones sintéticas en plataforma_service, sin invitación | indep | `plataforma` | EP-03, ORG-11, ORG-20 |
| [RM-24](../tareas/RM-24.md) | Cierre verificado: la hoja de ruta acepta un verificador externo antes de completar una tarea | indep | `roadmap` | RM-01 |
| [SEC-14](../tareas/SEC-14.md) | El frontend no publica mapas de fuente ni secretos en variables públicas | indep | `frontend, pruebas` | — |
| [SEC-18](../tareas/SEC-18.md) | lopdp_app inserta en tablas identity sin permiso sobre sus secuencias (regresión de mínimo privilegio, sin migración) | indep | `pasillo_central` | — |
| [SEC-20](../tareas/SEC-20.md) | La huella de producción reconoce Cloud SQL: función pura por la URL y comprobación de la base en la guardia, con marcador en las bases que no son producción | indep | `pasillo_central` | SEC-15, EP-01, EP-11 |
| [TEST-02](../tareas/TEST-02.md) | Reparar el arnés de Playwright de la raíz y valorar ejecutarlo en el CI | indep | `pruebas` | — |
| [TEST-05](../tareas/TEST-05.md) | Medir pruebas redundantes y consolidarlas sin perder cobertura ni mutaciones detectadas | indep | `operaciones` | — |
| [BIB-105](../tareas/BIB-105.md) | Administración editorial | backlog | `biblioteca, frontend, pasillo_central` | ORG-00, ORG-08, ORG-09, QA-04, RM-00, SEC-02 |
| [BIB-108](../tareas/BIB-108.md) | Migración e inventario inicial | backlog | `biblioteca, pasillo_central` | BIB-105 |
| [BIB-120](../tareas/BIB-120.md) | Fecha de negocio en America/Guayaquil para los filtros y estados de documentos de la Biblioteca | backlog | `biblioteca` | BIB-117 |
| [CI-01](../tareas/CI-01.md) | Exigir ramas al día en main (solo cuando haga falta) | backlog | `operaciones` | — |
| [CI-05](../tareas/CI-05.md) | Playwright por fragmentos si tras CI-04 sigue por encima de 5 minutos | backlog | `frontend` | CI-04, CI-06 |
| [CI-08](../tareas/CI-08.md) | Medir y reducir los archivos de prueba más lentos contra Neon | backlog | `operaciones` | CI-09 |
| [CI-22](../tareas/CI-22.md) | Árbitro de secciones en _exenciones_propiedad.txt: pares completos, líneas en su sección y ninguna sección vacía de una ficha hecha | backlog | `pruebas, gobernanza` | GOB-02, ADPA-10 |
| [CI-23](../tareas/CI-23.md) | Alcance de PR sin ficha: advertir de los archivos sin dueña viva y opción estricta | backlog | `gobernanza` | CI-19 |
| [CORE-01](../tareas/CORE-01.md) | Una sola zona de negocio: control periódico y recordatorios importan de app_core/zona_negocio.py | backlog | `auditoria_capa, roadmap, rat` | BIB-120 |
| [DEMO-05b](../tareas/DEMO-05b.md) | Purga de las personas ficticias de users | backlog | `operaciones` | DEMO-05 |
| [DEP-01](../tareas/DEP-01.md) | Dependencias de Cloud Storage y de Vertex AI en requirements.txt, con versión exacta | backlog | `operaciones` | BIB-205, SEC-03 |
| [DER-04](../tareas/DER-04.md) | Contracción de DER-03: retirar la columna tenant_id uuid y el trigger de compatibilidad de las solicitudes ARCO | backlog | `derechos_arco` | DER-03 |
| [DER-05](../tareas/DER-05.md) | Plazo por tipo de solicitud de derechos: tabla única, unidad estimada y campos de plazo en la respuesta | backlog | `derechos_arco` | DER-03 |
| [DER-06a](../tareas/DER-06a.md) | Tipos nuevos de solicitud (suspensión, decisiones automatizadas, queja): expandir el enum sin activarlos | backlog | `derechos_arco` | DER-05 |
| [DER-06b](../tareas/DER-06b.md) | Activar los tipos nuevos de solicitud y sus formularios: TIPOS_ACTIVOS y textos de la interfaz | backlog | `derechos_arco, frontend` | DER-06a, DER-07 |
| [DER-07](../tareas/DER-07.md) | Textos legales de la interfaz de derechos ARCO: plazo legal estimado y sin Art. 37, laborables, SLA ni 72h | backlog | `frontend` | BIB-118, DER-05, FE-28 |
| [DIAG-15](../tareas/DIAG-15.md) | Textos sin jerga en DiagnosticCanvas (Poka-Yoke, timebox y etiqueta de la huella) y retiro de su excepción en FE-28 | backlog | `frontend` | DIAG-07, DIAG-11, DIAG-14, EVI-01, EVI-01b, FE-27, FE-28 |
| [ENT-02](../tareas/ENT-02.md) | Un solo punto de entrada fija el bucle de eventos compatible con psycopg en Windows | backlog | `operaciones` | RM-00, RM-02 |
| [EVI-01](../tareas/EVI-01.md) | Evidencias guardadas y comprobadas por el servidor: migración, registro en base, almacén en Cloud Storage y rutas nuevas detrás de una bandera | backlog | `evidencias` | DEP-01, DIAG-03, DIAG-01, SEC-05, DIAG-11, ADPA-05, ADPA-07, ADPA-11, ORG-00, ORG-08 |
| [EVI-01b](../tareas/EVI-01b.md) | Pantalla de evidencias guardadas en el servidor: subida firmada, store desde el servidor y specs adaptados | backlog | `frontend` | CI-15, EVI-01, DIAG-04, FE-14, FE-16, FE-26, DIAG-09, DIAG-11, ADPA-07, ADPA-11 |
| [FIRMA-01](../tareas/FIRMA-01.md) | Firma electrónica con ANF (boceto) | backlog | `firma_electronica` | — |
| [FIRMA-03](../tareas/FIRMA-03.md) | Persistencia de sesiones de firma (firma_sessions) y compuerta async | backlog | `firma_electronica` | FIRMA-01 |
| [FIRMA-04](../tareas/FIRMA-04.md) | API HTTP de firma electrónica y webhook HMAC-SHA256 | backlog | `firma_electronica` | FIRMA-03 |
| [FIRMA-05](../tareas/FIRMA-05.md) | Matrices de aceptación deterministas de FIRMA-03 y FIRMA-04 | backlog | `firma_electronica` | FIRMA-03, FIRMA-04 |
| [FIRMA-06](../tareas/FIRMA-06.md) | Firma con ANF STB v2 en ambiente TEST: cliente real y API de envío y sincronización | backlog | `firma_electronica` | FIRMA-04, RM-00, SEC-05 |
| [IA-01](../tareas/IA-01.md) | Prueba de que el estado del preanálisis nunca nombra variables, claves ni modelos | backlog | `preanalisis` | — |
| [IA-02](../tareas/IA-02.md) | Motivo neutro del asistente de implementación: estado_proveedor_asistente sin proveedor ni variables | backlog | `ai_copilot` | RM-02, SEC-03 |
| [IA-03](../tareas/IA-03.md) | Compuerta de inferencia Gemini en Vertex AI sin clave: sala inferencia con DLP previo, tope de organización y falla cerrada | backlog | `inferencia` | DEP-01, GCP-01, SEC-13a, SEC-13b, IA-01 |
| [IA-04](../tareas/IA-04.md) | El preanálisis usa la compuerta de inferencia: sin OpenAI | backlog | `preanalisis` | IA-01, IA-03 |
| [IA-05](../tareas/IA-05.md) | El motor de inferencia del copiloto usa la compuerta: sin OpenAI, sin clave en el registro y sin plan simulado | backlog | `ai_copilot` | ADPA-03, IA-03 |
| [IA-06](../tareas/IA-06.md) | El cliente del roadmap sobre la compuerta de inferencia: sin DeepSeek | backlog | `roadmap` | IA-03 |
| [IA-07](../tareas/IA-07.md) | El asistente de implementación sobre la compuerta de inferencia: sin DeepSeek ni lectura del .env | backlog | `ai_copilot` | IA-02, IA-03 |
| [IA-08](../tareas/IA-08.md) | Guardia exógena sin OPENAI_, DEEPSEEK_ ni el paquete openai en el código de EVYDENTIA; retira deepseek_client.py y openai de requirements.txt | backlog | `inferencia` | IA-03, IA-04, IA-05, IA-06, IA-07, NEON-02 |
| [IA-09](../tareas/IA-09.md) | Aviso de consentimiento del preanálisis con la ubicación real donde se procesa | backlog | `preanalisis, frontend` | DIAG-09, IA-01, IA-03, IA-04 |
| [LEG-03](../tareas/LEG-03.md) | Verificación con el texto oficial de los artículos y plazos marcados (*) en el PRD, y fuente única de citas legales | backlog | `gobernanza` | — |
| [MARCA-01](../tareas/MARCA-01.md) | Nombre único EVYDENTIA en la plataforma: configuración, arranque, /health y contrato OpenAPI | backlog | `plataforma` | DIAG-01, DIAG-08, ENT-02, EP-01, FIRMA-06, MTGE-01, MTGE-02, OPS-03, OPS-07, ORG-00, RAT-01, RAT-02, RAT-03, RM-00, RM-13, RM-20, RM-21, RM-22, SEC-11, SEC-13, SEC-15, SEC-16, SEC-17 |
| [MARCA-02](../tareas/MARCA-02.md) | Nombre único EVYDENTIA en el diagnóstico: informes, descripción del campo y textos con prueba | backlog | `diagnostico` | DIAG-02, DIAG-08, DIAG-13 |
| [MARCA-03](../tareas/MARCA-03.md) | Nombre único EVYDENTIA en las notificaciones: plantilla de correo | backlog | `notificaciones` | NOTIF-01 |
| [MARCA-04](../tareas/MARCA-04.md) | Nombre único EVYDENTIA en el frontend: paleta, reporte, página de la plataforma y configuración del proyecto | backlog | `frontend` | DIAG-07, BIB-118, FE-28, DER-07 |
| [MARCA-05](../tareas/MARCA-05.md) | Nombre único EVYDENTIA en los lanzadores de Windows | backlog | `operaciones` | — |
| [MARCA-06](../tareas/MARCA-06.md) | Nombre único EVYDENTIA en los títulos de los documentos normativos y en la tabla de la firma electrónica | backlog | `gobernanza` | CI-02, CI-03, CI-10, CI-17, FIRMA-01, GOB-04 |
| [NEON-00](../tareas/NEON-00.md) | Árbitro sin Neon: git grep fuera de una lista blanca cerrada y de los pendientes por ficha | backlog | `pruebas` | — |
| [NEON-01](../tareas/NEON-01.md) | Pruebas y scripts sin la rama Neon propia: base local o evydentia-pruebas y guardias generalizadas a base remota | backlog | `pruebas` | NEON-00, BIB-120, RM-21, SEC-03, BIB-102, BIB-117, BIB-201, BIB-202, CI-02, CI-03, CI-08, CI-09, CI-10, CI-12, CI-13, CI-17, CI-18, GCP-01 |
| [NEON-02](../tareas/NEON-02.md) | Comentarios y docstrings sin Neon en pruebas y en la configuración de ejemplo | backlog | `pruebas` | NEON-00, ORG-13, ORG-14, ORG-16, RAT-01, RAT-02, RAT-05, RM-01, RM-21, RM-23, SEC-07, SEC-08, BIB-203, BIB-205, BIB-206, BIB-207, DER-03, DIAG-13, DPO-02, FE-26, FIRMA-03, FIRMA-05, FIRMA-06, GCP-01, INC-01, DIAG-07b, DIAG-07 |
| [NEON-03](../tareas/NEON-03.md) | Playwright sin rama Neon: configs con base local o evydentia-pruebas y manifiesto E2E con base_pruebas | backlog | `frontend` | NEON-00, TEST-03, BIB-105, FE-22 |
| [NEON-04](../tareas/NEON-04.md) | Gobernanza vigente sin Neon: documentos del PMV al histórico y menciones corregidas | backlog | `gobernanza` | NEON-00, OPS-01, OPS-02, OPS-04, OPS-06, ORG-08, QA-03, SEC-02, SEC-10, SEC-12, TEST-05, ADPA-10, BIB-105, CI-02, CI-03, CI-08, CI-10, CI-12, CI-13, CI-17, CI-18, DEV-01, EP-11, GCP-04, GOB-02, GOB-03, GOB-04, MARCA-06 |
| [NOTIF-01](../tareas/NOTIF-01.md) | Notificaciones por correo (boceto) | backlog | `notificaciones` | RM-08 |
| [ORG-14](../tareas/ORG-14.md) | Datos de la organización para documentos: domicilio, representante legal y contactos | backlog | `organizacion, frontend` | ORG-07, FE-16, BIB-108, ORG-13 |
| [ORG-22](../tareas/ORG-22.md) | Rol auditor: lectura de su tenant, registro y verificación en auditoria_capa, sin ejecutar ni cerrar | backlog | `organizacion` | DEMO-03 |
| [ORG-23](../tareas/ORG-23.md) | Lectura del auditor en diagnóstico, incidentes y hoja de ruta: auditor en ROLES_CONSULTA | backlog | `diagnostico, incidentes, roadmap` | ORG-22, DIAG-11, DIAG-07, EVI-01 |
| [PRD-01](../tareas/PRD-01.md) | El índice de tareas y la verificación de alcance leen el PRD y los artefactos de EVYDENTIA | backlog | `gobernanza` | ADPA-10, CI-19, CI-22, GOB-02, CI-23 |
| [PRD-02](../tareas/PRD-02.md) | Los invariantes citados existen en el archivo de EVYDENTIA; escala de madurez y mapa de rastros sobre sus archivos | backlog | `gobernanza` | DIAG-10, GOB-01 |
| [PRD-03](../tareas/PRD-03.md) | Aviso de inhabilitado en el PRD y los artefactos anteriores, con prueba de que nada los lee | backlog | `gobernanza` | PRD-01, PRD-02, BIB-105, GOB-01, GOB-03, ORG-00, ORG-01, ORG-08 |
| [REG-01](../tareas/REG-01.md) | Paquete normativo como dato, editable solo por el operador de la plataforma, con plazos como parámetros | backlog | `regulacion_rag, plataforma, frontend` | LEG-03, ORG-09, ORG-10, ORG-11, FE-10, ADPA-05, ADPA-06 |
| [REP-01](../tareas/REP-01.md) | Árbitro de copias en BRIEFS_POR_BLOQUE.md: Hecho si, Depende de, Objetivo y Sala(s) iguales a los de sus fichas | backlog | `gobernanza` | — |
| [SEC-21](../tareas/SEC-21.md) | Límite por IP en la ruta pública GET /api/v1/entorno | backlog | `pasillo_central` | SEC-13, SEC-13a |
| [TEST-01](../tareas/TEST-01.md) | Cobertura pendiente de evidencia y Redis | backlog | `pruebas` | RM-01 |
<!-- INDICE-TAREAS:FIN -->

<!-- ¤adpa/ -->
