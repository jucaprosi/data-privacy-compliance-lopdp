/**
 * Bloque 3 del banco de preguntas del assessment SGPDP (controles 49-80).
 *
 * Cubre las dimensiones D07 (Seguridad de datos personales), D08 (Incidentes y
 * vulneraciones), D09 (Riesgos, EIPD, LIA y privacidad desde el diseño) y D10
 * (Capacitación, cultura, auditoría y mejora continua).
 *
 * Doctrina 9 del PRD: este bloque concentra los controles más dependientes de
 * estructura organizacional (segregación de ambientes, simulacros, auditoría
 * interna), por lo que carga deliberadamente hacia tallas altas. El enunciado
 * base de cada control está redactado para la talla declarada en tamanoMinimo;
 * las variantes superiores no rebajan la obligación legal, solo ajustan la
 * forma en que el control se verifica.
 */

import type { PreguntaAssessment } from "@/lib/bancoPreguntas/tipos";

export const BLOQUE_3: PreguntaAssessment[] = [
  {
    id: 49,
    dimensionId: "D07",
    control: "Gestión de identidades y accesos",
    enunciado:
      "¿Existe una matriz de accesos por rol para POS, ERP, CRM, e-commerce, contabilidad, RR. HH., archivos y otros sistemas críticos?",
    criterioMadurez:
      "Los perfiles están documentados, aprobados y revisados periódicamente, conforme a funciones de tiendas/cajas, ventas, servicio al cliente, bodega, logística, administración y TI.",
    referenciaNormativa:
      "LOPDP Art. 38 y Art. 39 (Seguridad y confidencialidad); ISO/IEC 27002:2022 (gestión de identidades y control de acceso) como marco técnico complementario",
    criticidad: 5,
    evidenciaEsperada:
      "Listado de usuarios por sistema con el cargo asociado y registro de bajas ejecutadas",
    evidenciaPorTamano: {
      mediana:
        "Matriz de perfiles y privilegios por rol y actas de revisión periódica de accesos",
      corporativo:
        "Reportes de recertificación de accesos del proveedor de identidad, inventario de cuentas privilegiadas y trazabilidad de altas y bajas",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 50,
    dimensionId: "D07",
    control: "Autenticación multifactor",
    enunciado:
      "¿Se evita el uso de usuarios compartidos en sistemas críticos?",
    criterioMadurez:
      "Cada usuario tiene credenciales individuales, trazabilidad y baja oportuna.",
    referenciaNormativa:
      "LOPDP Art. 38 y Guía de Controles Técnicos SPDP; ISO/IEC 27002:2022 (autenticación segura) como marco técnico complementario",
    criticidad: 5,
    evidenciaEsperada:
      "Constancia de la configuración de doble factor activa en el proveedor de correo o de nube",
    evidenciaPorTamano: {
      corporativo:
        "Reporte de cobertura de multifactor por sistema y usuario, con el registro de excepciones aprobadas y su vigencia",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 51,
    dimensionId: "D07",
    control: "Cifrado en tránsito y en reposo",
    enunciado:
      "¿Se aplica autenticación robusta y MFA en correo, nube, core, VPN, administración y accesos críticos?",
    criterioMadurez:
      "Los accesos críticos tienen MFA o controles compensatorios, políticas de contraseña, bloqueo, gestión de privilegios y revisión periódica.",
    referenciaNormativa:
      "LOPDP Art. 25 y Art. 26 (datos sensibles) y Art. 38; ISO/IEC 27002:2022 (uso de criptografía) como marco técnico complementario",
    criticidad: 5,
    evidenciaEsperada:
      "Certificado TLS vigente del sitio y constancia de cifrado de disco en los equipos de trabajo",
    evidenciaPorTamano: {
      mediana:
        "Estándar de cifrado aprobado con el inventario de sistemas cubiertos y su configuración vigente",
      corporativo:
        "Política de gestión de llaves, registros de custodia y rotación e informe de verificación independiente de cobertura",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 52,
    dimensionId: "D07",
    control: "Registros de auditoría y monitoreo",
    enunciado:
      "¿Existen respaldos periódicos y pruebas de restauración de información crítica?",
    criterioMadurez:
      "Backups automatizados, protegidos, con pruebas documentadas y objetivos definidos.",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 38; ISO/IEC 27002:2022 (registro de eventos y monitoreo) como marco técnico complementario",
    criticidad: 4,
    evidenciaEsperada:
      "Muestra de registros de auditoría de los sistemas principales con marca de tiempo y usuario identificado",
    evidenciaPorTamano: {
      corporativo:
        "Reglas de correlación y alertamiento configuradas, política de retención de registros y bitácora de casos atendidos",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 53,
    dimensionId: "D07",
    control: "Respaldos y pruebas de restauración",
    enunciado:
      "¿Se aplican controles de cifrado o protección en laptops, móviles y medios removibles?",
    criterioMadurez:
      "Dispositivos con cifrado, bloqueo, control de USB y gestión de pérdida/robo.",
    referenciaNormativa:
      "LOPDP Art. 38 y Art. 39; ISO/IEC 27002:2022 (respaldo de la información) como marco técnico complementario",
    criticidad: 4,
    evidenciaEsperada:
      "Constancia de la última copia de respaldo y de al menos una restauración verificada",
    evidenciaPorTamano: {
      mediana:
        "Política de respaldos aprobada y reportes de ejecución y de pruebas de restauración",
      corporativo:
        "Matriz de RPO y RTO por sistema, calendario de pruebas, actas de resultados y reporte de cobertura sobre el inventario",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 54,
    dimensionId: "D07",
    control: "Gestión de vulnerabilidades y parcheo",
    enunciado:
      "¿Los sistemas críticos registran accesos, cambios y eventos relevantes?",
    criterioMadurez:
      "Logs habilitados, conservados y revisados para detectar accesos indebidos.",
    referenciaNormativa:
      "LOPDP Art. 38 (medidas técnicas de seguridad); ISO/IEC 27002:2022 (gestión de vulnerabilidades técnicas) como marco técnico complementario",
    criticidad: 4,
    evidenciaEsperada:
      "Registro de actualizaciones aplicadas en equipos y servidores durante el último período",
    evidenciaPorTamano: {
      corporativo:
        "Reportes de escaneo y de pruebas de intrusión, plan de remediación con plazos por severidad e indicadores de cierre",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 55,
    dimensionId: "D07",
    control: "Segregación de ambientes",
    enunciado:
      "¿Existe proceso de actualización, parches y gestión de vulnerabilidades?",
    criterioMadurez:
      "Se priorizan vulnerabilidades según criticidad y exposición de datos personales.",
    referenciaNormativa:
      "LOPDP Art. 38 y principio de minimización de datos; ISO/IEC 27002:2022 (separación de ambientes de desarrollo, prueba y producción) como marco técnico complementario",
    criticidad: 3,
    evidenciaEsperada:
      "Diagrama de ambientes y procedimiento de paso a producción",
    evidenciaPorTamano: {
      corporativo:
        "Política de gestión de ambientes, evidencia de enmascaramiento o generación de datos sintéticos y registro de accesos por ambiente",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 56,
    dimensionId: "D07",
    control: "Seguridad física de instalaciones",
    enunciado:
      "¿Existen controles físicos sobre documentos, archivos y puestos con datos personales?",
    criterioMadurez:
      "Archivo bajo control, acceso limitado, puesto limpio, impresión segura y destrucción adecuada.",
    referenciaNormativa:
      "LOPDP Art. 38 (medidas técnicas y organizativas); ISO/IEC 27002:2022 (controles físicos) como marco técnico complementario",
    criticidad: 3,
    evidenciaEsperada:
      "Constancia de archivadores con llave o área restringida y listado de responsables de custodia",
    evidenciaPorTamano: {
      corporativo:
        "Bitácora de accesos físicos, política de videovigilancia y matriz de autorizaciones vigentes por área",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 57,
    dimensionId: "D08",
    control: "Procedimiento de gestión de incidentes",
    enunciado:
      "¿Existe procedimiento formal para incidentes, envío indebido, acceso no autorizado, pérdida o indisponibilidad de datos personales?",
    criterioMadurez:
      "Define detección, registro, clasificación, contención, escalamiento, análisis de titulares afectados, comunicación, evidencias y lecciones aprendidas.",
    referenciaNormativa:
      "LOPDP Art. 40 y Art. 41 (Vulneración de la seguridad de datos personales)",
    criticidad: 5,
    evidenciaEsperada:
      "Instructivo de reporte de incidentes difundido al personal",
    evidenciaPorTamano: {
      mediana:
        "Plan de respuesta a incidentes aprobado con roles, flujos de atención y criterios de activación",
      corporativo:
        "Plan de respuesta vigente con matriz de responsabilidades, acta de revisión anual y evidencia de difusión",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 58,
    dimensionId: "D08",
    control: "Registro y bitácora de incidentes",
    enunciado:
      "¿Se mantiene un registro de incidentes, sospechas y eventos relevantes?",
    criterioMadurez:
      "El registro documenta fecha, tipo, datos afectados, medidas, responsables y lecciones aprendidas.",
    referenciaNormativa:
      "LOPDP Art. 40 y Art. 10 (Responsabilidad Proactiva)",
    criticidad: 4,
    evidenciaEsperada:
      "Bitácora o registro de incidentes con los casos de los últimos doce meses",
    evidenciaPorTamano: {
      corporativo:
        "Registro en herramienta de gestión con métricas de tiempo de detección y respuesta y reportes emitidos al DPD",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 59,
    dimensionId: "D08",
    control: "Clasificación de severidad",
    enunciado:
      "¿Los incidentes se clasifican según impacto en titulares y datos afectados?",
    criterioMadurez:
      "Se aplica criterio para diferenciar eventos, incidentes y vulneraciones de seguridad.",
    referenciaNormativa:
      "LOPDP Art. 40 y Art. 41 (criterios de riesgo para los derechos de los titulares)",
    criticidad: 3,
    evidenciaEsperada:
      "Matriz de severidad de incidentes con los criterios de clasificación aplicados",
    evidenciaPorTamano: {
      corporativo:
        "Matriz de severidad parametrizada en la herramienta y evidencia de su aplicación en casos reales",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 60,
    dimensionId: "D08",
    control: "Criterios de notificación a la autoridad",
    enunciado:
      "¿Existe escalamiento oportuno a dirección, TI, legal, DPO y áreas afectadas?",
    criterioMadurez:
      "Roles y contactos están definidos, con tiempos de respuesta por criticidad.",
    referenciaNormativa:
      "LOPDP Art. 40 (Notificación de vulneraciones a la autoridad de protección de datos)",
    criticidad: 5,
    evidenciaEsperada:
      "Procedimiento de notificación con el plazo legal y el responsable identificado",
    evidenciaPorTamano: {
      corporativo:
        "Expedientes de evaluación de riesgo por incidente, incluidas las decisiones motivadas de no notificar, y constancias de envío a la autoridad",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 61,
    dimensionId: "D08",
    control: "Contención y preservación de evidencia",
    enunciado:
      "¿Se documentan medidas de contención y preservación de evidencia?",
    criterioMadurez:
      "Se resguarda evidencia mínima para análisis y mejora sin exposición innecesaria.",
    referenciaNormativa:
      "LOPDP Art. 40 y Art. 41; ISO/IEC 27002:2022 (recolección de evidencia) como marco técnico complementario",
    criticidad: 4,
    evidenciaEsperada:
      "Instructivo de contención y preservación de evidencia ante incidentes",
    evidenciaPorTamano: {
      corporativo:
        "Acuerdo de respuesta con proveedor forense, formatos de cadena de custodia y expedientes de los casos atendidos",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 62,
    dimensionId: "D08",
    control: "Comunicación a titulares afectados",
    enunciado:
      "¿Existe criterio para evaluar si corresponde notificar a titulares o autoridad?",
    criterioMadurez:
      "El procedimiento incluye evaluación normativa, impacto y decisión documentada.",
    referenciaNormativa:
      "LOPDP Art. 41 (Comunicación de la vulneración al titular)",
    criticidad: 5,
    evidenciaEsperada:
      "Modelo de comunicación al titular y constancia de envío en los casos ocurridos",
    evidenciaPorTamano: {
      corporativo:
        "Plantillas validadas por el área legal, registro de envíos por canal y reporte de atención de consultas asociadas",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 63,
    dimensionId: "D08",
    control: "Pruebas o simulacros tabletop",
    enunciado:
      "¿Se realizan simulacros de incidentes de datos personales?",
    criterioMadurez:
      "Se prueban escenarios realistas, se miden tiempos y se corrigen brechas.",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 40; ISO/IEC 27002:2022 (preparación de la respuesta a incidentes) como marco técnico complementario",
    criticidad: 2,
    evidenciaEsperada:
      "Acta del simulacro con escenario, participantes y conclusiones",
    evidenciaPorTamano: {
      corporativo:
        "Programa anual de simulacros, informes por ejercicio con métricas de respuesta y plan de acción con seguimiento",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 64,
    dimensionId: "D08",
    control: "Lecciones aprendidas y cierre",
    enunciado:
      "¿Los incidentes generan acciones correctivas y seguimiento hasta cierre?",
    criterioMadurez:
      "Cada incidente relevante tiene causa raíz, acciones, responsables y evidencia de cierre.",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 40",
    criticidad: 3,
    evidenciaEsperada:
      "Informe de cierre de incidentes con causa raíz y medida adoptada",
    evidenciaPorTamano: {
      corporativo:
        "Expedientes de cierre con verificación de eficacia de las acciones y actas de revisión ante el comité de privacidad",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 65,
    dimensionId: "D09",
    control: "Metodología de gestión de riesgos",
    enunciado:
      "¿Existe metodología para identificar, analizar, evaluar y tratar riesgos de protección de datos?",
    criterioMadurez:
      "La metodología considera derechos y libertades de titulares, amenazas, vulnerabilidades y controles.",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva), Art. 38 y Art. 42",
    criticidad: 4,
    evidenciaEsperada:
      "Matriz de riesgos de los tratamientos con su valoración y las medidas definidas",
    evidenciaPorTamano: {
      mediana:
        "Metodología aprobada y registro de riesgos con dueños asignados y estado de tratamiento",
      corporativo:
        "Registro corporativo de riesgos de privacidad, actas de revisión periódica y reportes emitidos a la dirección",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 66,
    dimensionId: "D09",
    control: "Criterios de activación de EIPD",
    enunciado:
      "¿Existe registro actualizado de riesgos por tratamiento o proceso?",
    criterioMadurez:
      "El registro incluye escenarios, probabilidad, impacto, controles, riesgo residual y tratamiento.",
    referenciaNormativa:
      "LOPDP Art. 42 y Art. 43 (Evaluación de impacto en protección de datos)",
    criticidad: 4,
    evidenciaEsperada:
      "Listado de criterios de activación de la EIPD adoptado por la organización",
    evidenciaPorTamano: {
      corporativo:
        "Registro de evaluaciones previas por proyecto con decisión motivada, fecha y responsable",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 67,
    dimensionId: "D09",
    control: "Ejecución y aprobación de EIPD",
    enunciado:
      "¿Se cuenta con criterios para determinar cuándo realizar una EIPD?",
    criterioMadurez:
      "Los criterios consideran alto riesgo, datos sensibles, volumen, tecnología, perfilamiento y grupos vulnerables.",
    referenciaNormativa:
      "LOPDP Art. 42, Art. 43 y Art. 44 (Consulta previa a la autoridad)",
    criticidad: 5,
    evidenciaEsperada:
      "Informe de EIPD de los tratamientos de mayor riesgo identificados",
    evidenciaPorTamano: {
      mediana:
        "EIPD suscritas con intervención del DPD y constancia de aprobación previa al tratamiento",
      corporativo:
        "Repositorio versionado de EIPD, plan de revisión y oficios de consulta previa a la SPDP cuando corresponda",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 68,
    dimensionId: "D09",
    control: "Evaluación de interés legítimo (LIA)",
    enunciado:
      "¿Los tratamientos de alto riesgo cuentan con EIPD o evaluación proporcional documentada?",
    criterioMadurez:
      "Se documentan riesgos, medidas, necesidad/proporcionalidad, consulta y riesgo residual.",
    referenciaNormativa: "LOPDP Art. 7 numeral 8 (Interés legítimo)",
    criticidad: 4,
    evidenciaEsperada:
      "Informe de ponderación de interés legítimo por cada tratamiento que lo invoca",
    evidenciaPorTamano: {
      corporativo:
        "Repositorio de evaluaciones de interés legítimo vinculado al RAT, con fecha de última revisión",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 69,
    dimensionId: "D09",
    control: "Privacidad desde el diseño en proyectos",
    enunciado:
      "¿Cuando se usa interés legítimo existe análisis de ponderación documentado?",
    criterioMadurez:
      "Se evalúa finalidad, necesidad, balance con derechos del titular y salvaguardas.",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 42; Reglamento General a la LOPDP",
    criticidad: 4,
    evidenciaEsperada:
      "Requisitos de privacidad incorporados en la documentación de los proyectos recientes",
    evidenciaPorTamano: {
      corporativo:
        "Procedimiento de compuertas de privacidad en el ciclo de vida, listas de verificación aplicadas y actas de aprobación o rechazo",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 70,
    dimensionId: "D09",
    control: "Privacidad por defecto en configuraciones",
    enunciado:
      "¿Los nuevos proyectos/sistemas incorporan privacidad desde el diseño y por defecto?",
    criterioMadurez:
      "Existe checklist en gestión de proyectos, cambios, sistemas, formularios y automatizaciones.",
    referenciaNormativa:
      "LOPDP Art. 10 y principios de minimización y limitación de la finalidad; Reglamento General a la LOPDP",
    criticidad: 3,
    evidenciaEsperada:
      "Revisión de formularios y configuraciones que acredite la recolección mínima de datos",
    evidenciaPorTamano: {
      corporativo:
        "Informes de verificación de configuraciones por defecto y registro de desviaciones detectadas y corregidas",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 71,
    dimensionId: "D09",
    control: "Tratamiento de riesgo residual",
    enunciado:
      "¿Se aplican técnicas de anonimización/seudonimización cuando se usan datos para análisis o pruebas?",
    criterioMadurez:
      "Se evita usar datos reales si no es necesario y se documentan técnicas aplicadas.",
    referenciaNormativa:
      "LOPDP Art. 42 y Art. 44 (riesgo residual alto y consulta previa)",
    criticidad: 4,
    evidenciaEsperada:
      "Registro de riesgos residuales con la aceptación suscrita por el responsable",
    evidenciaPorTamano: {
      corporativo:
        "Portafolio de riesgos aceptados con vigencia y condiciones, y actas de revisión por la dirección",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 72,
    dimensionId: "D09",
    control: "Decisiones automatizadas y perfilado",
    enunciado:
      "¿Los cambios relevantes disparan revisión de riesgos, EIPD, avisos, contratos y controles?",
    criterioMadurez:
      "Existe flujo de gestión de cambios con participación de DPO/TI/legal según riesgo.",
    referenciaNormativa:
      "LOPDP, disposiciones sobre valoraciones automatizadas y elaboración de perfiles, y Art. 42 (Evaluación de impacto)",
    criticidad: 4,
    evidenciaEsperada:
      "Identificación de los tratamientos con decisiones automatizadas y el texto informativo entregado al titular",
    evidenciaPorTamano: {
      mediana:
        "EIPD del tratamiento automatizado y procedimiento de intervención humana documentado",
      corporativo:
        "Inventario de modelos con evaluaciones de sesgo y desempeño y bitácora de auditoría de las decisiones emitidas",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 73,
    dimensionId: "D10",
    control: "Plan de capacitación en protección de datos",
    enunciado:
      "¿Existe plan anual de capacitación en protección de datos personales?",
    criterioMadurez:
      "El plan cubre roles, riesgos, canales, incidentes, derechos y seguridad básica.",
    referenciaNormativa:
      "LOPDP Art. 47 numeral 3 (Capacitación) y Art. 10 (Responsabilidad Proactiva)",
    criticidad: 4,
    evidenciaEsperada:
      "Registro de asistencia y material de la capacitación impartida",
    evidenciaPorTamano: {
      mediana:
        "Plan anual de capacitación aprobado y reporte de cobertura por rol",
      corporativo:
        "Reportes de cumplimiento por área, mallas de contenido por rol y evidencia de refuerzos ante cambios normativos",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 74,
    dimensionId: "D10",
    control: "Campañas de concienciación",
    enunciado:
      "¿La inducción incluye confidencialidad y protección de datos desde el ingreso?",
    criterioMadurez:
      "Todo nuevo colaborador recibe capacitación y firma compromisos aplicables.",
    referenciaNormativa:
      "LOPDP Art. 47 numeral 3; ISO/IEC 27002:2022 (concienciación, educación y formación) como marco técnico complementario",
    criticidad: 2,
    evidenciaEsperada:
      "Piezas de comunicación interna difundidas y constancia de su envío",
    evidenciaPorTamano: {
      corporativo:
        "Plan anual de concienciación, métricas de alcance y resultados de los ejercicios de simulación aplicados",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 75,
    dimensionId: "D10",
    control: "Evaluación de eficacia de la formación",
    enunciado:
      "¿El personal recibe formación específica según su exposición a datos personales?",
    criterioMadurez:
      "Atención, TI, RRHH, marketing, finanzas y dirección reciben contenidos diferenciados.",
    referenciaNormativa:
      "LOPDP Art. 47 numeral 3 y Art. 10 (Responsabilidad Proactiva)",
    criticidad: 2,
    evidenciaEsperada:
      "Resultados de las evaluaciones de conocimiento aplicadas al personal",
    evidenciaPorTamano: {
      corporativo:
        "Tablero de indicadores de eficacia formativa y acta de ajuste del plan basada en esos resultados",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 76,
    dimensionId: "D10",
    control: "Programa de auditoría interna",
    enunciado:
      "¿Se mide la comprensión del personal después de las capacitaciones?",
    criterioMadurez:
      "Se aplican evaluaciones y refuerzos según resultados.",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 47; ISO/IEC 27002:2022 (revisión independiente de la seguridad de la información) como marco técnico complementario",
    criticidad: 3,
    evidenciaEsperada:
      "Programa anual de auditoría con alcance, frecuencia y responsables",
    evidenciaPorTamano: {
      corporativo:
        "Programa plurianual aprobado con enfoque de riesgos y declaración de independencia del equipo auditor",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 77,
    dimensionId: "D10",
    control: "Ejecución de auditorías del SGPDP",
    enunciado:
      "¿Existen campañas internas sobre confidencialidad, phishing, WhatsApp y datos personales?",
    criterioMadurez:
      "Se realizan comunicaciones periódicas y prácticas.",
    referenciaNormativa:
      "LOPDP Art. 10 y Art. 47; ISO/IEC 27002:2022 (revisión independiente) como marco técnico complementario",
    criticidad: 3,
    evidenciaEsperada:
      "Informes de auditoría con alcance, pruebas realizadas, evidencia recolectada y conclusiones por proceso",
    tamanoMinimo: "corporativo",
  },
  {
    id: 78,
    dimensionId: "D10",
    control: "Gestión de hallazgos",
    enunciado:
      "¿Se realizan revisiones internas del SGPDP y sus evidencias?",
    criterioMadurez:
      "Se revisan documentos, registros, incidentes, derechos, proveedores y controles al menos anualmente.",
    referenciaNormativa: "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 47",
    criticidad: 3,
    evidenciaEsperada:
      "Registro consolidado de hallazgos con severidad, causa raíz, responsable y estado de atención",
    tamanoMinimo: "corporativo",
  },
  {
    id: 79,
    dimensionId: "D10",
    control: "Seguimiento de acciones correctivas",
    enunciado:
      "¿Las brechas identificadas tienen responsable, plazo, estado y evidencia de cierre?",
    criterioMadurez:
      "Existe plan de acción activo y revisado periódicamente.",
    referenciaNormativa: "LOPDP Art. 10 y Art. 47",
    criticidad: 3,
    evidenciaEsperada:
      "Reportes de seguimiento con fechas comprometidas, estado, verificación de eficacia y escalamientos registrados",
    tamanoMinimo: "corporativo",
  },
  {
    id: 80,
    dimensionId: "D10",
    control: "Mejora continua y revisión por dirección",
    enunciado:
      "¿La alta dirección revisa periódicamente resultados, riesgos y madurez del SGPDP?",
    criterioMadurez:
      "Se presentan indicadores, brechas, riesgos residuales y decisiones de mejora.",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 47",
    criticidad: 3,
    evidenciaEsperada:
      "Acta de revisión por la dirección con indicadores presentados, decisiones adoptadas y asignación de recursos",
    tamanoMinimo: "corporativo",
  },
];
