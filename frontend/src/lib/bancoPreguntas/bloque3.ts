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
      "¿Cada persona que accede a sistemas o archivos con datos personales lo hace con un usuario propio y no compartido, y el acceso se retira cuando deja el cargo?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe un procedimiento de altas, cambios y bajas de usuarios que asigne los accesos según el cargo y retire los permisos al desvincularse la persona?",
      mediana:
        "¿Se administra el acceso a los sistemas que tratan datos personales bajo un modelo de roles con principio de mínimo privilegio y revisión periódica de privilegios?",
      corporativo:
        "¿La gestión de identidades se centraliza en un proveedor de identidad, con aprovisionamiento y desaprovisionamiento automatizados, control reforzado de cuentas privilegiadas y recertificación documentada de accesos?",
    },
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
      "¿Los accesos al correo corporativo y a los servicios en la nube que contienen datos personales exigen un segundo factor de autenticación?",
    enunciadoPorTamano: {
      pequena:
        "¿Se exige autenticación multifactor en todo acceso remoto y en las cuentas con privilegios administrativos sobre sistemas que tratan datos personales?",
      corporativo:
        "¿La autenticación multifactor se aplica de forma obligatoria y verificable a todo acceso a sistemas que tratan datos personales, con excepciones formalmente autorizadas, de vigencia limitada y con reporte periódico de cobertura?",
    },
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
      "¿Los sitios y formularios que recogen datos personales operan sobre canales cifrados (HTTPS/TLS) y los equipos que almacenan datos personales cuentan con cifrado de disco?",
    enunciadoPorTamano: {
      pequena:
        "¿Se cifran los datos personales en tránsito y en reposo en servidores, bases de datos, respaldos y dispositivos móviles de la organización?",
      mediana:
        "¿Existe un estándar de cifrado que defina algoritmos y longitudes mínimas para datos personales en tránsito y en reposo, con protección reforzada de las categorías especiales de datos?",
      corporativo:
        "¿El estándar de cifrado se aplica sobre el inventario completo de tratamientos, con gestión formal del ciclo de vida de las llaves (custodia, rotación y revocación) y verificación independiente de su cumplimiento?",
    },
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
      "¿Los sistemas que tratan datos personales generan registros de acceso y de operaciones (consulta, modificación y exportación) que permitan determinar quién hizo qué y cuándo?",
    enunciadoPorTamano: {
      mediana:
        "¿Los registros de auditoría se conservan por un plazo definido, se protegen contra alteración o borrado y se revisan periódicamente para detectar accesos indebidos?",
      corporativo:
        "¿Los registros se centralizan en una plataforma de correlación con alertas sobre accesos anómalos o exportaciones masivas de datos personales, y con monitoreo y atención de casos documentados?",
    },
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
      "¿Se realizan copias de respaldo de la información que contiene datos personales y se ha comprobado alguna vez que esa información pueda recuperarse?",
    enunciadoPorTamano: {
      pequena:
        "¿Los respaldos se ejecutan con una frecuencia definida, se almacenan en una ubicación separada del sistema de origen y se prueban restauraciones al menos una vez al año?",
      mediana:
        "¿Existe una política de respaldos con cobertura definida sobre los sistemas que tratan datos personales, y se ejecutan pruebas periódicas de restauración con resultados documentados?",
      corporativo:
        "¿La política de respaldos define RPO y RTO por sistema, con copias inmutables o fuera de línea, pruebas de restauración calendarizadas, evidencia de resultados y cobertura verificada sobre todo el inventario de tratamientos?",
    },
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
      "¿Se mantienen actualizados los sistemas operativos, aplicaciones y complementos de los equipos y servidores que tratan datos personales?",
    enunciadoPorTamano: {
      mediana:
        "¿Existe un proceso de gestión de vulnerabilidades con análisis periódicos, priorización por severidad y plazos definidos de remediación?",
      corporativo:
        "¿El proceso de gestión de vulnerabilidades cubre el inventario completo de activos, con escaneos recurrentes, pruebas de intrusión periódicas, plazos de remediación comprometidos por severidad e indicadores reportados a la dirección?",
    },
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
      "¿Los ambientes de desarrollo, pruebas y producción se encuentran separados, y se evita el uso de datos personales reales en ambientes distintos de producción?",
    enunciadoPorTamano: {
      corporativo:
        "¿La separación de ambientes está formalizada con control de accesos diferenciado, prohibición documentada del uso de datos personales reales fuera de producción y técnicas de anonimización o datos sintéticos cuando se requiere poblar pruebas?",
    },
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
      "¿Los archivos físicos y los equipos que contienen datos personales se guardan bajo llave o en áreas de acceso restringido?",
    enunciadoPorTamano: {
      pequena:
        "¿Existen controles de acceso físico a las áreas donde se custodian archivos o equipos con datos personales, y una práctica de escritorio y pantalla despejados?",
      corporativo:
        "¿El control de acceso físico a áreas críticas opera con registro auditable de ingresos, videovigilancia sujeta a su propia base de licitud e información al titular, y revisión periódica de las autorizaciones vigentes?",
    },
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
      "¿Se ha definido por escrito qué debe hacer el personal cuando detecta una posible pérdida, acceso indebido o divulgación no autorizada de datos personales, y a quién debe reportarlo?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe un procedimiento de gestión de incidentes con roles asignados, canal de reporte conocido por el personal y plazos internos de escalamiento?",
      mediana:
        "¿El procedimiento cubre detección, contención, erradicación, recuperación y cierre del incidente, con un equipo de respuesta designado y criterios formales de activación?",
      corporativo:
        "¿El plan de respuesta a incidentes se integra con la continuidad del negocio, define responsabilidades formales, escalamiento a la alta dirección y apoyo legal y forense, y se revisa al menos anualmente?",
    },
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
      "¿Se deja constancia escrita de los incidentes de seguridad que afectan datos personales, incluyendo fecha de detección, datos involucrados y acciones tomadas?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe una bitácora única de incidentes que registre detección, severidad, datos y titulares afectados, medidas adoptadas y la decisión sobre la notificación a la autoridad?",
      corporativo:
        "¿La bitácora se gestiona en una herramienta con trazabilidad de tiempos por etapa, indicadores de detección y respuesta, y reporte periódico al Delegado de Protección de Datos y a la dirección?",
    },
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
      "¿Se clasifica cada incidente según su severidad a partir del volumen de titulares, el tipo de datos comprometidos y el impacto probable sobre las personas?",
    enunciadoPorTamano: {
      mediana:
        "¿Existe una escala de severidad documentada que determine tiempos de respuesta, nivel de escalamiento y activación de la notificación a la autoridad?",
      corporativo:
        "¿La escala de severidad se encuentra integrada a la herramienta de gestión, se aplica de forma consistente y se calibra con base en los incidentes y simulacros ejecutados?",
    },
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
      "¿La organización conoce y tiene documentado en qué casos y dentro de qué plazo debe notificar una vulneración de seguridad a la Superintendencia de Protección de Datos Personales?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe un procedimiento que fije el criterio de riesgo para notificar, el contenido mínimo de la notificación, el responsable de emitirla y el control del plazo legal?",
      corporativo:
        "¿El procedimiento contempla una evaluación formal del riesgo documentada incluso cuando se decide no notificar, notificación por fases cuando la información aún es incompleta y validación legal previa al envío?",
    },
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
      "¿El procedimiento de incidentes indica cómo contener el evento (bloqueo de cuentas, aislamiento de equipos) sin destruir la información que permite reconstruir lo ocurrido?",
    enunciadoPorTamano: {
      mediana:
        "¿Se preservan registros, imágenes de sistemas y cadena de custodia que permitan el análisis posterior del incidente y su eventual uso probatorio?",
      corporativo:
        "¿Existe capacidad forense propia o contratada con acuerdos previos de respuesta, protocolos de cadena de custodia y criterios de retención de evidencia alineados a los plazos aplicables?",
    },
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
      "¿Se comunica a los titulares afectados cuando una vulneración de seguridad puede afectar sus derechos, indicándoles qué ocurrió y qué medidas pueden adoptar?",
    enunciadoPorTamano: {
      pequena:
        "¿Existen plantillas y un canal definido para comunicar la vulneración a los titulares, con el contenido mínimo exigido y registro de la fecha y el medio de envío?",
      corporativo:
        "¿La comunicación a titulares contempla criterios para la difusión pública cuando el contacto individual resulta desproporcionado, coordinación con comunicación corporativa y atención reforzada de las consultas derivadas del incidente?",
    },
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
      "¿Se ejecuta al menos un ejercicio de simulacro anual sobre un escenario de vulneración de datos personales, con participación de las áreas involucradas?",
    enunciadoPorTamano: {
      corporativo:
        "¿El programa de simulacros cubre escenarios diferenciados (secuestro de información, filtración por un encargado, exfiltración interna), incorpora a la alta dirección y al área legal, mide tiempos de respuesta y genera un plan de acción con responsables y plazos?",
    },
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
      "¿Al cerrar un incidente se identifica su causa raíz y se define al menos una medida concreta para evitar que vuelva a ocurrir?",
    enunciadoPorTamano: {
      mediana:
        "¿El cierre de cada incidente exige análisis de causa raíz, acciones correctivas con responsable y plazo, y verificación de su implementación antes de darlo por concluido?",
      corporativo:
        "¿Las lecciones aprendidas se consolidan en revisiones periódicas que actualizan políticas, controles y contenidos de capacitación, y se reportan al comité de privacidad o a la alta dirección?",
    },
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
      "¿Se identifican y valoran los riesgos para los derechos de los titulares asociados a los tratamientos de datos personales que realiza la organización?",
    enunciadoPorTamano: {
      mediana:
        "¿Existe una metodología documentada de gestión de riesgos de privacidad con criterios de probabilidad e impacto, apetito de riesgo definido y un registro de riesgos actualizado?",
      corporativo:
        "¿La metodología de riesgos de privacidad se integra al marco corporativo de riesgos, con dueños de riesgo designados, tratamiento formal de cada riesgo, revisión periódica y reporte a la alta dirección?",
    },
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
      "¿La organización sabe identificar cuándo un tratamiento nuevo o modificado exige realizar una Evaluación de Impacto en Protección de Datos antes de ponerlo en marcha?",
    enunciadoPorTamano: {
      pequena:
        "¿Existen criterios documentados de activación de la EIPD (datos sensibles, tratamiento a gran escala, elaboración de perfiles, tecnologías emergentes, videovigilancia) aplicados de forma sistemática a los proyectos?",
      corporativo:
        "¿La evaluación previa de necesidad de EIPD es obligatoria y trazable para todo proyecto o cambio, con registro de la decisión motivada aun cuando el resultado sea que no procede?",
    },
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
      "¿Se han realizado Evaluaciones de Impacto para los tratamientos de alto riesgo identificados, describiendo el tratamiento, los riesgos y las medidas adoptadas?",
    enunciadoPorTamano: {
      pequena:
        "¿Las EIPD se ejecutan con una metodología definida, incluyen el juicio de necesidad y proporcionalidad, y son aprobadas por un responsable antes del inicio del tratamiento?",
      mediana:
        "¿Las EIPD cuentan con la participación del Delegado de Protección de Datos, se aprueban formalmente y se revisan cuando cambian las condiciones del tratamiento?",
      corporativo:
        "¿Existe un repositorio de EIPD versionadas, con criterio y constancia de consulta previa a la autoridad cuando subsiste un riesgo residual alto, y con revisión programada ante cambios materiales?",
    },
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
      "¿Cuando el tratamiento se sustenta en interés legítimo, se documenta la ponderación entre ese interés y los derechos y expectativas razonables de los titulares?",
    enunciadoPorTamano: {
      mediana:
        "¿Las evaluaciones de interés legítimo siguen un formato estándar con juicio de idoneidad, necesidad y proporcionalidad, medidas compensatorias y constancia del derecho de oposición?",
      corporativo:
        "¿Cada tratamiento basado en interés legítimo cuenta con su evaluación vinculada al registro de actividades de tratamiento, revisada periódicamente y actualizada ante cambios de finalidad o de contexto?",
    },
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
      "¿Los nuevos proyectos, sistemas o productos que traten datos personales incorporan requisitos de privacidad desde su fase de diseño y no como un ajuste posterior?",
    enunciadoPorTamano: {
      corporativo:
        "¿Existe una compuerta formal de privacidad en el ciclo de vida de proyectos y de desarrollo, con requisitos obligatorios, revisión por el equipo de privacidad y capacidad de detener el paso a producción cuando no se cumplen?",
    },
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
      "¿Los sistemas y formularios recogen únicamente los datos necesarios y mantienen por defecto la configuración menos invasiva para el titular?",
    enunciadoPorTamano: {
      pequena:
        "¿Las configuraciones por defecto limitan la cantidad de datos recogidos, el alcance del tratamiento, el plazo de conservación y la accesibilidad, sin requerir acción del titular?",
      corporativo:
        "¿La privacidad por defecto se verifica de forma recurrente sobre las configuraciones productivas (visibilidad, retención, compartición y telemetría), con desviaciones registradas y corregidas?",
    },
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
      "¿El riesgo que permanece después de aplicar las medidas de mitigación se documenta y se somete a aceptación por un responsable con autoridad suficiente?",
    enunciadoPorTamano: {
      corporativo:
        "¿Las aceptaciones de riesgo residual se emiten por escrito con vigencia limitada y condiciones de revisión, se escalan a la alta dirección cuando el riesgo es alto y se administran como un portafolio con seguimiento?",
    },
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
      "¿Se ha identificado si la organización adopta decisiones sobre las personas de forma automatizada o mediante elaboración de perfiles, y se informa de ello a los titulares?",
    enunciadoPorTamano: {
      pequena:
        "¿Los tratamientos con decisiones automatizadas o elaboración de perfiles informan la lógica aplicada y sus consecuencias, y ofrecen un canal para solicitar intervención humana e impugnar la decisión?",
      mediana:
        "¿Estos tratamientos cuentan con EIPD, con medidas para evaluar sesgos y exactitud del modelo, y con revisión humana efectiva de las decisiones que afectan significativamente a las personas?",
      corporativo:
        "¿Existe un inventario de modelos y reglas automatizadas con dueño, base de licitud, evaluación de sesgo y desempeño, gobierno de cambios y auditoría periódica de las decisiones emitidas?",
    },
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
      "¿El personal que accede a datos personales ha recibido al menos una capacitación sobre sus obligaciones bajo la LOPDP y sobre el manejo adecuado de la información?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe un plan anual de capacitación en protección de datos con contenidos, destinatarios y frecuencia definidos, e inducción para el personal que ingresa?",
      mediana:
        "¿El plan de capacitación diferencia contenidos por rol (atención al titular, tecnología, talento humano, compras) y registra la cobertura alcanzada por cada grupo?",
      corporativo:
        "¿El plan de capacitación es obligatorio y medido, con cobertura reportada por área, contenidos especializados por rol, refuerzos ante cambios normativos y consecuencias definidas por incumplimiento?",
    },
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
      "¿Se refuerzan periódicamente los mensajes clave de protección de datos mediante comunicaciones internas, recordatorios o material de apoyo?",
    enunciadoPorTamano: {
      mediana:
        "¿Existe un calendario de concienciación con campañas temáticas (suplantación de identidad, manejo de documentos, uso de canales autorizados) dirigidas a toda la organización?",
      corporativo:
        "¿El programa de concienciación se planifica anualmente con segmentación por audiencia, indicadores de alcance y participación, y ejercicios prácticos con seguimiento de resultados?",
    },
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
      "¿Se evalúa si la capacitación en protección de datos logró su objetivo, mediante pruebas de conocimiento u otro mecanismo de verificación?",
    enunciadoPorTamano: {
      corporativo:
        "¿La eficacia de la formación se mide con indicadores definidos (resultados de evaluación, tasa de aprobación, reincidencia en errores e incidentes atribuibles al factor humano) y sus resultados retroalimentan el plan de capacitación?",
    },
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
      "¿Existe un programa que defina qué aspectos del cumplimiento en protección de datos serán revisados durante el año, con qué frecuencia y bajo responsabilidad de quién?",
    enunciadoPorTamano: {
      corporativo:
        "¿El programa de auditoría se construye con enfoque basado en riesgos, cubre de forma plurianual todas las dimensiones del SGPDP, es aprobado por la dirección o el comité y garantiza la independencia del auditor respecto del área auditada?",
    },
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
      "¿Las auditorías del SGPDP se ejecutan conforme al programa aprobado, con planes de auditoría, pruebas documentadas sobre muestras reales e informes formales dirigidos a los responsables de cada proceso?",
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
      "¿Los hallazgos de auditorías, revisiones e incidentes se consolidan en un registro único, con clasificación por severidad, causa raíz identificada y responsable asignado?",
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
      "¿El avance de los planes de acción derivados de los hallazgos se monitorea periódicamente, con verificación de eficacia antes del cierre y escalamiento de las acciones vencidas?",
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
      "¿La alta dirección revisa formalmente y al menos una vez al año el desempeño del SGPDP (indicadores, incidentes, hallazgos, cambios normativos y recursos) y adopta decisiones documentadas de mejora?",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 47",
    criticidad: 3,
    evidenciaEsperada:
      "Acta de revisión por la dirección con indicadores presentados, decisiones adoptadas y asignación de recursos",
    tamanoMinimo: "corporativo",
  },
];
