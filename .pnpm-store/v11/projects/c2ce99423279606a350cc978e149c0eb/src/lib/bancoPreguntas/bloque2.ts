/**
 * Bloque 2 del banco de preguntas del assessment SGPDP (controles 23 a 48).
 *
 * Cubre tres dimensiones consecutivas de la matriz de madurez:
 *   D04 - Derechos de titulares (23-32)
 *   D05 - Procesos críticos y ciclo de vida de datos (33-40)
 *   D06 - Encargados, proveedores y transferencias (41-48)
 *
 * Cada control declara la talla mínima desde la que es exigible (Doctrina 9 del
 * PRD) y, cuando aplica a varias tallas, reformula enunciado y evidencia según
 * la estructura esperable en cada una. La obligación legal no se rebaja: cambia
 * la forma en que se verifica.
 */

import type { PreguntaAssessment } from "@/lib/bancoPreguntas/tipos";

export const BLOQUE_2: PreguntaAssessment[] = [
  // ───────────────────────── D04 · Derechos de titulares ─────────────────────
  {
    id: 23,
    dimensionId: "D04",
    control: "Procedimiento de atención de derechos",
    enunciado:
      "¿Existen avisos específicos para empleados, candidatos y prestadores de servicios?",
    criterioMadurez:
      "La gestión de talento humano informa finalidades, bases, conservación, transferencias y derechos.",
    referenciaNormativa: "LOPDP Art. 22 al 24 y Art. 30 (trámite de solicitudes del titular)",
    criticidad: 5,
    evidenciaEsperada:
      "Procedimiento escrito de atención de derechos con responsable designado",
    evidenciaPorTamano: {
      mediana:
        "Procedimiento aprobado, matriz RACI por tipo de derecho y constancia de difusión interna",
      corporativo:
        "Procedimiento versionado, flujo en sistema de gestión, acuerdos de nivel de servicio y tablero de indicadores de atención",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 24,
    dimensionId: "D04",
    control: "Canales de recepción de solicitudes",
    enunciado:
      "¿La videovigilancia o controles de acceso físico cuentan con información visible al titular?",
    criterioMadurez:
      "Existen carteles, aviso complementario, finalidad, responsable y conservación de imágenes.",
    referenciaNormativa: "LOPDP Art. 30 (canales de atención) y Art. 47",
    criticidad: 4,
    evidenciaEsperada:
      "Captura del canal publicado (aviso de privacidad, sitio web o cartelera) y buzón activo",
    evidenciaPorTamano: {
      corporativo:
        "Inventario de canales habilitados, configuración de enrutamiento y reportes de recepción consolidada",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 25,
    dimensionId: "D04",
    control: "Registro y trazabilidad de solicitudes",
    enunciado:
      "¿Existe un procedimiento formal para atender derechos de clientes, prospectos, colaboradores, proveedores y demás titulares?",
    criterioMadurez:
      "El procedimiento define canales, responsables, verificación de identidad, registro, análisis, respuesta, escalamiento y evidencias.",
    referenciaNormativa: "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 30",
    criticidad: 4,
    evidenciaEsperada:
      "Registro o bitácora de solicitudes con fechas de ingreso y cierre",
    evidenciaPorTamano: {
      pequena:
        "Registro de solicitudes con expediente por caso y constancia de notificación al titular",
      corporativo:
        "Sistema de tickets con bitácora de auditoría, expedientes digitales y reportes de indicadores de atención",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 26,
    dimensionId: "D04",
    control: "Cumplimiento de plazos normativos",
    enunciado:
      "¿El titular conoce dónde y cómo presentar solicitudes de derechos?",
    criterioMadurez:
      "El canal está publicado en avisos, web, formularios o puntos de atención.",
    referenciaNormativa: "LOPDP Art. 31 (Plazo de atención)",
    criticidad: 5,
    evidenciaEsperada:
      "Registro de fechas de recepción y respuesta que acredite el cumplimiento del plazo",
    evidenciaPorTamano: {
      mediana:
        "Reporte de tiempos de atención por solicitud y constancias de prórroga notificada",
      corporativo:
        "Indicadores de cumplimiento de acuerdos de nivel de servicio, alertas de vencimiento y análisis de desviaciones",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 27,
    dimensionId: "D04",
    control: "Respuesta motivada al titular",
    enunciado:
      "¿Se lleva un registro de solicitudes de derechos y su estado?",
    criterioMadurez:
      "El registro permite trazabilidad de fecha, identidad, derecho, responsable, respuesta y cierre.",
    referenciaNormativa:
      "LOPDP Art. 31 y LOPDP, Capítulo de Derechos del Titular (respuesta motivada)",
    criticidad: 4,
    evidenciaEsperada:
      "Copias de respuestas emitidas al titular con el fundamento de lo resuelto",
    evidenciaPorTamano: {
      corporativo:
        "Plantillas controladas por derecho, expediente de respuestas emitidas y constancia de revisión jurídica de negativas",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 28,
    dimensionId: "D04",
    control: "Verificación de identidad",
    enunciado:
      "¿Existe un mecanismo proporcional para verificar identidad antes de entregar información?",
    criterioMadurez:
      "Se valida identidad y representación con medidas proporcionales al riesgo, especialmente antes de entregar datos sensibles, historial de cuenta, pedidos, pagos u otra información confidencial.",
    referenciaNormativa:
      "LOPDP, Capítulo de Derechos del Titular y Art. 10 (Responsabilidad Proactiva)",
    criticidad: 5,
    evidenciaEsperada:
      "Instrucción escrita de verificación de identidad y constancia del documento exigido en casos atendidos",
    evidenciaPorTamano: {
      mediana:
        "Criterios documentados de verificación por tipo de solicitud y expedientes con la validación aplicada",
      corporativo:
        "Matriz de niveles de aseguramiento por canal, bitácora auditable de validaciones y controles de representación legal",
    },
    tamanoMinimo: "micro",
    esEstructural: true,
  },
  {
    id: 29,
    dimensionId: "D04",
    control: "Gestión de representación y terceros",
    enunciado:
      "¿Existen modelos de respuesta y criterios para aceptación, rechazo o limitación?",
    criterioMadurez:
      "Hay plantillas y criterios documentados para responder de forma consistente.",
    referenciaNormativa:
      "LOPDP Art. 21 (representación legal) y LOPDP, Capítulo de Derechos del Titular",
    criticidad: 3,
    evidenciaEsperada:
      "Documentación habilitante archivada (poder, partida o designación) en los casos atendidos por terceros",
    evidenciaPorTamano: {
      corporativo:
        "Matriz de supuestos de representación, constancia de validación jurídica y repositorio de documentación habilitante",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 30,
    dimensionId: "D04",
    control: "Escalamiento de reclamos a la autoridad",
    enunciado:
      "¿Las solicitudes complejas se escalan a responsables adecuados?",
    criterioMadurez:
      "Existe escalamiento a DPO, legal, TI o área dueña del dato según complejidad.",
    referenciaNormativa:
      "LOPDP, Título de Procedimiento de Protección de Derechos ante la SPDP",
    criticidad: 3,
    evidenciaEsperada:
      "Texto informativo sobre la vía de reclamo ante la SPDP y expediente de los casos escalados",
    tamanoMinimo: "pequena",
  },
  {
    id: 31,
    dimensionId: "D04",
    control: "Portabilidad de datos",
    enunciado:
      "¿El personal de atención conoce cómo identificar y canalizar una solicitud de derechos?",
    criterioMadurez:
      "El personal reconoce solicitudes aunque no usen términos jurídicos.",
    referenciaNormativa:
      "LOPDP, Capítulo de Derechos del Titular (derecho a la portabilidad)",
    criticidad: 3,
    evidenciaEsperada:
      "Ejemplo de archivo exportable entregado al titular en formato estructurado",
    evidenciaPorTamano: {
      corporativo:
        "Especificación de formatos de exportación por sistema, procedimiento de entrega cifrada y casos atendidos",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 32,
    dimensionId: "D04",
    control: "Prueba o simulación de atención de derechos",
    enunciado:
      "¿Se han realizado pruebas o simulaciones para validar el procedimiento de derechos?",
    criterioMadurez:
      "Se realizan ejercicios, se documentan tiempos, fallas y mejoras.",
    referenciaNormativa: "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 47",
    criticidad: 2,
    evidenciaEsperada:
      "Informe de la prueba o simulacro con hallazgos, brechas detectadas y plan de corrección",
    tamanoMinimo: "corporativo",
  },

  // ─────────── D05 · Procesos críticos y ciclo de vida de datos ──────────────
  {
    id: 33,
    dimensionId: "D05",
    control: "Alta y vinculación de titulares",
    enunciado:
      "¿La captación de prospectos, registro de clientes, creación de cuentas y actualización de datos controla qué información se recolecta, para qué y quién accede?",
    criterioMadurez:
      "Se definen datos mínimos, finalidades, base de legitimación, origen, accesos, actualización y conservación para prospectos y clientes; se eliminan campos innecesarios.",
    referenciaNormativa:
      "LOPDP Art. 7, Art. 8 y LOPDP, Capítulo de Transparencia e Información al Titular",
    criticidad: 4,
    evidenciaEsperada:
      "Formularios de alta vigentes con la leyenda informativa incorporada",
    evidenciaPorTamano: {
      mediana:
        "Inventario de formularios y canales de alta con su base de legitimación declarada",
      corporativo:
        "Registro trazable de aceptación con versión del aviso, evidencia de controles de minimización y acta de revisión de campos",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 34,
    dimensionId: "D05",
    control: "Actualización de datos maestros",
    enunciado:
      "¿La venta en tienda o punto de venta y la facturación recolectan solo los datos necesarios y protegen su confidencialidad?",
    criterioMadurez:
      "POS, cajas y facturación delimitan datos requeridos, acceso por rol, visualización/impresión, exportaciones y conservación; se evita exponer datos innecesarios en comprobantes.",
    referenciaNormativa:
      "LOPDP, Capítulo de Derechos del Titular (rectificación y actualización) y principio de exactitud",
    criticidad: 3,
    evidenciaEsperada:
      "Procedimiento de actualización de datos y muestra de correcciones aplicadas",
    evidenciaPorTamano: {
      corporativo:
        "Modelo de gobierno de datos maestros, indicadores de calidad y bitácora de propagación de cambios",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 35,
    dimensionId: "D05",
    control: "Tratamiento en canales digitales",
    enunciado:
      "¿El sitio o plataforma de e-commerce gestiona de forma transparente y segura el registro, checkout, pedidos, historial y cuenta del cliente?",
    criterioMadurez:
      "Se minimizan campos de registro/checkout, se informa la finalidad, se controlan cuentas y sesiones, se protegen pedidos e historial y se revisan integraciones y cookies cuando correspondan.",
    referenciaNormativa: "LOPDP Art. 7 y Art. 8 (consentimiento en entornos digitales)",
    criticidad: 4,
    evidenciaEsperada:
      "Captura del aviso y del mecanismo de consentimiento publicado en el canal digital",
    evidenciaPorTamano: {
      mediana:
        "Inventario de cookies y rastreadores con su finalidad y base de legitimación",
      corporativo:
        "Reportes de la plataforma de gestión de consentimiento y evidencia de bloqueo previo de rastreadores",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 36,
    dimensionId: "D05",
    control: "Marketing y comunicaciones comerciales",
    enunciado:
      "¿Los flujos de pago y prevención de fraude minimizan la exposición de datos y delimitan responsabilidades con pasarelas, adquirentes u otros terceros?",
    criterioMadurez:
      "Se documentan flujos y proveedores de pago; se evita conservar información completa de tarjetas cuando no sea necesaria; accesos, registros, incidentes y transferencias están controlados.",
    referenciaNormativa:
      "LOPDP Art. 7 y Art. 8 y derecho de oposición del titular",
    criticidad: 4,
    evidenciaEsperada:
      "Ejemplo de comunicación enviada con enlace de baja y registro de bajas atendidas",
    evidenciaPorTamano: {
      corporativo:
        "Reporte de supresión automatizada por canal, sustento de legitimación por campaña y auditoría del origen de las bases",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 37,
    dimensionId: "D05",
    control: "Datos de talento humano",
    enunciado:
      "¿CRM, programas de fidelización, segmentación, promociones y campañas gestionan datos, preferencias y oposiciones de forma trazable?",
    criterioMadurez:
      "Se documenta el origen de los contactos, finalidades, segmentación/perfilamiento cuando aplique, preferencias, consentimiento cuando corresponda, baja/oposición y uso de listas.",
    referenciaNormativa:
      "LOPDP Art. 25 y Art. 26 (categorías especiales) y Código del Trabajo",
    criticidad: 4,
    evidenciaEsperada:
      "Constancia del resguardo de expedientes laborales y de la restricción de acceso aplicada",
    evidenciaPorTamano: {
      mediana:
        "Matriz de tratamientos de talento humano con finalidad, base de legitimación y plazo de conservación",
      corporativo:
        "Matrices de acceso por rol en sistemas de nómina y selección, y evidencia de depuración de postulantes",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 38,
    dimensionId: "D05",
    control: "Videovigilancia y control de acceso",
    enunciado:
      "¿La atención al cliente, devoluciones, garantías y reclamos verifican identidad y evitan solicitar o revelar información innecesaria?",
    criterioMadurez:
      "Los canales de atención definen datos mínimos, verificación proporcional de identidad, acceso al historial necesario, entrega de información a autorizados y conservación de tickets/reclamos.",
    referenciaNormativa:
      "LOPDP Art. 10 (Responsabilidad Proactiva) y Art. 26 (datos biométricos)",
    criticidad: 3,
    evidenciaEsperada:
      "Señalización instalada, definición del plazo de conservación y lista de personal autorizado a las grabaciones",
    evidenciaPorTamano: {
      corporativo:
        "Política de videovigilancia, evaluación de proporcionalidad, bitácora de accesos a grabaciones y actas de entrega a terceros",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 39,
    dimensionId: "D05",
    control: "Eliminación y bloqueo al cierre del ciclo",
    enunciado:
      "¿La preparación, despacho, entrega a domicilio o retiro en tienda comparte únicamente los datos necesarios y controla el acceso de personal y terceros?",
    criterioMadurez:
      "Se limitan nombres, teléfonos, direcciones y datos de entrega a lo necesario; se controlan accesos de bodega/logística, couriers, evidencias de entrega y eliminación/retención.",
    referenciaNormativa:
      "LOPDP, Capítulo de Derechos del Titular (eliminación) y Art. 35 (plazos de conservación del RAT)",
    criticidad: 4,
    evidenciaEsperada:
      "Definición escrita de plazos de conservación y constancia de la última depuración realizada",
    evidenciaPorTamano: {
      mediana:
        "Política de retención por tipo de registro y actas de eliminación o bloqueo ejecutados",
      corporativo:
        "Calendario de disposición documental, actas de destrucción certificada y verificación del alcance sobre respaldos",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 40,
    dimensionId: "D05",
    control: "Anonimización y seudonimización",
    enunciado:
      "¿La gestión de postulantes, colaboradores, nómina, beneficios y desvinculación aplica controles de privacidad, acceso y conservación?",
    criterioMadurez:
      "Se controlan expedientes laborales, selección, nómina, afiliaciones, accesos, confidencialidad, bajas, datos sensibles laborales cuando existan y conservación.",
    referenciaNormativa:
      "LOPDP Art. 38 y Art. 39 (medidas técnicas) y disposiciones sobre datos anonimizados",
    criticidad: 2,
    evidenciaEsperada:
      "Procedimiento de anonimización o seudonimización, informe de evaluación del riesgo de reidentificación y evidencia de su aplicación en ambientes no productivos",
    tamanoMinimo: "corporativo",
  },

  // ───────── D06 · Encargados, proveedores y transferencias ─────────────────
  {
    id: 41,
    dimensionId: "D06",
    control: "Inventario de encargados y proveedores",
    enunciado:
      "¿Existe inventario actualizado de proveedores que acceden o tratan datos personales por cuenta de la empresa?",
    criterioMadurez:
      "Incluye, según aplique, POS/ERP, e-commerce, nube, pasarelas de pago, CRM/marketing, fidelización, logística/couriers, call center, RR. HH., soporte TI, CCTV/seguridad, archivo y consultores.",
    referenciaNormativa: "LOPDP Art. 46 (Acuerdos DPA) y Art. 35 (RAT)",
    criticidad: 4,
    evidenciaEsperada:
      "Listado de proveedores con acceso a datos personales y el servicio que prestan",
    evidenciaPorTamano: {
      mediana:
        "Inventario de encargados conciliado con el RAT, con categorías de datos y ubicación del tratamiento",
      corporativo:
        "Inventario centralizado con clasificación de criticidad y acta de conciliación periódica contra compras y el RAT",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 42,
    dimensionId: "D06",
    control: "Debida diligencia previa a la contratación",
    enunciado:
      "¿Los contratos con encargados incluyen cláusulas de confidencialidad y tratamiento adecuado?",
    criterioMadurez:
      "Los contratos regulan instrucciones, seguridad, subencargados, devolución/eliminación y auditoría.",
    referenciaNormativa: "LOPDP Art. 46 y Art. 10 (Responsabilidad Proactiva)",
    criticidad: 3,
    evidenciaEsperada:
      "Cuestionario de evaluación del proveedor respondido y archivado antes de la contratación",
    evidenciaPorTamano: {
      corporativo:
        "Expediente de debida diligencia con evaluación por criticidad, certificaciones revisadas y plan de subsanación acordado",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 43,
    dimensionId: "D06",
    control: "Cláusulas contractuales de tratamiento",
    enunciado:
      "¿Se evalúa privacidad y seguridad antes de contratar proveedores críticos de la empresa?",
    criterioMadurez:
      "La evaluación considera datos tratados, acceso, ubicación, seguridad, subencargados, confidencialidad, continuidad, incidentes y salida/devolución.",
    referenciaNormativa: "LOPDP Art. 46 (Acuerdos DPA)",
    criticidad: 5,
    evidenciaEsperada:
      "Contratos o acuerdos firmados con las cláusulas de tratamiento incorporadas",
    evidenciaPorTamano: {
      mediana:
        "Modelo estándar de cláusulas y reporte de cobertura de firma sobre el inventario de encargados",
      corporativo:
        "Anexo contractual aprobado por legal, reporte de cobertura auditado y control de versiones ante cambios normativos",
    },
    tamanoMinimo: "micro",
  },
  {
    id: 44,
    dimensionId: "D06",
    control: "Gestión de subencargados",
    enunciado:
      "¿Los servicios cloud/SaaS tienen evaluación de seguridad, ubicación y condiciones de tratamiento?",
    criterioMadurez:
      "Se revisan términos, ubicación, seguridad, respaldo, soporte, subprocesadores y acceso administrativo.",
    referenciaNormativa: "LOPDP Art. 46 (subencargados y autorización previa)",
    criticidad: 3,
    evidenciaEsperada:
      "Cláusula de subcontratación en los contratos y autorizaciones emitidas a los subencargados declarados",
    evidenciaPorTamano: {
      corporativo:
        "Inventario de subencargados por proveedor, autorizaciones documentadas y evidencia del traslado de obligaciones",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 45,
    dimensionId: "D06",
    control: "Servicios en la nube y ubicación de datos",
    enunciado:
      "¿Se identifican y gestionan transferencias internacionales de datos personales?",
    criterioMadurez:
      "Las transferencias se documentan, justifican y respaldan con garantías aplicables.",
    referenciaNormativa:
      "LOPDP Art. 46 y Art. 56 (ubicación y transferencia de datos)",
    criticidad: 4,
    evidenciaEsperada:
      "Listado de servicios en la nube utilizados con la región de almacenamiento declarada",
    evidenciaPorTamano: {
      corporativo:
        "Inventario gobernado de servicios en la nube, evidencia de gestión de claves y reportes de revisión de configuraciones",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 46,
    dimensionId: "D06",
    control: "Transferencias internacionales y garantías",
    enunciado:
      "¿El soporte técnico interno/externo tiene controles de acceso temporal, trazabilidad y confidencialidad?",
    criterioMadurez:
      "Accesos con autorización, tiempo limitado, usuario individual, bitácora y mínimo privilegio.",
    referenciaNormativa: "LOPDP Art. 56 y Art. 57 (Transferencias internacionales)",
    criticidad: 5,
    evidenciaEsperada:
      "Identificación de los flujos hacia el exterior y garantía aplicada en cada caso",
    evidenciaPorTamano: {
      corporativo:
        "Registro de flujos internacionales, cláusulas contractuales tipo suscritas y evaluación del marco legal del destino",
    },
    tamanoMinimo: "pequena",
  },
  {
    id: 47,
    dimensionId: "D06",
    control: "Accesos de soporte técnico externo",
    enunciado:
      "¿Los proveedores informan o requieren autorización para subencargados?",
    criterioMadurez:
      "Los subencargados están identificados y se aplican obligaciones equivalentes.",
    referenciaNormativa:
      "LOPDP Art. 38 y Art. 39 (control de accesos) y Art. 46",
    criticidad: 3,
    evidenciaEsperada:
      "Registro de accesos otorgados a soporte externo con alcance, vigencia y constancia de revocación",
    evidenciaPorTamano: {
      corporativo:
        "Bitácora de sesiones de soporte externo, autorizaciones por ventana de trabajo y reporte de revisión de cuentas de terceros",
    },
    tamanoMinimo: "mediana",
  },
  {
    id: 48,
    dimensionId: "D06",
    control: "Salida de proveedores y devolución de datos",
    enunciado:
      "¿Se controla la devolución o eliminación de datos al finalizar una relación con proveedores?",
    criterioMadurez:
      "Existe procedimiento de cierre con evidencia de devolución, borrado o destrucción segura.",
    referenciaNormativa:
      "LOPDP Art. 46 (devolución o supresión al término del encargo)",
    criticidad: 3,
    evidenciaEsperada:
      "Acta de devolución o certificado de destrucción de datos y constancia de revocación de accesos",
    evidenciaPorTamano: {
      corporativo:
        "Protocolo de salida de proveedores, actas certificadas, evidencia de revocación de integraciones y cierre en el inventario de encargados",
    },
    tamanoMinimo: "mediana",
  },
];
