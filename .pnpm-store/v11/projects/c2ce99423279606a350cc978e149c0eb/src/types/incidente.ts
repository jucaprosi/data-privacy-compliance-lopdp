/**
 * Tipos e interfaces canónicas para el Playbook de Incidentes y Gestión de Vulneraciones.
 * Conforme a la Ley de Ciberseguridad 2026 y LOPDP (SLA legal inalterable de notificación de brechas).
 */

export type EstadoSLA = "A Tiempo" | "Crítico" | "Vencido";

export interface Incidente {
  /** Identificador único inmutable (UUID v4) */
  id: string;
  /** ISO 8601 string del momento exacto de detección provisto por el cliente o telemetría */
  fechaDeteccion: string;
  /** ISO 8601 string que suma rígidamente el plazo legal normativo (72 horas por defecto) */
  fechaLimiteNotificacion: string;
  /** Estado del SLA computado de forma determinista por el servidor */
  estadoSLA: EstadoSLA;
  /** Título o denominación del incidente de seguridad */
  titulo?: string;
  /** Descripción técnica o narrativa del vector de ataque / brecha detectada */
  descripcion?: string;
  /** Nivel de impacto y severidad técnica */
  severidad?: "Baja" | "Media" | "Alta" | "Crítica";
  /** Indicador booleano estricto de si compromete datos personales / titulares */
  afectacionDatosPersonales?: boolean;
  /** Categorías de datos vulnerados (financieros, salud, biométricos, identificativos) */
  categoriaDatosAfectados?: string[];
  /** Acciones inmediatas o de contención ejecutadas */
  medidasInmediatas?: string;
  /** Identificador o nombre del oficial / operador que registra la vulneración */
  reportadoPor?: string;
  /** Timestamp ISO 8601 de sellado exacto en el servidor */
  registradoEnServidor: string;
  /** Sello criptográfico SHA-256 para verificación de integridad (Tamper-Evident) */
  sha256Seal: string;
}

export interface RegistrarVulneracionInput {
  /** ISO 8601 string del momento de detección del incidente */
  fechaDeteccion: string;
  titulo?: string;
  descripcion?: string;
  severidad?: "Baja" | "Media" | "Alta" | "Crítica";
  afectacionDatosPersonales?: boolean;
  categoriaDatosAfectados?: string[];
  medidasInmediatas?: string;
  reportadoPor?: string;
  /** Plazo legal en horas. Por defecto: 72 horas según Ley Ciberseguridad 2026 / LOPDP */
  slaHorasPersonalizado?: number;
}

export interface CalculoCuentaRegresiva {
  fechaDeteccion: string;
  fechaLimiteNotificacion: string;
  horasRestantes: number;
  minutosRestantes: number;
  segundosRestantes: number;
  milisegundosRestantes: number;
  porcentajeConsumido: number;
  estadoSLA: EstadoSLA;
  haExpirado: boolean;
  umbralCriticoHoras: number;
}
