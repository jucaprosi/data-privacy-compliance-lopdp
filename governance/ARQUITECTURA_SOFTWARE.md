# Documento de Arquitectura de Software (SAD) — JUBYS Plataforma LOPDP 360
`¤arquitectura`
`¤adpa` `¤seguridad-tenant` `¤frontend-ide` `¤regulation-code` `¤rat`

> **ESTATUS DEL DOCUMENTO:** Especificación Técnica y Arquitectura de Referencia (Clean-Room).  
> **Patrón Arquitectónico:** SaaS Multi-Tenant Modular basado en **Salas ADPA (Bulkheads)**, **Event-Driven Compliance Graph** y **Frontend IDE-Grade**.  
> **Objetivo:** Garantizar desacoplamiento modular estricto ($\text{ImportsCruzados} \equiv \emptyset$), escalabilidad horizontal, seguridad con Cero Confianza y segregación criptográfica de funciones (SoD).

---

## 1. Visión Global y Estilo Arquitectónico (Stack Empresarial de 8 Capas)

La plataforma no se concibe como un monolito tradicional ni como un conjunto caótico de microservicios dispersos; adopta el patrón **Modular Monolith con Mamparos Estancos ADPA**, evolucionable hacia microservicios distribuidos mediante compuertas de servicio bien definidas. Conforme a la directiva técnica del **Tech Lead**, la arquitectura se estructura en **8 Capas Empresariales Herméticas** orientadas a la auditabilidad, aislamiento multi-tenant, trazabilidad normativa y estricta Segregación de Funciones (SoD):

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                        CAPA 1: FRONTEND IDE (ERGONOMÍA ANTIGRAVITY / RENDER)                    │
│   Next.js 15.5+ (Turbopack) · React 19 · Zustand · cmdk (Ctrl+K) · react-resizable-panels       │
│   react-dropzone (Validación Poka-Yoke) · Tailwind CSS v4 · TanStack Query · Playwright + Vitest│
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ HTTPS / WSS / REST / SSE (OpenAPI v3 Contract)
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│                         CAPA 2: BACKEND ADPA (MAMPAROS ESTANCOS EN PYTHON)                      │
│   Python 3.12+ · FastAPI · Pydantic v2 · Compuertas _service.py (ImportsCruzados ≡ ∅)           │
│   SQLAlchemy 2.0 + Alembic · Redis (Cache/Colas) · Temporal/Camunda (Workflows CAPA con SLAs)   │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Inyección de Contexto, Tenant Claims & AST Audit
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│                    CAPA 3: DATOS Y COMPLIANCE GRAPH (SSOT TRANSACCIONAL)                        │
│   PostgreSQL 16 (SSOT) · Row-Level Security (tenant_id UUID) · Apache AGE / CTE Recursivos       │
│   pgvector (Embeddings en perímetro transaccional) · JSONB (RAT/EIPD) · MinIO S3 (WORM SHA-256) │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Traza Ontológica: Fuente → RAT → Control → DPO
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│                     CAPA 4: REGULATION AS CODE (CORPUS NORMATIVO VERSIONADO)                    │
│   Git + YAML/JSON + JSON Schema (LOPDP, RGLOPDP, SPDP 2024-2026) · Motor de Diff en Python     │
│   Snapshots Inmutables por Auditoría · OpenSearch / Meilisearch (Full-Text & Semver Legal)     │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Ingesta Normativa & Citación Cerrada
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│                  CAPA 5: COPILOTO IA RAG DE CONFIANZA CERO (ZERO-TRUST COMPLIANCE)              │
│   LangChain / LlamaIndex · Búsqueda Híbrida (pgvector + OpenSearch) · DLP Pre-Inferencia        │
│   (Módulo 10 Cédulas EC + Presidio/spaCy) · Azure OpenAI / vLLM Local (Zero Training & Citas)   │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Directivas Criptográficas & Aislamiento
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│                   CAPA 6: SEGURIDAD, IAM Y AUDITORÍA (SEGREGACIÓN SOD CRIPTOGRÁFICA)            │
│   Keycloak / Auth0 / Entra ID (SSO, MFA) · OPA / Cedar (Políticas SoD DPO) · HashiCorp Vault    │
│   immudb / Hash-Chain Append-Only (Logs Tamper-Evident) · ClamAV + Magic Bytes Whitelist       │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Aprovisionamiento Declarativo & Métricas
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│                     CAPA 7: INFRAESTRUCTURA, CONTENEDORES Y DEVOPS                              │
│   Docker (Multi-stage Non-Root) · Kubernetes + Helm + Terraform · GitHub Actions / GitLab CI   │
│   OpenTelemetry + Prometheus + Grafana + Loki · Testcontainers + pytest + k6                   │
└───────────────────────────────────────────────┬─────────────────────────────────────────────────┘
                                                │ Arbitraje Booleano Exógeno {0, 1}
┌───────────────────────────────────────────────▼─────────────────────────────────────────────────┐
│                  CAPA 8: ARNÉS DE VERIFICACIÓN EXÓGENO (TEOREMA PROAÑO-GEMINI-DIJKSTRA)         │
│   ejecutar_arnes_verificacion.bat · Pytest (Salas ADPA) · Linters AST · Validación UTF-8 BOM    │
│   Purga Atómica Multirregulatoria · Cero Huellas Abiertas · Cero Regresiones (Exit Code 0)      │
└─────────────────────────────────────────────────────────────────────────────────────────────────┘
```

### 1.1 Desglose de Responsabilidades por Capa

1. **Capa 1 — Frontend IDE:**
   - Diseñado bajo la ergonomía de herramientas de desarrollo avanzadas (Antigravity / Cursor / Render.com).
   - Componentes principales: `cmdk` para Command Palette universal (`Ctrl+K`), `react-resizable-panels` para los 3 Split Panes, `react-dropzone` integrado con validación condicional por normativa y `Tailwind CSS v4` con jerarquía tonal invertida acromática.
   - Gestión de estado: `Zustand` (`useAuditStore`) para estado de sesión y `TanStack Query` para sincronización con caché del servidor. Pruebas visuales mediante `Playwright` y `Vitest`.
2. **Capa 2 — Backend ADPA:**
   - Modular Monolith particionado en salas estancas dentro de `features/`.
   - Compuertas públicas `_service.py` como único punto de contacto entre salas ($\text{ImportsCruzados} \equiv \emptyset$).
   - Contratos de API unificados con OpenAPI y Pydantic v2; motor de workflows `Temporal` / `Camunda` para orquestación de tickets CAPA y alertas normativas con SLAs estrictos.
3. **Capa 3 — Datos y Compliance Graph:**
   - **PostgreSQL 16 como Fuente Única de Verdad (SSOT)** transaccional con `tenant_id UUID NOT NULL` forzado por Row-Level Security (RLS).
   - Grafo de cumplimiento implementado mediante Apache AGE o Common Table Expressions (CTE) recursivos en PostgreSQL.
   - `pgvector` para indexación semántica en el mismo límite de seguridad de los datos.
   - Almacenamiento de evidencias en MinIO / S3 con retención inmutable WORM (Write Once, Read Many) y sellado de integridad SHA-256.
4. **Capa 4 — Regulation as Code:**
   - Corpus normativo ecuatoriano (LOPDP, Reglamento, Resoluciones SPDP 2024–2026) versionado como código estructurado en Git con esquemas JSON/YAML.
   - Motor de diff en Python que calcula el impacto sobre los tratamientos sin alterar auditorías congeladas; OpenSearch / Meilisearch para búsqueda textual exhaustiva.
5. **Capa 5 — Copiloto IA RAG de Confianza Cero:**
   - Orquestación con LangChain / LlamaIndex con política estricta de citación oficial cerrada (*"sin artículo o resolución formal, no hay respuesta"*).
   - Filtro DLP pre-inferencia obligatorio: validación algorítmica Módulo 10 para cédulas y RUC ecuatorianos más sanitización de PII sensible con Presidio/spaCy.
   - Modelos hosteados en Azure OpenAI o vLLM on-premise con cláusula contractual de cero re-entrenamiento.
6. **Capa 6 — Seguridad, IAM y Auditoría:**
   - Autenticación federada (SSO/MFA) con Keycloak / Entra ID.
   - Motor de políticas desacoplado con OPA / Cedar para hacer cumplir las reglas inviolables de Segregación de Funciones (SoD) del DPO.
   - Custodia criptográfica de secretos en HashiCorp Vault y bitácora de auditoría inalterable (*tamper-evident*) mediante cadena de bloques de hashes append-only.
7. **Capa 7 — Infraestructura y DevOps:**
   - Contenedores Docker multi-stage securizados, manifiestos de Kubernetes y despliegues reproducibles con Terraform.
   - Observabilidad completa mediante OpenTelemetry, Prometheus y Grafana.
8. **Capa 8 — Arnés de Verificación Exógeno:**
   - Ejecutable físico en disco (`ejecutar_arnes_verificacion.bat`) que actúa como árbitro matemático exógeno bajo el Teorema de Proaño-Gemini-Dijkstra.
   - Evalúa contratos booleanos estrictos: linters AST de mamparos ADPA, verificación de codificación UTF-8 sin BOM, ausencia de huellas de desarrollo abiertas y ejecución de suites de pruebas con Exit Code 0.

### 1.2 Antipatrones Arquitectónicos Prohibidos

Para preservar la integridad del sistema y evitar fallas sistémicas, se establecen los siguientes **Cinco Antipatrones Prohibidos**:

*   ❌ **Antipadrón 1: Low-Code Cerrado / Plataformas Propietarias:**
    *   *Razón de exclusión:* Impide el versionado granular en Git, anula la trazabilidad matemática de cambios normativos, genera dependencia tecnológica cautiva (*vendor lock-in*) y dificulta auditorías de código independiente.
*   ❌ **Antipadrón 2: Formularios Estáticos y Autodeclaraciones Vacías:**
    *   *Razón de exclusión:* Un formulario estático desconectado de la ley viva propicia respuestas complacientes sin respaldo. Toda afirmación en la plataforma exige evidencia documental verificada ($E1+$) o un *rationale* formal justificado.
*   ❌ **Antipadrón 3: IA Generativa Desanclada (Sin Citación Cerrada):**
    *   *Razón de exclusión:* Respuestas de IA basadas en conocimiento probabilístico general sin citar el artículo específico de la LOPDP o resolución SPDP constituyen un riesgo jurídico grave en materia sancionatoria.
*   ❌ **Antipadrón 4: Base de Datos de Grafos (Neo4j) como Fuente Primaria de Verdad:**
    *   *Razón de exclusión:* Desincroniza el aislamiento transaccional ACID y debilita las políticas RLS por inquilino. PostgreSQL 16 es la única fuente primaria de verdad (SSOT); los grafos operan como proyecciones analíticas de solo lectura o mediante Apache AGE / CTE recursivos sobre el motor relacional.
*   ❌ **Antipadrón 5: Promedios Escalares Engañosos:**
    *   *Razón de exclusión:* Un porcentaje agregado (ej. *"89% de cumplimiento global"*) oculta brechas normativas letales (como la falta de consentimiento en datos sensibles de salud o transferencias internacionales ilegales). La conformidad es una cuadratura multidimensional no conmutable.

---

## 2. Estructura de Directorios y Salas ADPA

El backend se organiza en **Salas Herméticas** dentro de `features/`. Cada sala posee su propio modelo, lógica de negocio y pruebas unitarias. Ningún módulo externo puede importar archivos internos de una sala; toda comunicación transita de forma exclusiva a través de su compuerta pública `_service.py`.

```text
Plataforma LOPDP 360/
├── app_core/                         # Sala transversal de infraestructura
│   ├── config.py                     # Variables de entorno y settings tipados
│   ├── database.py                   # Engine asíncrono SQLAlchemy y pool de conexiones
│   ├── security.py                   # JWT, hashing Argon2, context var tenant_id
│   ├── tenant_middleware.py          # Resolución y aislamiento estricto de tenants
│   └── app_service.py                # Compuerta pública de infraestructura
│
├── features/                         # SALAS ADPA DE NEGOCIO (Mamparos Estancos)
│   ├── diagnostico/                  # Módulo 1: Assessment adaptativo (Timebox 60 min)
│   │   ├── domain/                   # Entidades puras y reglas de scoring
│   │   ├── services/                 # Motor de poda condicional (límite 80 preguntas)
│   │   ├── diagnostico_service.py    # COMPUERTA PÚBLICA DE LA SALA
│   │   └── tests/                    # Tests de sala autónomos
│   │
│   ├── rat/                          # Módulo 2: Registro de Actividades (SSOT / Master Record)
│   │   ├── domain/                   # Entidades de procesos, datos, finalidades, bases
│   │   ├── services/                 # Generación y versionado del RAT
│   │   ├── rat_service.py            # COMPUERTA PÚBLICA DE LA SALA
│   │   └── tests/
│   │
│   ├── riesgos_mtge/                 # Módulo 2B: Motor de Riesgos y Cálculo MTGE Gran Escala
│   │   ├── domain/                   # Matrices de calor, algoritmo paramétrico MTGE
│   │   ├── services/                 # Evaluación EIPD y disparador de obligaciones
│   │   ├── riesgos_service.py        # COMPUERTA PÚBLICA DE LA SALA
│   │   └── tests/
│   │
│   ├── dpo_cockpit/                  # Módulo 4: Cockpit DPD/DPO (SoD Criptográfica)
│   │   ├── domain/                   # Dictámenes, bitácora de diligencia, agenda
│   │   ├── services/                 # Supervisión Read-Only y canal de escalación
│   │   ├── dpo_service.py            # COMPUERTA PÚBLICA DE LA SALA
│   │   └── tests/
│   │
│   ├── auditoria_capa/               # Módulo 3: Auditorías LOPDP y Planes de Acción
│   │   ├── domain/                   # Checklists versionados, no conformidades, CAPA
│   │   ├── services/                 # Muestreo, verificación independiente de cierre
│   │   ├── auditoria_service.py      # COMPUERTA PÚBLICA DE LA SALA
│   │   └── tests/
│   │
│   ├── evidencias/                   # Módulo Transversal: Repositorio de Evidencias
│   │   ├── domain/                   # Metadatos EVD-AAAA-NNNN, hashes SHA-256
│   │   ├── services/                 # Sandbox, antimalware y escáner DLP preventivo
│   │   ├── evidencias_service.py     # COMPUERTA PÚBLICA DE LA SALA
│   │   └── tests/
│   │
│   └── regulacion_rag/               # Base de Conocimiento "Regulation as Code" y Copiloto
│       ├── domain/                   # Corpus legal versionado (LOPDP, resoluciones SPDP)
│       ├── services/                 # Diff normativo, embeddings vectoriales, RAG
│       ├── regulacion_service.py     # COMPUERTA PÚBLICA DE LA SALA
│       └── tests/
│
├── frontend/                         # Aplicación Web (Estilo Antigravity / Cursor)
│   ├── src/
│   │   ├── app/                      # Rutas de aplicación (App Router)
│   │   ├── components/               # Componentes atómicos e interactivos
│   │   │   ├── command-palette/      # Cmd/Ctrl+K Search Dialog
│   │   │   ├── split-pane/           # Layout de paneles ajustables
│   │   │   ├── ui/                   # Badges, tablas densas, inputs, dialogs
│   │   │   └── dpo/                  # Vistas segregadas de supervisión
│   │   ├── hooks/                    # Custom hooks de acceso a APIs y shortcuts
│   │   └── lib/                      # Cliente API tipado y utilitarios
│
└── governance/                       # Nido Vivo de Artefactos de Gobernanza
    ├── artefactos/                   # PRD, INVARIANTS, FUENTES, APORTES, VPA_MAP, TASKS
    ├── METODOLOGIAS.md
    └── DOCTRINAS.md
```

> **Detalle de módulo:** la arquitectura del módulo Hoja de Ruta Inteligente (salas `features/organizacion/` y `features/roadmap/`, convenciones para trabajo en paralelo, modelo de datos y contrato de API) está en `governance/arquitectura/HOJA_DE_RUTA_ADPA.md`.

---

## 3. Modelo de Datos Relacional y Aislamiento Multi-Tenant

### 3.1 Estrategia de Multi-Tenancy
*   **Aislamiento Lógico Fuerte mediante Row-Level Security (RLS) en PostgreSQL:**
    Cada tabla de negocio contiene la columna obligatoria `tenant_id UUID NOT NULL`.
    El motor de base de datos activa políticas RLS en tiempo de conexión mediante la variable de sesión:
    ```sql
    ALTER TABLE rat_actividades ENABLE ROW LEVEL SECURITY;
    CREATE POLICY tenant_isolation_policy ON rat_actividades
        USING (tenant_id = current_setting('app.current_tenant_id')::UUID);
    ```
    Ninguna consulta puede acceder a registros de otra organización, aun en caso de inyección SQL accidental en la capa de aplicación.

### 3.2 Esquema Core de Entidades (Compliance Graph)

```sql
-- 1. Tenants y Organizaciones
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    nombre_comercial VARCHAR(255) NOT NULL,
    razon_social VARCHAR(255) NOT NULL,
    ruc_identificacion VARCHAR(20) UNIQUE NOT NULL,
    sector VARCHAR(100) NOT NULL, -- Salud, Educación, Fintech, Retail, etc.
    tamano VARCHAR(50) NOT NULL,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- 2. Usuarios y Segregación de Funciones (SoD)
CREATE TYPE rol_usuario AS ENUM (
    'ADMIN_PLATAFORMA',
    'CONSULTOR_LIDER',
    'RESPONSABLE_TRATAMIENTO',
    'ENCARGADO_TRATAMIENTO',
    'DPD_DPO_INTERNO',
    'DPD_DPO_EXTERNO',
    'AUDITOR',
    'GESTOR_PROCESO'
);

CREATE TABLE usuarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE RESTRICT,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    rol rol_usuario NOT NULL,
    mfa_secret VARCHAR(255),
    mfa_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp(),
    CONSTRAINT uq_tenant_email UNIQUE(tenant_id, email)
);

-- 3. RAT Maestro (Single Source of Truth)
CREATE TABLE rat_actividades (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE RESTRICT,
    codigo_actividad VARCHAR(50) NOT NULL, -- ej. RAT-RH-001
    nombre VARCHAR(255) NOT NULL,
    area_responsable VARCHAR(150) NOT NULL,
    finalidad_principal TEXT NOT NULL,
    base_legal_primaria VARCHAR(100) NOT NULL, -- Consentimiento, Contrato, Ley, Interés Legítimo
    es_gran_escala BOOLEAN DEFAULT FALSE,
    requiere_eipd BOOLEAN DEFAULT FALSE,
    datos_sensibles BOOLEAN DEFAULT FALSE,
    version INT DEFAULT 1,
    estado VARCHAR(50) DEFAULT 'BORRADOR', -- BORRADOR, APROBADO, EN_REVISION
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- 4. Motor de Riesgos y MTGE
CREATE TABLE riesgos_tratamiento (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    rat_id UUID NOT NULL REFERENCES rat_actividades(id) ON DELETE CASCADE,
    amenaza TEXT NOT NULL,
    vulnerabilidad TEXT NOT NULL,
    probabilidad INT CHECK (probabilidad BETWEEN 1 AND 5),
    impacto INT CHECK (impacto BETWEEN 1 AND 5),
    riesgo_inherente INT GENERATED ALWAYS AS (probabilidad * impacto) STORED,
    riesgo_residual INT,
    rationale TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- 5. Repositorio de Evidencias y Reglas de Calidad
CREATE TABLE evidencias (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    codigo_evidencia VARCHAR(50) NOT NULL, -- EVD-2026-0001
    nombre_archivo VARCHAR(255) NOT NULL,
    storage_path TEXT NOT NULL,
    sha256_hash CHAR(64) NOT NULL,
    calidad_nivel VARCHAR(10) NOT NULL, -- E0, E1, E2, E3
    fecha_vigencia DATE NOT NULL,
    propietario_id UUID REFERENCES usuarios(id),
    verificado_por UUID REFERENCES usuarios(id),
    verificado_en TIMESTAMPTZ,
    dlp_estado VARCHAR(50) DEFAULT 'LIMPIO', -- LIMPIO, ALERTA_PII, REVISADO
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);

-- 6. Bitácora Inviolable del DPD/DPO (Append-Only)
CREATE TABLE dpo_bitacora_diligencia (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    dpo_id UUID NOT NULL REFERENCES usuarios(id),
    tipo_accion VARCHAR(100) NOT NULL, -- DICTAMEN, ADVERTENCIA, AUDITORIA, ESCALACION
    referencia_normativa TEXT NOT NULL,
    cuerpo_dictamen TEXT NOT NULL,
    acuse_recibo_gerencia TIMESTAMPTZ,
    hash_anterior CHAR(64), -- Encadenamiento criptográfico anti-manipulación
    created_at TIMESTAMPTZ DEFAULT clock_timestamp()
);
```

---

## 4. Arquitectura de Seguridad y Guardrails de Inteligencia Artificial

### 4.1 Inviolabilidad de SoD del DPO
Se define un constraint a nivel de base de datos y un validador en la compuerta `dpo_service.py`:
*   Si `rol == 'DPD_DPO_INTERNO'` o `'DPD_DPO_EXTERNO'`, la plataforma rechaza cualquier transacción que intente asignarlo como:
    *   `propietario_id` de una evidencia o control operativo.
    *   Ejecutor de remediación de un hallazgo CAPA.
    *   Aprobador de finalidades de negocio en el RAT.

### 4.2 Pipeline del Copiloto RAG con Filtro DLP Pre-Inferencia
1. **Entrada de Usuario:** Consulta jurídica o solicitud de borrador de política.
2. **Filtro DLP Local (Pre-Inferencia):**
   * El módulo `app_core/dlp_sanitizer.py` detecta mediante expresiones regulares y reconocimiento de entidades nombradas: cédulas de identidad ecuatorianas (algoritmo Módulo 10), números telefónicos, direcciones de correo y datos de salud.
   * Enmascara los valores sensibles: `[CEDULA_REDACTADA]`, `[EMAIL_REDACTADO]`.
3. **Búsqueda Vectorial Aislada (pgvector):**
   * La búsqueda semántica de fragmentos legales consulta exclusivamente la colección de la base de conocimiento oficial de la SPDP (leyes, decretos, resoluciones 2024–2026).
4. **Inferencia del LLM:**
   * Temperatura = 0.0 (determinista).
   * Prompt canónico: *"Responda únicamente en base al contexto normativo adjunto. Si la norma no contiene la respuesta, declare explícitamente incertidumbre. Cita obligatoria de artículo y resolución."*
5. **Post-Procesamiento:** Validación sintáctica de que la respuesta contiene citas normativas antes de ser renderizada en el cliente.

---

## 5. Arquitectura del Frontend (Estilo Antigravity / Cursor)

### 5.1 Especificación Tecnológica
*   **Framework:** Next.js 15.5.25 con Turbopack (React 19, TypeScript estricto).
*   **Gestión de Estado Global:** `zustand` (`src/store/useAuditStore.ts`) para manejo reactivo y atómico de `companyData`, `normativaSeleccionada`, `archivosCargados` e `isConfigured` con purga transaccional inmediata al cambiar de dominio.
*   **Estilos:** Tailwind CSS con variables CSS semánticas, paleta Render.com (`#0a0a0c`, `#141417`, `#26262b`), jerarquía tonal invertida y gradientes de acción (`#9a3bf1` a `#3892f3`).
*   **Librerías de UI:** Radix UI primitives (accesibilidad WAI-ARIA nativa) + Lucide Icons de tamaño natural en dock lateral dinámico con botón de abatimiento.
*   **Gestión de Paneles:** `react-resizable-panels` para soporte de Split Panes colapsables en tres áreas (Dock, Workspace, Copilot).
*   **Buscador Rápido:** `cmdk` para el Command Palette universal (`Ctrl+K`).
*   **Carga y Validación de Evidencias:** `react-dropzone` conectada directamente a la lógica de validación condicional y purga de `useAuditStore`.
*   **Ecosistema Proyectado (Próximas Fases):**
    *   *XState (Statecharts):* Modelado matemático de flujos de trabajo con SLAs normativos estrictos (ARCO+, notificación de brechas en <72h).
    *   *React Flow / VisX:* Renderizado visual interactivo del "Compliance Graph" y linaje del RAT.
    *   *Vercel AI SDK (`ai/react`):* Streaming de inferencia asistida con soporte para agentes RAG con Humano en el Circuito.
    *   *Vitest:* Suite de pruebas unitarias y de integración rápida para contratos y componentes React.

### 5.2 Estructura de Componentes Visuales y Ficha Antecedente

```
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│ [Topbar]  Plataforma LOPDP 360  │ Tenant: Acme Corp │ Rol: Consultor L. │ [Ctrl+K Command Palette]│
├───────────────────┬─────────────────────────────────────────────┬───────────────────────────────┤
│ [Dock Izquierdo]  │ [Panel Central de Trabajo]                  │ [Panel Derecho: Copiloto RAG] │
│                   │                                             │                               │
│ ⚙️ CONFIG PROYECTO │ 🏢 Ficha Organizacional & Árbol de Poda     │ 🤖 Asistente Jurídico SPDP    │
│   (useAuditStore) │ ─────────────────────────────────────────── │                               │
│                   │ Razón Social / Sector / Tamaño de Empresa   │ > ¿Aplica DPO obligatorio a   │
│ 📁 DIAGNÓSTICO    │ Selector Normativa: [ PI ▼ ]                │   este cliente?               │
│   (Banco Podado   │ Whitelist Dinámica: [.pdf,.docx,.md,.txt]   │                               │
│    <= 80 preg)    │ Evidencias: [Dropzone Reactivo Poka-Yoke]   │ ⚖️ Respuesta Oficial:         │
│                   │ [Comenzar Diagnóstico] ──(Navegación)───►   │ "Conforme al Art. 12.2 de la  │
│ 📋 RAT MAESTRO    │                                             │ Resolución 2026-0005, el      │
│   ├── Procesos    │ 📌 Evaluación Adaptativa (Session Timebox)  │ umbral MTGE se supera cuando: │
│   └── 60-min Eval │ Dominio: G06 - Gestión de Riesgos y EIPD   │ > ¿Aplica DPO obligatorio a   │
│                   │                                             │   este cliente?               │
│ 📋 RAT MAESTRO    │ P14: ¿Se realizan tratamientos a gran       │                               │
│   ├── Procesos    │ escala según Resolución SPDP 2026-0005?     │ ⚖️ Respuesta Oficial:         │
│   └── Bases Leg.  │ [ ] Sí   [ ] No   [ ] Pendiente de Val.     │ "Conforme al Art. 12.2 de la  │
│                   │                                             │ Resolución 2026-0005, el      │
│ 🛡️ DPO COCKPIT    │ Evidencia Requerida:                        │ umbral MTGE se supera cuando: │
│   ├── Dictámenes  │ [Subir Ficha MTGE] (Hash SHA-256 verificado)│ 1. Volumen > 50,000 titulares │
│   └── Diligencias │ Calidad: [E2 - Implementada]                │ 2. Datos sensibles continuos" │
│                   │                                             │                               │
│ 📊 DASHBOARD      │ [Botón: Guardar & Siguiente (Enter)]        │ [Insertar Cita en Rationale]  │
└───────────────────┴─────────────────────────────────────────────┴───────────────────────────────┘
```

---

## 6. Pipeline de Despliegue, CI/CD y Verificación Exógena

1. **Compilación y Linters de Código Limpio:**
   * `ruff` y `flake8` para Python; `eslint` y `prettier` para TypeScript.
   * `adpa_linter.py`: Comprueba que no existan imports relativos o directos entre carpetas hermanas de `features/` ($\text{ImportsCruzados} \equiv \emptyset$).
   * `utf8_linter.ps1`: Verifica ausencia de marcas BOM en todos los archivos.
2. **Suite de Tests de Integración:**
   * Pruebas de aislamiento RLS: Comprobación automatizada de que una consulta con `tenant_id_A` genera 0 resultados al intentar leer datos de `tenant_id_B`.
   * Pruebas de SoD: Validación de que la API rechaza con HTTP 403 cualquier intento de mutación operativa proveniente de un token con rol DPO.
3. **Contenedores y Orquestación:**
   * Dockerfiles multi-stage para backend y frontend con usuarios sin privilegios (`non-root`).
   * Despliegue mediante Docker Compose para desarrollo local y Kubernetes (Helm charts) para entornos de nube empresarial (Azure AKS / AWS EKS).
4. **Gobernanza Técnica y Rol del Tech Lead (`¤¤tech-lead`):**
   * El Tech Lead asume la custodia técnica unificada del sistema, asegurando la sincronización estricta entre la doctrina normativa y el código ejecutable.
   * **Alcance de Custodia Obligatoria:**
     * *Artefactos de Requerimientos y Tareas:* `PRD.md` y `TASKS.md`.
     * *Fundamentación Normativa y Operativa:* `INVARIANTS.md`, compendios doctrinales y metodológicos (BBAP).
     * *Diseño Técnico y Esquema de Datos:* `ARQUITECTURA_SOFTWARE.md`, `schema.sql`, DDL multi-tenant y compuertas ADPA `_service.py`.
     * *Tratados Científicos:* `APORTES_INEDITOS.md` y `FUENTES_Y_BIBLIOGRAFIA.md`.
     * *Árbitros Exógenos:* Arnés físico determinista (`ejecutar_arnes_verificacion.bat`), linters AST y suites de no-regresión (Exit Code 0).


---

## 7. Roadmap Técnico de Implementación

*   **Sprint 1 (Fundación & Core ADPA):**
    *   Configuración de base de datos PostgreSQL 16 con RLS y pool async.
    *   Implementación de `app_core/` (Auth, JWT, Tenant Middleware).
    *   Andamiaje de salas ADPA en `features/`.
*   **Sprint 2 (Diagnóstico & Scoring 60 min):**
    *   Motor de preguntas condicionales ($N \le 80$) en `features/diagnostico/`.
    *   Algoritmo de scoring multidimensional cuádruple.
    *   Generador automático de informe preliminar en PDF/Markdown.
*   **Sprint 3 (RAT Maestro & Compliance Graph):**
    *   CRUD relacional del RAT en `features/rat/`.
    *   Cálculo automático de MTGE y disparo de EIPD en `features/riesgos_mtge/`.
*   **Sprint 4 (DPO Cockpit & Frontend IDE):**
    *   Implementación del Shell de navegación Next.js con Command Palette `Ctrl+K`.
    *   Bandeja de dictámenes y bitácora inviolable en `features/dpo_cockpit/`.
*   **Sprint 5 (Copiloto RAG & Auditoría):**
    *   Indexación de resoluciones SPDP 2024–2026 en pgvector.
    *   Filtro DLP pre-inferencia y módulo de auditorías CAPA.
