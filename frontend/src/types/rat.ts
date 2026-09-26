/**
 * Tipos estrictos para el RAT Maestro (Registro de Actividades de Tratamiento)
 * y el algoritmo MTGE conforme a la LOPDP, RGLOPDP y Resolucion SPDP-SPD-2026-0005-R.
 * Doctrina 5: Fuente Unica de Verdad (Single Source of Truth).
 */

/**
 * Bases de legitimacion segun Art. 7 y 8 de la LOPDP y Res. SPDP-SPD-2025-0041-R
 */
export type BaseJuridicaRAT =
  | "Consentimiento"
  | "Obligación Legal"
  | "Ejecución Contractual"
  | "Interés Legítimo";

/**
 * Categorias de datos personales segun Art. 25, 26 y 27 de la LOPDP
 */
export type CategoriaDato =
  | "Identificativos"
  | "Laborales"
  | "Financieros"
  | "Biométricos"
  | "Salud"
  | "Menores de Edad"
  | "Penales / Judiciales"
  | string;

/**
 * Entidad Maestro de Actividad de Tratamiento (Art. 35 LOPDP - Doctrina 5 SSOT)
 */
export interface ActividadTratamiento {
  id: string; // UUID unico e inmutable
  nombre: string; // Denominacion formal del tratamiento (ej: "Gestion de Nomina", "Videovigilancia")
  finalidad: string; // Principio de finalidad determinada, explicita y legitima (Art. 10 num. 2 LOPDP)
  baseJuridica: BaseJuridicaRAT; // Base de legitimacion estricta (Art. 7 LOPDP)
  categoriasDatos: CategoriaDato[]; // Tipologia de datos tratados (ej: ['Identificativos', 'Biometricos', 'Salud'])
  volumenRegistros: number; // Numero estimado de titulares de datos en el sistema
  permanenciaAnos: number; // Anos de retencion antes de su supresion / bloqueo (Res. 0030-R)

  // Metadatos calculados derivados del motor MTGE (Resolucion SPDP-SPD-2026-0005-R)
  requiereEIPD?: boolean; // Gatillo Art. 44 LOPDP (Evaluacion de Impacto)
  alertaForzosaDPO?: boolean; // Gatillo Art. 48 LOPDP (Designacion de DPO)
  puntajeMTGE?: number; // Puntuacion de Gran Escala calculada
  criterioActivacionMTGE?: string; // Trazabilidad del supuesto normativo activado
  fechaCreacion?: string; // Timestamp ISO 8601
  fechaActualizacion?: string; // Timestamp ISO 8601
}

/**
 * Dictamen determinista del algoritmo MTGE (Resolucion SPDP-SPD-2026-0005-R)
 */
export interface ResultadoEvaluacionMTGE {
  actividadId: string;
  puntajeMTGE: number;
  esGranEscala: boolean;
  requiereEIPD: boolean;
  alertaForzosaDPO: boolean;
  criterioActivacion:
    | "CASO_DIRECTO_SENSIBLES"
    | "CASO_DIRECTO_VOLUMEN"
    | "UMBRAL_PARAMETRICO"
    | "NO_ALCANZA";
  factores: {
    puntosVolumen: number;
    puntosSensibilidad: number;
    puntosPermanencia: number;
  };
  rationale: string;
}

/**
 * Respuesta generica serializable para Server Actions
 */
export interface ServerActionResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
