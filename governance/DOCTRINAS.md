# Doctrinas Constitucionales de JUBYS Plataforma LOPDP 360
`¤doctrinas`
`¤reglas` `¤dpo-independencia` `¤evidencias` `¤regulation-code` `¤copiloto-ia`

> **CANON FUNDACIONAL Y LEYES DE DISEÑO NO NEGOCIABLES:**
> Este documento establece los principios ontológicos, éticos, jurídicos y de ingeniería que rigen el desarrollo y la operación de la **Plataforma LOPDP 360**. Fundamentado en el blueprint oficial de diseño funcional (*Guía de diseño de la Plataforma LOPDP 360 JUBYS 2026 v1.1*), estas directrices constituyen los límites inviolables que ningún código, automatización o modelo de inteligencia artificial puede transgredir.

---

## 1. Doctrina del Cumplimiento Demostrable (Accountability Real)
`¤reglas` `¤implementacion`

> *"La plataforma no 'certifica' ni garantiza cumplimiento. Convierte obligaciones aplicables en controles, evidencias, responsables, riesgos, acciones y verificaciones trazables."*

*   **Principio:** Ningún software tiene la facultad jurídica de otorgar un "certificado de conformidad" legal definitivo. La responsabilidad proactiva (*accountability*) consagrada en el Art. 12 de la LOPDP recae de forma exclusiva sobre la organización responsable del tratamiento.
*   **Mandato:** La plataforma es un instrumento de gestión, trazabilidad y aseguramiento probatorio; su función es estructurar la evidencia objetiva para que la empresa pueda sostener y demostrar su debida diligencia ante la Superintendencia de Protección de Datos Personales (SPDP) o auditores externos.

---

## 2. Doctrina de la Independencia Sagrada del DPD/DPO
`¤dpo-cockpit` `¤dpo-independencia`

> *"El DPD/DPO continúa siendo una persona natural independiente; la herramienta habilita y documenta su trabajo, pero no lo sustituye ni ejecuta sus obligaciones."*

*   **Principio:** La LOPDP (Art. 47 y ss.) y el Reglamento del DPD (Resolución SPDP-SPD-2025-0028-R) definen al delegado como un profesional con plena autonomía e imparcialidad técnica, prohibiendo expresamente cualquier conflicto de interés.
*   **Mandato Arquitectónico:**
    1.  **Separación Estricta de Funciones (SoD):** La plataforma bloquea físicamente que un usuario con rol DPD/DPO sea asignado como propietario de un control operativo, ejecutor de remediaciones o aprobador de finalidades de negocio.
    2.  **Cockpit Exclusivo de Asesoría y Supervisión:** El DPO dispone de visibilidad transversal de auditoría (Read-Only operacional) y una bandeja formal para emitir dictámenes, advertencias y recomendaciones técnicas no vinculantes, registrando la constancia de recepción por parte de la alta dirección.
    3.  **Inviolabilidad de la Bitácora del DPO:** Ninguna recomendación u observación del DPO puede ser borrada o editada unilateralmente por las áreas auditadas.

---

## 3. Doctrina de la Evidencia antes que la Autodeclaración
`¤evidencias` `¤diagnostico-scoring`

> *"Una respuesta 'Sí' sin soporte no equivale a cumplimiento verificado."*

*   **Principio:** La cultura del cumplimiento nominal o autocomplaciente ("marcar casillas") expone a la organización a severas sanciones administrativas.
*   **Mandato:** 
    *   Una respuesta afirmativa en cualquier cuestionario o evaluación no otorga conformidad por sí sola; se clasifica inicialmente en nivel $E0$ (Autodeclaración sin evidencia).
    *   Para alcanzar niveles de madurez media o alta ($\ge 2$) o marcar un control como efectivamente verificado, es obligatoria la vinculación de evidencia documental aprobada ($E2$) o pruebas operativas de eficacia ($E3$), o en su defecto un rationale formal validado por el consultor responsable.

---

## 4. Doctrina de la Cuadratura de Métricas (No Fusión Engañosa)
`¤diagnostico-scoring`

> *"Un proceso puede ser técnicamente maduro y conservar una brecha jurídica crítica; una obligación legal binaria jamás debe diluirse en un porcentaje."*

*   **Principio:** Un promedio aritmético general (ej. "87% de cumplimiento") genera una falsa sensación de seguridad ante la alta dirección, enmascarando infracciones tipificadas como graves o muy graves en la ley.
*   **Mandato:** Los dashboards ejecutivos deben presentar por separado y de forma balanceada:
    1.  *Cobertura de requisitos aplicables.*
    2.  *Conformidad jurídica verificada (estado booleano).*
    3.  *Índice de madurez SPDP (0 a 3).*
    4.  *Cobertura y vigencia de evidencias.*
    5.  *Riesgo residual y bloqueadores críticos.*

---

## 5. Doctrina de la Fuente Única de Verdad (Compliance Graph)
`¤rat` `¤adpa`

> *"Un dato se registra una vez y se reutiliza; prohibición absoluta de duplicar matrices que divergen en el tiempo."*

*   **Principio:** La fragmentación de la información es el principal causante de incoherencias en las auditorías de protección de datos.
*   **Mandato:** El **Registro de Actividades de Tratamiento (RAT)** constituye el núcleo indivisible del sistema. De cada actividad registrada en el RAT derivan de forma reactiva y vinculada: la matriz de riesgos, la necesidad de EIPD, la evaluación de gran escala (MTGE), el catálogo de encargados, el registro de transferencias y los avisos de privacidad. Ningún módulo satélite puede crear entidades de tratamiento paralelas o huérfanas.

---

## 6. Doctrina de "Regulation as Code" y Explicabilidad
`¤regulation-code`

> *"Cada regla operativa debe citar su fuente exacta, artículo, versión, vigencia y conservar su cadena de razonamiento visible."*

*   **Principio:** El motor de cumplimiento no puede operar como una caja negra arbitraria.
*   **Mandato:** Cada conclusión automática de aplicabilidad (ej. obligación de nombrar DPO o ejecutar EIPD) debe mostrar de manera transparente al usuario:
    *   Los hechos ingresados.
    *   La regla normativa activada.
    *   La cita exacta (Ley, reglamento, resolución SPDP, artículo y fecha de corte).
    *   Los aspectos pendientes de validación por el criterio profesional humano.

---

## 7. Doctrina de la Inteligencia Artificial Ética y Asistida (HITL)
`¤copiloto-ia`

> *"El Copiloto IA asiste, resume, relaciona y propone; jamás emite una conclusión jurídica definitiva ni cierra controles automáticamente."*

*   **Principio:** La interpretación del derecho y la toma de decisiones sancionatorias o de riesgo legal exigen discernimiento y responsabilidad humana indelegable.
*   **Mandato:**
    1.  **Sin fuente no hay respuesta:** Toda respuesta normativa del Copiloto RAG debe anclarse en el corpus cerrado oficial versionado de la SPDP. Si no existe norma aplicable, la IA debe declarar incertidumbre explícita.
    2.  **Cero Aprendizaje con Datos del Cliente:** Prohibición absoluta de utilizar datos de clientes para el reentrenamiento de modelos globales.
    3.  **Human-in-the-Loop (HITL):** Decisiones de aplicabilidad, cierre de no conformidades, notificaciones de incidentes a la SPDP y firma de documentos exigen intervención humana autorizada.

---

## 8. Doctrina de la Privacidad por Diseño de la Propia Plataforma
`¤seguridad-tenant` `¤adpa`

> *"La plataforma que audita privacidad debe ser en sí misma un modelo ejemplar de privacidad y seguridad desde el diseño y por defecto."*

*   **Principio:** Tratar datos sobre el cumplimiento de terceros impone el más alto nivel de aseguramiento tecnológico.
*   **Mandato:**
    *   **Minimización radical:** La plataforma prohíbe y advierte preventivamente no cargar bases de datos masivas de clientes o historiales clínicos reales cuando baste con metadatos, reportes o muestras anonimizadas.
    *   **Filtro DLP Activo:** Detección y advertencia inmediata ante números de cédula, correos o datos sensibles en archivos de evidencia.
    *   **Aislamiento Multi-tenant Hermético:** Separación lógica y criptográfica rigurosa que impide el acceso cruzado entre diferentes organizaciones o clientes.
    *   **Logs Inalterables (Tamper-evident):** Registro cronológico inmutable de accesos, modificaciones de RAT, aprobaciones de documentos y acciones de auditoría.

---

## 9. Doctrina de la Antecedencia Paramétrica y Poda Ontológica
`¤diagnostico-motor` `¤diagnostico`

> *"La parametrización de la entidad es la raíz causal del árbol de aplicabilidad; la configuración del proyecto siempre antecede y se desacopla de la ejecución diagnóstica."*

*   **Principio:** Un sistema de auditoría no puede evaluar el cumplimiento de requisitos sobre un espacio normativo no acotado. La coexistencia o anidación de la ficha empresarial dentro del cuestionario induce bucles cognitivos y altera el alcance mientras se responde.
*   **Mandato:**
    1.  **Desacoplamiento Estructural:** La Ficha Organizacional / Configuración del Proyecto reside en una pestaña antecedente e independiente.
    2.  **Poda Previa:** La selección de normativa, sector y tamaño genera de forma determinista el subconjunto acotado de preguntas ($\le 80$) antes de que el usuario interactúe con el módulo de diagnóstico.

---

## 10. Doctrina del Aislamiento Probatorio y Purga Multidominio
`¤evidencias` `¤diagnostico`

> *"La evidencia documental de un dominio normativo es ontológicamente incompatible con otro; conmutar de regulación purga de forma inmediata el búfer probatorio."*

*   **Principio:** La validez de una prueba de auditoría es específica al régimen jurídico examinado. Mezclar contratos de cesión de marcas con asientos contables o informes de pentesting desvirtúa la trazabilidad probatoria y genera falsos positivos legales.
*   **Mandato:**
    1.  **Whitelists Estrictas por Dominio:** Propiedad Intelectual admite exclusivamente formatos documentales no estructurados (`.pdf,.docx,.md,.txt`), mientras que normativas contables y técnicas exigen registros estructurados (`.csv,.xlsx,.xbrl,.ixbrl,.json,.xml,.sql`).
    2.  **Purga Atómica:** Cualquier cambio en el selector de normativa vacía automáticamente el arreglo de archivos cargados en el estado global (`useAuditStore`), impidiendo la contaminación cruzada entre expedientes.

---

## 11. Doctrina del Arbitraje Exógeno Determinista (Teorema Proaño-Gemini-Dijkstra)
`¤bbap` `¤adpa`

> *"La verificación de la no-regresión y de la verdad operativa reside exclusivamente en procesos físicos observables en disco con Exit Code 0; ninguna IA es juez de su propio código."*

*   **Principio:** Los modelos generativos son intrínsecamente estocásticos y propensos a la complacencia conversacional. Las afirmaciones verbales sobre la superación de pruebas carecen de validez jurídica y de ingeniería.
*   **Mandato:**
    *   La validez de cada entrega técnica se somete a árbitros exógenos booleanos $\{0, 1\}$: arneses de ejecución por lotes `.bat`, suites canónicas `pytest`, transpiladores `turbopack` y linters AST con verificación notarial en disco.
    *   Tolerancia cero a aserciones tautológicas ($1 == 1$) o mocks que no evalúen la lógica real del sistema.

---

## 12. Doctrina de Trazabilidad y Cadena de Validez
`¤incidentes` `¤bbap` `¤reglas`

> *"Cada regla, restricción o cálculo matemático implementado en la plataforma responde a un mandato legal, estándar internacional o teorema científico demostrable; ninguna decisión técnica o de diseño es arbitraria."*

*   **Principio:** El código de cumplimiento es la traducción literal del derecho y la ciencia formal a la ingeniería de software. Para que la plataforma sea defendible ante auditorías técnicas y peritajes jurídicos de la SPDP, su arquitectura debe poder leerse de forma descendente (de la norma al código) a través de una **Cadena de Validez**.
*   **Mandato (Ejemplo Canónico — El Reloj Legal de Incidentes):**
    *   **La Obligación (El Derecho):** La Ley Ciberseguridad 2026 (Art. 14) crea la obligación ineludible de notificar brechas en máximo 72 horas.
    *   **La Confianza (La Criptografía):** NIST FIPS 180-4 (SHA-256) sella la información; el cálculo del tiempo se confina físicamente al servidor (`"use server"` en Next.js) para neutralizar manipulaciones del reloj del navegador del cliente.
    *   **La Identidad (El Estándar):** El RFC 4122 (UUID v4 con 122 bits de entropía) garantiza que cada incidente sea único e irrepetible ante un juez, sin ambigüedades.
    *   **La Legibilidad (El Formato):** El RFC 4648 (Codificación Hexagonal) permite que el sello forense sea leído por humanos y máquinas en un JSON de texto plano sin depender de software propietario.
    *   **Los Estados (El Formalismo):** El plazo legal se modela como una Máquina de Estados (Harel, 1987) de tres fases ("A Tiempo", "Crítico", "Vencido"), impidiendo matemáticamente las transiciones a estados huérfanos o inconsistentes.
    *   **La Prevención (La Ergonomía):** Dado que el registro criptográfico es irreversible, exigir el protocolo de previsualización antes de guardar (Two-Phase Commit) respeta la Heurística 5 de Nielsen (prevención radical de errores).
    *   **La Inviolabilidad (El Paradigma):** Un diseño *Append-Only Log* (Kleppmann, 2019) asegura que ningún registro pueda ser borrado o alterado (`UPDATE/DELETE` bloqueados), preservando la bitácora intacta.
    *   **La Verificación (La Física):** La ley hecha código se valida con árbitros exógenos físicos (`tsc --noEmit`, `pytest`) que deben emitir Exit Code 0 de manera observable en disco.
