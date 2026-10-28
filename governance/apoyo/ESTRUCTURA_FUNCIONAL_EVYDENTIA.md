# Estructura funcional EVYDENTIA: contraste con la plataforma y optimizaciones

> **Estado:** análisis del Tech Leader para decisión del propietario (2026-10-28).
> **Fuentes:** «EVYDENTIA: estructura funcional» (27/10/2026, `https://claude.ai/artifact/5YxfcnaahMT9rrNZQBmhLo`) y «EVYDENTIA: documento maestro de diseño funcional» v0.1 (27/10/2026, `https://claude.ai/artifact/JafRaCpekKdrzPHiGT3DQ8`), leídos íntegros salvo los dos mapas embebidos (imágenes).
> **Contraste:** `governance/artefactos/PRD.md`, `governance/artefactos/INVARIANTS.md`, catálogo de salas (PRD §7.1), `frontend/src/components/layout/dashboardNavigation.ts` y las fichas `ORG-13`, `FE-21`, `LEG-02`.
> **Árbitro:** cada conflicto cita la doctrina o la invariante que lo decide; cada artículo legal no confirmado lleva (*).

---

## 1. Qué aporta la estructura

La estructura funcional organiza la plataforma por el **trabajo del usuario**, no por la sala técnica que lo sirve. Tres ideas valen por sí solas y son compatibles con las diez doctrinas del PRD:

1. **Diagnóstico como puerta de entrada** (assessment → reporte → hoja de ruta). Ya existe; la estructura lo convierte en el primer menú.
2. **Un solo plan de acción.** Todo hallazgo (assessment, auditoría, EIPD, vulneración, tercero sin contrato, control periódico vencido) termina como tarea de la hoja de ruta, con origen trazable. Es la aplicación operativa de la Doctrina 5 (Compliance Graph) al lado correctivo.
3. **Tableros desde el inicio**, con semáforos de plazos por organización y por cartera.

Además define una **pantalla común de cinco zonas** (barra superior con nueve menús, selector de organización, ficha resumen, menú lateral del menú activo y contenido), **seis tipos de pantalla** (tablero, lista con filtros, ficha, asistente, grilla de verificación, editor de documento) y **siete asistentes** paso a paso (alta de organización, assessment, vulneración, EIPD, auditoría, garantías del encargado, firma).

El documento maestro añade la pieza que la estructura da por supuesta: el **paquete normativo como dato** (fuentes → requisitos → controles comunes → preguntas → parámetros → plantillas → catálogos → glosario). Coincide con la Doctrina 6 («Regulation as Code») y con `INV_LOPDP_REGULATION_AS_CODE_DIFF`.

## 2. Mapa: nueve menús ↔ salas ADPA ↔ navegación actual

La navegación actual (`dashboardNavigation.ts`) es una lista plana de 14 vistas LOPDP y 10 NIIF, nombradas por la sala que las sirve («RAT Maestro», «Cockpit DPD / DPO», «MTGE Relacional»). La estructura propone agruparlas por menú. **Las salas no cambian**: el mapa es una capa de presentación.

| Menú | Submenús de la estructura | Salas ADPA que responden | Vistas actuales que se reubican | Brecha |
| :--- | :--- | :--- | :--- | :--- |
| 1. Inicio (cartera) | Tablero de cartera, Organizaciones, Nueva organización, Calendario de plazos, Archivadas | `organizacion`, `plataforma` (alta), `notificaciones` | `dashboard` (pasa a ser el tablero de la organización) | Tablero de cartera, calendario único, archivar/restaurar |
| 2. Diagnóstico | Assessment, Reporte, Hoja de ruta, Comparativo | `diagnostico`, `preanalisis`, `roadmap` | `diagnostico`, `reportes`, `roadmap` | Asignar dominios a responsables, comparativo entre assessments |
| 3. Inventario | Perfil, Sedes y áreas, Tratamientos (RAT), Activos y sistemas, Soportes, Personas, Encargados y terceros, Clientes, Titulares | `organizacion`, `rat`, `terceros`, `transferencias`, `conservacion` | `rat`, `terceros`, `configuracion` | Activos y sistemas, soportes, personas, clientes (si es encargado), titulares (solo colectivos y consentimientos) |
| 4. Biblioteca | Documentos de la organización (por tipo), Plantillas, Firmas, Evidencias | `biblioteca`, `firma_electronica`, `evidencias` | `evidencias` | En curso (BIB-1xx…3xx); firmas y vínculos documento↔tarea↔tratamiento |
| 5. Operación | Solicitudes de titulares, Vulneraciones, Consultas, Formación, Agenda y horas | `derechos_arco`, `incidentes`, `dpo_cockpit` (consultas), `formacion` (nueva) | `arco`, `incidentes` | Portal público de solicitudes, formación, agenda (capa comercial) |
| 6. Riesgos y auditoría | Matriz de riesgos, EIPD, Auditorías, Controles periódicos, Garantías de encargados | `riesgos_mtge`, `auditoria_capa`, `terceros` | `riesgos`, `mtge_relacional`, `auditoria`, `mitigacion_ia` | Controles periódicos con vencimiento de evidencias; cuestionario de garantías por portal externo |
| 7. DPO | Panel, Obligaciones, Informe anual, Registro SPDP, Consultas atendidas | `dpo_cockpit` | `dpo` | Calendario de obligaciones, informe anual generado, estado de inscripción |
| 8. Conocimiento | Normativa Ecuador, Resúmenes y guías, Cursos, Ayuda, Material comercial | `regulacion_rag`, `ai_copilot` | — (hoy solo copiloto lateral) | Menú de consulta para el usuario final |
| 9. Configuración | Usuarios y roles, Plantillas, Paquetes normativos, Marca blanca, Plan y cupos, Proveedores comunes, Papelera, Verificar documento, Exportar datos | `organizacion`, `plataforma`, `regulacion_rag`, `evidencias` | `configuracion` | Paquetes normativos (solo operador), marca blanca, cupos, papelera, verificador de hash, exportación completa |

El módulo NIIF 18 (PRD Módulo 6) **no cabe** en los nueve menús: la estructura es solo LOPDP. Se conserva como **paquete normativo** independiente, elegido en el selector de paquete (hoy «Normativa»), con su propia navegación.

## 3. Conflictos con la doctrina y resolución propuesta

La estructura y el documento maestro se escribieron sin el PRD a la vista. Donde chocan, **prevalecen el PRD y las invariantes**, que son la fuente única de verdad del proyecto; la resolución propuesta conserva la intención del documento.

| # | Lo que dice el documento | Con qué choca | Resolución propuesta |
| :--- | :--- | :--- | :--- |
| D-1 | «Nivel de cumplimiento calculado» en la ficha resumen, en el tablero de cartera y como indicador («puntaje ponderado de controles cumplidos»). | Doctrina 4 (cuadratura multidimensional) e `INV_LOPDP_MULTIDIMENSIONAL_METRICS`: prohibido el porcentaje general. | Ficha y tableros muestran las **cuatro dimensiones** por separado (madurez, conformidad, evidencia, riesgo) y el **número de brechas críticas abiertas**. En la cartera, un semáforo por dimensión; ninguna cifra única. |
| D-2 | La «cuenta profesional» es el DPO: tiene «Mi plantilla», genera documentos, «convierte hallazgos en tareas», «aprueba y envía» respuestas a titulares, «cierra tareas con justificación» y «aprueba documentos» (RN-DOC-01, RN-PLA-01, flujos B y D; «el rol DPO tiene los permisos del consultor más la firma de informes»). | Doctrina 2 e `INV_LOPDP_DPO_INDEPENDENCE`; PRD §5.3 (el `dpo` audita, no ejecuta ni edita); Reglamento del Delegado (Res. SPDP-SPD-2025-0028-R, Arts. 15 a 18); decisión ORG-13 (2026-10-26). | La cuenta profesional es la **consultora o partner**, cuyo personal entra como `implementador` en cada organización. El `dpo` es una persona distinta con rol exclusivo: revisa el assessment, valida evidencia, dictamina y supervisa; **no** edita plantillas, no genera documentos, no cierra tareas ni aprueba documentos. Las plantillas propias son «de la cuenta profesional», no «del DPO». |
| D-3 | «Aprobar el documento cierra la tarea con evidencia»; ciclo de documento «borrador, aprobado, vencido». | PRD Biblioteca D («aprobar o descargar no cierra una brecha ni acredita eficacia»), `INV_LOPDP_EVIDENCE_BEFORE_COMPLIANCE`, `INV_LOPDP_EVIDENCE_FOUR_EYES`. | Aprobar un documento **adjunta evidencia** a la tarea vinculada; el cierre lo valida otra persona y lo marca el `implementador`. El ciclo de nueve estados del PRD se mantiene; «vencido» y «próxima revisión» entran como **vigencia**, atributo de la versión, no como estado que sustituya a «verificado eficaz». |
| D-4 | Auditoría con «certificados por área». | Doctrina 1: la plataforma no certifica. | **Acta de auditoría por área**, con alcance, lo verificado y la evidencia revisada. Nunca «certificado de cumplimiento». |
| D-5 | Asistentes que copian «de otra organización de la cartera» (RF-ORG-03, RF-RIE-05). | `INV_LOPDP_TENANT_BULKHEAD`, `INV_LOPDP_APP_ROLE_NO_BYPASSRLS`. | Se copia **solo estructura** (plantilla de organización, tratamientos sugeridos, catálogos), nunca datos personales, evidencias ni respuestas. Acción explícita, registrada, por un usuario con rol vigente en ambas organizaciones; por ORG-13 solo puede serlo un `implementador` (el `dpo` no edita). |
| D-6 | Entidad «Persona» con cédula; menú «Titulares»; «Personas» con carga masiva. | Doctrina 8 (minimización) y RNF-05 del propio documento maestro. | Personas: solo lo necesario para asignar tareas, formación y firmas (nombre, cargo, área, correo); la cédula solo si la firma la exige y cifrada. Titulares: **colectivos y registros de consentimiento o firma**, nunca bases de titulares. DLP en toda subida (Doctrina 7). |
| D-7 | Portal público de solicitudes de titulares y portal externo de encargados. | Doctrina 8; superficie pública nueva sin diseño de seguridad. | Se incorporan al PRD como **fase posterior** con precondiciones: verificación proporcional de identidad, enlaces que caducan, sin exposición de datos de otros titulares, límites de abuso. Tareas SEC previas. |
| D-8 | Escala de madurez **0–5**, «promedio ponderado por dominio», «no aplica exige justificación». | PRD Módulo 1: madurez SPDP 0–3 y scoring cuádruple; `INV_LOPDP_60MIN_TIMEBOX_LIMIT`. | Se mantiene la escala **0–3** de la SPDP y la cota de 80 preguntas. El promedio ponderado solo describe un dominio, nunca la organización (D-1). La justificación obligatoria de «no aplica» **se adopta**. |
| D-9 | Plazos «2 días encargado→responsable, 5 días responsable→SPDP, 3 días a titulares, 15 días derechos». | Hoy el frontend fija «SLA 72h» (incidentes) y «SLA 15d» (derechos) en texto. | Los plazos son **parámetros del paquete normativo** (LEG-02 documenta la Res. SPDP-SPD-2026-0040-R). Ningún plazo en texto fijo; cada valor lleva (*) hasta su verificación y la unidad (hábiles o calendario) se decide con la norma. |
| D-10 | «Firma electrónica por enlace» y «aceptación simple (clic)». | PRD §5.9: la firma con ANF está fuera del alcance inmediato. | La **aceptación simple** (acuse con sello hash, IP y fecha) entra como primera modalidad de `firma_electronica`, útil para políticas internas; la firma con certificado sigue fuera del alcance inmediato y su proveedor es decisión abierta. |
| D-11 | Marca blanca, plan y cupos, material comercial, agenda y horas, transferir una organización entre cuentas. | Sala `plataforma` «no accede a datos de ningún tenant». | Capa **comercial** en `plataforma`: solo metadatos de cuenta (marca, cupos, planes). Agenda y horas no entran en el alcance del producto de cumplimiento. Transferir una organización exige autorización del cliente y queda como decisión abierta. |
| D-12 | Borrado: «ningún registro se borra; el borrado definitivo solo al cerrar una cuenta, con exportación previa». | PRD Módulo 2 (conservación y supresión) y plazos legales de retención aún por fijar (§5.3.1). | **Se adopta** la papelera (archivar, no borrar) y la exportación completa. El plazo de retención del registro de auditoría sigue pendiente de confirmación legal. |

Citas legales del documento marcadas (*): en esta sesión se confirmaron por fuentes secundarias el Art. 42 (EIPD), el Art. 43 (notificación a la autoridad, cinco días) y el Art. 48 (delegado). **No se confirmaron** los Arts. 12–24 (derechos), 47 (registro) ni 55–61 (transferencias). El frontend cita hoy «Art. 35» (RAT), «Arts. 21-24» (derechos), «Art. 37» (ARCO) y «Art. 60» (transferencias), en contradicción con el documento. Una sola fuente de citas (el paquete normativo) y una tarea LEG lo resuelven.

## 4. Optimizaciones concretas de la plataforma

| # | Optimización | Qué cambia | Qué no cambia |
| :--- | :--- | :--- | :--- |
| O-1 | **Navegación por menús** | `dashboardNavigation.ts` pasa de lista plana a nueve menús con submenús y contadores; el dock lateral muestra el submenú del menú activo; `Ctrl+K` busca entre todas las pantallas. | Salas, compuertas y rutas de API. |
| O-2 | **Plan de acción único** | Entidad `hallazgo` (origen, severidad, control, organización) y una sola compuerta `roadmap_service` para crear tareas desde hallazgos. Assessment, auditoría, EIPD, vulneraciones, terceros y controles periódicos **producen hallazgos**; solo `roadmap` crea tareas. | La matriz de permisos del Módulo 5 y el audit log. |
| O-3 | **Repositorio único de evidencias** | `evidencias` es la única sala de custodia (hash, vigencia, visibilidad, controles y tareas vinculados). Biblioteca, roadmap, auditoría y operación **enlazan**, no duplican. «Paquete para inspección» ordenado por requisito. | Object Lock, SHA-256 y RLS existentes. |
| O-4 | **Cartera sin abrir la RLS** | Fase 1: la cartera se arma iterando las organizaciones de `mis_organizaciones` (ORG-13) con contexto de tenant por consulta. Cuando una cuenta supere unas decenas de organizaciones: **proyección de cartera** (tabla de contadores por organización, sin datos personales, escrita por cada tenant en su propia transacción y leída por pertenencia). | `FORCE ROW LEVEL SECURITY`, rol sin `BYPASSRLS`. |
| O-5 | **Paquete normativo como dato** | Pantalla «Paquetes normativos» solo para el operador de la plataforma; requisitos, controles comunes, preguntas, plazos, plantillas y catálogos versionados; el motor de diff (§6) avisa qué plantillas y organizaciones afecta un cambio. NIIF 18 es otro paquete. | Doctrina 6 y `INV_LOPDP_REGULATION_AS_CODE_DIFF`. |
| O-6 | **Un patrón de asistente** | Un componente de asistente (progreso, guardado automático, saltar pasos, copiar estructura) reutilizado por los siete flujos; cada asistente termina creando tareas por O-2. | — |
| O-7 | **Alta de organización en el servidor** | El asistente de siete pasos sustituye la configuración local del Módulo 0 (`isConfigured` en Zustand): perfil, sedes, áreas, tratamientos sugeridos, terceros típicos y personas clave viven en `organizacion`; medidas y documentos salen del assessment y de la hoja de ruta. | Doctrina 9 (la ficha antecede al cuestionario). |
| O-8 | **Controles periódicos** | En `auditoria_capa`: control con frecuencia y responsable; la evidencia vencida **reabre** el control y genera hallazgo (O-2). | — |
| O-9 | **Plazos como parámetros** | Derechos y vulneraciones leen sus plazos del paquete normativo; se retiran los textos fijos «SLA 72h» y «SLA 15d». | Reloj normativo de `incidentes` (INC-01). |
| O-10 | **Tableros sin cifra única** | Tablero de organización y de cartera con las cuatro dimensiones y brechas críticas; semáforos de plazos (tareas, solicitudes, vulneraciones, revisiones, contratos, documentos). | Doctrina 4. |

## 5. Orden de construcción (alineado con las cinco fases del documento maestro)

| Fase | Alcance | Estado real en el repositorio |
| :--- | :--- | :--- |
| 1. Conectar lo existente | Pertenencia a varias organizaciones (ORG-13) y selector (FE-21); cartera; hallazgo → tarea (O-2); evidencias únicas (O-3); navegación por menús (O-1); tableros sin cifra única (O-10). | ORG-13 en tanda 19, FE-21 en tanda 20; roadmap y evidencias existen. |
| 2. Inventario y documentos | RAT con validaciones y versiones; activos, soportes y personas; Biblioteca generando desde el RAT; terceros con hallazgos automáticos. | `rat`, `terceros`, `transferencias` existen; Biblioteca en curso (BL-83). |
| 3. Operación | Solicitudes con plazos parametrizados; vulneraciones con asistente de ocho secciones e informes de la norma técnica; aceptación simple. | `derechos_arco` e `incidentes` existen (INC-01); plazos aún en texto fijo. |
| 4. Madurez | Riesgos y EIPD guiada; auditoría con grilla y controles periódicos; formación; garantías de encargados por portal externo. | `riesgos_mtge` y `auditoria_capa` existen; formación y portal externo sin sala. |
| 5. Escala | Marca blanca, centro de conocimiento, tickets, planes y cupos; segundo paquete normativo. | `plataforma` y `regulacion_rag` existen; NIIF 18 ya es un segundo paquete. |

Prioridad inmediata que recomienda el propio documento y que coincide con el estado del repositorio: **validar la hoja de ruta antes de conectarla con la Biblioteca**, porque ahí se unen el diagnóstico y los documentos.

## 6. Tareas que esto abre (para el coordinador; una ficha por tarea)

- **FE:** navegación por nueve menús con submenús y contadores (O-1); patrón de asistente (O-6); tablero de organización y de cartera sin cifra única (O-10).
- **RM:** entidad `hallazgo` y compuerta única de creación de tareas (O-2); vistas lista, tablero y cronograma; vista de cartera de tareas vencidas.
- **EVI:** vigencia, visibilidad y paquete para inspección (O-3).
- **ORG:** alta en siete pasos en el servidor (O-7); cartera por pertenencia y, después, proyección (O-4); activos, soportes y personas mínimas.
- **AUD / CAPA:** controles periódicos y reapertura por evidencia vencida (O-8); acta por área.
- **DIAG:** asignación de dominios a responsables, revisión del DPO con grilla declarado-verificado, comparativo con línea base, justificación obligatoria de «no aplica».
- **DPO:** calendario de obligaciones, informe anual generado, estado de inscripción ante la SPDP.
- **LEG:** una sola fuente de citas legales y verificación de los artículos con (*); unidad de los plazos (hábiles o calendario).
- **SEC:** diseño de seguridad de los portales externos (titulares y encargados) antes de cualquier implementación.
- **INVARIANTS (propuesta, con árbitro):** `INV_LOPDP_SINGLE_ACTION_PLAN` (todo hallazgo abierto tiene tarea con origen; prueba en `roadmap`) e `INV_LOPDP_PORTFOLIO_BY_MEMBERSHIP` (la cartera lista solo organizaciones con rol vigente; prueba ORG-13).

## 7. Decisiones que esperan al propietario

1. Confirmar que la **cuenta profesional es la consultora** y que el DPO no edita ni aprueba (D-2). Si se decide lo contrario, hay que reabrir `INV_LOPDP_DPO_INDEPENDENCE`, ORG-13 y el Reglamento del Delegado.
2. Confirmar la **tercera capa de plantillas** (maestra → cuenta profesional → organización) y quién la edita (D-2, PRD Biblioteca G).
3. Mantener la **madurez 0–3** frente a la 0–5 del documento (D-8).
4. Aceptación simple como primera modalidad de firma (D-10).
5. Qué entra de la capa comercial (marca blanca, cupos, transferir organizaciones) y cuándo (D-11).
6. Verificación legal de todos los valores con (*) antes de activarlos (D-9).
