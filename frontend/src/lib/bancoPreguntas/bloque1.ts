/**
 * Bloque 1 del banco de preguntas del assessment SGPDP (controles 1-22).
 *
 * Cubre las dimensiones D01 (Gobierno y responsabilidad proactiva),
 * D02 (Inventario, RAT, finalidades y legitimación) y D03 (Transparencia e
 * información al titular).
 *
 * Doctrina 9 del PRD: la talla declarada en `tamanoMinimo` decide si el control
 * entra al cuestionario; las variantes por talla reformulan la verificación sin
 * rebajar la obligación legal subyacente.
 */

import type { PreguntaAssessment } from "@/lib/bancoPreguntas/tipos";

export const BLOQUE_1: PreguntaAssessment[] = [
  {
    id: 1,
    dimensionId: "D01",
    control: "Política de protección de datos personales",
    enunciado:
      "¿Existe una política interna de protección de datos personales aprobada, comunicada y adaptada a la operación comercial de la empresa?",
    criterioMadurez:
      "La política está aprobada, vigente, asigna roles y contempla clientes, prospectos, colaboradores, proveedores, puntos de venta, canales digitales, CRM, e-commerce si aplica y se revisa periódicamente.",
    referenciaNormativa: "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 47",
    criticidad: 4,
    evidenciaEsperada:
      "Documento de política firmado con fecha de aprobación y constancia de comunicación al personal",
    evidenciaPorTamano: {
      mediana:
        "Política aprobada, acta de directorio o resolución institucional y registro de difusión",
      corporativo:
        "Cuerpo normativo aprobado, control de versiones, actas de aprobación y evidencia de despliegue por unidad de negocio",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 2,
    dimensionId: "D01",
    control: "Roles, responsabilidades y sponsor ejecutivo",
    enunciado:
      "¿Están definidos los responsables internos de protección de datos por área/proceso?",
    criterioMadurez:
      "Existen responsables, sponsor ejecutivo y responsabilidades documentadas para procesos críticos.",
    referenciaNormativa:
      "LOPDP Art. 47 (Deberes del responsable del tratamiento)",
    criticidad: 4,
    evidenciaEsperada:
      "Designación escrita del responsable con descripción de funciones",
    evidenciaPorTamano: {
      mediana:
        "Manual de funciones por área, designación del sponsor y actas de reporte",
      corporativo:
        "Matriz RACI por proceso, acta de designación del sponsor ejecutivo y bitácora de reportes a la Alta Dirección",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 3,
    dimensionId: "D01",
    control: "Evaluación de aplicabilidad y designación del DPD",
    enunciado:
      "¿La empresa ha evaluado y documentado si está obligada a designar Delegado de Protección de Datos y, cuando corresponde, la designación está formalizada?",
    criterioMadurez:
      "Existe análisis documentado de aplicabilidad; si corresponde designación, el DPD está formalmente nombrado, registrado y cuenta con canal de contacto y acceso a dirección.",
    referenciaNormativa:
      "LOPDP Art. 48 y Resolución SPDP-SPD-2026-0005-R",
    criticidad: 4,
    evidenciaEsperada:
      "Informe de evaluación de aplicabilidad con criterios aplicados y conclusión firmada",
    evidenciaPorTamano: {
      mediana:
        "Informe de aplicabilidad, nombramiento del DPD y constancia de notificación a la SPDP",
      corporativo:
        "Informe de aplicabilidad por línea de negocio, contrato o nombramiento del DPD, notificación a la SPDP y canal de contacto publicado",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 4,
    dimensionId: "D01",
    control: "Independencia, recursos y seguimiento del DPD",
    enunciado:
      "¿Cuando existe DPD, la empresa garantiza independencia, acceso a dirección, recursos y evidencia de seguimiento de sus recomendaciones?",
    criterioMadurez:
      "La función mantiene independencia y segregación respecto de decisiones sobre fines y medios del tratamiento; existe acceso a alta dirección y trazabilidad de recomendaciones.",
    referenciaNormativa:
      "LOPDP Art. 48 y Resolución SPDP-SPD-2026-0005-R",
    criticidad: 3,
    evidenciaEsperada:
      "Estatuto o carta de independencia del DPD, presupuesto asignado, declaración de conflictos de interés y bitácora de seguimiento de recomendaciones",
    tamanoMinimo: "corporativo",
  },
  {
    id: 5,
    dimensionId: "D01",
    control: "Mapa de obligaciones y base normativa aplicable",
    enunciado:
      "¿La organización tiene identificadas las obligaciones LOPDP aplicables a su operación?",
    criterioMadurez:
      "Existe un mapa normativo que vincula obligaciones con procesos, controles y evidencias.",
    referenciaNormativa:
      "LOPDP Art. 47 (Deberes del responsable) y Reglamento General a la LOPDP",
    criticidad: 3,
    evidenciaEsperada:
      "Matriz de obligaciones legales con responsable asignado y estado de cumplimiento",
    evidenciaPorTamano: {
      corporativo:
        "Matriz de obligaciones por jurisdicción y línea de negocio, con dueño, estado, fecha de última revisión y reportes de vigilancia normativa",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 6,
    dimensionId: "D01",
    control: "Comité de privacidad y gobierno del SGPDP",
    enunciado:
      "¿Existe asignación de recursos para sostener el sistema de protección de datos?",
    criterioMadurez:
      "Se asignan recursos para capacitación, herramientas, seguridad, consultoría, auditoría y mejoras.",
    referenciaNormativa: "Guía de Gobernanza SPDP 2024",
    criticidad: 2,
    evidenciaEsperada:
      "Actas de reunión del comité y designación de sus integrantes",
    evidenciaPorTamano: {
      corporativo:
        "Estatuto del comité, actas de sesión, matriz de compromisos con responsable y fecha, y reportes de escalamiento a la Alta Dirección",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 7,
    dimensionId: "D01",
    control: "Gestión documental del SGPDP",
    enunciado:
      "¿Los documentos de protección de datos tienen control de versión, dueño y fecha de revisión?",
    criterioMadurez:
      "Documentos controlados, aprobados, versionados y disponibles para responsables internos.",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva) y Guía de Gobernanza SPDP 2024",
    criticidad: 3,
    evidenciaEsperada:
      "Repositorio documental del SGPDP con identificación de versión vigente y responsable de custodia",
    tamanoMinimo: "mediana",
  },
  {
    id: 8,
    dimensionId: "D01",
    control: "Indicadores y reportes a dirección",
    enunciado:
      "¿Se reportan indicadores de protección de datos a la alta dirección?",
    criterioMadurez:
      "Existen KPIs de incidentes, derechos, capacitación, riesgos, proveedores y avance de acciones.",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva) y Guía de Gobernanza SPDP 2024",
    criticidad: 2,
    evidenciaEsperada:
      "Reportes periódicos de indicadores con fecha y destinatario",
    evidenciaPorTamano: {
      corporativo:
        "Tablero de indicadores con metas y umbrales, actas de presentación a la Alta Dirección y evidencia de decisiones adoptadas",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 9,
    dimensionId: "D02",
    control: "Inventario de tratamientos",
    enunciado:
      "¿Existe un inventario actualizado de tratamientos de datos personales por proceso comercial y corporativo?",
    criterioMadurez:
      "El inventario identifica captación y registro de clientes, ventas/POS, facturación, e-commerce si aplica, pagos, marketing/CRM, servicio al cliente, logística, RR. HH., proveedores y seguridad.",
    referenciaNormativa:
      "LOPDP Art. 35 y Guía de Inventario de Tratamientos SPDP",
    criticidad: 5,
    evidenciaEsperada:
      "Listado de tratamientos con datos recogidos, finalidad, ubicación y responsable",
    evidenciaPorTamano: {
      mediana:
        "Inventario por proceso con dueño, sistemas asociados, categorías de titulares y constancia de validación por área",
      corporativo:
        "Inventario consolidado por línea de negocio conciliado con el inventario de activos, con dueños, flujos a terceros y evidencia de validación periódica",
    },
    tamanoMinimo: "micro",
    esEstructural: true,
  },
  {
    id: 10,
    dimensionId: "D02",
    control: "Registro de Actividades de Tratamiento (RAT)",
    enunciado:
      "¿Existe un RAT actualizado y alineado con los procesos reales de la empresa?",
    criterioMadurez:
      "El RAT contiene actividades, finalidades, categorías de titulares, datos, destinatarios, conservación, medidas de seguridad, encargados y transferencias cuando correspondan.",
    referenciaNormativa: "LOPDP Art. 35 y Directiva SPDP-2025-0012",
    criticidad: 5,
    evidenciaEsperada:
      "RAT con finalidad, categorías de datos, destinatarios y plazos por actividad",
    evidenciaPorTamano: {
      mediana:
        "RAT completo por área con constancia de validación por los dueños de proceso y registro de última actualización",
      corporativo:
        "RAT centralizado con control de versiones, validación formal por dueño de proceso y reporte exportable en el formato requerido por la SPDP",
    },
    tamanoMinimo: "micro",
    esEstructural: true,
  },
  {
    id: 11,
    dimensionId: "D02",
    control: "Finalidades declaradas por tratamiento",
    enunciado:
      "¿Cada tratamiento tiene finalidades claras, específicas y documentadas?",
    criterioMadurez:
      "Las finalidades son explícitas, legítimas, no genéricas y se reflejan en avisos y procesos.",
    referenciaNormativa: "LOPDP Art. 10 (Principio de finalidad)",
    criticidad: 4,
    evidenciaEsperada:
      "Finalidad declarada por tratamiento en el RAT y coincidencia con lo informado al titular",
    evidenciaPorTamano: {
      corporativo:
        "Catálogo de finalidades gobernado centralmente y expedientes de análisis de compatibilidad de usos secundarios con su aprobación",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 12,
    dimensionId: "D02",
    control: "Bases de legitimación documentadas",
    enunciado:
      "¿Cada tratamiento tiene identificada y justificada su base de legitimación?",
    criterioMadurez:
      "La base se asigna por tratamiento, con racionales y criterios de aplicabilidad.",
    referenciaNormativa: "LOPDP Art. 7 (Bases de legitimación) y Art. 8",
    criticidad: 4,
    evidenciaEsperada:
      "Base de legitimación registrada por tratamiento con su respaldo documental",
    evidenciaPorTamano: {
      mediana:
        "Registro de bases por tratamiento con validación legal y expedientes de sustento de las bases distintas al consentimiento",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 13,
    dimensionId: "D02",
    control: "Datos sensibles y de mayor riesgo",
    enunciado:
      "¿La empresa identifica datos sensibles y otros datos de mayor riesgo o impacto, y aplica controles reforzados cuando corresponde?",
    criterioMadurez:
      "Se identifican, según aplique, datos sensibles, biometría, datos de niñas/niños, geolocalización, datos de pago, perfiles de consumo u otra información de alto impacto, con controles proporcionales.",
    referenciaNormativa: "LOPDP Art. 25 y Art. 26",
    criticidad: 5,
    evidenciaEsperada:
      "Identificación de los datos sensibles tratados y listado del personal autorizado a acceder",
    evidenciaPorTamano: {
      mediana:
        "Matriz de clasificación de datos sensibles por tratamiento, controles reforzados asociados y revisión periódica de privilegios",
      corporativo:
        "Política de clasificación corporativa, matriz de controles reforzados por categoría, evidencia de cifrado y registros de monitoreo de accesos",
    },
    tamanoMinimo: "micro",
    esEstructural: true,
  },
  {
    id: 14,
    dimensionId: "D02",
    control: "Plazos de conservación",
    enunciado:
      "¿Existen plazos de conservación documentados por tipo de dato y proceso?",
    criterioMadurez:
      "Los plazos están definidos, justificados y conectados con archivo, eliminación y respaldo.",
    referenciaNormativa: "LOPDP Art. 10 (Principio de conservación)",
    criticidad: 4,
    evidenciaEsperada:
      "Definición escrita de plazos de conservación por tipo de dato y del destino al vencer el plazo",
    evidenciaPorTamano: {
      mediana:
        "Política de conservación y supresión con tabla por tratamiento y actas o registros de depuración",
      corporativo:
        "Reglas de retención configuradas en los sistemas, reportes de ejecución de supresión o anonimización y cobertura declarada de respaldos",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 15,
    dimensionId: "D02",
    control: "Minimización y calidad del dato",
    enunciado:
      "¿Los formularios y procesos recolectan solo los datos necesarios para la finalidad?",
    criterioMadurez:
      "La recolección se revisa periódicamente para reducir campos innecesarios.",
    referenciaNormativa:
      "LOPDP Art. 10 (Principios de pertinencia y minimización, y de calidad y exactitud)",
    criticidad: 3,
    evidenciaEsperada:
      "Revisión de campos de formularios y sistemas con justificación de cada dato solicitado",
    tamanoMinimo: "pequena",
  },
  {
    id: 16,
    dimensionId: "D02",
    control: "Actualización del RAT por cambios",
    enunciado:
      "¿Existe procedimiento para actualizar el RAT cuando cambian procesos, sistemas o proveedores?",
    criterioMadurez:
      "Todo cambio relevante dispara revisión de inventario, RAT, riesgos, avisos y proveedores.",
    referenciaNormativa: "LOPDP Art. 35 inciso final",
    criticidad: 3,
    evidenciaEsperada:
      "Bitácora de cambios del RAT con fecha, motivo y responsable de cada actualización",
    evidenciaPorTamano: {
      corporativo:
        "Control de versiones del RAT y evidencia de su vinculación con los flujos de gestión de cambios y de incorporación de proveedores",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 17,
    dimensionId: "D03",
    control: "Aviso de privacidad vigente",
    enunciado:
      "¿La empresa informa a clientes, prospectos y otros titulares sobre el tratamiento de sus datos personales?",
    criterioMadurez:
      "Los avisos son claros y accesibles en formularios, tiendas/puntos de venta, web, e-commerce/app si aplica, WhatsApp, CRM, programas de fidelización, entregas y reclamos.",
    referenciaNormativa:
      "LOPDP, régimen de información al titular; Guía de Avisos de Privacidad SPDP",
    criticidad: 4,
    evidenciaEsperada:
      "Aviso de privacidad vigente con fecha y contenido mínimo informado al titular",
    evidenciaPorTamano: {
      mediana:
        "Catálogo de avisos por tipo de titular y punto de recolección, con versión vigente y constancia de revisión",
      corporativo:
        "Repositorio de avisos con control de versiones, aprobación legal y trazabilidad de la versión desplegada por canal y fecha",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 18,
    dimensionId: "D03",
    control: "Información en canales digitales",
    enunciado:
      "¿Los canales de recolección informan al titular antes o durante la captura de datos?",
    criterioMadurez:
      "Formularios, WhatsApp, web, presencial, teléfono y CRM incluyen información mínima y enlaces.",
    referenciaNormativa:
      "LOPDP Art. 10 (Principio de transparencia) y Guía de Transparencia SPDP",
    criticidad: 3,
    evidenciaEsperada:
      "Captura o enlace del aviso de privacidad publicado en los canales digitales activos",
    evidenciaPorTamano: {
      corporativo:
        "Inventario de puntos de captura digital con el aviso asociado, configuración del gestor de consentimiento de cookies y reportes de verificación periódica",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 19,
    dimensionId: "D03",
    control: "Información en puntos de atención",
    enunciado:
      "¿La información al titular se presenta en lenguaje claro y comprensible?",
    criterioMadurez:
      "El aviso evita tecnicismos y permite comprensión por parte del titular promedio.",
    referenciaNormativa: "LOPDP, régimen de información al titular",
    criticidad: 2,
    evidenciaEsperada:
      "Aviso impreso, señalética o guion de atención que evidencie la información entregada al titular",
    tamanoMinimo: "pequena",
  },
  {
    id: 20,
    dimensionId: "D03",
    control: "Lenguaje claro y accesible",
    enunciado:
      "¿Los consentimientos se solicitan de forma específica, separada y verificable cuando corresponde?",
    criterioMadurez:
      "El consentimiento es libre, específico, informado, verificable y revocable.",
    referenciaNormativa:
      "LOPDP Art. 10 (Principios de transparencia y lealtad)",
    criticidad: 2,
    evidenciaEsperada:
      "Texto del aviso de privacidad redactado en lenguaje claro, verificable por lectura directa",
    tamanoMinimo: "micro",
  },
  {
    id: 21,
    dimensionId: "D03",
    control: "Gestión del consentimiento cuando aplica",
    enunciado:
      "¿La página web, landing pages y formularios digitales contienen información de privacidad adecuada?",
    criterioMadurez:
      "La web incluye aviso, cookies si aplica, bases, finalidades y mecanismo de derechos.",
    referenciaNormativa: "LOPDP Art. 7 y Art. 8",
    criticidad: 4,
    evidenciaEsperada:
      "Formulario o registro de consentimiento con fecha, finalidad y texto informado al titular",
    evidenciaPorTamano: {
      mediana:
        "Procedimiento de consentimiento y registros por finalidad con trazabilidad de la versión del aviso aplicada",
      corporativo:
        "Plataforma de gestión de consentimiento con logs de opt-in por finalidad, canal, fecha y versión del texto, exportables para auditoría",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 22,
    dimensionId: "D03",
    control: "Revocatoria del consentimiento",
    enunciado:
      "¿Los canales como WhatsApp o mensajería incluyen aviso corto y límites de uso de datos?",
    criterioMadurez:
      "Se usa guion/plantilla, se minimizan datos y se evita envío innecesario de información sensible.",
    referenciaNormativa:
      "LOPDP Art. 7 y Art. 8 (Revocatoria del consentimiento)",
    criticidad: 4,
    evidenciaEsperada:
      "Canal de revocatoria informado al titular y registro de las revocatorias atendidas",
    evidenciaPorTamano: {
      corporativo:
        "Flujo automatizado de propagación de la revocatoria, logs de cese de tratamiento por sistema y controles de supresión en listas de comunicación",
    },
    tamanoMinimo: "micro",
  },
];
