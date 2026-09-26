/**
 * Tipos estrictos para el modulo de Gestion de Hallazgos y CAPA
 * (Acciones Correctivas y Preventivas Auditadas con SoD).
 * Normativa: LOPDP Arts. 10 num. 7, 41-44 | Doctrina 4 y 10 | Teorema 4 (SoD).
 * Invariante: INV_CAPA_SOD (auditorId != usuarioQueSubioEvidencia).
 */

export type EstadoCAPA =
  | 'Abierto'
  | 'Pendiente de Verificacion'
  | 'Cerrado Conforme'
  | 'Rechazado';

export type SeveridadHallazgo =
  | 'No Conformidad Mayor'
  | 'No Conformidad Menor'
  | 'Observacion'
  | 'Oportunidad de Mejora';

export interface TicketCAPA {
  id: string;
  preguntaIdOriginaria: string;
  descripcionHallazgo: string;
  accionCorrectiva: string;
  responsableArea: string;
  auditorAsignado: string;
  estado: EstadoCAPA;
  evidenciaMitigacion: string | null;
  severidad?: SeveridadHallazgo;
  descripcionBrechaOriginal?: string;
  usuarioQueSubioEvidencia?: string | null;
  fechaCreacion: string;
  fechaUltimaActualizacion: string;
  fechaCierreConforme?: string | null;
  dictamenAuditor?: string | null;
  historialCambios?: CambioEstadoCAPA[];
}

export interface CambioEstadoCAPA {
  estadoAnterior: EstadoCAPA;
  estadoNuevo: EstadoCAPA;
  actor: string;
  timestamp: string;
  nota?: string;
}

export interface CrearPlanCorrectivoInput {
  preguntaIdOriginaria: string;
  descripcionHallazgo: string;
  accionCorrectiva: string;
  responsableArea: string;
  auditorAsignado: string;
  severidad?: SeveridadHallazgo;
  descripcionBrechaOriginal?: string;
}

export interface ResultadoValidacionSoD {
  valido: boolean;
  auditorId: string;
  usuarioEvidencia: string | null | undefined;
  motivo?: string;
}
