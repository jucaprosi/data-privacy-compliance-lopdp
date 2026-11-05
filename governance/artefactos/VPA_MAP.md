# VPA_MAP — Raíz de la Trazabilidad Estigmérgica y Núcleo Neuronal de LOPDP 360
`¤vpa`
`¤¤developer-architect-adpa` `¤¤tech-lead-architect`

> **AQUÍ NACE CADA RASTRO DEL ECOSISTEMA PLATAFORMA LOPDP 360.**
> Cada capacidad, módulo y regla de negocio del sistema está anclada a un **Rastro Estigmérgico (`¤`)**, permitiendo que una búsqueda en disco (`rg --hidden "¤rastro"`) recupere de forma unívoca su código fuente, contratos, pruebas, bibliografía y justificación en el PRD.

---

## 1. Módulos y Capacidades del Sistema LOPDP 360
<!-- ¤adpa -->

### Eje Discovery y Diagnóstico
`¤diagnostico`

| Rastro | Gen | Significado | Rol | Entidades / Alcance |
| :--- | :--- | :--- | :--- | :--- |
| `¤diagnostico` | G1 | Módulo de evaluación inicial adaptativa y diagnóstico de 60 minutos | `¤¤consultant` | Ficha organizacional inteligente, perfilamiento, alcance |
| `¤diagnostico-motor` | G2 | Motor de reglas de aplicabilidad condicional (límite técnico 80 preguntas) | `¤¤backend-developer` | Árbol condicional de preguntas, poda de no aplicables |
| `¤diagnostico-scoring`| G2 | Scoring multidimensional (Madurez SMARTCIDI 1-5 por dimensión vs Conformidad vs Riesgo) | `¤¤backend-developer` | Índices de permeabilidad, cobertura de evidencias |
| `¤diagnostico-reporte`| G2 | Generador del informe diagnóstico ejecutivo y técnico con brechas | `¤¤consultant` | PDF/DOCX ejecutivo, matriz técnica de hallazgos |
| `¤diagnostico-asignacion` | G2 | Asignación de dominios del assessment a responsables de área (estructura funcional EVYDENTIA, 2026-10-28) | `¤¤backend-developer` | DIAG-04 |
| `¤diagnostico-no-aplica` | G2 | «No aplica» exige justificación guardada con la respuesta | `¤¤backend-developer` | DIAG-05 |
| `¤diagnostico-comparativo` | G2 | Comparativo de un assessment con la línea base, por dimensión y dominio, sin cifra única | `¤¤backend-developer` | DIAG-06 |

---

### Eje Implementación y Operación
`¤implementacion`

| Rastro | Gen | Significado | Rol | Entidades / Alcance |
| :--- | :--- | :--- | :--- | :--- |
| `¤implementacion` | G1 | Gestión operativa de planes de adecuación y remediación de brechas | `¤¤lead-implementer` | Backlog de implementación, tareas, responsables, SLA |
| `¤roadmap` | G2 | Hoja de ruta de cumplimiento: olas, tareas, evidencias y su validación por roles | `¤¤lead-implementer` | Roadmaps, olas, tareas, evidencias, KPIs, auditoría de tareas |
| `¤hallazgos` | G2 | Hallazgos con origen y compuerta única hallazgo → tarea (plan de acción único, `INV_LOPDP_SINGLE_ACTION_PLAN`) (estructura funcional EVYDENTIA, 2026-10-28) | `¤¤lead-implementer` | RM-21, RM-22, CAPA-02 |
| `¤rbac-tenant` | G1 | Roles por organización y aislamiento entre organizaciones | `¤¤tech-lead-architect` | Asignación de roles, separación de funciones del DPO, RLS por tenant, operador de plataforma |
| `¤cartera` | G2 | Cartera de organizaciones por pertenencia, sin abrir la RLS (`INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP`) (estructura funcional EVYDENTIA, 2026-10-28) | `¤¤tech-lead-architect` | ORG-15 |
| `¤alta-organizacion` | G2 | Alta de la organización en el servidor con el asistente de siete pasos | `¤¤lead-implementer` | ORG-16 |
| `¤inventario` | G2 | Activos y sistemas, soportes y personas mínimas de la organización | `¤¤lead-implementer` | ORG-17 |
| `¤rat` | G1 | Registro de Actividades de Tratamiento (Single Source of Truth) | `¤¤lead-implementer` | Procesos, finalidades, bases de legitimación, flujos |
| `¤niif18` | G1 | Módulo NIIF 18 existente: clasificación, estado de resultados, MPM, diagnóstico y exportación; alta del rastro histórico usado en el PRD | `¤¤developer-architect-adpa` | `features/niif18`, `niif18_service.py`, frontend NIIF 18 |
| `¤legitimacion` | G2 | Matriz de bases jurídicas, consentimiento y test de interés legítimo | `¤¤legal-counsel` | Consentimientos, contratos, ponderación de interés legítimo |
| `¤derechos` | G1 | Gestión del ciclo de vida de Derechos de Titulares (ARCO+) | `¤¤support-specialist` | Intake, validación de identidad, cronómetro de SLA, respuesta |
| `¤incidentes` | G1 | Playbook de respuesta a vulneraciones y reloj normativo de notificación | `¤¤security-engineer` | Triage, evaluación de riesgo, CSIRT, notificación SPDP |
| `¤transferencias` | G1 | Registro de transferencias y debida diligencia de terceros/encargados | `¤¤legal-counsel` | Contratos de encargo, transferencias internacionales, garantías |
| `¤conservacion` | G2 | Reglas de retención, ciclo de vida, anonimización y bloqueo legal | `¤¤security-engineer` | Tablas de conservación, protocolos de destrucción segura |

---

### Eje Riesgos y Gran Escala
`¤riesgos`

| Rastro | Gen | Significado | Rol | Entidades / Alcance |
| :--- | :--- | :--- | :--- | :--- |
| `¤riesgos-eipd` | G1 | Motor de gestión de riesgos para derechos y libertades y EIPD | `¤¤risk-analyst` | Contexto, amenazas, probabilidad, impacto, plan de mitigación |
| `¤mtge-granescala` | G2 | Motor determinista de cálculo MTGE y casos directos de gran escala | `¤¤risk-analyst` | Variables cuantitativas, umbrales de activación obligatoria |
| `¤privacy-gate` | G2 | Puerta de control de Privacidad desde el Diseño para nuevas iniciativas | `¤¤lead-implementer` | Checklists preventivos antes de pase a producción de sistemas |

---

### Eje Supervisión e Independencia (DPD / DPO)
`¤dpo`

| Rastro | Gen | Significado | Rol | Entidades / Alcance |
| :--- | :--- | :--- | :--- | :--- |
| `¤dpo-cockpit` | G1 | Cockpit exclusivo para el Delegado de Protección de Datos | `¤¤dpo-officer` | Supervisión read-only, portafolio multicliente, métricas |
| `¤dpo-asesoria` | G2 | Bandeja de consultas internas, emisión y versionado de dictámenes | `¤¤dpo-officer` | Recomendaciones formales, registro de respuestas gerenciales |
| `¤dpo-independencia`| G2 | Controles de segregación de funciones (SoD) y bitácora de diligencia | `¤¤dpo-officer` | Declaración de no-conflicto de interés, canal de escalación |
| `¤dpo-informe-anual` | G2 | Informe anual del DPO desde su bitácora y estado de inscripción ante la SPDP | `¤¤dpo-officer` | DPO-02 |

---

### Eje Auditoría y Aseguramiento
`¤auditoria`

| Rastro | Gen | Significado | Rol | Entidades / Alcance |
| :--- | :--- | :--- | :--- | :--- |
| `¤auditoria-programa`| G1 | Programa anual de auditorías y checklists normativos basados en snapshot| `¤¤auditor` | Plan de auditoría, asignación independiente de auditores |
| `¤auditoria-capa` | G2 | Gestión de hallazgos, no conformidades y acciones correctivas (CAPA) | `¤¤auditor` | Causa raíz, acciones preventivas/correctivas, verificación |
| `¤evidencias` | G1 | Repositorio de evidencias con metadatos, hashing y control DLP | `¤¤security-engineer` | Archivos, hashes SHA-256, vigencia, clasificación sensible |
| `¤controles-periodicos` | G2 | Controles periódicos con frecuencia y responsable; el vencido o con evidencia vencida produce un hallazgo | `¤¤auditor` | CAPA-02, CAPA-03 |
| `¤evidencias-vigencia` | G2 | Vigencia y visibilidad de evidencias y paquete para inspección por requisito | `¤¤security-engineer` | EVI-02 |

---

### Eje Inteligencia y "Regulation as Code"
`¤regulacion`

| Rastro | Gen | Significado | Rol | Entidades / Alcance |
| :--- | :--- | :--- | :--- | :--- |
| `¤regulation-code` | G1 | Corpus normativo versionado como dato ejecutable | `¤¤legal-engineer` | Artículos, resoluciones SPDP, reglas operativas, diff |
| `¤inteligencia-normativa` | G1 | Módulo de vigilancia regulatoria, ingesta de fuentes oficiales SPDP y base documental estructurada | `¤¤legal-engineer` | `features/inteligencia_normativa`, BRF-001 |
| `¤vigilancia-spdp` | G2 | Monitoreo automatizado diario de resoluciones SPDP, deduplicación en 3 capas y validación SHA-256 | `¤¤backend-developer` | `features/inteligencia_normativa`, BRF-001 |
| `¤paquete-normativo` | G2 | Paquete normativo como dato, editable solo por el operador, con plazos como parámetros | `¤¤legal-engineer` | REG-01 |
| `¤copiloto-ia` | G1 | Asistente RAG con citas normativas obligatorias y guardrails | `¤¤ai-engineer` | Consultas semánticas, redacción de borradores, gap assistant |
| `¤gemini-vertex` | G1 | Modelos nativos Google Gemini en Vertex AI (`gemini-2.5-pro`, `gemini-2.5-flash`, `text-embedding-005`) con Structured Outputs, ADC y cero entrenamiento | `¤¤ai-engineer` | `features/ai_copilot`, `features/regulacion_rag`, `features/roadmap`, VTX-01 |
| `¤vertex-cache` | G2 | Caché explícita de contexto normativo en Vertex AI sobre el corpus LOPDP/SPDP | `¤¤ai-engineer` | VTX-01, `features/regulacion_rag`, `features/ai_copilot` |
| `¤dlp-muestreo` | G2 | Descubrimiento muestreado de datos sensibles en Cloud DLP y validador Módulo 10 para el RAT | `¤¤security-engineer` | DLP-01, `features/dlp_discovery` |

---

### Eje Arquitectura, Seguridad, Nube Híbrida y Frontend
`¤arquitectura` `¤boveda-cloud` `¤videovigilancia-cctv` `¤motor-go-hibrido`

| Rastro | Gen | Significado | Rol | Entidades / Alcance |
| :--- | :--- | :--- | :--- | :--- |
| `¤adpa` | G1 | Aislamiento de módulos en salas ADPA con compuertas `_service.py` | `¤¤developer-architect-adpa` | Mamparos herméticos sin acoplamiento circular |
| `¤boveda-cloud` | G1 | Bóveda Cloud certificada en Google Cloud Storage (buckets duales `short-ttl` y `long-retention`, cuotas de reventa, URLs firmadas V4 y carril forense dual) | `¤¤security-engineer` | BOV-01, BOV-02, BOV-03, BOV-04, `features/boveda_cloud` |
| `¤videovigilancia-cctv` | G1 | Gobernanza automatizada de videovigilancia LOPDP (ciclo de 15 días, estándar H.265 sin audio, *Hold Legal* WORM y actas criptográficas de destrucción) | `¤¤security-engineer` | CCTV-01, CCTV-02, `features/videovigilancia` |
| `¤motor-go-hibrido` | G1 | Satélites compilados en `.go` (`services_go/vault_worker` en Cloud Run y `services_go/cctv_agent` en el borde del cliente) acoplados al Core Python ADPA | `¤¤developer-architect-adpa` | GOVW-01, GOCA-01, `services_go/vault_worker`, `services_go/cctv_agent` |
| `¤cloud-run-perf` | G2 | Optimización de Cloud Run ASGI (`uvloop`, `Startup CPU Boost`, concurrencia 80), sesión RLS en 1 RTT con `PgBouncer` y TIA determinista por grafo ADPA en CI/CD | `¤¤tech-lead-architect` | GCP-01, GCP-02, `app_core/db`, `app_core/cloud` |
| `¤sdd` | G1 | Especificaciones ejecutables orientadas por pruebas y contratos deterministas por tarea (`governance/especificaciones/<ID>.md`) | `¤¤developer-architect-adpa` | `scripts/verificar_especificaciones.py`, `governance/especificaciones/` |
| `¤frontend-ide` | G1 | Interfaz estilo Antigravity/Cursor (Command Palette, Split Panes) | `¤¤frontend-architect` | Paleta de colores dark/light, Ctrl+K, layout de alta densidad |
| `¤navegacion-menus` | G2 | Navegación por los nueve menús de la estructura funcional; capa de presentación sobre las salas (estructura funcional EVYDENTIA, 2026-10-28) | `¤¤frontend-architect` | FE-22 |
| `¤asistente` | G2 | Patrón único de asistente para los flujos guiados | `¤¤frontend-architect` | FE-23, ORG-16 |
| `¤tablero-dimensiones` | G2 | Tableros con las cuatro dimensiones y brechas críticas, sin cifra única | `¤¤frontend-architect` | FE-24, ORG-15, DIAG-06 |
| `¤portales-externos` | G2 | Diseño de seguridad de los portales de titulares y encargados | `¤¤security-engineer` | SEC-12 |
| `¤seguridad-tenant`| G1 | Segregación multi-tenant estricta, RBAC, logs tamper-evident y MFA | `¤¤security-engineer` | Aislamiento de datos por organización, auditoría de accesos |
| `¤seguridad` | G1 | Controles de seguridad transversales: identidad, credenciales, permisos mínimos y cabeceras | `¤¤security-engineer` | Autenticación OIDC, roles de base de datos, CSP, operador de plataforma |
| `¤entorno-pruebas` | G2 | Entorno de pruebas de EVYDENTIA en un proyecto de Google Cloud propio: misma topología e imagen que producción, datos ficticios y paso obligado antes de producción (`PRD_EVYDENTIA_REVENTA_NUBE.md` §5.5) | `¤¤tech-lead-architect` | EP-01…EP-09, `governance/operaciones/ENTORNO_DE_PRUEBAS.md`, `governance/operaciones/entornos/pruebas` |
| `¤observabilidad` | G2 | Observabilidad de la plataforma: registro estructurado sin datos personales, errores, disponibilidad y alertas de gasto | `¤¤security-engineer` | OPS-07, Cloud Logging, Error Reporting, alertas de presupuesto |
| `¤firma-electronica` | G2 | Firma electrónica de documentos y evidencias del cumplimiento | `¤¤backend-developer` | Sala `features/firma_electronica`, transacciones de firma |
| `¤interfaz` | G1 | Capa de presentación limpia: la interfaz de usuario no muestra tokens de gobernanza | `¤¤frontend-architect` | Vistas, etiquetas y notificaciones de producción |

---


<!-- ¤adpa/ -->

## 2. Meta-Proceso de Gobernanza y Metodología Heredada
<!-- ¤adpa -->
`¤bbap` `¤triaje` `¤metodologias` `¤doctrinas`

| Rastro | Gen | Significado | Rol | Entidades / Alcance |
| :--- | :--- | :--- | :--- | :--- |
| `¤bbap` | G1 | Metodología de desarrollo en 2 pasos: Boceto libre ➔ Sellado con verificación | `¤¤developer-architect-adpa` | Ciclo de tareas, arneses físicos, tests y cierre |
| `¤triaje` | G1 | Aduana y reestructuración determinista de precondición C antes de código | `¤¤developer-architect-adpa` | Orquestación MCP, transducción de prompt, foco |
| `¤metodologias` | G1 | Compendio metodológico (DMAT, Odoo, Antigravity/Cursor, Global Suite, etc.) | `¤¤tech-lead-architect` | Procedimientos de diagnóstico, RAT, BBAP y auditoría |
| `¤doctrinas` | G1 | Principios rectores constitucionales y límites no negociables del sistema | `¤¤tech-lead-architect` | Accountability, independencia DPO, evidencias E0-E3 |

---


<!-- ¤adpa/ -->

## 3. Nido de Artefactos Maestros y Gobernanza del Tech Lead (`¤¤tech-lead-architect`)
<!-- ¤adpa -->
`¤artefactos-prd` `¤tasks` `¤invariantes` `¤arquitectura` `¤fuentes` `¤aportes` `¤vpa` `¤arnes-verificacion`

| Rastro | Gen | Significado | Rol | Entidades / Alcance |
| :--- | :--- | :--- | :--- | :--- |
| `¤artefactos-prd` | G1 | Documento de Requisitos de Producto (PRD vivo) y criterios MVP | `¤¤tech-lead-architect` | Alcance funcional, benchmarks, integración de módulos |
| `¤tasks` | G1 | Tablero de tareas, backlog técnico y control de fases de desarrollo | `¤¤tech-lead-architect` | Desglose por sprint, dependencias ADPA, criterios de cierre |
| `¤doctrinas` | G1 | Principios rectores, mandatos constitucionales y límites no negociables | `¤¤tech-lead-architect` | Accountability, SoD DPO, Compliance Graph, invariantes |
| `¤metodologias` | G1 | Marco de ejecución metodológica (BBAP, Odoo Master Record, IDE UX) | `¤¤tech-lead-architect` | Procedimientos de diagnóstico, RAT, desarrollo en 2 pasos |
| `¤invariantes` | G1 | Catálogo central de invariantes duras y precondiciones del sistema | `¤¤tech-lead-architect` | Cota 80 preguntas, whitelists dinámicas, UTF-8 sin BOM |
| `¤arquitectura` | G1 | Documento de Arquitectura de Software (SAD), salas ADPA y contratos | `¤¤tech-lead-architect` | Topología de compuertas, middleware, DDL, API Gateway |
| `¤fuentes` | G1 | Linaje normativo oficial (SPDP) y bibliografía científica de ingeniería | `¤¤tech-lead-architect` | Papers científicos (Hick, Fitts, Harel), normas ISO, SPDP |
| `¤aportes` | G1 | Tratado de teoremas demostrables e innovaciones arquitectónicas | `¤¤tech-lead-architect` | Formalización matemática, Teoremas 1–14, Aportes 1–13 |
| `¤vpa` | G1 | Raíz de trazabilidad estigmérgica, asignación de rastros y roles agénticos | `¤¤tech-lead-architect` | Mapa estigmérgico, topología VPA, integridad de rastros |
| `¤arnes-verificacion`| G1 | Árbitros exógenos deterministas, arneses físicos y suites de no-regresión | `¤¤tech-lead-architect` | `ejecutar_arnes_verificacion.bat`, linters AST, CI/CD |
| `¤arbitro` | G1 | Árbitros exógenos que deciden el éxito de cada tarea (pruebas, verificadores, mutación) | `¤¤tech-lead-architect` | Vigilantes de pruebas, `verificar_reparto.py`, `generar_indice_tareas.py` |
| `¤ci-cd` | G1 | Integración continua: checks obligatorios del PR y protección de `main` | `¤¤tech-lead-architect` | Workflow del CI, Arnés Físico Determinista, Playwright Frontend |




<!-- ¤adpa/ -->
