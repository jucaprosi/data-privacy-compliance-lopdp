/**
 * Bitácora de incidentes de seguridad (INC-01): forma de los datos que intercambia la pantalla con
 * el servidor (api/routers/incidentes.py).
 *
 * Los plazos de notificación siguen aplazados por decisión del propietario (LEG-02): aquí no hay
 * ningún plazo legal. Autoría, hora de registro y huellas las pone el servidor.
 */

export type SeveridadIncidente = "Baja" | "Media" | "Alta" | "Crítica";

export const SEVERIDADES_INCIDENTE: readonly SeveridadIncidente[] = ["Baja", "Media", "Alta", "Crítica"];

export interface NuevoIncidente {
  /** Momento de la detección, en ISO 8601. No puede ser futuro. */
  fecha_deteccion: string;
  titulo: string;
  descripcion: string;
  severidad: SeveridadIncidente;
  afecta_datos_personales: boolean;
  categorias_datos: string[];
  medidas_inmediatas: string;
}

export interface Incidente extends NuevoIncidente {
  id: string;
  /** Posición en la cadena de la organización: 1, 2, 3... */
  secuencia: number;
  /** Usuario autenticado que lo registró. */
  registrado_por: string;
  /** Hora del servidor al registrarlo. */
  registrado_en: string;
  huella_anterior: string;
  huella: string;
}

export interface BitacoraIncidentes {
  /** Del más reciente al más antiguo. */
  incidentes: Incidente[];
  cadena_integra: boolean;
  primer_alterado: string | null;
}
