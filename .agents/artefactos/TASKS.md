# Tablero de Tareas y Control de Avance (`TASKS.md`)
`¤bbap`

> **MEMORIA OPERATIVA Y CONTROL DE EJECUCIÓN:**
> Este archivo registra las tareas pendientes, activas y completadas de **JUBYS Plataforma LOPDP 360**. Cada hito está anclado a su rastro estigmérgico (`¤`) y garantiza la trazabilidad del roadmap desde la Fase 0 (Discovery y Diseño) hasta el despliegue del MVP y módulos avanzados.

---

## Estado General del Proyecto
* **Fase Actual:** `Fase 0 — Diseño, Discovery y Gobernanza`
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

### 🟣 FASE 2: Implementación Avanzada y Motor MTGE (PENDIENTE)
- [ ] **Motor de Riesgos y EIPD:**
  - [ ] Matriz de riesgos sobre derechos y libertades (`IMP-06`). `¤riesgos-eipd`
  - [ ] Calculadora algorítmica de Tratamiento a Gran Escala MTGE (`IMP-13`). `¤mtge-granescala`
- [ ] **Derechos de Titulares e Incidentes:**
  - [ ] Workflow de solicitudes ARCO+ con cronómetro de vencimiento (`IMP-05`). `¤derechos`
  - [ ] Playbook de gestión de brechas y reloj de notificación SPDP/CSIRT (`IMP-12`). `¤incidentes`
- [ ] **Terceros y Transferencias:**
  - [ ] Inventario de encargados, debida diligencia y cláusulas obligatorias (`IMP-08`). `¤transferencias`

---

### 🟡 FASE 3: Auditoría y Copiloto IA (PENDIENTE)
- [ ] **Módulo de Auditoría y CAPA:**
  - [ ] Generación de checklists normativos desde snapshot histórico (`AUD-02`). `¤auditoria-programa`
  - [ ] Workflow de hallazgos, planes de acción y verificación de cierre independiente (`AUD-06`, `AUD-07`). `¤auditoria-capa`
- [ ] **Copiloto RAG Legal con Guardrails:**
  - [ ] Indexación vectorial del corpus normativo cerrado de la SPDP. `¤regulation-code`
  - [ ] Filtro DLP pre-inferencia y obligación de citación exacta de artículos. `¤copiloto-ia`
