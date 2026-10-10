# Product Requirements Document (PRD) — JUBYS Plataforma LOPDP 360
`¤artefactos-prd`
`¤rat` `¤diagnostico` `¤dpo-cockpit` `¤frontend-ide` `¤regulation-code`
`¤roadmap` `¤rbac-tenant`

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


### 3.1 Roles del Módulo Hoja de Ruta Inteligente (RBAC por tenant)
Los perfiles anteriores describen a las personas que usan la plataforma; el módulo Hoja de Ruta (Módulo 5) los materializa en **cinco roles de sistema**, asignados por tenant en `user_tenant_roles` y, cuando aplica, acotados a un área. El detalle de permisos está en el Módulo 5, §5.2.

| Rol de sistema | Alcance | Función principal |
| :--- | :--- | :--- |
| `responsable_area` | Un área (y sus subáreas) | Ejecuta las tareas de su área y **sube evidencia**. |
| `encargado` | Toda la organización | **Supervisa**, distribuye tareas entre responsables y valida evidencia. |
| `dpo` | Toda la organización | **Audita**: valida o rechaza evidencia y consulta el audit log; no ejecuta ni edita. |
| `implementador` | Toda la organización | **Genera la hoja de ruta con IA**, edita tareas y cierra por implementación. |
| `admin_organizacion` | Toda la organización | Gestiona miembros, áreas y asignación de roles. |

El alias heredado `GESTOR_PROCESO` se resuelve internamente a `encargado`.

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

### Módulo 5: Hoja de Ruta Inteligente (`¤roadmap` `¤rbac-tenant`)
**Objetivo.** Convertir el Reporte de Assessment SGPDP (estático) en un módulo interactivo: el usuario completa variables de planeación, la IA genera una hoja de ruta personalizada, y esta se expresa como **tareas** con check de cumplimiento y carga de **evidencia**, operadas por cada rol según su función, aisladas por organización y con trazabilidad auditable. Base legal: LOPDP (Ecuador).

#### 5.1 Arquitectura: salas ADPA y núcleo compartido
El módulo se confina en dos salas herméticas; toda dependencia entre ellas transita por compuertas `_service.py` ($\text{ImportsCruzados} \equiv \emptyset$).

| Componente | Ubicación objetivo | Responsabilidad | Compuerta pública |
| :--- | :--- | :--- | :--- |
| Sala **Organización** (`¤rbac-tenant`) | `features/organizacion/` | Usuarios, áreas, asignación de roles, SoD del DPO, cuatro ojos, alcance por área. | `organizacion_service.py` |
| Sala **Hoja de Ruta** (`¤roadmap`) | `features/roadmap/` | Generación con IA, olas y tareas, evidencia, KPIs, audit log, worker. | `roadmap_service.py` |
| Núcleo compartido (no es sala) | `app_core/` | Infraestructura sin reglas de negocio: `db/session.py` (única fuente de sesión), `queue/`, `storage/`, `ai/deepseek_client.py`, `security.py`, `config.py`. | — |
| Capa REST | `api/routers/roadmaps*.py`, `organizacion.py`, `api/rbac.py` | Importan **solo** la compuerta y los tipos de `domain/` de la sala. | — |
| Frontend | `frontend/src/components/modules/roadmap/` | Pestaña «Hoja de Ruta»; store propio `useRoadmapStore`. | Contrato OpenAPI congelado |

La sala Hoja de Ruta necesita las reglas de SoD y cuatro ojos de la sala Organización: las consume **únicamente** a través de `organizacion_service.py`.

#### 5.2 Matriz de permisos (normativa)
✅ puede · ❌ no puede · ⚠️ condicional. Esta matriz es el contrato que verifica `INV_LOPDP_ROADMAP_RBAC_MATRIX`.

| Acción | `responsable_area` | `encargado` | `dpo` | `implementador` | `admin_organizacion` |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Ver assessment | ✅ su área | ✅ | ✅ | ✅ | ✅ |
| Ver hoja de ruta | ✅ su área | ✅ | ✅ | ✅ | ✅ |
| Generar roadmap con IA | ❌ | ❌ | ❌ | ✅ | ❌ |
| Editar tareas (título, fechas, responsable, KPI, entregable) | ❌ | ❌ | ❌ | ✅ | ❌ |
| Marcar tarea completada | ❌ | ❌ | ❌ | ✅ | ❌ |
| Distribuir tareas a responsables | ❌ | ✅ | ❌ | ❌ | ❌ |
| Subir evidencia | ✅ | ⚠️ solo si no hay responsables de área | ❌ | ❌ | ❌ |
| Validar o rechazar evidencia | ❌ | ✅ | ✅ | ✅ | ❌ |
| Ver toda la evidencia | ❌ solo la suya | ✅ | ✅ | ✅ | ✅ |
| Ver audit log | ❌ | ✅ | ✅ | ✅ | ✅ |
| Gestionar usuarios | ❌ | ❌ solicita altas (§5.3.1); no las ejecuta | ❌ | ❌ | ✅ |
| Crear y editar áreas | ❌ | ❌ | ❌ | ❌ | ✅ |
| Asignar y revocar roles | ❌ | ❌ | ❌ | ❌ | ✅ |
| Solicitar el alta de un responsable de área | ❌ | ✅ | ❌ | ❌ | ❌ |
| Aprobar, rechazar y ejecutar el alta de un responsable | ❌ | ❌ | ❌ | ✅ | ❌ |

#### 5.3 Reglas de jerarquía y separación de funciones (SoD)
1. En una organización pequeña, el `encargado` puede actuar también como `responsable_area`; si existen responsables de área, el `encargado` deja de subir evidencia y solo supervisa.
2. Los responsables de área los da de alta el `implementador` a solicitud del `encargado`; el `encargado` no los crea directamente (flujo completo en §5.3.1).
3. El `dpo` y el `implementador` no modifican documentos ni evidencia: solo auditan.
4. **Bloqueos automáticos** (`INV_LOPDP_DPO_INDEPENDENCE`): `dpo` con `implementador` o con `encargado` activos en el mismo tenant ⟹ **409**; quien sube una evidencia no puede validarla ⟹ **403** (`INV_LOPDP_EVIDENCE_FOUR_EYES`); no se revoca el último `admin_organizacion` activo del tenant ⟹ **409**.
5. La restricción aplica solo a roles **activos** (`valid_to IS NULL OR valid_to > now()`); un DPO histórico no bloquea nuevas asignaciones.
6. Defensa en tres capas: trigger PL/pgSQL en `user_tenant_roles` (BD), validación en `organizacion_service` (servicio) y respuesta 409/403 (API).
7. Combinaciones permitidas: `dpo` + `admin_organizacion`; `dpo` + `responsable_area` sujeta a la regla de cuatro ojos.

##### 5.3.1 Flujo de alta de responsables de área
**Regla base:** *el encargado solicita, el implementador ejecuta.* Ningún rol completa el flujo solo ni puede saltarse pasos, y cada transición queda registrada. Fundamento: jerarquía (quien supervisa no configura la estructura), trazabilidad (un solo punto de creación y de auditoría) y consistencia con `INV_LOPDP_DPO_INDEPENDENCE`.

* **Actores:** `encargado` (solicita), `implementador` (analiza, aprueba o rechaza, y ejecuta), `admin_organizacion` (da de alta al usuario solo si todavía no existe en la plataforma) y `responsable_area` (rol que se asigna).
* **Estados:** `pendiente` → `aprobada` | `rechazada` | `cancelada`; `aprobada` → `ejecutada`. Cancela el `encargado` solo si está `pendiente`. Aprobar y ejecutar son pasos separados para permitir aprobación diferida o por lotes.
* **Validación del usuario destino:**

| Rol que ya tiene el usuario destino | Resultado |
| :--- | :--- |
| Ninguno, `admin_organizacion` o `implementador` | Aprobado |
| `responsable_area` en otra área | Aprobado (se permite más de un área) |
| `encargado` | Solo con `also_responsable = true` y organización micro o pequeña; en organización grande, 409 |
| `dpo` | **409** (`INV_LOPDP_DPO_INDEPENDENCE`) |

* **Otros rechazos:** el usuario ya es responsable de esa área (409); el implementador intenta asignarse a sí mismo (409); el `encargado` intenta ejecutar (403). Si el área no existe, el implementador la crea en el mismo acto; el aislamiento entre tenants lo garantiza el RLS.
* **Tamaño de la organización (decisión del Tech Lead: fallar cerrado):** se lee de `tenants.tamano`, que hoy está vacío en todos los tenants y no tiene ningún endpoint que lo escriba (RM-15). Valores válidos: `micro`, `pequena`, `mediana`, `corporativo` (los del banco de preguntas), protegidos con una restricción `CHECK`. Si es nulo o inválido, la asignación se rechaza con **409** y el error explícito `TENANT_SIZE_NOT_CONFIGURED` con `action_required: configure_tenant_size`. **No hay valor por defecto:** uno ocultaría un dato que nadie decidió. El `encargado` solo puede ser también `responsable_area` en organizaciones `micro` o `pequena`; en `mediana` y `corporativo` el rechazo es `SOD_VIOLATION`.
* **Defensa en tres capas de esa regla:** el servicio devuelve el error guiado; un trigger en `user_tenant_roles` valida **ambas direcciones** (insertar `responsable_area` a quien ya tiene `encargado` activo, e insertar `encargado` a quien ya tiene `responsable_area` activo) y **no depende del indicador `also_responsable`**, que el llamador podría falsear; ese indicador queda solo como dato para la interfaz (RM-16).
* **Datos:** tabla nueva `area_responsable_requests` (`id`, `tenant_id`, `area_id` opcional, `area_nombre_propuesto`, `user_id` opcional, `user_email_propuesto`, `justificacion`, `status`, `requested_by`, `requested_at`, `reviewed_by`, `reviewed_at`, `review_notes`, `executed_at`) con RLS por `tenant_id` y `GRANT` explícito al rol `lopdp_app` (las tablas nuevas no heredan permisos). Se añade `user_tenant_roles.request_id` (clave foránea opcional) para reconstruir solicitud, aprobación y rol asignado.
* **Ejecución atómica:** el `INSERT` en `user_tenant_roles`, el registro de auditoría y el cambio de estado ocurren en una sola transacción.
* **Auditoría (decisión del Tech Lead):** tabla genérica `audit_events` (`id`, `tenant_id`, `entity_type`, `entity_id`, `action`, `user_id`, `timestamp`, `payload`), append-only, con RLS y `FORCE ROW LEVEL SECURITY`, `lopdp_app` solo con `SELECT` e `INSERT` e índice por (`tenant_id`, `entity_type`, `entity_id`, `timestamp`) (RM-14). Registra las solicitudes de responsables (`responsable_request_created`, `_approved`, `_rejected`, `_executed`, `_cancelled`) y la asignación y revocación de roles, que hoy no dejan registro de eventos. `task_audit_log` se queda para las acciones sobre tareas: su `task_id` es obligatorio y sus registros se eliminan en cascada con la tarea (latente: ningún código de la aplicación borra tareas hoy).
* **Fase posterior:** notificaciones por correo y expiración automática de solicitudes pendientes tras 30 días.
* **Retención del registro de auditoría:** el plazo legal debe confirmarse antes de fijarlo en el sistema.

#### 5.4 Aislamiento multi-tenant (RLS efectivo)
* Tablas con RLS y `FORCE ROW LEVEL SECURITY`: `areas`, `roadmaps`, `roadmap_waves`, `roadmap_tasks`, `task_evidence`, `task_audit_log`, `user_tenant_roles`.
* Cada transacción fija el tenant con `set_config('app.current_tenant_id', :tid, true)` (nunca `SET LOCAL` con valor interpolado). `get_session` lee `X-Tenant-ID` y `X-User-ID` de las cabeceras; sin tenant fijado, las políticas devuelven 0 filas.
* La aplicación se conecta con un rol **sin `BYPASSRLS` ni propiedad de tablas** (`lopdp_app`); las migraciones usan el rol dueño. Con un rol dueño con `BYPASSRLS` las políticas serían inertes (`INV_LOPDP_APP_ROLE_NO_BYPASSRLS`).
* `task_audit_log` es append-only para la aplicación: `lopdp_app` solo tiene `SELECT` e `INSERT`.

#### 5.5 Trazabilidad
Cada acción relevante inserta un registro inmutable en `task_audit_log` (`id`, `task_id`, `tenant_id`, `action`, `user_id`, `timestamp`, `payload` JSON). Eventos auditados: cambio de estado de tarea, edición, asignación, subida de evidencia, validación o rechazo, generación o regeneración del roadmap, y asignación o revocación de roles.

#### 5.6 Contrato de API (`/api/v1`)
**Formato de error:** los errores de negocio conservan `detail` como texto y añaden `code` y `action_required` (compatible con los clientes actuales). Catálogo en `app_core/errors.py`: `TENANT_SIZE_NOT_CONFIGURED`, `SOD_VIOLATION`, `DPO_INDEPENDENCE_VIOLATED`, `SELF_VALIDATION_FORBIDDEN`, entre otros (RM-16).
| Endpoint | Método | Rol requerido | Estado |
| :--- | :--- | :--- | :--- |
| `/roadmaps/generate` | POST | `implementador` | Implementado |
| `/roadmaps/jobs/{job_id}` | GET | cualquier rol activo | Implementado |
| `/roadmaps/{id}` | GET | cualquier rol activo | Implementado |
| `/roadmaps/{id}/kpis` | GET | cualquier rol activo | Implementado |
| `/roadmaps/tasks/{id}` | PATCH (estado) | `implementador` | Implementado |
| `/roadmaps/tasks/{id}` | PATCH (campos de la tarea) | `implementador` | **Pendiente** (RM-07) |
| `/roadmaps/tasks/{id}/assign` | POST | `encargado` | **Pendiente** (RM-08) |
| `/roadmaps/{id}/audit-log` | GET | `encargado`, `dpo`, `implementador`, `admin_organizacion` | **Pendiente** (RM-09) |
| `/roadmaps/tasks/{id}/evidence/upload-url` | POST | `responsable_area`, `encargado` | Implementado |
| `/roadmaps/tasks/{id}/evidence` | POST / GET | `responsable_area`, `encargado` / cualquier rol activo | Implementado |
| `/roadmaps/tasks/{id}/evidence/{eid}` | PATCH | `encargado`, `dpo`, `implementador` | Implementado |
| `/organizacion/me/roles` | GET | cualquier rol activo | Implementado |
| `/organizacion/usuarios`, `/areas`, `/roles` | GET / POST / PATCH / DELETE | `admin_organizacion` | Implementado |
| `/organizacion/configuracion` | GET / PATCH (tamaño y sector) | cualquier rol activo (GET); `admin_organizacion` (PATCH) | **Pendiente** (RM-15) |
| `/areas/responsable-requests` | POST | `encargado` | **Pendiente** (RM-10) |
| `/areas/responsable-requests` y `/areas/responsable-requests/{id}` | GET | `encargado`, `implementador` | **Pendiente** (RM-10) |
| `/areas/responsable-requests/{id}` | PATCH (cancelar si `pendiente`) | `encargado` | **Pendiente** (RM-10) |
| `/areas/responsable-requests/{id}/approve` y `/reject` | POST | `implementador` | **Pendiente** (RM-10) |
| `/areas/responsable-requests/{id}/execute` | POST | `implementador` | **Pendiente** (RM-10) |

#### 5.7 Identidad y requisitos de despliegue
* **Identidad (brecha conocida):** hoy el módulo identifica al usuario por las cabeceras `X-User-ID`, `X-Tenant-ID` y `X-Role`, que **envía el propio cliente**; el servidor solo verifica que esa combinación exista y esté activa en `user_tenant_roles`. Quien conozca un identificador válido puede suplantarlo. **Requisito previo a producción con clientes reales:** **SSO con Google (OIDC)**, decisión del usuario. El servidor valida el token de identidad (emisor, audiencia, vigencia y correo verificado) y obtiene de él **solo quién es el usuario**; el tenant y el rol que declare el cliente se autorizan contra `user_tenant_roles` del usuario ya verificado y nunca se aceptan por sí solos (tarea SEC-03). La cuenta se vincula por correo verificado y se guarda el identificador estable de Google (`sub`).
* **Generación con IA (decisión D-1):** en la etapa de prueba, con el plan gratuito (Hobby) de Vercel, cuyas funciones admiten hasta 300 s, la generación se ejecuta **en línea** en la propia solicitud, sin worker ni cola. Las llamadas medidas duran de 13 a 19 s. Se reevaluará una cola con entrega HTTP cuando haya volumen o la generación se acerque al límite (tarea RM-13).
* La carga de evidencia usa URLs prefirmadas de Cloudflare R2; el entorno de producción y de vista previa necesita las variables de R2 y, mientras el estado de los trabajos siga allí, de Redis, además de `DATABASE_URL` (rol `lopdp_app`), `JWT_SECRET`, `CORS_ORIGINS` y la clave del proveedor de IA.
* Verificación exógena del despliegue: `GET /api/v1/health` ⟹ 200, `OPERATIONAL` y todos los routers cargados (503 y `DEGRADED` si alguno falló).

#### 5.8 Notificaciones
Quien tiene tareas asignadas recibe **notificaciones sobre ellas** (decisión del usuario), **solo por correo**. Como mínimo, al asignársele una tarea (`POST /roadmaps/tasks/{id}/assign`); los demás eventos (cambio de estado, validación o rechazo de su evidencia) están por definir (NOTIF-01). El correo lleva el mínimo de datos (enlace a la tarea, sin contenido de evidencias) y se agrupa por usuario y por lote para respetar el límite diario del proveedor. Proveedor propuesto: Resend (plan gratuito: 3 000 correos al mes y 100 al día), por confirmar; exige verificar un dominio remitente. Es una sala propia, `features/notificaciones/`, que recibe los eventos por su compuerta: las demás salas no envían mensajes por su cuenta. Respeta el aislamiento por tenant. Las notificaciones de las solicitudes de alta de responsables (§5.3.1) siguen siendo de fase posterior.

#### 5.9 Fases fuera del alcance inmediato
* **Firma electrónica** de evidencia y actas mediante entidad de certificación acreditada por la ARCOTEL: el proveedor definido es **ANF**; falta diseñar la sala (FIRMA-01).
* **Integración de arbitraje ZERAG ↔ agente de código** por transporte `stdio`.

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
*   **Aislamiento Multi-Tenant Hermético:** Segregación lógica y criptográfica estricta en base de datos mediante RLS (`tenant_id`) y vector stores aislados. La aplicación opera con un rol de base de datos **sin `BYPASSRLS` ni propiedad de tablas** y con `FORCE ROW LEVEL SECURITY` (Módulo 5, §5.4).
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
10. **Matriz de Permisos de la Hoja de Ruta:** cada par (rol, endpoint) responde según el Módulo 5, §5.2; ninguna fila de `tests/test_matriz_permisos.py` queda marcada como pendiente.
11. **RLS Efectivo:** con la conexión de la aplicación, un tenant ajeno o sin tenant fijado ve 0 filas de las 7 tablas con RLS; `lopdp_app` no tiene `BYPASSRLS`.
12. **Hoja de Ruta de Punta a Punta:** un `implementador` genera el roadmap, el `encargado` distribuye tareas, el `responsable_area` sube evidencia y el `dpo` la valida, con registro en `task_audit_log` de cada paso.
13. **Despliegue Verificable:** tras cada despliegue, `GET /api/v1/health` responde 200 con todos los routers cargados.


---
*Documento de Requerimientos de Producto vivo y alineado al tratado epistémico del proyecto.*
