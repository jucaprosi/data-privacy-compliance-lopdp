# Product Requirements Document (PRD) — JUBYS Plataforma LOPDP 360
`¤artefactos-prd`
`¤rat` `¤diagnostico` `¤dpo-cockpit` `¤frontend-ide` `¤regulation-code`
`¤roadmap` `¤rbac-tenant`

---

## 1. Resumen Ejecutivo y Marco Doctrinal
<!-- ¤adpa -->
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


<!-- ¤adpa/ -->

## 2. Objetivos del Producto
<!-- ¤adpa -->
*   **Diagnosticar:** Realizar evaluaciones iniciales en sesiones ágiles timeboxed de máximo 60 minutos con cota fija de 80 preguntas visibles.
*   **Implementar:** Transformar brechas en planes de trabajo con dueños, plazos, controles y evidencias trazables.
*   **Auditar:** Evaluar eficacia operativa, documentar hallazgos y accionar planes correctivos (CAPA) con verificación independiente.
*   **Supervisar (DPD/DPO):** Dotar al Delegado de un *cockpit* de supervisión independiente (Read-Only operacional) y bitácora inviolable de dictámenes.
*   **Actualizar:** Analizar el impacto de reformas normativas de la SPDP mediante un motor de diff regulatorio que previene la desactualización.

---


<!-- ¤adpa/ -->

## 3. Usuarios Objetivo, Roles y Segregación de Funciones (SoD)
<!-- ¤adpa -->
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
| `coordinador` | Toda la organización | **Supervisa**, distribuye tareas entre responsables y valida evidencia. |
| `dpo` | Toda la organización | **Audita**: valida o rechaza evidencia y consulta el audit log; no ejecuta ni edita. |
| `implementador` | Toda la organización | **Genera la hoja de ruta con IA**, edita tareas y cierra por implementación. |
| `admin_organizacion` | Toda la organización | Gestiona miembros, áreas y asignación de roles. |

### 3.2 Cuentas, cartera y pertenencia a varias organizaciones
Fuente: estructura funcional y documento maestro EVYDENTIA (27/10/2026); contraste en `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

La plataforma sirve a tres niveles de cuenta, de fuera hacia dentro:

| Nivel | Quién es | Qué tiene | Sala |
| :--- | :--- | :--- | :--- |
| Plataforma (operador) | SMARTCIDI | Paquetes normativos, plantillas maestras, planes y cupos, alta de cuentas y organizaciones | `plataforma`; no accede a datos de ningún tenant |
| Cuenta profesional | Consultora o partner que atiende a varias organizaciones | Cartera de organizaciones, equipo, plantillas propias (Biblioteca G) y marca | `organizacion` (pertenencia), `plataforma` (metadatos de cuenta) |
| Organización | Empresa o entidad pública; es el tenant | Perfil, sedes, áreas, inventario, documentos, evidencias y tareas | todas las salas de producto, aisladas por RLS |

Una organización puede contratar sin cuenta profesional: es su propia cartera de una. El grupo empresarial (varias organizaciones con consolidado) es fase posterior.

**Reglas**
1. El personal de la cuenta profesional entra en cada organización con el rol `implementador`. Una persona pertenece a varias organizaciones **solo** con los roles `dpo` o `implementador` en todas ellas (decisión del propietario, 2026-10-26; tarea ORG-13). Quien tiene `admin_organizacion`, `coordinador` o `responsable_area` pertenece a una sola.
2. El `dpo` no es la cuenta profesional ni forma parte de su equipo operativo: es la persona independiente que revisa, valida, dictamina y supervisa en cada organización donde está designada (`INV_LOPDP_DPO_INDEPENDENCE`). No edita plantillas, no genera documentos, no cierra tareas ni aprueba documentos.
3. La **cartera** de una persona son las organizaciones donde tiene un rol vigente, y nada más. Se obtiene por pertenencia (`mis_organizaciones`, ORG-13) y se elige en la interfaz (FE-21); nunca por despliegue ni por cabecera que envíe el cliente.
4. Copiar «de otra organización de la cartera» copia **solo estructura** (perfil tipo, tratamientos sugeridos, catálogos): nunca datos personales, evidencias ni respuestas. Es una acción explícita, registrada y reservada al `implementador` con rol vigente en ambas (`INV_LOPDP_TENANT_BULKHEAD`).
5. Las vistas de cartera (tablero, calendario de plazos, tareas vencidas) no abren la RLS: en primera fase se arman organización por organización con el contexto de tenant de cada consulta; cuando el volumen lo exija, con una proyección de contadores por organización sin datos personales, leída por pertenencia.


---


<!-- ¤adpa/ -->

## 4. Análisis de Mercado y Benchmarking Hexagonal
<!-- ¤adpa -->
El diseño funcional integra los mejores patrones de la industria global:
*   **Odoo:** Arquitectura de datos relacional donde el **RAT opera como Master Record**, centralizando y propagando el estado hacia riesgos, terceros y auditorías sin duplicar matrices.
*   **Antigravity / Cursor:** Ergonomía técnica de alta densidad, navegación por Command Palette (`Ctrl+K`), Split Panes contextuales y temas Dark/Light de alto contraste.
*   **Global Suite:** Cruce normativo multiestándar (LOPDP articulada con buenas prácticas ISO 27002 / ISO 27701) sin contaminar la naturaleza obligatoria de la ley local.
*   **Novoser:** Gestión de tickets de no conformidades (CAPA) con verificación independiente obligatoria y reloj de incidentes de seguridad con SLA.
*   **Pirani (Pirámid):** Democratización de la gestión de riesgos con matrices visuales intuitivas (3x3 y 5x5) comprensibles para usuarios no matemáticos.
*   **Isotools:** Automatización de recordatorios periódicos, alertas de caducidad de evidencias y workflows formales de aprobación documental.

---


<!-- ¤adpa/ -->

## 5. Módulos y Funcionalidades Principales
<!-- ¤adpa -->

> Cada módulo declara las **salas ADPA** que responden de él (`**Salas:**`). El catálogo de salas, con su ubicación y su compuerta, está en el apartado 7.1; cada tarea declara en su especificación la sala que la ejecuta.

### Mapa de navegación por menús
`¤frontend-ide` `¤roadmap`

La interfaz se organiza por el **trabajo del usuario** en nueve menús superiores (estructura funcional EVYDENTIA, 27/10/2026). Cada menú agrupa pantallas de uno o varios módulos de este apartado; **las salas no cambian**: el mapa es una capa de presentación. El contraste completo, con las brechas y las decisiones pendientes, está en `governance/apoyo/ESTRUCTURA_FUNCIONAL_EVYDENTIA.md`.

| Menú | Pantallas | Módulos del PRD |
| :--- | :--- | :--- |
| 1. Inicio (cartera) | Tablero de cartera, organizaciones, nueva organización, calendario de plazos, archivadas | 0, 4, 5 (§3.2) |
| 2. Diagnóstico | Assessment, reporte, hoja de ruta, comparativo | 1, 5 |
| 3. Inventario | Perfil, sedes y áreas, tratamientos (RAT), activos y sistemas, soportes, personas, encargados y terceros, clientes (si es encargado), titulares | 0, 2 |
| 4. Biblioteca | Documentos de la organización por tipo, plantillas, firmas, evidencias | 7, 0 (evidencias) |
| 5. Operación | Solicitudes de titulares, vulneraciones, consultas al DPO, formación | 2, 4 |
| 6. Riesgos y auditoría | Matriz de riesgos, evaluaciones de impacto, auditorías, controles periódicos, garantías de encargados | 2, 3 |
| 7. DPO | Panel, obligaciones, informe anual, registro SPDP, consultas atendidas | 4 |
| 8. Conocimiento | Normativa Ecuador, resúmenes y guías, cursos, ayuda | 6 (apartado 6) |
| 9. Configuración | Usuarios y roles, plantillas propias, paquetes normativos, marca blanca, plan y cupos, proveedores comunes, papelera, verificar documento, exportar datos | 5, 7, apartados 6 y 7 |

El Módulo 6 (NIIF 18) no entra en estos menús: es otro **paquete normativo**, elegido en el selector de paquete, con su propia navegación.

**Principio transversal: plan de acción único.** Todo hallazgo, venga del assessment, de una auditoría, de una evaluación de impacto, de una vulneración, de un tercero sin garantías o de un control periódico vencido, termina como tarea de la hoja de ruta con su origen trazable (Módulo 5, §5.10). Ningún módulo lleva su propia lista de medidas correctoras.

### Módulo 0: Configuración del Proyecto y Ficha Organizacional (Árbol de Poda)
`¤diagnostico-motor` `¤evidencias` `¤frontend-ide`
**Salas:** `diagnostico`, `evidencias`, `frontend`.
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
*   **Alta de organización en siete pasos (forma servidor de esta ficha; salas `organizacion` y `plataforma`):** (1) origen: plantilla sectorial, plantilla propia de la cuenta profesional o estructura copiada de otra organización (§3.2, regla 4); (2) perfil: razón social, RUC, sector, tamaño, pública o privada, responsable o encargado, actividades de riesgo (menores, biometría, videovigilancia, perfilamiento, transferencias internacionales, gran volumen de datos sensibles); (3) sedes y áreas; (4) tratamientos sugeridos por la plantilla, a aceptar, ajustar o descartar; (5) terceros y sistemas típicos del sector; (6) personas clave e invitaciones; (7) lanzar el assessment. Las medidas de seguridad y los documentos **no** se cargan en el alta: salen del assessment y de la hoja de ruta. El perfil vive en el servidor y antecede al cuestionario (Doctrina 9); cambiar el perfil de una organización activa no borra datos, solo sugiere lo que falta. El tamaño sin configurar falla cerrado (§5.3.1).

### Módulo 1: Diagnóstico de la Empresa (Discovery en 60 Minutos)
**Salas:** `diagnostico`, `preanalisis`.
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
*   **Assessment por dominios con responsables:** el `implementador` o el `coordinador` asigna dominios a responsables de área y ve el avance por persona; cada respuesta admite evidencia; guardado automático y reanudación. Responder «no aplica» exige justificación escrita.
*   **Revisión del DPO:** el `dpo` revisa los puntos clave con la grilla declarado-verificado (lo declarado, lo verificado, la evidencia, quién revisó) sin editar respuestas; una respuesta «no» o «parcial» en un control obligatorio genera un **hallazgo** automático (§5.10).
*   **Reporte congelado:** nivel por dominio en las cuatro dimensiones, hallazgos priorizados por severidad (obligatoriedad del requisito × riesgo del tratamiento), mapa de calor riesgo × madurez; cada emisión queda como versión con sello hash y los cambios posteriores crean otra versión. Ningún reporte muestra una cifra única de cumplimiento (Doctrina 4).
*   **Comparativo:** repetir el assessment conserva el anterior como línea base; el comparativo muestra la evolución por dominio y el avance del plan.
*   **Escala y cota:** la madurez sigue la escala 0–3 de este módulo y la cota de 80 preguntas (`INV_LOPDP_60MIN_TIMEBOX_LIMIT`); el promedio ponderado solo describe un dominio, nunca la organización.

### Módulo 2: Implementación y RAT Maestro
**Salas:** `rat`, `riesgos_mtge`, `derechos_arco`, `incidentes`, `terceros`, `transferencias`, `conservacion`.
*   **RAT Maestro (Single Source of Truth):** Catálogo estructurado de actividades de tratamiento, finalidades, bases jurídicas, categorías de datos, destinatarios y flujos.
*   **Motor MTGE y Gran Escala:** Algoritmo paramétrico (Resolución SPDP-SPD-2026-0005-R) que calcula el volumen, permanencia y alcance para activar forzosamente EIPD y DPO.
*   **Gestión de Derechos (ARCO+):** Intake multicanal, verificación proporcional de identidad, cronómetro de SLA normativo y expediente probatorio de respuesta.
*   **Incidentes y Vulneraciones:** Playbook adaptado a la Ley de Ciberseguridad 2026; reloj normativo de notificación a SPDP y CSIRT nacional.
*   **Terceros y Transferencias:** Registro de encargados, debida diligencia previa, cláusulas contractuales obligatorias y garantías de transferencias internacionales.
*   **Conservación y Supresión:** Tablas de retención, reglas de bloqueo legal y procedimientos de anonimización verificable.
*   **Inventario ampliado (menú Inventario):** además del RAT, la organización registra **activos y sistemas** (aplicaciones, nube, equipos; proveedor y ubicación de los datos; medidas por activo), **soportes** (dispositivos y respaldos; salidas y devoluciones), **personas** (solo lo necesario para asignar tareas, formación y firmas: nombre, cargo, área, correo; la cédula solo si la firma la exige, cifrada), **clientes** (cuando la organización actúa como encargada: para quién trata datos y contratos recibidos) y **titulares** (solo colectivos y registros de consentimiento o firma; nunca bases de titulares, Doctrina 8). Cada ficha se vincula a tratamientos y lleva panel lateral de hallazgos y tareas.
*   **RAT con validaciones y versiones:** fichas como responsable, encargado, corresponsable o de titularidad pública; campos mínimos (finalidad, base de legitimación, categorías de titulares y datos, datos sensibles, origen, destinatarios, transferencias internacionales, plazo de conservación, medidas, área, sistemas). Las validaciones las define el paquete normativo: datos sensibles exigen la condición que los habilita; menores, perfilamiento o biometría marcan para EIPD; un campo no conforme se muestra en rojo y genera hallazgo. Cada cambio crea versión con fecha y autor; dar de baja conserva el histórico. Exportación completa a XLSX y PDF.
*   **Terceros con hallazgos automáticos:** ficha de tercero con rol (encargado, destinatario, corresponsable, transferencia internacional), país, contrato, garantías, criticidad y próxima revisión. Un encargado sin contrato de encargo vigente genera hallazgo; una transferencia internacional sin garantía registrada genera hallazgo de alta severidad. El **cuestionario de garantías por portal externo** (enlace que caduca, evidencias, revisión conforme / corrección / rechazo, informe) es fase posterior y exige diseño de seguridad previo.
*   **Derechos de los titulares:** tipos de derecho según el paquete normativo (LOPDP: acceso, rectificación y actualización, eliminación, oposición, portabilidad, suspensión del tratamiento y no ser objeto de decisiones automatizadas (*)); registro por cualquier canal; verificación proporcional de identidad antes de responder; vencimiento calculado desde la recepción con el **plazo parámetro del paquete normativo** (LOPDP: 15 días (*), unidad por confirmar) y semáforo (en plazo, por vencer, vencida); modelos de respuesta por derecho y resultado; la respuesta enviada queda como evidencia. El **portal público** por organización es fase posterior con las mismas precondiciones de seguridad que el de encargados.
*   **Vulneraciones de seguridad (asistente de ocho secciones):** identificación (fechas de ocurrencia y detección, quién reporta, plazos calculados); tratamientos afectados; titulares y datos afectados; descripción y tipo (confidencialidad, integridad, disponibilidad); efectos y medidas; resolución y recuperación; decisión de notificar a la SPDP y comunicar a titulares con criterios configurables y **justificación guardada**; informes generados con el contenido mínimo de la norma técnica (Resolución SPDP-SPD-2026-0040-R, tarea LEG-02) y evidencia de la notificación. Plazos como parámetros del paquete: encargado → responsable 2 días (*), responsable → SPDP 5 días (*), titulares 3 días (*); nunca en texto fijo. Todo incidente queda registrado aunque no se notifique; cualquier colaborador puede reportar; si la organización es encargada, el flujo cambia a notificar al responsable; las lecciones aprendidas crean tareas (§5.10).
*   **Formación (sala `formacion`, fase posterior):** contenidos y banco de preguntas; acción formativa con personas, fechas, examen, nota mínima y diploma; seguimiento por persona y cobertura (personas formadas / personas que tratan datos). El diploma y las notas se guardan como evidencia del control de capacitación.

### Módulo 3: Auditorías LOPDP y CAPA
**Salas:** `auditoria_capa`.
*   **Programa de Auditoría:** Plan anual con snapshots congelados de la normativa vigente al momento del corte.
*   **Muestreo y Pruebas de Eficacia:** Registro de poblaciones, muestras y evidencias operativas revisadas.
*   **Gestión de Hallazgos y CAPA:** Flujo de no conformidades con análisis de causa raíz, acciones preventivas/correctivas y verificación de cierre independiente.
*   **Grilla de verificación:** auditoría por tratamiento o por dominio con lista generada desde los controles del paquete normativo; por fila: lo declarado, riesgo inicial, lo verificado, evidencia, riesgo final y quién revisó. Cierra con **acta de auditoría por área** (alcance, lo verificado, evidencia revisada); la plataforma no emite certificados de cumplimiento (Doctrina 1). Los hallazgos pasan a la hoja de ruta (§5.10).
*   **Controles periódicos:** revisiones con frecuencia (mensual, trimestral, anual) y responsable; una **evidencia vencida reabre el control**, genera aviso y hallazgo. Es la fuente de las alertas de caducidad de evidencias.
*   **Matriz de riesgos y EIPD guiada:** riesgo inherente y residual por tratamiento (amenaza, probabilidad, impacto, medidas) con mapa de calor; asistente de obligatoriedad con informe de la decisión; EIPD de ocho pasos (identificación precargada desde el RAT; consulta a titulares si aplica; ciclo de vida del dato y amenazas; necesidad y proporcionalidad; cumplimiento e incumplimientos que van a la hoja de ruta; riesgos para los derechos; decisión: aceptar, nuevas medidas o consulta previa a la SPDP (*); informe final). Un riesgo residual alto impide cerrar sin decisión documentada. Catálogos de amenazas y medidas en el paquete normativo; metodología de la SPDP (*). La obligatoriedad por MTGE sigue siendo determinista (`INV_LOPDP_MTGE_DETERMINISTIC_TRIGGER`).

### Módulo 4: Cockpit del DPD/DPO
**Salas:** `dpo_cockpit`.
*   **Supervisión Read-Only:** Visibilidad transversal sin interferir en la gestión operativa ni asumir propiedad de controles.
*   **Bandeja de Asesoría:** Emisión de dictámenes y recomendaciones técnicas versionadas, con acuse de recibo de la alta dirección.
*   **Bitácora de Diligencia:** Historial cronológico inviolable de advertencias y consultas atendidas.
*   **Gestión Multi-Cliente:** Portafolio seguro para DPOs externos con aislamiento estricto de expedientes.
*   **Panel del DPO (menú DPO):** organizaciones donde la persona tiene el rol `dpo` vigente (§3.2, regla 3), alertas y próximas obligaciones; **calendario de obligaciones** (revisiones, informes a la dirección, renovaciones); **informe anual** generado desde los datos de la plataforma, versionado con sello hash; **estado de inscripción ante la SPDP** y datos para el registro (*); **consultas atendidas**: tickets de la organización al DPO con historial como evidencia de asesoría.
*   **Lo que el DPO hace y no hace:** revisa el assessment con la grilla declarado-verificado, valida o rechaza evidencia, dictamina y supervisa; no edita plantillas ni documentos, no genera documentos, no distribuye ni cierra tareas, no aprueba documentos ni respuestas a titulares y no pertenece al equipo de la cuenta profesional (Doctrina 2, `INV_LOPDP_DPO_INDEPENDENCE`, §5.2).

### Módulo 5: Hoja de Ruta Inteligente (`¤roadmap` `¤rbac-tenant`)
**Salas:** `roadmap`, `organizacion`, `firma_electronica`, `notificaciones`, `frontend`.

**Objetivo.** Convertir el Reporte de Assessment SGPDP (estático) en un módulo interactivo: el usuario completa variables de planeación, la IA genera una hoja de ruta personalizada, y esta se expresa como **tareas** con check de cumplimiento y carga de **evidencia**, operadas por cada rol según su función, aisladas por organización y con trazabilidad auditable. Base legal: LOPDP (Ecuador).

> La arquitectura (salas, datos, contrato de API y despliegue) está en `governance/arquitectura/HOJA_DE_RUTA_ADPA.md`; las tareas, en `governance/tareas/`; el plan y las decisiones, en `governance/PLAN_HOJA_DE_RUTA_INTELIGENTE.md`. Este documento fija **qué** se exige, no cómo ni cuándo.

#### 5.1 Flujo
1. El `implementador` completa las variables de planeación (plazo, presupuesto, equipo, DPO, prioridades) y la IA genera la hoja de ruta a partir del Assessment.
2. La hoja de ruta son olas y tareas, cada una con responsable, entregable, KPI y estado.
3. El `coordinador` distribuye las tareas; los `responsable_area` las ejecutan y suben evidencia.
4. El `coordinador`, el `dpo` y el `implementador` validan o rechazan la evidencia; el `dpo` audita sin ejecutar.
5. Cada paso queda registrado de forma inmutable y consultable.

#### 5.2 Matriz de permisos (normativa)
✅ puede · ❌ no puede · ⚠️ condicional. Esta matriz es el contrato que verifica `INV_LOPDP_ROADMAP_RBAC_MATRIX`.

| Acción | `responsable_area` | `coordinador` | `dpo` | `implementador` | `admin_organizacion` |
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
| Crear y editar áreas | ❌ | ❌ | ❌ | ❌ | ❌ |
| Asignar y revocar roles | ❌ | ❌ | ❌ | ❌ | ✅ |
| Configurar la organización (tamaño y sector) | ❌ | ❌ | ❌ | ❌ | ✅ |
| Solicitar el alta de un responsable de área | ❌ | ✅ | ❌ | ❌ | ❌ |
| Aprobar, rechazar y ejecutar el alta de un responsable | ❌ | ❌ | ❌ | ✅ | ❌ |

#### 5.3 Reglas de jerarquía y separación de funciones (SoD)
1. En una organización pequeña, el `coordinador` puede actuar también como `responsable_area`; si existen responsables de área, el `coordinador` deja de subir evidencia y solo supervisa.
2. Los responsables de área los da de alta el `implementador` a solicitud del `coordinador`; el `coordinador` no los crea directamente (§5.3.1).
3. El `dpo` y el `implementador` no modifican documentos ni evidencia: solo auditan.
4. **Bloqueos automáticos** (`INV_LOPDP_DPO_INDEPENDENCE`): El `dpo` no puede tener ningún otro rol en la plataforma en el mismo tenant (`coordinador`, `implementador`, `responsable_area`, `admin_organizacion`) ⟹ **409** (Arts. 49 y 50 LOPDP; Arts. 15 a 18 del Reglamento del Delegado de Protección de Datos); quien sube una evidencia no puede validarla ⟹ **403** (`INV_LOPDP_EVIDENCE_FOUR_EYES`); no se revoca el último `admin_organizacion` activo del tenant ⟹ **409**.
5. La restricción aplica solo a roles **activos**; un DPO histórico no bloquea nuevas asignaciones.
6. Cada regla se aplica en tres capas: base de datos, servicio y respuesta de la API.
7. Combinaciones permitidas: el delegado no tiene ningún otro rol en la plataforma en el mismo tenant (independencia estricta del DPD). Las organizaciones cubren su independencia mediante contratación externa por servicios si su estructura es reducida (Art. 49 del Reglamento General).

##### 5.3.1 Flujo de alta de responsables de área
**Regla base:** *el coordinador solicita, el implementador ejecuta.* Ningún rol completa el flujo solo ni puede saltarse pasos, y cada transición queda registrada. Fundamento: jerarquía (quien supervisa no configura la estructura), trazabilidad (un solo punto de creación y de auditoría) y consistencia con `INV_LOPDP_DPO_INDEPENDENCE`.

* **Actores:** `coordinador` (solicita), `implementador` (analiza, aprueba o rechaza, y ejecuta), `admin_organizacion` (da de alta al usuario solo si todavía no existe) y `responsable_area` (rol que se asigna).
* **Estados:** `pendiente` → `aprobada` | `rechazada` | `cancelada`; `aprobada` → `ejecutada`. Cancela el `coordinador` solo si está `pendiente`. Aprobar y ejecutar son pasos separados, para permitir aprobación diferida o por lotes.
* **Validación del usuario destino:**

| Rol que ya tiene el usuario destino | Resultado |
| :--- | :--- |
| Ninguno, `admin_organizacion` o `implementador` | Aprobado |
| `responsable_area` en otra área | Aprobado (se permite más de un área) |
| `coordinador` | Solo en organización `micro` o `pequena`; en `mediana` o `corporativo`, 409 |
| `dpo` | **409** (`INV_LOPDP_DPO_INDEPENDENCE`) |

* **Otros rechazos:** el usuario ya es responsable de esa área (409); el implementador intenta asignarse a sí mismo (409); el `coordinador` intenta ejecutar (403). Si el área no existe, el implementador la crea en el mismo acto.
* **Tamaño de la organización: fallar cerrado.** Si el tamaño no está configurado, la asignación se rechaza con **409** y un error explícito que indica cómo resolverlo (`TENANT_SIZE_NOT_CONFIGURED`, acción `configure_tenant_size`). **No hay valor por defecto**: uno ocultaría un dato que nadie decidió. Valores válidos: `micro`, `pequena`, `mediana`, `corporativo`.
* **Fase posterior:** notificaciones por correo y expiración automática de las solicitudes pendientes tras 30 días.
* **Retención del registro de auditoría:** el plazo legal debe confirmarse antes de fijarlo en el sistema.

#### 5.4 Aislamiento multi-tenant
Un tenant nunca lee ni escribe datos de otro. El aislamiento lo impone la base de datos con RLS efectivo: la aplicación opera con un rol **sin `BYPASSRLS` y sin propiedad de las tablas**, y con `FORCE ROW LEVEL SECURITY`; un tenant ajeno, o ninguno, ve 0 filas. Los registros de auditoría son append-only para la aplicación.

#### 5.5 Trazabilidad
Cada acción relevante deja un registro inmutable: cambio de estado de tarea, edición, asignación, subida de evidencia, validación o rechazo, generación del roadmap, solicitudes de alta de responsables, asignación o revocación de roles y cambios de configuración. Lo consultan los roles que indica la matriz (§5.2).

#### 5.6 Identidad
**SSO con Google (OIDC)**, decisión del usuario. Hoy el módulo toma la identidad de cabeceras que **envía el propio cliente** (`X-User-ID`, `X-Tenant-ID`, `X-Role`): quien conozca un identificador válido puede suplantarlo. **Requisito previo a producción con clientes reales:** el servidor valida el token de identidad (emisor, audiencia, vigencia y correo verificado) y obtiene de él **solo quién es el usuario**; el tenant y el rol que declare el cliente se autorizan contra la pertenencia del usuario ya verificado y nunca se aceptan por sí solos.

#### 5.7 Generación con IA
* La IA devuelve un documento **válido y completo** conforme al esquema de la hoja de ruta; una respuesta inválida o cortada no se persiste y se reintenta con el error de validación.
* En la etapa de prueba (plan gratuito de Vercel, funciones de hasta 300 s) la generación se ejecuta **en línea** en la propia solicitud: las llamadas medidas duran de 13 a 19 s. Se reevaluará una cola cuando haya volumen.

#### 5.8 Notificaciones
Quien tiene tareas asignadas recibe **notificaciones sobre ellas**, **solo por correo** (decisión del usuario). Como mínimo, al asignársele una tarea; los demás eventos están por definir. El correo lleva el mínimo de datos (enlace a la tarea, sin contenido de evidencias) y se agrupa por usuario y por lote para respetar el límite diario del proveedor. Proveedor confirmado: Resend; exige verificar un dominio remitente. Las notificaciones de las solicitudes de alta de responsables siguen siendo de fase posterior.

#### 5.9 Fuera del alcance inmediato
* **Firma electrónica** de evidencia y actas con **ANF**, entidad de certificación acreditada por la ARCOTEL.
* **Integración de arbitraje ZERAG ↔ agente de código:** pertenece a ZERAG, no a este proyecto.

#### 5.10 Plan de acción único
1. **Hallazgo.** Entidad con origen (assessment, auditoría, EIPD, vulneración, tercero, control periódico), severidad, control afectado y organización. Lo producen los módulos 1, 2 y 3; nadie más crea tareas correctoras.
2. **Una sola compuerta.** Toda tarea nace por `roadmap_service` a partir de un hallazgo o de la generación con IA (§5.7); conserva el enlace a su origen y, cuando aplica, la plantilla sugerida del paquete normativo y la evidencia requerida.
3. **Vistas.** Lista, tablero por estado y cronograma; agrupación en olas o fases; vista de cartera con las tareas vencidas de todas las organizaciones de la persona (§3.2).
4. **Cierre.** Una tarea no se cierra sin evidencia validada por alguien distinto de quien la subió (`INV_LOPDP_EVIDENCE_FOUR_EYES`); la marca completada el `implementador` (§5.2). Aprobar un documento de la Biblioteca **adjunta** evidencia a la tarea vinculada; no la cierra ni acredita eficacia (Biblioteca D). El `dpo` no cierra tareas.
5. **Recordatorios.** Antes del vencimiento y al vencer, por correo y con el mínimo de datos (§5.8).
6. **Ningún módulo mantiene una lista propia de medidas correctoras.** Es la aplicación correctiva de la Doctrina 5.

### Módulo 6: Cumplimiento Contable y Normativo (NIIF 18)
`¤niif18`
**Salas:** `niif18`, `frontend`.
*   **Pipeline Lineal Reactivo (ADPA Strict):** Flujo obligatorio dividido en pasos estancos que previenen la regresión de datos contables: Ingesta $\rightarrow$ Reclasificación $\rightarrow$ Subtotales $\rightarrow$ MPM $\rightarrow$ Exportación XBRL.
*   **Motor Matemático y Conciliación:** Ingestión de Balances de Comprobación y cálculo automático de los nuevos subtotales obligatorios (Categoría Operativa, Inversión, Financiación, Impuestos).
*   **Medidas de Rendimiento de la Dirección (MPM):** Módulo de justificación doctrinal, registro de ajustes (recortes/añadidos sobre subtotales NIIF) y trazabilidad matemática hacia XBRL.
*   **Visor Doctrinal Integrado:** Acceso in-situ a las directrices de la IFRS para auditar la categorización del estado de resultados.

### Módulo 7: Biblioteca documental EVYDENTIA
`¤adpa` `¤rbac-tenant`
**Salas:** `biblioteca`, `frontend`, `pasillo_central` y compuertas de las salas colaboradoras.

La Biblioteca administra maestros documentales y documentos de cada organización sin confundir existencia, descarga, aprobación, implementación y eficacia. El catálogo maestro es global y solo admite escritura con capacidades editoriales explícitas. Las instancias, evidencias y decisiones de clientes permanecen aisladas por organización y se autorizan en el servidor.

#### Biblioteca A. Entregas acumulativas

| Entrega | Resultado visible | Puerta de salida |
| :--- | :--- | :--- |
| 1. Biblioteca descargable | Catálogo, ficha, descarga controlada, administración editorial y documentos externos por empresa | Acceso aislado, archivos revisados y publicación controlada |
| 2. Creación guiada | Formularios versionados, datos reutilizables, reglas explicables y generación DOCX/XLSX | Ocho esquemas probados, salidas fieles y recuperación de errores |
| 3. Gestión e integración | Revisión, aprobación, acciones, evidencias, conservación e indicadores | Trazabilidad completa y aceptación reproducible de extremo a extremo |

El alcance se descompone en 23 requisitos: BIB-101…108, BIB-201…208 y BIB-301…307. Sus 70 criterios de aceptación y propiedad de archivos están en `governance/tareas/BIB-*.md`. El orden y los contratos compartidos están en `governance/apoyo/BIBLIOTECA_PLAN.md`.

#### Biblioteca B. Catálogo e inventario inicial

El inventario de diseño contiene 50 códigos: ocho maestros v0.1 con archivo en revisión, dos salidas existentes por mapear y 40 elementos planificados. Un elemento planificado nunca se muestra como archivo disponible. Los originales y sus huellas se conservan en `data/biblioteca/kit_v1/`; su incorporación al repositorio no los publica ni los convierte en versiones aprobadas.

Los ocho maestros iniciales son INV-01, INV-02, RAT-01, LEG-01 y PLA-01 en XLSX, y EIPD-00, AVI-01 y PRO-01 en DOCX. Cada archivo requiere revisión editorial, técnica y jurídica aplicable antes de publicarse. La generación guiada se implementa en una entrega posterior y no depende de IA.

#### Biblioteca C. Roles y separación de funciones

Los permisos editoriales globales se separan en editor, revisor técnico, revisor jurídico y publicador. Ser administrador de una organización o de la plataforma no concede estas capacidades. Nadie revisa ni publica su propia versión. Mientras no existan asignaciones humanas explícitas, las mutaciones editoriales se deniegan por defecto.

El consultor asignado trabaja únicamente con organizaciones autorizadas; el dueño del proceso valida hechos y aporta evidencia; jurídico valida fundamentos; el responsable o delegado decide; el DPD asesora y supervisa con independencia; el auditor consulta el alcance autorizado. La autorización considera identidad, capacidad, organización, recurso, operación y estado.

#### Biblioteca D. Estados e inmutabilidad

Una versión maestra transita por elaboración, revisión técnica y jurídica, publicada, sustituida o retirada. Publicar exige archivo, ficha, responsable editorial y dictámenes independientes requeridos. Una versión publicada es inmutable: corregirla crea una sucesora y conserva archivo, checksum, decisiones e historial. Retirar impide nuevas instancias, sin borrar la evidencia histórica.

Los documentos de empresa tienen su propio ciclo: borrador, generado para revisión, en revisión, devuelto, aprobado, implementado, verificado eficaz, sustituido o archivado. Aprobar o descargar un documento no cierra una brecha ni acredita eficacia.

#### Biblioteca E. Reglas funcionales y trazabilidad

Los IDs se resuelven en el servidor y nunca prueban autorización. Las relaciones entre organización, tratamiento, requisito, brecha, acción, documento, evidencia y revisión validan el mismo ámbito. Los datos precargados conservan procedencia, versión, fecha y estado de validación. Los valores desconocidos permanecen como información insuficiente y no se convierten en “No”.

La generación usa una instantánea de datos, esquema y versión de plantilla, y conserva checksum. Los DOCX deben mantener estilos y tablas; los XLSX, tipos, fórmulas y validaciones. Los resultados no contienen instrucciones, ejemplos, bloques no aplicables ni variables sin resolver. Los borradores incompletos se identifican como tales.

#### Biblioteca F. Aceptación y límites

La aceptación incluye permisos negativos, aislamiento entre organizaciones, idempotencia, concurrencia, recuperación, fidelidad visual y trazabilidad. La aceptación final recorre tres perfiles ficticios —microempresa de servicios, centro médico y entidad pública— con datos sintéticos y sin asignaciones reales.

La importación inteligente de documentos externos, edición colaborativa de Word, firma electrónica, certificación automática de cumplimiento y producción de los otros 40 documentos quedan fuera del alcance comprometido. Las fuentes jurídicas y reglas de aplicabilidad requieren revisión versionada; ninguna recomendación automática sustituye una decisión humana autorizada.

El diseño detallado está en `governance/apoyo/BIBLIOTECA_DISENO.md`; el mapa de las ocho fichas, en `governance/apoyo/BIBLIOTECA_FICHAS_OCHO_PLANTILLAS.md`; los contratos JSON y originales, en `data/biblioteca/kit_v1/`.

#### Biblioteca G. Capas de plantillas, documentos por tipo y vínculos

Incorpora la estructura funcional EVYDENTIA (27/10/2026) sin alterar los apartados A a F.

**Tres capas de plantilla** (decisión pendiente del propietario: hoy el PRD define dos):

| Capa | Dueño | Quién escribe | Campos |
| :--- | :--- | :--- | :--- |
| Maestra | Catálogo global (SMARTCIDI) | Solo capacidades editoriales (Biblioteca C) | Paquete normativo, tipo, sector, naturaleza pública o privada, idioma, versión, estado, variables |
| De la cuenta profesional | Cuenta profesional (§3.2) | `implementador` de esa cuenta; nunca el `dpo` | Los de la maestra más plantilla de origen y marca; se aplica a varias organizaciones |
| De la organización | Tenant | Según la matriz §5.2 y las capacidades de la Biblioteca | Organización, plantilla y versión de origen, contenido, marca de editado, estado, aprobación, sello hash, vigencia y próxima revisión |

Si cambia una maestra, la plataforma avisa qué copias derivan de ella, permite comparar y aplicar; nunca aplica sola. Una capa inferior se edita sin tocar la superior.

**Documentos de la organización por tipo** (vista principal, con etiqueta de origen: basado en plantilla, propio o subido): avisos y cláusulas (generados desde el RAT, uno por tratamiento o por conjunto; variantes pública y privada), consentimientos (por finalidad y colectivo, con registro de aceptación), políticas, protocolos (derechos, vulneraciones, datos sensibles, transferencias, conservación), contratos (encargo, confidencialidad, corresponsabilidad; con variables y vencimiento), formularios de derechos, textos web, informes (RAT, reporte, EIPD, auditoría, informe del DPO). Los usuarios de la organización no ven el catálogo de plantillas.

**Vínculos.** Un documento se relaciona con los tratamientos que usa, con los controles que respalda y con la tarea de la hoja de ruta que lo exige. Si cambia o se da de baja un tratamiento, la plataforma avisa qué documentos lo usan. Aprobarlo adjunta evidencia a esa tarea y no la cierra (§5.10). Mientras no exista inventario de tratamientos, las variables se alimentan del perfil y del assessment; el formato admite variables del RAT desde el inicio.

**Vigencia.** Cada versión de documento lleva fecha de próxima revisión; vencida, reabre el control que respalda (Módulo 3) sin cambiar el ciclo de nueve estados del apartado D.

**Firmas (sala `firma_electronica`).** Primera modalidad: **aceptación simple** (acuse con nombre, correo, fecha y hora, IP y sello hash) para políticas internas y acuses de personal, con envío por enlace y seguimiento; firma con certificado de entidad acreditada sigue fuera del alcance inmediato (§5.9) y su proveedor es decisión abierta. **Verificar documento:** comprobar por hash si un archivo coincide con el original. Las evidencias de firma se custodian en la sala `evidencias`, repositorio único (apartado 7).

---


<!-- ¤adpa/ -->

## 6. Base de Conocimiento "Regulation as Code" y Copiloto IA
<!-- ¤adpa -->
**Salas:** `regulacion_rag`, `ai_copilot`.
*   **Corpus Normativo Versionado:** Base de datos estructurada con leyes, decretos y resoluciones SPDP 2024–2026.
*   **Motor de Diff Regulatorio:** Ante nuevas publicaciones oficiales, calcula el grafo de impacto en clientes y sugiere revalidaciones sin alterar auditorías pasadas.
*   **Copiloto IA RAG de Confianza Cero:**
    *   Consultas normativas con citación obligatoria (artículo, resolución, fecha de vigencia).
    *   Generador de borradores documentales a partir de plantillas aprobadas.
    *   **Filtro DLP Pre-Inferencia:** Enmascaramiento automático de cédulas, nombres y datos médicos antes de consultar los modelos.
    *   Cero entrenamiento con datos del cliente.
*   **Paquete normativo como dato (menú Configuración › Paquetes normativos, solo operador de la plataforma):** cada norma es un paquete versionado con fuentes, requisitos (uno por obligación, con artículo, obligatoriedad y a quién aplica), controles comunes (mapeo requisito → control, ponderación por dominio), preguntas del assessment por control y perfil, **parámetros** (plazos, autoridad, canal de notificación, bases de legitimación, categorías sensibles, tipos de derecho), plantillas, catálogos (amenazas, medidas, actividades de riesgo) y glosario. Un control común puede cumplir requisitos de varias normas; una evidencia puede respaldar varios controles. Para añadir una norma se suma un paquete; los módulos no cambian. Todo parámetro marcado (*) se confirma con el texto oficial, incluida la unidad de los plazos, antes de activarse en producción. El motor de diff avisa qué plantillas y organizaciones afecta cada cambio.
*   **Centro de conocimiento (menú Conocimiento):** normativa de Ecuador (LOPDP, Reglamento, resoluciones y normas técnicas de la SPDP) servida por el corpus versionado; resúmenes y guías con la marca de la cuenta profesional; cursos base por perfil para la formación; ayuda contextual por módulo con cita de la base legal. Lo que no esté en el corpus no se responde (Doctrina 7).

---


<!-- ¤adpa/ -->

## 7. Requisitos No Funcionales y Seguridad (Stack Empresarial de 8 Capas)
<!-- ¤adpa -->
*   **Stack de 8 Capas Herméticas:** 
    1. *Frontend IDE:* Next.js 15.5+ (Turbopack), React 19, Zustand (`useAuditStore`), `cmdk` (`Ctrl+K`), `react-resizable-panels`, `react-dropzone` (validación condicional Poka-Yoke), Tailwind CSS v4, TanStack Query, Playwright + Vitest.
    2. *Backend ADPA:* Python 3.12+, FastAPI, Pydantic v2, salas herméticas `features/` con compuertas `_service.py` ($\text{ImportsCruzados} \equiv \emptyset$), SQLAlchemy 2.0 + Alembic, Temporal / Camunda para workflows CAPA.
    3. *Datos y Compliance Graph:* PostgreSQL 16 (SSOT transaccional), Row-Level Security (`tenant_id UUID NOT NULL`), Apache AGE / CTE recursivos, `pgvector`, JSONB, MinIO / S3 con Object Lock WORM y hashes SHA-256.
    4. *Regulation as Code:* Git + YAML/JSON + JSON Schema para corpus normativo versionado (LOPDP, RGLOPDP, SPDP 2024–2026), motor de diff en Python, OpenSearch / Meilisearch.
    5. *Copiloto IA RAG de Confianza Cero:* LangChain / LlamaIndex, búsqueda híbrida, DLP pre-inferencia (cédulas Módulo 10 + Presidio/spaCy), Azure OpenAI / vLLM local con cero entrenamiento y citación cerrada obligatoria.
    6. *Seguridad, IAM y Auditoría:* Keycloak / Entra ID (SSO, MFA), OPA / Cedar para políticas SoD del DPO, HashiCorp Vault (TLS 1.3, AES-256), immudb / hash chain append-only, ClamAV + magic bytes.
    7. *Infraestructura y DevOps:* Docker (multi-stage non-root), Kubernetes, Helm, Terraform, CI/CD, OpenTelemetry + Prometheus + Grafana + Loki.
    8. *Arnés de Verificación Exógeno:* `ejecutar_arnes_verificacion.bat`, linters AST, validación UTF-8 estricta sin BOM, cero huellas abiertas y Exit Code 0.
*   **Cinco Antipatrones Prohibidos:** Prohibición explícita de: (1) Low-code cerrado / plataformas propietarias; (2) Formularios estáticos sin evidencia verificable ($E1+$); (3) IA generativa sin citación oficial cerrada; (4) Neo4j como fuente primaria de verdad (rompe ACID y RLS; solo admisible como proyección read-only); (5) Promedios escalares engañosos.
*   **Aislamiento Multi-Tenant Hermético:** Segregación lógica y criptográfica estricta en base de datos mediante RLS (`tenant_id`) y vector stores aislados. La aplicación opera con un rol de base de datos **sin `BYPASSRLS` ni propiedad de tablas** y con `FORCE ROW LEVEL SECURITY` (Módulo 5, §5.4).
*   **Identidad y Accesos:** IAM con soporte SSO (Entra ID, Google Workspace), MFA obligatorio y roles granulares RBAC/ABAC con SoD del DPO.
*   **Cifrado Integral:** Cifrado en tránsito (TLS 1.3) y en reposo (AES-256) con gestión centralizada de llaves.
*   **Logs Inalterables (Tamper-evident):** Registro de auditoría inmutable de accesos, mutaciones y aprobaciones mediante hash chain append-only.
*   **Arquitectura de Salas ADPA:** Backend modular desacoplado en salas herméticas comunicadas exclusivamente por compuertas `_service.py`.
*   **Repositorio único de evidencias:** la sala `evidencias` custodia toda evidencia de la organización (archivo o enlace, tipo, autor, fecha, vigencia, visibilidad, controles y tareas vinculados) con sello hash al cargar; el original no se sobrescribe, solo se versiona. Biblioteca, hoja de ruta, auditoría y operación enlazan, no duplican. **Paquete para inspección** de la SPDP exportable y ordenado por requisito.
*   **Minimización activa:** la plataforma guarda inventarios y evidencias, no las bases de datos de los clientes; al subir archivos con datos personales advierte y aplica el DLP (Doctrina 8).
*   **Ubicación de los datos:** se declara dónde se alojan; si es fuera de Ecuador, se trata como transferencia internacional en los contratos y en el propio RAT de la plataforma (*).
*   **Papelera y exportación:** ningún registro se borra físicamente: se archiva y queda en la bitácora; el borrado definitivo solo al cerrar una cuenta, con exportación previa. Toda organización puede exportar sus datos y documentos completos. El plazo de retención del registro de auditoría sigue pendiente de confirmación legal (§5.3.1).
*   **Capa comercial (sala `plataforma`):** marca blanca (logo, colores, pie de documentos y correos), planes y cupos de organizaciones activas (archivar libera cupo y conserva datos), proveedores comunes de la cuenta. Solo metadatos de cuenta; nunca datos de un tenant. Transferir una organización entre cuentas profesionales exige autorización del cliente y es decisión abierta.

### 7.1 Catálogo de Salas ADPA
Una **sala** es la unidad autónoma de trabajo y de contención de fallos: tiene dueño de sus archivos, una compuerta pública y módulos del producto de los que responde. Un agente de desarrollo escribe solo en los archivos de su sala (propiedad exclusiva de cada tarea en `governance/tareas/`); lo que necesite de otra sala lo obtiene por su compuerta. Cada tarea declara en su cabecera una sala de esta tabla, y `scripts/generar_indice_tareas.py --verificar` lo comprueba.

| Sala | Ubicación | Compuerta | Módulos | Estado |
| :--- | :--- | :--- | :--- | :--- |
| `diagnostico` | `features/diagnostico` | `diagnostico_service.py` | 0, 1 | existe |
| `preanalisis` | `features/preanalisis` | `preanalisis_service.py` | 1 | existe |
| `evidencias` | `features/evidencias` | `evidencias_service.py` | 0 | existe |
| `biblioteca` | `features/biblioteca` | `biblioteca_service.py` (BIB-105) | Biblioteca documental EVYDENTIA, entregas 1 a 3 | planificada, sin código; tareas BIB-101…108, BIB-201…208 y BIB-301…307 |
| `rat` | `features/rat` | `rat_service.py` | 2 | existe |
| `riesgos_mtge` | `features/riesgos_mtge` | `riesgos_mtge_service.py` | 2 | existe |
| `derechos_arco` | `features/derechos_arco` | por crear (ADPA-01) | 2 | sin compuerta |
| `terceros` | `features/terceros` | por crear (ADPA-01) | 2 | sin compuerta |
| `transferencias` | `features/transferencias` | por crear (ADPA-01) | 2 | sin compuerta |
| `incidentes` | `features/incidentes` | `incidentes_service.py` (INC-01) | 2 | existe |
| `conservacion` | `features/conservacion` | por crear | 2 | planificada, sin código |
| `auditoria_capa` | `features/auditoria_capa` | `auditoria_capa_service.py` | 3 | existe |
| `dpo_cockpit` | `features/dpo_cockpit` | `dpo_cockpit_service.py` | 4 | existe |
| `organizacion` | `features/organizacion` | `organizacion_service.py` (RM-01) | 5 | por crear |
| `plataforma` | `features/plataforma` | `plataforma_service.py` (ORG-09) | 5 | planificada, sin código: operador de la plataforma (alta de organizaciones e invitaciones); no accede a datos de ningún tenant |
| `roadmap` | `features/roadmap` | `roadmap_service.py` (RM-01) | 5 | por crear |
| `firma_electronica` | `features/firma_electronica` | por crear (FIRMA-01) | 5 | planificada, sin código |
| `notificaciones` | `features/notificaciones` | por crear (NOTIF-01) | 5 | planificada, sin código |
| `formacion` | `features/formacion` | por crear | 2 (Formación) | planificada, sin código; fase posterior |
| `niif18` | `features/niif18` | `niif18_service.py` | 6 | existe |
| `regulacion_rag` | `features/regulacion_rag` | `regulacion_rag_service.py` | 6 de la sección 6 | existe |
| `ai_copilot` | `features/ai_copilot` | `ai_copilot_service.py` | 6 de la sección 6 | existe |
| `frontend` | `frontend` | cliente de API en `frontend/lib` | todos | existe |
| `pasillo_central` | `app_core`, `api`, `main.py` | `api/routers` | transversal | existe |
| `gobernanza` | `governance`, `scripts` de gobernanza | índice de tareas | transversal | existe |
| `operaciones` | `governance/operaciones`, scripts de despliegue | procedimientos | transversal | existe |
| `pruebas` | `tests` | arnés de verificación | transversal | existe |

**Reglas de las salas**

1. **Solo por compuerta.** Una sala importa a otra únicamente por su compuerta (`ImportsCruzados = ∅`); `pasillo_central` invoca compuertas y no importa nada privado de ninguna sala.
2. **Una sola fuente de asignación.** El PRD declara las salas y los módulos que responden; cada tarea declara su sala. El índice de `TASKS.md` se genera de las especificaciones y nunca se edita a mano.
3. **Pruebas decisivas.** Las pruebas de una sala son las mínimas que pueden fallar por una razón que importa; no se crean pruebas ni requisitos para alcanzar un número.

---


<!-- ¤adpa/ -->

## 8. Lineamientos de Diseño Frontend (Estilo Antigravity / Cursor / Render.com)
<!-- ¤adpa -->
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
*   **Estructura común de pantalla (cinco zonas):** (1) barra superior con la marca de la cuenta, los nueve menús (apartado 5, mapa), buscador global (`Ctrl+K`), notificaciones y usuario; (2) **selector de organización** con la organización activa, limitado a la cartera de la persona (§3.2; FE-21): al cambiar, cambia todo el contenido; (3) **ficha resumen** fija: nombre y RUC, sector, tamaño, naturaleza, DPO, consultor asignado, alertas abiertas (tareas vencidas, solicitudes y vulneraciones con plazo) y las **cuatro dimensiones** del diagnóstico, nunca una cifra única (Doctrina 4); (4) dock lateral con el submenú del menú activo y contadores; (5) contenido con ayuda contextual que cita la base legal.
*   **Seis tipos de pantalla:** tablero (inicio, organización, DPO), lista con filtros guardados, columnas configurables y exportación; ficha con panel lateral de hallazgos y tareas vinculadas; asistente; grilla de verificación con evidencia por fila; editor de documento con variables visibles, versiones y comparación. Acciones rápidas en toda ficha: crear tarea, adjuntar evidencia, comentar, ver historial.
*   **Un solo patrón de asistente:** barra de progreso, guardado automático, saltar entre pasos, empezar en blanco o copiar estructura (§3.2, regla 4); todo asistente termina creando tareas (§5.10). Lo usan los siete flujos largos: alta de organización, assessment, vulneración, EIPD, auditoría, garantías del encargado y firma.

---


<!-- ¤adpa/ -->

## 9. Criterios de Aceptación Clave (MVP)
<!-- ¤adpa -->
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
9. **Arbitraje Exógeno Determinista:** Aprobación del arnés físico en disco (`ejecutar_arnes_verificacion.bat`) con Exit Code 0 antes de todo pase a producción.
10. **Matriz de Permisos de la Hoja de Ruta:** cada par (rol, endpoint) responde según el Módulo 5, §5.2; ninguna fila de `tests/test_matriz_permisos.py` queda marcada como pendiente.
11. **RLS Efectivo:** con la conexión de la aplicación, un tenant ajeno o sin tenant fijado ve 0 filas de todas las tablas con datos de organización y RLS forzado (13 el 2026-10-22; el inventario lo deriva del catálogo `tests/test_rls_todas_las_tablas.py`, QA-04); `lopdp_app` no tiene `BYPASSRLS`.
12. **Hoja de Ruta de Punta a Punta:** un `implementador` genera el roadmap, el `coordinador` distribuye tareas, el `responsable_area` sube evidencia y el `dpo` la valida, con registro en `task_audit_log` de cada paso.
13. **Despliegue Verificable:** tras cada despliegue, `GET /api/v1/health` responde 200 con todos los routers cargados.
14. **Plan de Acción Único:** todo hallazgo abierto de cualquier módulo tiene una tarea en la hoja de ruta con su origen; ninguna sala persiste medidas correctoras propias (§5.10).
15. **Cartera por Pertenencia:** una persona ve y elige solo las organizaciones donde tiene un rol vigente; `coordinador`, `responsable_area` y `admin_organizacion` pertenecen a una sola (ORG-13, FE-21).
16. **Tableros sin Cifra Única:** ficha resumen, tablero de organización y tablero de cartera muestran las cuatro dimensiones y las brechas críticas; ninguna vista expone un porcentaje general de cumplimiento (Doctrina 4).
17. **Evidencia Vencida Reabre el Control:** una evidencia con vigencia cumplida reabre su control periódico y genera hallazgo (Módulo 3).
18. **Plazos como Parámetros:** derechos y vulneraciones toman sus plazos del paquete normativo; ningún plazo legal aparece en texto fijo del código ni de la interfaz, y todo valor (*) está verificado antes de producción.

---


<!-- ¤adpa/ -->

## 10. Glosario: Equivalencias con la LOPDP
<!-- ¤adpa -->
*   **Coordinador (`coordinador`):** Rol organizativo interno de la plataforma que coordina y supervisa el programa de protección de datos de la organización, designa y supervisa a los responsables de área. En términos de la LOPDP ecuatoriana (Arts. 4 y 47), el `coordinador` ejerce internamente la función ejecutiva y de supervisión del responsable del tratamiento.
*   **Encargado del tratamiento (Tercero):** Conforme al Art. 4 de la LOPDP, es la persona natural o jurídica, pública o privada, autoridad pública, u otro organismo que trate datos personales por cuenta del responsable del tratamiento (proveedor externo). No debe confundirse con el rol interno `coordinador`.
*   **Responsable de área (`responsable_area`):** Líder departamental o de proceso interno encargado de la ejecución de actividades de tratamiento y aportación de evidencias operativas (Reglamento del Delegado Art. 18.1).
*   **Delegado de Protección de Datos (`dpo`):** Persona natural independiente que asesora, supervisa el cumplimiento y actúa como punto de contacto con la Superintendencia de Protección de Datos Personales (Arts. 49 y 50 LOPDP; Arts. 48, 49 y 56 del Reglamento General - Decreto Ejecutivo 904; Arts. 3, 15 a 18 del Reglamento del Delegado - Resolución SPDP-SPD-2025-0028-R). El DPD reporta al más alto nivel directivo, no puede ejecutar actividades de tratamiento, ni implementar directamente la ley, ni tomar decisiones sobre la gestión interna de la entidad, por lo que **no puede tener ningún otro rol operativo o administrativo en la plataforma**.
*   **Implementador (`implementador`):** Perfil técnico/operativo que configura la hoja de ruta y ejecuta las altas estructurales autorizadas (Reglamento del Delegado Art. 15.5).
*   **Administrador de la organización (`admin_organizacion`):** Administrador del tenant a nivel de cuentas, identidades y parámetros globales (Reglamento del Delegado Arts. 15.6 y 18.3).
*   **Cuenta profesional:** consultora o partner que atiende a varias organizaciones desde una sola cartera; su personal actúa como `implementador` en cada organización (§3.2). No es el DPO.
*   **Cartera:** conjunto de organizaciones donde una persona tiene un rol vigente; para una organización sin cuenta profesional, su cartera es ella misma.
*   **Paquete normativo:** conjunto versionado de fuentes, requisitos, controles comunes, preguntas, parámetros, plantillas y catálogos de una norma (apartado 6). La LOPDP y la NIIF 18 son paquetes distintos.
*   **Control común:** medida que la organización aplica y que puede cumplir requisitos de varias normas; une requisitos, preguntas, evidencias y tareas.
*   **Hallazgo:** incumplimiento o debilidad detectada por un módulo, con origen, severidad y control; se convierte en tarea de la hoja de ruta (§5.10).
*   **Control periódico:** revisión con frecuencia y responsable cuya evidencia vence y, al vencer, reabre el control (Módulo 3).
*   **Acta de auditoría por área:** constancia del alcance, lo verificado y la evidencia revisada; no es un certificado de cumplimiento (Doctrina 1).

---
*Documento de Requerimientos de Producto vivo y alineado al tratado epistémico del proyecto.*

<!-- ¤adpa/ -->
