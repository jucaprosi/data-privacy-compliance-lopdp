import type { DimensionId } from "@/lib/dimensionesSGPDP";

interface AlertaDimension {
  titular: string;
  enfoque: string;
  impacto: string;
  accion: string;
  beneficio: string;
}

/** Consecuencias posibles, no calificaciones jurídicas automáticas por dimensión. */
export const ALERTAS_DIMENSION: Readonly<Record<DimensionId, AlertaDimension>> = {
  D01: {
    titular: "Asigne el mando antes de exigir resultados.",
    enfoque: "quién decide, supervisa y mantiene las reglas de privacidad, y si esas responsabilidades quedan aprobadas y comunicadas",
    impacto: "Sin responsables ni una política vigente, las decisiones quedan dispersas y resulta difícil demostrar quién controla el tratamiento ante una inspección o un cliente estratégico.",
    accion: "Designe al responsable del programa, apruebe la política y deje constancia de su difusión. Verifique si corresponde nombrar un delegado de protección de datos.",
    beneficio: "Decisiones trazables y una dirección capaz de demostrar supervisión.",
  },
  D02: {
    titular: "Conozca sus datos antes de asumir su riesgo.",
    enfoque: "qué datos trata la organización, para qué, con qué fundamento y dónde queda registrado cada tratamiento",
    impacto: "Una base de datos sin finalidad y fundamento identificados puede comprometer campañas, contratos y decisiones comerciales, además de dificultar su defensa ante reclamaciones.",
    accion: "Identifique los tratamientos prioritarios, su finalidad y base de legitimación; documente el registro de actividades.",
    beneficio: "Bases de datos defendibles y decisiones comerciales con fundamento.",
  },
  D03: {
    titular: "La claridad protege la confianza del cliente.",
    enfoque: "si cada persona entiende qué datos se recopilan, para qué se usan y cómo ejercer sus derechos",
    impacto: "La información poco clara deteriora la confianza y puede obligar a revisar formularios, avisos y comunicaciones con clientes.",
    accion: "Revise el aviso de privacidad de su principal canal de captación y compárelo con el tratamiento real.",
    beneficio: "Comunicación coherente con el uso real de los datos.",
  },
  D04: {
    titular: "Responda a tiempo y conserve la evidencia.",
    enfoque: "si la organización recibe, responde y demuestra la atención de las solicitudes de los titulares",
    impacto: "Una solicitud sin dueño, plazo ni registro puede convertirse en un reclamo formal y afectar la confianza del cliente.",
    accion: "Defina un canal único, un responsable y un registro de recepción, respuesta y cierre.",
    beneficio: "Solicitudes atendidas con trazabilidad y menos fricción con clientes.",
  },
  D05: {
    titular: "Conserve solo lo que puede justificar.",
    enfoque: "cómo se recogen, usan, conservan y eliminan los datos durante todo su ciclo de vida",
    impacto: "Conservar o reutilizar datos sin control eleva la exposición operativa y puede afectar procesos comerciales que dependen de esas bases.",
    accion: "Documente plazos de conservación y reglas de eliminación para los tratamientos de mayor volumen o sensibilidad.",
    beneficio: "Menor exposición de datos y procesos más fáciles de controlar.",
  },
  D06: {
    titular: "Extienda el control a quienes tratan sus datos.",
    enfoque: "qué proveedores acceden a datos personales, bajo qué acuerdos y si existen transferencias internacionales",
    impacto: "Un proveedor sin responsabilidades claras puede interrumpir servicios, generar disputas contractuales y ampliar el alcance de una incidencia, especialmente si los datos cruzan fronteras.",
    accion: "Liste proveedores con acceso a datos y revise contratos, instrucciones y mecanismos de transferencia aplicables.",
    beneficio: "Servicios y relaciones contractuales con responsabilidades claras.",
  },
  D07: {
    titular: "Proteja los datos para proteger la operación.",
    enfoque: "si las medidas técnicas y organizativas protegen datos y mantienen los servicios disponibles",
    impacto: "Una brecha de seguridad puede afectar la continuidad, exigir respuesta urgente y erosionar la confianza de clientes y aliados.",
    accion: "Priorice accesos, copias de seguridad y protección de los sistemas con datos más sensibles.",
    beneficio: "Mayor continuidad y capacidad de respuesta ante una falla.",
  },
  D08: {
    titular: "Una respuesta preparada reduce el impacto.",
    enfoque: "si la organización detecta, contiene, documenta y gestiona oportunamente las vulneraciones",
    impacto: "Responder tarde agrava el daño posible y dificulta demostrar qué ocurrió, a quién afectó y cómo se contuvo.",
    accion: "Nombre un equipo de respuesta y pruebe un flujo de registro, evaluación y notificación cuando corresponda.",
    beneficio: "Incidentes contenidos con decisiones y tiempos verificables.",
  },
  D09: {
    titular: "Evalúe el riesgo antes de invertir en el lanzamiento.",
    enfoque: "si los riesgos se evalúan antes de lanzar procesos o productos que usan datos personales",
    impacto: "Descubrir el riesgo después del lanzamiento puede exigir rediseños costosos y retrasar iniciativas estratégicas.",
    accion: "Introduzca una revisión de privacidad previa al lanzamiento y determine cuándo se requiere una evaluación de impacto.",
    beneficio: "Menos rediseños tardíos y proyectos que avanzan con control.",
  },
  D10: {
    titular: "Convierta la política en una práctica constante.",
    enfoque: "si el personal conoce las reglas y si la dirección verifica que se cumplen y mejoran",
    impacto: "Las políticas que nadie aplica dejan a la organización expuesta a errores repetidos y dificultan demostrar diligencia ante terceros.",
    accion: "Programe formación por rol, revise una muestra de cumplimiento y asigne seguimiento a los hallazgos.",
    beneficio: "Equipos preparados y mejoras que la dirección puede verificar.",
  },
};
