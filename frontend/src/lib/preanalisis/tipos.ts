/**
 * Contrato del pre-llenado asistido del cuestionario.
 *
 * La IA propone, el auditor decide. Reglas que este contrato hace explícitas:
 *  - Solo puede proponer Conforme, Parcial o "Sin sustento". Nunca "No Conforme":
 *    el silencio de un documento no prueba un incumplimiento.
 *  - Toda propuesta distinta de "Sin sustento" cita fragmentos que se verificaron
 *    literalmente contra el texto enviado; las citas no verificables se descartan.
 *  - Un documento respalda como máximo el nivel E1 (práctica documentada). Los
 *    niveles E2 y E3 los declara el auditor con su propia evidencia.
 *  - Ninguna propuesta se aplica sin decisión explícita del auditor.
 */

export type EstadoPropuesta = "Conforme" | "Parcial" | "Sin sustento";

export type DecisionPropuesta = "pendiente" | "aceptada" | "editada" | "descartada";

export interface CitaVerificada {
  /** Texto literal encontrado en los fragmentos enviados al modelo. */
  fragmento: string;
  motivo: string;
}

/** Fragmento de un documento, ya enmascarado, que saldría hacia el modelo. */
export interface FragmentoDocumento {
  texto: string;
  /** Ubicación legible dentro del documento (p. ej. "p. 4" u "hoja Inventario"). */
  origen: string;
}

export interface PropuestaIA {
  id: string;
  preguntaId: number;
  evidenciaId: string;
  evidenciaCodigo: string;
  estado: EstadoPropuesta;
  /** 1 solo con al menos una cita verificada; 0 en cualquier otro caso. */
  nivelEvidenciaMaximo: 0 | 1;
  citas: CitaVerificada[];
  /** Citas del modelo que no aparecieron en los fragmentos y se descartaron. */
  citasDescartadas: number;
  razonamiento: string;
  limitaciones: string[];
  modelo: string;
  generadaEn: string;
  decision: DecisionPropuesta;
  decididaEn?: string;
}

/** Rastro que queda en la respuesta cuando el auditor acepta o edita una propuesta. */
export interface RastroPreanalisis {
  propuestaId: string;
  evidenciaCodigo: string;
  modelo: string;
  decision: "aceptada" | "editada";
  fecha: string;
}

export interface EstadoServicioIA {
  disponible: boolean;
  proveedor: string | null;
  modelo: string | null;
  motivo: string | null;
}

/** Datos de un control que se envían al servicio junto con los fragmentos. */
export interface ControlParaAnalisis {
  control_id: number;
  control: string;
  enunciado: string;
  evidencia_esperada: string;
  referencia_normativa: string;
}

/** Respuesta de POST /api/v1/preanalisis/preparar. */
export interface PreparacionDocumento {
  formato: string;
  caracteres_totales: number;
  fragmentos: Array<FragmentoDocumento & { relevancia: number }>;
  pii_enmascarada: number;
  advertencias: string[];
}

/** Respuesta de POST /api/v1/preanalisis/analizar. */
export interface ResultadoAnalisis {
  estado: EstadoPropuesta;
  nivel_evidencia_maximo: 0 | 1;
  citas: CitaVerificada[];
  citas_descartadas: number;
  razonamiento: string;
  limitaciones: string[];
  modelo: string;
}
