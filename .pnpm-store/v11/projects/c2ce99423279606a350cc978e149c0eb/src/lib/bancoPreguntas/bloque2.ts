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
      "¿Existe un procedimiento escrito que indique quién recibe, resuelve y responde las solicitudes de acceso, rectificación, eliminación y oposición del titular?",
    enunciadoPorTamano: {
      pequena:
        "¿El procedimiento de atención de derechos está documentado con responsables designados, pasos de validación y plazos internos de resolución?",
      mediana:
        "¿El procedimiento de atención de derechos está aprobado, difundido a las áreas involucradas y articulado con las unidades que custodian las bases de datos?",
      corporativo:
        "¿El procedimiento de atención de derechos opera bajo flujo formalizado extremo a extremo, con acuerdos de nivel de servicio internos, matriz de responsabilidades por derecho e indicadores reportados a la Alta Dirección?",
    },
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
      "¿Se publica al menos un canal gratuito, accesible y permanente (correo, formulario o ventanilla) para que el titular presente sus solicitudes?",
    enunciadoPorTamano: {
      mediana:
        "¿Los canales de recepción están publicados en los puntos de contacto con el titular, con instrucciones claras de uso y responsable asignado por canal?",
      corporativo:
        "¿Los canales de recepción se encuentran integrados y monitoreados de forma centralizada, con cobertura multicanal, acuses de recibo automáticos y consolidación de solicitudes recibidas por vías no oficiales?",
    },
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
      "¿Se lleva un registro de las solicitudes recibidas con fecha de ingreso, derecho solicitado, respuesta entregada y fecha de cierre?",
    enunciadoPorTamano: {
      pequena:
        "¿El registro de solicitudes permite reconstruir cada caso con su fecha de ingreso, gestiones internas, respuesta entregada y evidencia de notificación al titular?",
      corporativo:
        "¿La trazabilidad de solicitudes se sostiene en un sistema con bitácora inalterable, custodia de la evidencia de cada gestión y reportes periódicos de volumen, tipo de derecho y tiempos de atención?",
    },
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
      "¿Se responde al titular dentro del plazo legal de quince (15) días, contados desde la recepción de la solicitud?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe un control de plazos que alerte el vencimiento de cada solicitud y deje constancia de la prórroga cuando la normativa la permite?",
      corporativo:
        "¿El cumplimiento de plazos se gestiona con alertas automáticas escalonadas, medición de tiempos por tipo de derecho y reporte de desviaciones al responsable del cumplimiento?",
    },
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
      "¿La respuesta entregada al titular explica de forma comprensible lo resuelto y, cuando se niega total o parcialmente el derecho, expresa el fundamento de la negativa?",
    enunciadoPorTamano: {
      mediana:
        "¿Se emplean modelos de respuesta revisados jurídicamente que motiven la decisión, informen las vías de reclamo disponibles y se adapten al derecho ejercido?",
      corporativo:
        "¿Las respuestas se emiten sobre plantillas controladas por tipo de derecho, con validación jurídica de las negativas, registro del sustento aplicado y seguimiento de la conformidad del titular?",
    },
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
      "¿Se verifica la identidad de quien solicita el ejercicio de un derecho antes de entregar información o ejecutar la acción pedida?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe una regla conocida por el personal sobre qué documentación se exige para acreditar la identidad del solicitante antes de resolver?",
      mediana:
        "¿Existen criterios documentados de verificación de identidad proporcionales al tipo de solicitud y al riesgo de la información requerida?",
      corporativo:
        "¿La verificación de identidad está estandarizada por canal, con niveles de aseguramiento diferenciados, gestión de representación legal y registro auditable de cada validación?",
    },
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
      "¿Se exige y conserva la acreditación de la representación cuando la solicitud la presenta un apoderado, el representante legal de un menor o un heredero?",
    enunciadoPorTamano: {
      mediana:
        "¿Están definidos los supuestos de representación admitidos, la documentación habilitante exigible en cada uno y el tratamiento diferenciado para niñas, niños y adolescentes?",
      corporativo:
        "¿La gestión de representación opera con criterios estandarizados por supuesto, validación jurídica de los poderes presentados, custodia de la documentación habilitante y trazabilidad del vínculo acreditado?",
    },
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
      "¿Se informa al titular su derecho a presentar reclamo ante la Superintendencia de Protección de Datos Personales y se atiende internamente el requerimiento que esta formule?",
    enunciadoPorTamano: {
      mediana:
        "¿Existe una ruta interna definida para atender requerimientos de la autoridad de control, con responsable designado, plazos de respuesta y custodia del expediente?",
      corporativo:
        "¿La gestión de reclamos ante la autoridad cuenta con protocolo formal de atención, vocería designada, análisis de causa raíz de los casos escalados y seguimiento de las medidas correctivas adoptadas?",
    },
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
      "¿Puede la organización entregar al titular, cuando lo solicite, los datos que él mismo proporcionó en un formato electrónico de uso común y lectura mecánica?",
    enunciadoPorTamano: {
      mediana:
        "¿Están identificados los tratamientos alcanzados por el derecho de portabilidad y definidos los formatos de exportación y el procedimiento de entrega segura al titular?",
      corporativo:
        "¿La portabilidad se resuelve con capacidades de exportación estructurada por sistema fuente, formatos interoperables documentados, canal de entrega cifrado y, cuando resulta técnicamente viable, transmisión directa a otro responsable?",
    },
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
      "¿Se realizan pruebas o simulaciones periódicas del circuito de atención de derechos, con casos representativos por tipo de solicitud, para verificar tiempos, calidad de la respuesta y correcta propagación de la acción a todos los sistemas afectados?",
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
      "¿En el momento de captar los datos de un cliente, usuario o afiliado se informa la finalidad del tratamiento y se recoge únicamente lo necesario para esa finalidad?",
    enunciadoPorTamano: {
      pequena:
        "¿Los formularios y medios de captación en el alta de titulares declaran finalidad y base de legitimación, y se encuentran alineados con el aviso de privacidad vigente?",
      mediana:
        "¿Los procesos de alta y vinculación están estandarizados con criterios de minimización, validación de la base de legitimación y registro del momento y la versión del aviso aceptado?",
      corporativo:
        "¿El alta de titulares opera con controles de minimización verificables por canal, captura trazable de la base de legitimación, versionado del aviso aceptado y revisión periódica de los campos solicitados?",
    },
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
      "¿Existe un mecanismo para mantener actualizados y exactos los datos de los titulares, y para propagar la corrección a los registros donde el dato se replica?",
    enunciadoPorTamano: {
      mediana:
        "¿La actualización de datos maestros cuenta con responsables por dominio de dato, reglas de calidad definidas y sincronización verificable entre los sistemas que consumen el dato?",
      corporativo:
        "¿Existe gobierno de datos maestros con propietario por dominio, reglas de calidad medidas, propagación controlada hacia sistemas satélite e indicadores de exactitud reportados periódicamente?",
    },
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
      "¿El sitio web, la aplicación o las redes sociales de la organización informan qué datos se recogen y solicitan el consentimiento antes de activar cookies o rastreadores no imprescindibles?",
    enunciadoPorTamano: {
      pequena:
        "¿Los canales digitales cuentan con aviso de privacidad accesible y un mecanismo de consentimiento que permita aceptar o rechazar cookies y rastreadores no necesarios?",
      mediana:
        "¿Existe inventario de cookies, píxeles y kits de desarrollo de terceros embebidos en los canales digitales, con base de legitimación declarada y consentimiento registrado por visitante?",
      corporativo:
        "¿La gestión del consentimiento digital opera con plataforma dedicada, bloqueo previo de rastreadores no esenciales, registro auditable de la preferencia de cada visitante y revisión periódica de los terceros embebidos?",
    },
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
      "¿Las comunicaciones comerciales se envían solo a quienes lo consintieron y ofrecen en cada mensaje una forma sencilla y gratuita de darse de baja?",
    enunciadoPorTamano: {
      mediana:
        "¿Las campañas de marketing se ejecutan sobre bases depuradas contra el registro de oposiciones y bajas, con la base de legitimación documentada por campaña y canal?",
      corporativo:
        "¿La operación de marketing aplica supresión automatizada de oposiciones y bajas en todos los canales, segmentación con base de legitimación acreditada, control de perfilamiento y auditoría del origen de cada base utilizada?",
    },
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
      "¿Los datos del personal (hojas de vida, certificados médicos, datos familiares y bancarios) se conservan con acceso restringido y se usan solo para fines laborales?",
    enunciadoPorTamano: {
      pequena:
        "¿El expediente laboral se custodia con acceso restringido al personal autorizado y existe regla escrita sobre qué datos se piden en selección y por cuánto tiempo se conservan?",
      mediana:
        "¿El tratamiento de datos de talento humano tiene finalidades y bases de legitimación declaradas por proceso (selección, nómina, salud ocupacional, evaluación) con controles reforzados sobre las categorías especiales?",
      corporativo:
        "¿El ciclo de datos de talento humano opera con controles de acceso por rol en cada sistema, segregación de las categorías especiales, plazos de conservación diferenciados por proceso y depuración verificable de postulantes no contratados?",
    },
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
      "¿Las zonas videovigiladas están señalizadas, las grabaciones tienen un plazo de conservación definido y el acceso a ellas está limitado a personas autorizadas?",
    enunciadoPorTamano: {
      mediana:
        "¿La videovigilancia y el control de acceso cuentan con finalidad declarada, zonas excluidas de captación, plazo de conservación aplicado de forma automática y registro de las visualizaciones o entregas de imágenes?",
      corporativo:
        "¿El sistema de videovigilancia y control de acceso opera bajo política formal con evaluación de proporcionalidad, controles reforzados sobre datos biométricos, bitácora auditable de accesos a las grabaciones y protocolo documentado de entrega a terceros o autoridades?",
    },
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
      "¿Se eliminan o bloquean los datos personales cuando concluye la finalidad que justificó su recolección o vence el plazo de conservación aplicable?",
    enunciadoPorTamano: {
      pequena:
        "¿Están definidos los plazos de conservación por tipo de registro y se ejecuta una depuración periódica que alcance también a los respaldos y archivos físicos?",
      mediana:
        "¿La política de retención declara plazo, base legal y destino final por tipo de registro, y su ejecución deja constancia documentada de las eliminaciones y bloqueos realizados?",
      corporativo:
        "¿La retención y disposición final se ejecuta de forma controlada en todos los repositorios, incluidos respaldos y sistemas heredados, con bloqueo previo a la eliminación definitiva, actas de destrucción y verificación independiente del cumplimiento?",
    },
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
      "¿Se aplican técnicas de anonimización o seudonimización a los conjuntos de datos empleados en analítica, pruebas de sistemas o desarrollo, con criterios documentados de irreversibilidad y custodia separada de la información de reidentificación?",
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
      "¿Se tiene identificado qué proveedores o terceros acceden a datos personales de la organización y para qué servicio lo hacen?",
    enunciadoPorTamano: {
      pequena:
        "¿Existe un listado de proveedores con acceso a datos personales que indique el servicio prestado, los datos involucrados y el responsable interno del contrato?",
      mediana:
        "¿El inventario de encargados registra servicio, categorías de datos, ubicación del tratamiento y estado contractual, y se mantiene conciliado con el Registro de Actividades de Tratamiento?",
      corporativo:
        "¿El inventario de encargados se gestiona de forma centralizada con clasificación de criticidad, conciliación periódica contra compras y el RAT, y control de altas y bajas durante todo el ciclo de vida del proveedor?",
    },
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
      "¿Se evalúan las garantías de protección de datos y seguridad del proveedor antes de contratarlo y de entregarle información personal?",
    enunciadoPorTamano: {
      corporativo:
        "¿La debida diligencia previa aplica un cuestionario de evaluación proporcional a la criticidad del proveedor, revisa certificaciones e informes de auditoría independiente, documenta los hallazgos y condiciona la adjudicación a la subsanación de las brechas detectadas?",
    },
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
      "¿Los contratos o acuerdos con quienes tratan datos por cuenta de la organización incluyen por escrito la finalidad, las instrucciones, el deber de confidencialidad y las obligaciones de seguridad?",
    enunciadoPorTamano: {
      pequena:
        "¿Todos los contratos con encargados incorporan las cláusulas obligatorias de tratamiento, incluidos el deber de asistencia ante solicitudes del titular y la notificación de vulneraciones?",
      mediana:
        "¿Existe un modelo estándar de cláusulas de tratamiento aplicado a la totalidad de encargados vigentes, con control del estado de firma y de las adendas suscritas?",
      corporativo:
        "¿Las cláusulas de tratamiento se gestionan como anexo contractual obligatorio con modelo aprobado por el área legal, cobertura verificada sobre el total de encargados vigentes, auditoría del estado de suscripción y actualización ante cambios normativos?",
    },
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
      "¿Los contratos con encargados exigen autorización previa para subcontratar el tratamiento y obligan a trasladar al subencargado las mismas condiciones pactadas?",
    enunciadoPorTamano: {
      corporativo:
        "¿La cadena de subencargados se mantiene inventariada y actualizada por proveedor, con autorización documentada de cada incorporación, traslado verificable de obligaciones y retención de la responsabilidad del encargado principal frente a la organización?",
    },
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
      "¿Se conoce en qué servicios en la nube se alojan los datos personales y en qué país se encuentran almacenados?",
    enunciadoPorTamano: {
      mediana:
        "¿Los servicios en la nube que alojan datos personales están inventariados con su ubicación de almacenamiento, condiciones contractuales aplicables y controles de acceso configurados por la organización?",
      corporativo:
        "¿La adopción de servicios en la nube se gobierna con aprobación previa por criticidad del dato, control de la ubicación de almacenamiento y procesamiento, gestión de claves bajo custodia de la organización y revisión periódica de configuraciones frente a servicios no autorizados?",
    },
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
      "¿Se identifican las transferencias de datos personales hacia el exterior y se verifica que el destino ofrezca nivel adecuado de protección o cuente con garantías contractuales suscritas?",
    enunciadoPorTamano: {
      mediana:
        "¿Las transferencias internacionales están registradas con destino, finalidad y mecanismo de legitimación aplicado, y se informa esta circunstancia al titular en el aviso de privacidad?",
      corporativo:
        "¿Las transferencias internacionales se gestionan con registro completo por flujo, cláusulas contractuales tipo o mecanismo equivalente suscrito, evaluación del marco legal del país de destino y revisión periódica de la vigencia de las garantías adoptadas?",
    },
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
      "¿Los accesos remotos o presenciales de proveedores de soporte técnico a sistemas con datos personales se otorgan con alcance limitado, por tiempo definido y con registro de la actividad realizada?",
    enunciadoPorTamano: {
      corporativo:
        "¿Los accesos de soporte externo operan bajo credenciales nominativas, autorización previa por ventana de trabajo, privilegios mínimos, monitoreo o grabación de sesión y revocación verificada al término de la intervención?",
    },
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
      "¿Al terminar la relación con un encargado se exige la devolución o eliminación certificada de los datos personales y se revocan sus accesos a los sistemas de la organización?",
    enunciadoPorTamano: {
      corporativo:
        "¿La desvinculación de encargados sigue un protocolo formal con acta de devolución o destrucción certificada, revocación verificada de credenciales e integraciones, cierre de la cuenta en el inventario y validación del alcance sobre respaldos del proveedor?",
    },
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
