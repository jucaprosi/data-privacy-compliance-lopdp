/**
 * Conjunto de respuestas de referencia del assessment SGPDP.
 *
 * Reproduce la estructura de una matriz de madurez completa (80 controles
 * distribuidos en las 10 dimensiones ponderadas) para que el tablero disponga
 * de una línea base operable mientras el diagnóstico real no se ha ejecutado.
 * Los controles estructurales aparecen degradados a propósito: es el escenario
 * que obliga al tablero a degradar el nivel final pese a un score alto, y que
 * de otro modo no quedaría ejercitado.
 */

import type { DimensionId } from "@/lib/dimensionesSGPDP";

type EstadoRef = "Conforme" | "Parcial" | "No Conforme" | "Pendiente";

/** [id, dimensión, control, estado, nivel evidencia (0-3), criticidad (1-5)] */
type FilaReferencia = [number, DimensionId, string, EstadoRef, number, number];

const FILAS: FilaReferencia[] = [
  // D01 · Gobierno y responsabilidad proactiva
  [1, "D01", "Política de protección de datos personales", "Conforme", 3, 5],
  [2, "D01", "Roles, responsabilidades y sponsor ejecutivo", "Conforme", 3, 5],
  [3, "D01", "Evaluación de aplicabilidad y designación del DPD", "Conforme", 2, 4],
  [4, "D01", "Independencia, recursos y seguimiento del DPD", "Conforme", 2, 4],
  [5, "D01", "Mapa de obligaciones y base normativa aplicable", "Conforme", 3, 4],
  [6, "D01", "Comité de privacidad y gobierno del SGPDP", "Conforme", 2, 3],
  [7, "D01", "Gestión documental del SGPDP", "Parcial", 1, 4],
  [8, "D01", "Indicadores y reportes a dirección", "Parcial", 1, 4],

  // D02 · Inventario, RAT, finalidades y legitimación
  [9, "D02", "Inventario de tratamientos", "No Conforme", 0, 5],
  [10, "D02", "Registro de Actividades de Tratamiento (RAT)", "No Conforme", 0, 5],
  [11, "D02", "Finalidades declaradas por tratamiento", "Conforme", 3, 4],
  [12, "D02", "Bases de legitimación documentadas", "Conforme", 3, 4],
  [13, "D02", "Datos sensibles y de mayor riesgo", "No Conforme", 0, 5],
  [14, "D02", "Plazos de conservación", "No Conforme", 0, 5],
  [15, "D02", "Minimización y calidad del dato", "Conforme", 2, 3],
  [16, "D02", "Actualización del RAT por cambios", "No Conforme", 0, 5],

  // D03 · Transparencia e información al titular
  [17, "D03", "Aviso de privacidad vigente", "Conforme", 3, 4],
  [18, "D03", "Información en canales digitales", "Conforme", 3, 4],
  [19, "D03", "Información en puntos de atención", "Conforme", 3, 3],
  [20, "D03", "Lenguaje claro y accesible", "Conforme", 3, 3],
  [21, "D03", "Gestión del consentimiento cuando aplica", "Conforme", 3, 4],
  [22, "D03", "Revocatoria del consentimiento", "Conforme", 2, 4],

  // D04 · Derechos de titulares
  [23, "D04", "Procedimiento de atención de derechos", "Conforme", 3, 5],
  [24, "D04", "Canales de recepción de solicitudes", "Conforme", 3, 4],
  [25, "D04", "Registro y trazabilidad de solicitudes", "Conforme", 3, 4],
  [26, "D04", "Cumplimiento de plazos normativos", "Conforme", 2, 5],
  [27, "D04", "Respuesta motivada al titular", "Conforme", 2, 4],
  [28, "D04", "Verificación de identidad", "No Conforme", 0, 5],
  [29, "D04", "Gestión de representación y terceros", "Parcial", 1, 4],
  [30, "D04", "Escalamiento de reclamos a la autoridad", "Conforme", 2, 3],
  [31, "D04", "Portabilidad de datos", "Conforme", 2, 3],
  [32, "D04", "Prueba o simulación de atención de derechos", "Parcial", 1, 4],

  // D05 · Procesos críticos y ciclo de vida de datos
  [33, "D05", "Alta y vinculación de titulares", "Conforme", 3, 5],
  [34, "D05", "Actualización de datos maestros", "Conforme", 3, 4],
  [35, "D05", "Tratamiento en canales digitales", "Conforme", 3, 4],
  [36, "D05", "Marketing y comunicaciones comerciales", "Conforme", 2, 3],
  [37, "D05", "Datos de talento humano", "Conforme", 3, 4],
  [38, "D05", "Videovigilancia y control de acceso", "Conforme", 2, 3],
  [39, "D05", "Eliminación y bloqueo al cierre del ciclo", "Parcial", 1, 4],
  [40, "D05", "Anonimización y seudonimización", "Conforme", 2, 3],

  // D06 · Encargados, proveedores y transferencias
  [41, "D06", "Inventario de encargados y proveedores", "Conforme", 3, 5],
  [42, "D06", "Debida diligencia previa a la contratación", "Conforme", 3, 4],
  [43, "D06", "Cláusulas contractuales de tratamiento", "Conforme", 3, 5],
  [44, "D06", "Gestión de subencargados", "Conforme", 2, 4],
  [45, "D06", "Servicios en la nube y ubicación de datos", "Conforme", 3, 4],
  [46, "D06", "Transferencias internacionales y garantías", "Conforme", 3, 5],
  [47, "D06", "Accesos de soporte técnico externo", "Conforme", 2, 4],
  [48, "D06", "Salida de proveedores y devolución de datos", "Conforme", 2, 4],

  // D07 · Seguridad de datos personales
  [49, "D07", "Gestión de identidades y accesos", "Conforme", 3, 5],
  [50, "D07", "Autenticación multifactor", "Conforme", 3, 5],
  [51, "D07", "Cifrado en tránsito y en reposo", "Conforme", 3, 5],
  [52, "D07", "Registros de auditoría y monitoreo", "Conforme", 2, 4],
  [53, "D07", "Respaldos y pruebas de restauración", "Conforme", 2, 5],
  [54, "D07", "Gestión de vulnerabilidades y parcheo", "Conforme", 2, 4],
  [55, "D07", "Segregación de ambientes", "Conforme", 3, 4],
  [56, "D07", "Seguridad física de instalaciones", "Conforme", 2, 3],

  // D08 · Incidentes y vulneraciones
  [57, "D08", "Procedimiento de gestión de incidentes", "Conforme", 3, 5],
  [58, "D08", "Registro y bitácora de incidentes", "Conforme", 2, 4],
  [59, "D08", "Clasificación de severidad", "No Conforme", 0, 5],
  [60, "D08", "Criterios de notificación a la autoridad", "Conforme", 2, 5],
  [61, "D08", "Contención y preservación de evidencia", "No Conforme", 0, 5],
  [62, "D08", "Comunicación a titulares afectados", "Conforme", 2, 4],
  [63, "D08", "Pruebas o simulacros tabletop", "Parcial", 1, 4],
  [64, "D08", "Lecciones aprendidas y cierre", "Conforme", 2, 3],

  // D09 · Riesgos, EIPD, LIA y privacidad desde el diseño
  [65, "D09", "Metodología de gestión de riesgos", "Conforme", 3, 5],
  [66, "D09", "Criterios de activación de EIPD", "Conforme", 3, 5],
  [67, "D09", "Ejecución y aprobación de EIPD", "Conforme", 3, 5],
  [68, "D09", "Evaluación de interés legítimo (LIA)", "Conforme", 3, 4],
  [69, "D09", "Privacidad desde el diseño en proyectos", "Conforme", 3, 4],
  [70, "D09", "Privacidad por defecto en configuraciones", "Conforme", 2, 4],
  [71, "D09", "Tratamiento de riesgo residual", "Conforme", 3, 4],
  [72, "D09", "Decisiones automatizadas y perfilado", "Conforme", 2, 4],

  // D10 · Capacitación, cultura, auditoría y mejora continua
  [73, "D10", "Plan de capacitación en protección de datos", "Conforme", 2, 4],
  [74, "D10", "Campañas de concienciación", "Parcial", 1, 3],
  [75, "D10", "Evaluación de eficacia de la formación", "Parcial", 1, 3],
  [76, "D10", "Programa de auditoría interna", "Conforme", 3, 4],
  [77, "D10", "Ejecución de auditorías del SGPDP", "Conforme", 3, 4],
  [78, "D10", "Gestión de hallazgos", "Conforme", 2, 4],
  [79, "D10", "Seguimiento de acciones correctivas", "No Conforme", 0, 5],
  [80, "D10", "Mejora continua y revisión por dirección", "No Conforme", 0, 5],
];

export interface RespuestaReferencia {
  preguntaId: number;
  cumple: EstadoRef;
  evidenciaNivel: number;
  esCritica: boolean;
  riesgoBase: number;
  pendienteValidacion: boolean;
  dimensionId: DimensionId;
  criticidad: number;
  control: string;
  esReferencia: true;
}

export const RESPUESTAS_REFERENCIA: RespuestaReferencia[] = FILAS.map(
  ([preguntaId, dimensionId, control, cumple, evidenciaNivel, criticidad]) => ({
    preguntaId,
    cumple,
    evidenciaNivel,
    esCritica: criticidad >= 5,
    riesgoBase: criticidad * 2,
    pendienteValidacion: false,
    dimensionId,
    criticidad,
    control,
    esReferencia: true,
  })
);

export const TOTAL_CONTROLES_REFERENCIA = RESPUESTAS_REFERENCIA.length;
