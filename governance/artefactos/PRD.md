# Product Requirements Document (PRD) — JUBYS Plataforma LOPDP 360
`¤artefactos-prd`
`¤rat` `¤diagnostico` `¤dpo-cockpit` `¤frontend-ide` `¤regulation-code`

---

## 1. Resumen Ejecutivo y Marco Doctrinal
**Nombre del Producto:** JUBYS Plataforma LOPDP 360  
**Visión:** Plataforma SaaS multiempresa y multisectorial para gestionar de forma demostrable el ciclo integral de protección de datos personales en Ecuador (LOPDP, RGLOPDP, normativas SPDP 2024–2026 y leyes conexas).  
**Enfoque de Negocio:** Sistema de gestión continuo basado en un **"Compliance Graph"** relacional y auditable que erradica la dependencia de formularios estáticos y carpetas documentales desvinculadas.  

### Las 10 Doctrinas Fundacionales No Negociables:
1. **Cumplimiento Demostrable (Accountability Real):** La plataforma no "certifica" mágicamente; estructura controles, evidencias y verificaciones observables para sostener la debida diligencia.
2. **Independencia Sagrada del DPD/DPO:** El DPO es una persona natural autónoma; la herramienta asiste y documenta su labor, prohibiendo asignarle tareas de ejecución operativa.
3. **Evidencia antes que Autodeclaración:** Respuestas afirmativas sin soporte documental ($E0$) carecen de valor probatorio; la conformidad exige evidencia válida ($E1+$) o rationale formal.
4. **Cuadratura Multidimensional:** Prohibición del porcentaje general engañoso (ej. "87% de cumplimiento"); ningún promedio puede enmascarar una brecha jurídica crítica.
5. **Fuente Única de Verdad (Compliance Graph):** Un dato se captura una sola vez en el RAT y alimenta en cascada riesgos, EIPD, transferencias y avisos.
6. **"Regulation as Code":** La ley no es texto estático; es un modelo de datos versionado, trazable y explicable ante el usuario.
7. **Copiloto IA con Humano en el Circuito (HITL):** Asistencia RAG sobre corpus oficial cerrado ("sin fuente no hay respuesta"), filtro DLP preventivo y cero decisiones automáticas sin aprobación humana.
8. **Privacidad por Diseño de la Propia Plataforma:** Minimización radical de datos, prohibición de subir bases reales innecesarias, cifrado y aislamiento multi-tenant estricto.
9. **Antecedencia Paramétrica y Poda Ontológica:** La configuración corporativa y normativa es la raíz generadora del árbol de aplicabilidad ($\text{Root}(\mathcal{T}_{\text{poda}}) \prec \mathcal{Q}_{\text{diag}}$); siempre antecede y se desacopla del cuestionario diagnóstico.
10. **Aislamiento Probatorio y Purga Multidominio:** La evidencia de un régimen normativo no puede contaminar otro; el cambio de normativa purga atómicamente el buffer probatorio y aplica whitelists estrictas de extensión.

---

## 2. Objetivos del Producto
*   **Diagnosticar:** Realizar evaluaciones iniciales en sesiones ágiles timeboxed de máximo 60 minutos con cota fija de 80 preguntas visibles.
*   **Implementar:** Transformar brechas en planes de trabajo con dueños, plazos, controles y evidencias trazables.
*   **Auditar:** Evaluar eficacia operativa, documentar hallazgos y accionar planes correctivos (CAPA) con verificación independiente.
*   **Supervisar (DPD/DPO):** Dotar al Delegado de un *cockpit* de supervisión independiente (Read-Only operacional) y bitácora inviolable de dictámenes.
*   **Actualizar:** Analizar el impacto de reformas normativas de la SPDP mediante un motor de diff regulatorio que previene la desactualización.

---

## 3. Usuarios Objetivo, Roles y Segregación de Funciones (SoD)
El sistema implementa **Separación de Obligaciones (Separation of Duties - SoD)** a nivel de base de datos y compuertas ADPA:
1.  **Consultor Implementador:** Modela aplicabilidad, configura la organización, guía la adecuación y valida evidencias en alcance.
2.  **Responsable / Encargado (Cliente):** Toma decisiones de negocio, asigna dueños de control, aprueba políticas y acepta riesgos residuales.
3.  **Propietario de Proceso (Área):** Ejecuta tareas operativas y aporta registros/evidencias de operación.
4.  **DPD / DPO:** Asesora, supervisa, recibe consultas y emite dictámenes. *Restricción inviolable: Prohibición física de asignarle controles operativos o ejecución de EIPDs en el mismo tenant.*
5.  **Auditor Interno / Externo:** Evalúa controles contra checklists normativos cerrados; no puede auditar acciones que él mismo ejecutó.
6.  **Alta Dirección:** Consume tableros ejecutivos, mapas de calor de riesgos, dictámenes del DPO y reportes de avance.
7.  **TI / Seguridad:** Implementa salvaguardas técnicas, administra accesos, gestiona incidentes y aporta logs de evidencia.
8.  **Tech Lead / Arquitecto Técnico de Gobernanza (`¤¤tech-lead`):** Autoridad técnica responsable del diseño, coherencia e implementación de los artefactos maestros del sistema: `PRD.md` (criterios de producto), `TASKS.md` (roadmap y dependencias ADPA), `INVARIANTS.md` (leyes inmutables), compendios doctrinales y metodológicos (BBAP en 2 pasos), `ARQUITECTURA_SOFTWARE.md` (salas ADPA y DDL), tratados científicos (`APORTES_INEDITOS.md`, `FUENTES_Y_BIBLIOGRAFIA.md`), mapa estigmérgico (`VPA_MAP.md`) y custodia del árbitro exógeno determinista (`ejecutar_arnes_verificacion.bat`).


---

## 4. Análisis de Mercado y Benchmarking Hexagonal
El diseño funcional integra los mejores patrones de la industria global:
*   **Odoo:** Arquitectura de datos relacional donde el **RAT opera como Master Record**, centralizando y propagando el estado hacia riesgos, terceros y auditorías sin duplicar matrices.
*   **Antigravity / Cursor:** Ergonomía técnica de alta densidad, navegación por Command Palette (`Ctrl+K`), Split Panes contextuales y temas Dark/Light de alto contraste.
*   **Global Suite:** Cruce normativo multiestándar (LOPDP articulada con buenas prácticas ISO 27002 / ISO 27701) sin contaminar la naturaleza obligatoria de la ley local.
*   **Novoser:** Gestión de tickets de no conformidades (CAPA) con verificación independiente obligatoria y reloj de incidentes de seguridad con SLA.
*   **Pirani (Pirámid):** Democratización de la gestión de riesgos con matrices visuales intuitivas (3x3 y 5x5) comprensibles para usuarios no matemáticos.
*   **Isotools:** Automatización de recordatorios periódicos, alertas de caducidad de evidencias y workflows formales de aprobación documental.

---

## 5. Módulos y Funcionalidades Principales

### Módulo 0: Configuración del Proyecto y Ficha Organizacional (Árbol de Poda)
`¤diagnostico-motor` `¤evidencias` `¤frontend-ide`
*   **Pestaña Estructural Antecedente:** Ubicada en la parte superior del dock de navegación, desacoplada por completo del lienzo de preguntas.
*   **Ficha de la Empresa:** Parametrización de Razón Social, Sector y Tamaño de empresa gestionada de forma reactiva con Zustand (`useAuditStore`).
*   **Selector Multirregulatorio Dinámico:**
    *   Soporte inicial activo para **Propiedad Intelectual (`PI`)**, preparado para escalar a **Normas Contables (`NIIF`)** y **Estándares de Seguridad (`ISO`)**.
*   **Whitelist Evidencial Dinámica con Poka-Yoke:**
    *   *Propiedad Intelectual (`PI`):* Exclusivamente `.pdf, .docx, .md, .txt`.
    *   *Normativas Contables/Técnicas (`NIIF`/`ISO`):* Exclusivamente `.csv, .xlsx, .xbrl, .ixbrl, .json, .xml, .sql`.
    *   Validación nativa en diálogo y en tiempo real durante eventos *Drag & Drop* con alerta semántica inmediata en `#ff1744`.
*   **Purga Transaccional Inmediata:** Conmutar entre normativas vacía automáticamente el arreglo de evidencias previas para garantizar que no existan contaminaciones cruzadas.
*   **Disparador de Poda:** El botón *"Comenzar Diagnóstico"* valida campos obligatorios, sella `isConfigured: true` e instanciar el banco podado de preguntas.

### Módulo 1: Diagnóstico de la Empresa (Discovery en 60 Minutos)
*   **Ficha Inteligente & Perfilamiento (5 min):** Captura de sector, tamaño, canales, nube, IA, biometría y transferencias para determinar aplicabilidad.
*   **Assessment Adaptativo Timeboxed (40 min):**
    *   16 dominios JUBYS (G01–G16) $\times$ hasta 3 preguntas núcleo = 48 preguntas.
    *   Preguntas condicionales críticas: hasta 12 preguntas adicionales.
    *   **Cota Técnica Superior:** Máximo 80 preguntas visibles por sesión (ruta operativa típica: 45–68 preguntas).
    *   **Criterio de Cierre:** Lo que demande auditoría forense profunda se marca *"Pendiente de Validación"*.
*   **Scoring Multidimensional Cuádruple:**
    *   Madurez SPDP (0: Caótico, 1: Implícito, 2: Temprano explícito, 3: Maduro explícito).
    *   Conformidad Legal Booleana (`Conforme`, `Parcial`, `No Conforme`, `No Verificado`).
    *   Cobertura y Calidad de Evidencias ($E0$ a $E3$).
    *   Riesgo Residual sobre Derechos y Libertades.
*   **Informes Automáticos:** Generación de Informe Ejecutivo (visión gerencial) e Informe Técnico de Brechas (detalle control por control).

### Módulo 2: Implementación y RAT Maestro
*   **RAT Maestro (Single Source of Truth):** Catálogo estructurado de actividades de tratamiento, finalidades, bases jurídicas, categorías de datos, destinatarios y flujos.
*   **Motor MTGE y Gran Escala:** Algoritmo paramétrico (Resolución SPDP-SPD-2026-0005-R) que calcula el volumen, permanencia y alcance para activar forzosamente EIPD y DPO.
*   **Gestión de Derechos (ARCO+):** Intake multicanal, verificación proporcional de identidad, cronómetro de SLA normativo y expediente probatorio de respuesta.
*   **Incidentes y Vulneraciones:** Playbook adaptado a la Ley de Ciberseguridad 2026; reloj normativo de notificación a SPDP y CSIRT nacional.
*   **Terceros y Transferencias:** Registro de encargados, debida diligencia previa, cláusulas contractuales obligatorias y garantías de transferencias internacionales.
*   **Conservación y Supresión:** Tablas de retención, reglas de bloqueo legal y procedimientos de anonimización verificable.

### Módulo 3: Auditorías LOPDP y CAPA
*   **Programa de Auditoría:** Plan anual con snapshots congelados de la normativa vigente al momento del corte.
*   **Muestreo y Pruebas de Eficacia:** Registro de poblaciones, muestras y evidencias operativas revisadas.
*   **Gestión de Hallazgos y CAPA:** Flujo de no conformidades con análisis de causa raíz, acciones preventivas/correctivas y verificación de cierre independiente.

### Módulo 4: Cockpit del DPD/DPO
*   **Supervisión Read-Only:** Visibilidad transversal sin interferir en la gestión operativa ni asumir propiedad de controles.
*   **Bandeja de Asesoría:** Emisión de dictámenes y recomendaciones técnicas versionadas, con acuse de recibo de la alta dirección.
*   **Bitácora de Diligencia:** Historial cronológico inviolable de advertencias y consultas atendidas.
*   **Gestión Multi-Cliente:** Portafolio seguro para DPOs externos con aislamiento estricto de expedientes.

---

## 6. Base de Conocimiento "Regulation as Code" y Copiloto IA
*   **Corpus Normativo Versionado:** Base de datos estructurada con leyes, decretos y resoluciones SPDP 2024–2026.
*   **Motor de Diff Regulatorio:** Ante nuevas publicaciones oficiales, calcula el grafo de impacto en clientes y sugiere revalidaciones sin alterar auditorías pasadas.
*   **Copiloto IA RAG de Confianza Cero:**
    *   Consultas normativas con citación obligatoria (artículo, resolución, fecha de vigencia).
    *   Generador de borradores documentales a partir de plantillas aprobadas.
    *   **Filtro DLP Pre-Inferencia:** Enmascaramiento automático de cédulas, nombres y datos médicos antes de consultar los modelos.
    *   Cero entrenamiento con datos del cliente.

---

## 7. Requisitos No Funcionales y Seguridad (Stack Empresarial de 8 Capas)
*   **Stack de 8 Capas Herméticas:** 
    1. *Frontend IDE:* Next.js 15.5+ (Turbopack), React 19, Zustand (`useAuditStore`), `cmdk` (`Ctrl+K`), `react-resizable-panels`, `react-dropzone` (validación condicional Poka-Yoke), Tailwind CSS v4, TanStack Query, Playwright + Vitest.
    2. *Backend ADPA:* Python 3.12+, FastAPI, Pydantic v2, salas herméticas `features/` con compuertas `_service.py` ($\text{ImportsCruzados} \equiv \emptyset$), SQLAlchemy 2.0 + Alembic, Temporal / Camunda para workflows CAPA.
    3. *Datos y Compliance Graph:* PostgreSQL 16 (SSOT transaccional), Row-Level Security (`tenant_id UUID NOT NULL`), Apache AGE / CTE recursivos, `pgvector`, JSONB, MinIO / S3 con Object Lock WORM y hashes SHA-256.
    4. *Regulation as Code:* Git + YAML/JSON + JSON Schema para corpus normativo versionado (LOPDP, RGLOPDP, SPDP 2024–2026), motor de diff en Python, OpenSearch / Meilisearch.
    5. *Copiloto IA RAG de Confianza Cero:* LangChain / LlamaIndex, búsqueda híbrida, DLP pre-inferencia (cédulas Módulo 10 + Presidio/spaCy), Azure OpenAI / vLLM local con cero entrenamiento y citación cerrada obligatoria.
    6. *Seguridad, IAM y Auditoría:* Keycloak / Entra ID (SSO, MFA), OPA / Cedar para políticas SoD del DPO, HashiCorp Vault (TLS 1.3, AES-256), immudb / hash chain append-only, ClamAV + magic bytes.
    7. *Infraestructura y DevOps:* Docker (multi-stage non-root), Kubernetes, Helm, Terraform, CI/CD, OpenTelemetry + Prometheus + Grafana + Loki.
    8. *Arnés de Verificación Exógeno:* `ejecutar_arnes_verificacion.bat`, linters AST, validación UTF-8 estricta sin BOM, cero huellas abiertas y Exit Code 0 (21/21 tests).
*   **Cinco Antipatrones Prohibidos:** Prohibición explícita de: (1) Low-code cerrado / plataformas propietarias; (2) Formularios estáticos sin evidencia verificable ($E1+$); (3) IA generativa sin citación oficial cerrada; (4) Neo4j como fuente primaria de verdad (rompe ACID y RLS; solo admisible como proyección read-only); (5) Promedios escalares engañosos.
*   **Aislamiento Multi-Tenant Hermético:** Segregación lógica y criptográfica estricta en base de datos mediante RLS (`tenant_id`) y vector stores aislados.
*   **Identidad y Accesos:** IAM con soporte SSO (Entra ID, Google Workspace), MFA obligatorio y roles granulares RBAC/ABAC con SoD del DPO.
*   **Cifrado Integral:** Cifrado en tránsito (TLS 1.3) y en reposo (AES-256) con gestión centralizada de llaves.
*   **Logs Inalterables (Tamper-evident):** Registro de auditoría inmutable de accesos, mutaciones y aprobaciones mediante hash chain append-only.
*   **Arquitectura de Salas ADPA:** Backend modular desacoplado en salas herméticas comunicadas exclusivamente por compuertas `_service.py`.

---

## 8. Lineamientos de Diseño Frontend (Estilo Antigravity / Cursor / Render.com)
*   **Command Palette Universal (`Ctrl + K` / `Cmd + K`):** Búsqueda instantánea de cualquier artículo, control, cliente o documento sin tocar el ratón.
*   **Paneles Divididos (Split Panes):** Vista simultánea del árbol de navegación, formulario de trabajo y asistente contextual RAG lateral.
*   **Estética Render.com & Jerarquía Tonal Invertida:**
    *   *Fondo Base (Oscuro Absoluto):* `#0a0a0c`.
    *   *Contenedores y Paneles:* `#141417`.
    *   *Bordes y Separadores:* `#26262b`.
    *   *Acentos Semánticos y CTA:* Gradientes vibrantes Púrpura-Azul (`linear-gradient(135deg, #9a3bf1, #3892f3)`).
    *   *Estados Notariales:* Éxito (`#00c853`), Error/Purga (`#ff1744`), Advertencia (`#ffab00`).
    *   *Base Acromática:* Eliminación de azules distractores en elementos estáticos para mitigar fatiga visual en auditorías de datos intensivas.
    *   *Jerarquía Tonal Invertida:* Dock lateral y menús con menor luminancia para concentrar la atención foveal en el canvas central de trabajo.
*   **Dock Dinámico Plegable:** Menú lateral dinámico sin rótulos redundantes ("Salas de cumplimiento") que compriman los íconos; despliegue asistido y botón de abatimiento.
*   **Dual-Theme Purificado:** Tema claro en escala de grises de alta luminosidad sin artefactos oscuros residuales; tema oscuro de alto contraste técnico.

---

## 9. Criterios de Aceptación Clave (MVP)
1. **SoD del DPO:** La base de datos y la UI bloquean cualquier intento de asignar al DPO como dueño de control operativo o ejecutor de EIPD.
2. **Precondición de Evidencia:** Ningún control alcanza estado "Conforme" o madurez $\ge 2$ sin evidencia $E1+$ o rationale formal validado.
3. **Timebox 60 Minutos:** El motor de diagnóstico no muestra más de 80 preguntas en una sesión y genera el informe ejecutivo automáticamente.
4. **Compliance Graph Unificado:** El RAT alimenta unívocamente riesgos, transferencias y EIPD; no existen matrices paralelas.
5. **Copiloto RAG Confiable:** Toda respuesta normativa incluye cita textual a la fuente oficial; en ausencia de norma, declara incertidumbre.
6. **Ergonomía IDE:** Interfaz con Command Palette `Ctrl+K`, Split Panes y soporte nativo Dark/Light mode.
> **6. Ecosistema de Librerías del IDE (MVP):**
> - Utiliza `cmdk` para sentar las bases de la Command Palette (`Ctrl+K`).
> - Implementa `react-resizable-panels` para la división del layout en tres Split Panes ajustables (Sidebar, Formulario, Chat de IA).
> - Configura la zona de arrastre de archivos usando `react-dropzone` conectada directamente a la lógica de validación condicional de Zustand según la normativa activa.
7. **Desacoplamiento de Ficha Organizacional:** Pestaña superior independiente con sincronización global vía `useAuditStore` que parametriza la empresa antes de instanciar preguntas.
8. **Whitelist Evidencial y Purga Atómica:** Control Poka-Yoke dinámico por normativa (`.pdf,.docx,.md,.txt` para PI; formatos estructurados para NIIF/ISO) con purga automática al alternar dominio regulatorio.
9. **Arbitraje Exógeno Determinista:** Aprobación del arnés físico en disco (`ejecutar_arnes_verificacion.bat`) con 21/21 tests y Exit Code 0 antes de todo pase a producción.


---
*Documento de Requerimientos de Producto vivo y alineado al tratado epistémico del proyecto.*
