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
      "¿Cuenta la organización con una política escrita de protección de datos personales, aprobada por el propietario o la gerencia y comunicada al personal?",
    enunciadoPorTamano: {
      pequena:
        "¿Cuenta la organización con una política de protección de datos personales formalmente aprobada, difundida al personal y con responsable de su mantenimiento?",
      mediana:
        "¿La política general de protección de datos personales está aprobada por la Alta Dirección, con alcance declarado, vigencia y revisión periódica documentada?",
      corporativo:
        "¿Existe un cuerpo normativo interno de protección de datos (política general y políticas específicas por proceso) aprobado por la Alta Dirección, con control de versiones, vigencia y difusión verificable en todas las filiales y unidades?",
    },
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
      "¿Existe una persona designada como responsable de la protección de datos personales, aunque ejerza la función a tiempo parcial junto con otras tareas?",
    enunciadoPorTamano: {
      pequena:
        "¿Están asignadas por escrito las responsabilidades de protección de datos y se conoce a quién escalar las decisiones que exceden esa función?",
      mediana:
        "¿Están formalmente asignadas las responsabilidades de protección de datos por área, con un sponsor ejecutivo identificado?",
      corporativo:
        "¿Existe una matriz RACI de responsabilidades de protección de datos por proceso, con sponsor ejecutivo y reporte periódico a la Alta Dirección?",
    },
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
      "¿Se ha evaluado y documentado si la organización está obligada a designar un Delegado de Protección de Datos, y se actuó conforme al resultado de esa evaluación?",
    enunciadoPorTamano: {
      mediana:
        "¿La evaluación de aplicabilidad del DPD está documentada con los criterios de gran escala y datos sensibles, y el Delegado se encuentra designado y notificado a la SPDP cuando corresponde?",
      corporativo:
        "¿Se mantiene la evaluación de aplicabilidad del DPD actualizada por línea de negocio, con designación formal, notificación a la SPDP y publicación de su canal de contacto?",
    },
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
      "¿El Delegado de Protección de Datos cuenta con independencia funcional, presupuesto y acceso directo a la Alta Dirección, con control documentado de conflictos de interés y seguimiento de sus recomendaciones?",
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
      "¿Se mantiene un mapa de obligaciones legales de protección de datos aplicables a la organización, con el área responsable de cada una y su estado de cumplimiento?",
    enunciadoPorTamano: {
      corporativo:
        "¿El mapa de obligaciones de protección de datos se mantiene actualizado por jurisdicción y línea de negocio, con dueño por obligación, estado de cumplimiento y vigilancia normativa formalizada?",
    },
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
      "¿Existe un comité o instancia formal de privacidad que sesione periódicamente y decida sobre el estado del sistema de gestión de protección de datos?",
    enunciadoPorTamano: {
      corporativo:
        "¿El comité de privacidad opera con estatuto aprobado, composición multidisciplinaria, periodicidad definida y decisiones con seguimiento hasta su cierre, escalando a la Alta Dirección?",
    },
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
      "¿La documentación del sistema de gestión de protección de datos (políticas, procedimientos y registros) está centralizada, con versión vigente identificable y control de accesos?",
    enunciadoPorTamano: {
      corporativo:
        "¿La documentación del SGPDP se administra bajo control formal de versiones, aprobación, distribución, retención y baja documental, con trazabilidad de quién accede y modifica cada documento?",
    },
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
      "¿Se miden indicadores de cumplimiento en protección de datos (solicitudes de titulares, incidentes, avance de planes) y se reportan periódicamente a la gerencia?",
    enunciadoPorTamano: {
      corporativo:
        "¿Existe un tablero de indicadores de protección de datos con metas, umbrales de alerta y periodicidad definida, reportado formalmente a la Alta Dirección y al órgano de gobierno?",
    },
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
      "¿Existe un listado de todos los tratamientos de datos personales que realiza la organización, identificando qué datos se recogen, dónde se guardan y quién los usa?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe un inventario de tratamientos de datos personales por proceso, con los sistemas y repositorios donde residen los datos y el área responsable de cada uno?",
      mediana:
        "¿El inventario de tratamientos cubre todas las áreas y sistemas, identifica dueño por proceso, categorías de titulares y flujos hacia terceros, y se valida con los responsables?",
      corporativo:
        "¿El inventario de tratamientos se mantiene consolidado por línea de negocio y filial, conciliado con el inventario de activos y sistemas, con dueño por proceso y validación periódica documentada?",
    },
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
      "¿Mantiene la organización un Registro de Actividades de Tratamiento (RAT) que describa, para cada actividad, la finalidad, las categorías de datos, los destinatarios y el plazo de conservación?",
    enunciadoPorTamano: {
      pequena:
        "¿El RAT está construido sobre los procesos reales de la organización conforme al estándar SPDP, con responsable de su mantenimiento y fecha de última actualización?",
      mediana:
        "¿El RAT cubre la totalidad de las actividades de tratamiento por área, se valida con los dueños de proceso y refleja encargados, transferencias y medidas de seguridad asociadas?",
      corporativo:
        "¿El RAT se administra en una herramienta única para todas las unidades y filiales, con validación formal por dueño de proceso, control de versiones y capacidad de exportación ante requerimiento de la SPDP?",
    },
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
      "¿Cada tratamiento tiene declarada una finalidad concreta y explícita, y los datos se usan únicamente para esa finalidad?",
    enunciadoPorTamano: {
      mediana:
        "¿Las finalidades están declaradas por tratamiento, son específicas y legítimas, y existe control documentado para impedir usos incompatibles con la finalidad original?",
      corporativo:
        "¿Las finalidades declaradas se gobiernan de forma centralizada, con análisis de compatibilidad documentado para todo uso secundario (analítica, modelos, cesiones internas) y aprobación previa registrada?",
    },
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
      "¿Para cada tratamiento se identificó y dejó por escrito la base que lo legitima (consentimiento, contrato, obligación legal u otra prevista en la ley)?",
    enunciadoPorTamano: {
      pequena:
        "¿El RAT consigna la base de legitimación de cada tratamiento y se puede sustentar documentalmente la base invocada?",
      mediana:
        "¿Las bases de legitimación están documentadas por tratamiento, revisadas por la función legal, y se sustentan con el respaldo correspondiente cuando se invoca interés legítimo u obligación legal?",
      corporativo:
        "¿Existe un procedimiento formal de determinación y revisión de bases de legitimación, con validación legal por tratamiento, expedientes de sustento y control de cambios ante nuevos usos?",
    },
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
      "¿Se identificó qué datos sensibles trata la organización (salud, biométricos, origen étnico, afiliación u otros) y quién puede acceder a ellos?",
    enunciadoPorTamano: {
      pequena:
        "¿Los datos sensibles y de mayor riesgo están identificados por tratamiento, con acceso restringido al personal estrictamente necesario y medidas de resguardo definidas?",
      mediana:
        "¿Existe una clasificación formal de datos sensibles y de mayor riesgo por tratamiento, con controles reforzados definidos, acceso por rol y revisión periódica de privilegios?",
      corporativo:
        "¿La clasificación de datos sensibles y de mayor riesgo está integrada al gobierno del dato corporativo, con controles reforzados por categoría, segregación de accesos, cifrado y monitoreo de uso?",
    },
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
      "¿Se definió por cuánto tiempo se conservan los datos personales de cada tratamiento y qué se hace con ellos cuando ese plazo vence?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe una tabla de plazos de conservación por tratamiento, con el criterio legal o contractual que la sustenta y el destino final del dato?",
      mediana:
        "¿La política de conservación y supresión está formalizada por tratamiento, con criterio de sustento, responsable de ejecución y evidencia de depuraciones efectuadas?",
      corporativo:
        "¿Los plazos de conservación se aplican de forma sistematizada en los repositorios (incluidos respaldos y ambientes no productivos), con supresión o anonimización verificable y trazabilidad de su ejecución?",
    },
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
      "¿Se verifica que los formularios y sistemas soliciten únicamente los datos necesarios para la finalidad declarada y que exista un mecanismo para mantenerlos exactos y actualizados?",
    enunciadoPorTamano: {
      mediana:
        "¿Existe una revisión formal de campos por formulario y sistema para eliminar datos innecesarios, junto con controles de exactitud y actualización de los datos de titulares?",
      corporativo:
        "¿La minimización se aplica como control de diseño en todo cambio de sistema o formulario, con revisión documentada de campos y métricas de calidad del dato (exactitud, completitud, duplicidad)?",
    },
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
      "¿Se actualiza el RAT cuando se incorpora un nuevo tratamiento, sistema o proveedor, y al menos una vez al año?",
    enunciadoPorTamano: {
      mediana:
        "¿Existe un procedimiento que obliga a actualizar el RAT ante modificaciones sustanciales de procesos, sistemas o encargados, con responsable, plazo y revisión anual documentada?",
      corporativo:
        "¿La actualización del RAT está integrada a los procesos de gestión de cambios y de alta de proveedores, de modo que ningún tratamiento nuevo entre en producción sin quedar registrado?",
    },
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
      "¿Dispone la organización de un aviso de privacidad vigente que informe al titular quién trata sus datos, con qué finalidad y cómo ejercer sus derechos?",
    enunciadoPorTamano: {
      pequena:
        "¿El aviso de privacidad se encuentra vigente, es coherente con los tratamientos registrados e identifica finalidades, base de legitimación, destinatarios y canal de ejercicio de derechos?",
      mediana:
        "¿Existen avisos de privacidad diferenciados por tipo de titular y punto de recolección, con versión vigente identificada y revisión periódica documentada?",
      corporativo:
        "¿Los avisos de privacidad se gobiernan de forma centralizada por punto de recolección y jurisdicción, con control de versiones, aprobación legal y registro histórico de la versión mostrada a cada titular?",
    },
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
      "¿Los canales digitales de la organización (sitio web, aplicaciones, formularios y redes) muestran el aviso de privacidad de forma accesible antes de recolectar datos personales?",
    enunciadoPorTamano: {
      mediana:
        "¿Cada formulario y punto de captura digital enlaza el aviso de privacidad aplicable, y la información sobre cookies y tecnologías de seguimiento se presenta antes de su activación?",
      corporativo:
        "¿Se mantiene un inventario de puntos de captura digital con el aviso vinculado a cada uno, gestión de preferencias de cookies y verificación periódica de que ningún canal recolecte datos sin informar?",
    },
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
      "¿En los puntos de atención presencial y canales telefónicos se informa al titular sobre el tratamiento de sus datos antes de recolectarlos?",
    enunciadoPorTamano: {
      corporativo:
        "¿Existe un estándar corporativo de información al titular en atención presencial y telefónica (señalética, guiones y avisos impresos), con verificación periódica de su aplicación en cada punto?",
    },
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
      "¿La información de privacidad está redactada en lenguaje sencillo y comprensible para el titular, sin tecnicismos innecesarios?",
    enunciadoPorTamano: {
      mediana:
        "¿Los textos de privacidad se someten a una revisión de comprensibilidad, con estructura por capas que permita al titular acceder primero a la información esencial?",
      corporativo:
        "¿Existe un estándar de lenguaje claro y accesibilidad para los textos de privacidad (información por capas, formatos accesibles y versiones para públicos específicos), con validación documentada antes de su publicación?",
    },
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
      "¿Cuando el tratamiento se sustenta en el consentimiento, este se obtiene de forma libre, específica e informada, mediante una acción afirmativa del titular, y queda registrado?",
    enunciadoPorTamano: {
      pequena:
        "¿Se conserva el registro del consentimiento obtenido, indicando qué se informó al titular, en qué fecha y para qué finalidad, de modo que pueda acreditarse ante un requerimiento?",
      mediana:
        "¿Existe un procedimiento de obtención y conservación del consentimiento por finalidad, con casillas no premarcadas, separación de finalidades y trazabilidad de la versión del aviso mostrada?",
      corporativo:
        "¿La gestión del consentimiento se administra en una plataforma con trazabilidad extremo a extremo (finalidad, canal, fecha, versión del texto y evidencia de la acción afirmativa), auditable por tratamiento?",
    },
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
      "¿Puede el titular revocar su consentimiento por un medio tan sencillo como el que utilizó para otorgarlo, y la organización deja de tratar sus datos cuando lo hace?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe un canal identificado para revocar el consentimiento, con registro de las revocatorias recibidas y constancia de que el tratamiento cesó?",
      mediana:
        "¿El procedimiento de revocatoria define plazo de atención, responsable y propagación de la baja a todos los sistemas y encargados que tratan esos datos?",
      corporativo:
        "¿La revocatoria se propaga de forma automatizada a los sistemas, listas de contacto y encargados, con evidencia de cese del tratamiento y control de reingreso del titular a campañas o comunicaciones?",
    },
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
