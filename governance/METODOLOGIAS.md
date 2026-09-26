# Metodologías de JUBYS Plataforma LOPDP 360
`¤metodologias`
`¤bbap` `¤diagnostico` `¤rat` `¤frontend-ide`

> **MARCO METODOLÓGICO INTEGRAL DE TRABAJO, CUMPLIMIENTO Y EXPERIENCIA:**
> Este documento define las metodologías de diagnóstico, diseño, gestión de riesgos, orquestación de tareas y experiencia de usuario que rigen la **Plataforma LOPDP 360**. Integra las mejores prácticas y ergonomías analizadas de referentes globales y herramientas líderes del mercado (**Antigravity / Cursor, Global Suite, Novoser, Pirani, Isotools y Odoo**), articuladas con el rigor normativo ecuatoriano de la SPDP.

---

## 1. Metodología de Diagnóstico Ágil: Sesión Timeboxed de 60 Minutos
`¤diagnostico` `¤diagnostico-motor`

Inspirada en el benchmark metodológico europeo **DMAT (Digital Maturity Assessment Tool)** y en la flexibilidad del Anexo de la Guía de Gestión de Riesgos de la SPDP:
*   **Timebox Estricto (60 minutos):** Diseñado para que una reunión ejecutiva de consultoría sea suficiente para trazar la línea base preliminar sin fatiga cognitiva.
*   **Estructura de la Sesión:**
    1. *Minuto 0 a 5:* Ficha Organizacional Inteligente (sector, tamaño, nube, sistemas críticos).
    2. *Minuto 5 a 45:* Núcleo Común (16 Dominios JUBYS $\times$ hasta 3 preguntas = 48 preguntas clave).
    3. *Minuto 45 a 55:* Preguntas Condicionales Críticas (solo si se activan por sector o tratamiento especial, máx. 12).
    4. *Minuto 55 a 60:* Validación de Hallazgos y Próximos Pasos.
*   **Poda Lógica Condicional:** La interfaz impone un **límite técnico infranqueable de 80 preguntas visibles por sesión**, con una ruta operativa promedio de **45 a 68 preguntas**.
*   **Regla de Cierre de Sesión:** Cualquier asunto que demande auditoría forense, muestreo de logs o análisis contractual profundo no detiene la entrevista: se etiqueta como `"Pendiente de Validación"` y se deriva a la fase de implementación.

---

## 2. Metodología de Evaluación y Madurez Multidimensional
`¤diagnostico-scoring`

Superación del paradigma del "porcentaje único ficticio". La plataforma evalúa mediante cuatro vectores ortogonales:
1.  **Índice de Madurez SPDP (0 a 3):**
    *   *Nivel 0 (Caótico - 0%):* El principio no es conocido ni aplicado.
    *   *Nivel 1 (Implícito - <25%):* Conocido, aplicado en menos del 25% del proceso.
    *   *Nivel 2 (Temprano Explícito - 25%–75%):* Implementación parcial formalizada.
    *   *Nivel 3 (Maduro Explícito - >75%):* Implementado, integrado y probado en más del 75%.
2.  **Estado de Conformidad Jurídica:** Clasificación booleana estricta: `Conforme`, `Parcial`, `No Conforme`, `No Verificado` o `No Aplicable`.
3.  **Jerarquía de Calidad de Evidencia:**
    *   *E0 (Sin Evidencia):* Autodeclaración pura (no califica como verificado).
    *   *E1 (Documentada):* Existe política o borrador sin prueba de uso en caliente.
    *   *E2 (Implementada):* Documento aprobado y registros recientes de operación.
    *   *E3 (Probada):* Evidencia de muestreo, métricas o auditoría de eficacia.
4.  **Vector de Riesgo Residual:** Identificación de brechas de impacto crítico sobre derechos y libertades que bloquean la conformidad independientemente del nivel de madurez alcanzado.

---

## 3. Metodología de "Compliance Graph" y Fuente Única de Verdad (Inspiración Odoo)
`¤rat` `¤implementacion`

Tomando como referencia la arquitectura modular y el modelo relacional unificado de **Odoo**:
*   **El RAT como Registro Maestro ("Master Record"):**
    *   En Odoo, el *Partner Record* es el eje sobre el cual giran compras, ventas y contabilidad sin duplicar entidades.
    *   En LOPDP 360, la **Actividad de Tratamiento del RAT** es el registro maestro. Un tratamiento se ingresa una sola vez y de él derivan:
        - La matriz de riesgos para derechos y libertades.
        - La evaluación de Tratamiento a Gran Escala (MTGE).
        - La necesidad de EIPD.
        - El inventario de terceros encargados y contratos asociados.
        - Las transferencias internacionales.
        - El aviso de privacidad y la asignación de controles.
*   **Cero Matrices Paralelas:** Erradicación de hojas de cálculo independientes que se desincronizan. Un cambio en una finalidad del RAT actualiza en cascada todos los módulos satélite.

---

## 4. Metodología de Ergonomía y Experiencia de Usuario: IDE / Command-Center (Inspiración Antigravity / Cursor)
`¤frontend-ide`

Dirigida a consultores, auditores, oficiales de seguridad y DPOs que requieren procesar grandes volúmenes de evidencia con máxima velocidad y precisión:
*   **Command Palette Universal (`Ctrl + K` / `Cmd + K`):**
    *   Permite saltar inmediatamente a cualquier artículo de la ley, actividad del RAT, cliente tenant, reporte o evidencia sin navegar por menús lentos.
*   **Layout de Paneles Divididos (Split Panes):**
    *   *Panel Izquierdo:* Árbol colapsable de módulos, dominios G01–G16 y tratamientos.
    *   *Panel Central:* Espacio de trabajo activo (cuestionario adaptativo, editor de control o tabla de RAT).
    *   *Panel Derecho Contextual:* Copiloto IA de cumplimiento y visor de evidencias/artículos vinculados.
*   **Estética Minimalista y Alta Densidad Técnica:**
    *   Soporte nativo Dark/Light mode con paletas de baja fatiga visual.
    *   Bordes ultra-finos de 1px, eliminación de sombras pesadas o animaciones innecesarias, tipografía dual: Inter/Geist para lectura y JetBrains Mono para códigos, metadatos, artículos y hashes de integridad.

---

## 5. Metodología de Integración Normativa y Continuidad (Inspiración Global Suite)
`¤regulation-code` `¤adpa`

Inspirada en la capacidad de **Global Suite** para articular marcos regulatorios locales con estándares internacionales:
*   **Cruce y Coexistencia Normativa:**
    *   El núcleo opera con la LOPDP, RGLOPDP y normativa de la SPDP de Ecuador.
    *   Permite incorporar catálogos de buenas prácticas internacionales como **ISO/IEC 27002:2022** e **ISO/IEC 27701:2019**, etiquetándolos con claridad como *estándares complementarios* sin confundirlos con obligaciones legales vinculantes.
*   **Módulos de Continuidad y Ciberseguridad Conexa:**
    *   Articulación con la Ley Orgánica para el Fortalecimiento de la Ciberseguridad (notificación ágil de brechas) y marcos de continuidad operativa.

---

## 6. Metodología de Auditoría, Tickets y CAPA (Inspiración Novoser)
`¤auditoria` `¤incidentes`

Inspirada en los flujos de gestión de tickets y aseguramiento de **Novoser**:
*   **Trazabilidad de Hallazgos a Acciones Correctivas (CAPA):**
    *   Cada no conformidad u observación genera un ticket con causa raíz, acción correctiva/preventiva, responsable asignado, fecha compromiso y evidencia de cierre.
*   **Verificación Independiente de Cierre:**
    *   Ningún ejecutor puede cerrar su propia no conformidad; la verificación de eficacia es realizada por un rol independiente o auditor.
*   **Gestión de Incidentes con Reloj Normativo:**
    *   Cronómetro de cuenta regresiva para cumplimiento de plazos legales de notificación a la SPDP y CSIRT nacional.

---

## 7. Metodología de Gestión Visual de Riesgos (Inspiración Pirani / Pirámid)
`¤riesgos-eipd` `¤mtge-granescala`

Inspirada en el enfoque de **Pirani** para democratizar la gestión de riesgos en América Latina:
*   **Matrices Intuitivas de Calor:**
    *   Visualización clara de Probabilidad $\times$ Impacto en cuadrículas interactivas 3x3 y 5x5.
    *   Desmitificación de la matemática de riesgo mediante racionalidades guiadas, permitiendo que jefes de área de negocio identifiquen amenazas sin requerir formación actuarial avanzada.
*   **Cálculo Asistido de Gran Escala (MTGE):**
    *   Parámetros sencillos de volumen, permanencia y sensibilidad que arrojan automáticamente si el tratamiento detona obligaciones reforzadas.

---

## 8. Metodología de Orquestación y Comités (Inspiración Isotools)
`¤implementacion` `¤dpo-cockpit`

Inspirada en los flujos de gobierno y automatización de comités de **Isotools**:
*   **Automatización de Notificaciones y Recordatorios:**
    *   Alertas automáticas por correo y notificación in-app ante vencimiento de controles, expiración de evidencias o solicitudes de derechos ARCO+.
*   **Gestión Documental con Flujo de Aprobación Formal:**
    *   Workflow estricto: `Borrador → En Revisión (Legal/DPO) → Aprobado (Responsable) → Publicado/Vigente`.
    *   Control estricto de próximas fechas de revisión y control de versiones con historial de cambios inmutable.

---

## 9. Metodología de Desarrollo del Software: BBAP y Confinamiento ADPA
`¤bbap` `¤adpa`

Rige la construcción del software bajo el canon Zero-Regression:
1.  **Metodología BBAP en 2 Pasos:**
    *   *Paso 1 (Boceto libre):* Prototipado rápido de componentes, pantallas y esquemas con máxima apertura creativa.
    *   *Paso 2 (Sellado):* Verificación física observable con pruebas automatizadas, linters AST y sellado de compuertas sin código propietario ajeno.
2.  **Confinamiento Modular en Salas ADPA:**
    *   Cada dominio (`rat`, `diagnostico`, `riesgos`, `dpo_cockpit`, etc.) se aísla en una sala hermética con compuerta pública `_service.py`. Cero acoplamiento circular.

---

## 10. Metodología de Poda Ontológica y Parametrización en 2 Fases
`¤diagnostico-motor` `¤diagnostico`

Rige la instanciación de diagnósticos multirregulatorios escalables:
1.  **Fase 1: Parametrización de la Ficha Organizacional (Raíz de Poda):**
    *   El usuario define Razón Social, Sector, Tamaño de empresa y la Normativa objetivo (`Propiedad Intelectual`, `NIIF`, `ISO`).
    *   Esta configuración se almacena en el store reactivo global (`useAuditStore`) de forma desacoplada antes de generar cualquier pregunta.
2.  **Fase 2: Instanciación del Cuestionario Podado ($\le 80$ preguntas):**
    *   El motor proyecta las reglas del sector y normativa elegida, ocultando o podando todas las ramas no aplicables.
    *   Se evita la sobrecarga cognitiva del auditor, asegurando un recorrido enfocado y determinista.

---

## 11. Metodología de Whitelist Evidencial y Validación Poka-Yoke
`¤evidencias` `¤diagnostico`

Garantiza la integridad probatoria y evita inyecciones de archivos incompatibles:
1.  **Barrera Declarativa de Sistema Operativo:**
    *   El selector de archivos implementa el atributo `accept` dinámico según la normativa seleccionada (`.pdf,.docx,.md,.txt` para PI; formatos tabulares/estructurados `.csv,.xlsx,.xbrl,.ixbrl,.json,.xml,.sql` para NIIF/ISO).
2.  **Intercepción Reactiva en Memoria y Drag-and-Drop:**
    *   Tanto en la selección por diálogo como en la zona de arrastre (*Dropzone*), un validador JavaScript inspecciona las extensiones en tiempo real.
    *   Cualquier archivo fuera de whitelist es rechazado instantáneamente con feedback semántico `#ff1744` sin contaminar el arreglo global.
3.  **Purga Transaccional Inmediata:**
    *   Si el usuario cambia el selector de normativa, el método mutador `setNormativa` vacía automáticamente el arreglo de evidencias previas para garantizar que no existan documentos huérfanos o fuera de contexto normativo.

---

## 12. Metodología de Ergonomía Visual Acromática y Jerarquía Tonal Invertida
`¤frontend-ide`

Fundamentada en la Ley de Fitts, la Psicología de la Gestalt (Koffka, 1935) y el *Data-Ink Ratio* de Edward Tufte (1990) para mitigar la fatiga visual en auditorías prolongadas:
1.  **Base Acromática Estricta (Achromatic Baseline):**
    *   Los componentes estructurales estáticos (tarjetas, divisores, inputs, contenedores) se mantienen en escalas neutras de negros (`#0a0a0c`), grises oscuros (`#141417`, `#26262b`) y grises claros/blancos en tema claro, suprimiendo azules o tintes saturados que distraen la fovea.
2.  **Señalética Semántica Reservada:**
    *   El color se utiliza exclusivamente para comunicar estados críticos: Verde (`#00c853`) para éxito/conformidad, Rojo (`#ff1744`) para purga/brecha crítica, y gradiente púrpura-azul (`#9a3bf1` a `#3892f3`) para el desencadenante de acción principal (CTA).
3.  **Jerarquía Tonal Invertida:**
    *   La periferia de control (dock lateral de navegación y barra superior) posee la menor luminancia para estabilizar el horizonte visual, proyectando el mayor contraste y pureza lumínica sobre el lienzo central de trabajo.
4.  **Dock Dinámico Plegable:**
    *   El menú lateral mantiene sus íconos en tamaño natural y prescinde de títulos estáticos comprimidos ("Salas de cumplimiento"). Permite expansión suave y botón de abatimiento para ceder el 100% del espacio al análisis documental cuando sea requerido.

