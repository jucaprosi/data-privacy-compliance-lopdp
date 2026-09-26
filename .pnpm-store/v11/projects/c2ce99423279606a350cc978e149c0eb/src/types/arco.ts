/**
 * Tipos estrictos para el modulo de Gestion de Derechos ARCO+
 * conforme a la Ley Organica de Proteccion de Datos Personales (LOPDP Arts. 21-24, 37),
 * RGLOPDP y Doctrina 3 (Expedientes Probatorios Invariables).
 */

export type TipoDerechoARCO =
  | "Acceso"
  | "Rectificacion"
  | "Cancelacion"
  | "Oposicion"
  | "Portabilidad"
  | "Eliminacion";

export type EstadoSolicitudARCO =
  | "Recibido"
  | "En Revision"
  | "Resuelto"
  | "Excedido";

/**
 * Entidad Inmutable de Solicitud de Ejercicio de Derechos ARCO+ (Ticket ARCO+)
 * Art. 37 LOPDP: plazo de respuesta de 15 dias laborables.
 */
export interface SolicitudARCO {
  /** UUID unico invariable generado criptograficamente en el servidor */
  id: string;
  /** Tipo de derecho solicitado por el titular */
  tipoDerecho: TipoDerechoARCO;
  /** Fecha de recepcion de la solicitud en formato ISO 8601 */
  fechaSolicitud: string;
  /** Plazo legal de respuesta calculado en el servidor (15 dias laborables segun Art. 37 LOPDP) */
  fechaLimiteSLA: string;
  /** Estado del ciclo de vida del tramite */
  estado: EstadoSolicitudARCO;
  /** Enlace o identificador probatorio del expediente formal de respuesta (Doctrina 3, E1+) */
  evidenciaRespuesta: string | null;
  /** Datos del titular (opcionales segun canal de recepcion) */
  titularNombre?: string;
  titularIdentificacion?: string;
  titularEmail?: string;
  detalleSolicitud?: string;
  canalRecepcion?: "Web" | "Email" | "Presencial" | "Ventanilla" | string;
  fechaResolucion?: string | null;
  observaciones?: string;
}

/**
 * Payload de entrada para crearSolicitudArco()
 */
export interface CrearSolicitudArcoInput {
  tipoDerecho: TipoDerechoARCO;
  titularNombre?: string;
  titularIdentificacion?: string;
  titularEmail?: string;
  detalleSolicitud?: string;
  canalRecepcion?: string;
  /** Si no se provee, el servidor aplica Date.now() */
  fechaSolicitud?: string;
}

/**
 * Payload de entrada para resolverSolicitudArco().
 * La evidenciaUrl es OBLIGATORIA (Doctrina 3 - Invariante INV_ARCO_EVIDENCIA_E1).
 */
export interface ResolverSolicitudArcoInput {
  id: string;
  evidenciaUrl: string;
  observaciones?: string;
}

// ServerActionResponse<T> re-exportado desde @/types/rat (Doctrina 5 - SSOT)
