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
      "¿La organización tiene por escrito los pasos y las personas encargadas para atender cuando alguien pide ver, corregir, borrar o limitar el uso de sus datos?",
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
      "¿La organización tiene al menos un medio gratuito, fácil de encontrar y siempre disponible (correo, formulario, ventanilla) para que las personas hagan esas solicitudes?",
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
      "¿La organización anota cada solicitud que recibe: fecha, qué pidió la persona, qué se le respondió y cuándo se cerró?",
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
      "¿La organización responde a estas solicitudes dentro del plazo de la ley, que es de 15 días desde que las recibe?",
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
      "¿La respuesta a la persona explica con claridad qué se hizo y, si se le dijo que no a algo, explica por qué?",
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
      "Antes de entregar o cambiar datos, ¿la organización comprueba que quien lo pide es realmente la persona dueña de esos datos?",
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
      "Si alguien pidiera datos en nombre de otra persona (apoderado, padre o madre de un menor, heredero), ¿se sabe que hay que pedir y guardar el documento que lo autoriza antes de entregarle nada?",
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
      "¿La organización sabe que la persona puede quejarse ante la Superintendencia de Protección de Datos Personales y atiende los pedidos que esta autoridad le haga?",
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
      "Si una persona lo pide, ¿la organización puede entregarle en un archivo digital común (como Excel o PDF) los datos que ella misma dio?",
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
      "¿La organización hace de vez en cuando una prueba (con un caso inventado) para comprobar que sabría atender bien una solicitud de datos y a tiempo?",
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
      "Cuando la organización registra a un cliente nuevo, ¿le explica para qué usará sus datos y le pide solo lo necesario?",
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
      "¿La organización tiene alguna forma de mantener actualizados los datos de las personas y de corregirlos en todos los lugares donde estén guardados?",
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
      "Si la organización tiene sitio web, aplicación o redes sociales, ¿informa qué datos recoge y pide permiso antes de usar cookies (pequeños archivos que siguen lo que hace la persona en la página)?",
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
      "Si la organización envía publicidad o promociones, ¿se las manda solo a quienes lo aceptaron y cada mensaje incluye una forma fácil y gratuita de dejar de recibirlas?",
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
      "¿Los datos de los empleados (hojas de vida, certificados médicos, datos familiares y bancarios) se guardan con acceso limitado y se usan solo para temas de trabajo?",
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
      "Si la organización tiene cámaras de seguridad, ¿hay carteles que avisan, se decidió por cuánto tiempo se guardan las grabaciones y solo ciertas personas pueden verlas?",
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
      "¿La organización borra o bloquea los datos de las personas cuando ya no los necesita o cuando se cumple el plazo para guardarlos?",
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
      "Cuando se usan datos para estadísticas, pruebas o desarrollo de sistemas, ¿se quitan o se ocultan los nombres y datos que identifican a las personas?",
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
      "¿La organización sabe qué proveedores o terceros (contador, nube, empresa de nómina, mensajería) reciben o ven datos de personas y para qué servicio?",
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
      "Antes de contratar a un proveedor que va a manejar datos personales, ¿la organización revisa si ese proveedor los protege bien?",
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
      "¿Los contratos con proveedores que manejan datos por cuenta de la organización dicen por escrito para qué pueden usarlos, que deben guardar reserva y cómo deben protegerlos?",
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
      "Si un proveedor necesita contratar a su vez a otra empresa para trabajar con los datos, ¿el contrato exige que pida permiso antes y que esa otra empresa cumpla las mismas reglas?",
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
      "Si la organización guarda datos en servicios en internet (nube, como Google Drive u otros), ¿sabe cuáles son y en qué país están guardados?",
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
      "Si la organización envía datos de personas a otro país, ¿lo tiene identificado y comprobó que allá los protegen bien o firmó un acuerdo para que los protejan?",
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
      "Cuando un técnico externo entra a revisar o reparar un sistema con datos, ¿se le da acceso solo a lo necesario, solo por un tiempo y se anota lo que hizo?",
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
      "Cuando termina el contrato con un proveedor, ¿la organización pide que devuelva o borre los datos, lo confirme por escrito y se le quitan sus accesos?",
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
