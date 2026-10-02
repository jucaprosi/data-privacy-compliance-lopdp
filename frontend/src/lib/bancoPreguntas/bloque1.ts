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
      "¿La organización tiene una política de protección de datos personales por escrito, aprobada por quien la dirige y comunicada al personal?",
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
      "¿Hay una persona designada como responsable de la protección de datos personales, aunque lo haga junto con otras tareas?",
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
      "¿La organización revisó si la ley le obliga a nombrar un Delegado de Protección de Datos (la persona que vigila que se cumpla la ley) y dejó por escrito qué decidió?",
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
      "Si la organización tiene un Delegado de Protección de Datos, ¿puede hacer su trabajo con libertad, comunicarse directamente con quien dirige la organización y se da seguimiento a sus recomendaciones?",
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
      "¿La organización tiene identificadas las obligaciones que le exige la ley de protección de datos personales y la persona o área responsable de cumplir cada una?",
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
      "¿Existe un comité u otra instancia formal de la organización (por ejemplo, de privacidad o de seguridad de la información) que se reúna periódicamente para revisar el cumplimiento de la protección de datos personales y decidir las acciones necesarias?",
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
      "¿Los documentos de protección de datos (políticas, procedimientos, formatos) están centralizados, con la versión vigente identificada?",
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
      "¿La organización mide indicadores de cumplimiento en protección de datos (por ejemplo, el número de solicitudes de las personas o de incidentes de seguridad) y los reporta periódicamente a la dirección?",
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
      "¿La organización tiene un inventario de las actividades en las que trata datos personales (por ejemplo, registro de clientes o socios, pago de sueldos, cámaras de seguridad), con los datos que se usan en cada una?",
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
      "¿La organización tiene un registro por escrito (llamado RAT) donde anota, por cada actividad, para qué usa los datos, cuáles son, quién los recibe y por cuánto tiempo los guarda?",
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
      "¿Cada actividad tiene definida por escrito su finalidad (para qué se usan los datos) y los datos se usan solo para esa finalidad?",
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
      "¿Para cada actividad se identificó y documentó la base legal que permite usar los datos (consentimiento, contrato, obligación legal u otra prevista en la ley)?",
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
      "¿La organización tiene identificados los datos sensibles que maneja (salud, huellas digitales, religión, origen étnico, datos de niñas, niños y adolescentes u otros) y las personas que tienen acceso a ellos?",
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
      "¿La organización definió los plazos de conservación de cada tipo de datos personales y qué hace con ellos al vencer el plazo (eliminarlos o destruirlos)?",
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
      "¿Los formularios y sistemas piden solo los datos que realmente se necesitan, y la organización corrige los datos que cambian o están mal?",
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
      "¿Se actualiza el Registro de Actividades de Tratamiento (RAT) cuando empieza una actividad, sistema o proveedor nuevo, y se revisa al menos una vez al año?",
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
      "¿La organización tiene un aviso de privacidad actualizado que informa a las personas quién usa sus datos, para qué y cómo pueden pedir su corrección o eliminación?",
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
      "Si la organización tiene página web, redes sociales, aplicación o formularios en línea, ¿ahí se muestra el aviso de privacidad antes de que la persona deje sus datos?",
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
      "Cuando la organización pide datos en persona o por teléfono, ¿se le avisa a la persona para qué se usarán?",
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
      "¿Los avisos de privacidad están escritos con palabras sencillas que cualquier persona entienda?",
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
      "Cuando la organización usa datos con permiso de la persona, ¿le pide ese permiso de forma clara y voluntaria, y guarda constancia de que lo dio?",
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
      "¿La persona puede retirar su permiso de forma tan fácil como lo dio, y la organización deja de usar sus datos para eso cuando lo retira?",
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
