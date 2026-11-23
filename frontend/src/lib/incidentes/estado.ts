// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * Estado del incidente en la bitácora (INC-03f): abierto o cerrado, y el cierre con la decisión de
 * notificar pendiente. Cierra y reabre en el servidor (api/routers/incidentes_estado.py); la pantalla
 * sigue lo que la API entrega y no deduce el estado de nada más.
 *
 * Los mensajes de error son fijos por código: nunca se muestra el texto del servidor.
 */
import { fetchAutenticado } from "@/lib/auth";
import type { Incidente } from "@/types/incidente";
import { cabecerasComo } from "./roles";

const RUTA = "/api/v1/incidentes";

/** Mínimo y máximo del motivo, los mismos de la API. */
export const MOTIVO_MINIMO = 10;
export const MOTIVO_MAXIMO = 2000;

export type EstadoIncidente = "abierto" | "cerrado";
export type AccionEstado = "cerrar" | "reabrir";

export interface DetalleEstado {
  estado: EstadoIncidente;
  decision_notificacion: string | null;
  ultimo_motivo: string | null;
  ultimo_cambio_en: string | null;
}

/** Incidente de la lista con su estado; un incidente sin eventos de estado llega como abierto. */
export interface IncidenteConEstado extends Incidente {
  estado?: EstadoIncidente;
  estado_detalle?: DetalleEstado | null;
}

export type InsigniaEstado = "abierto" | "cerrado" | "cerrado_pendiente";

export const TEXTO_INSIGNIA: Record<InsigniaEstado, string> = {
  abierto: "Abierto",
  cerrado: "Cerrado",
  cerrado_pendiente: "Cerrado, notificación pendiente",
};

export const LINEA_PENDIENTE = "Falta registrar la decisión de notificar.";

/** Qué insignia corresponde al incidente según lo que entrega la API. */
export function insigniaDe(incidente: IncidenteConEstado): InsigniaEstado {
  const estado = incidente.estado ?? incidente.estado_detalle?.estado ?? "abierto";
  if (estado !== "cerrado") return "abierto";
  return incidente.estado_detalle?.decision_notificacion === "pendiente" ? "cerrado_pendiente" : "cerrado";
}

/** Longitud del motivo sin los espacios del inicio ni del final. */
export function largoMotivo(motivo: string): number {
  return motivo.trim().length;
}

export function motivoSuficiente(motivo: string): boolean {
  return largoMotivo(motivo) >= MOTIVO_MINIMO;
}

/** Error de la API con su estado HTTP y su código de negocio, para elegir el texto fijo. */
export class ErrorEstadoIncidente extends Error {
  constructor(
    public readonly estadoHttp: number,
    public readonly codigo: string | null,
  ) {
    super(`HTTP ${estadoHttp}${codigo ? ` ${codigo}` : ""}`);
    this.name = "ErrorEstadoIncidente";
  }
}

/** Dónde se muestra el error y si hay que volver a pedir la lista. */
export interface MensajeError {
  texto: string;
  /** "dialogo": el diálogo sigue abierto; "lista": el diálogo se cierra y se recarga el estado. */
  lugar: "dialogo" | "lista";
  recargar: boolean;
}

const MENSAJES_409: Record<string, string> = {
  INCIDENTE_YA_CERRADO: "Este incidente ya estaba cerrado. Actualizamos su estado.",
  INCIDENTE_YA_ABIERTO: "Este incidente ya estaba abierto. Actualizamos su estado.",
  DECISION_NOTIFICAR_PENDIENTE:
    "Antes de cerrar, registra si hay que notificar esta vulneración. Hazlo en el paso 7 del asistente, «Decisión de notificar».",
  INCIDENTE_CAMBIO_CONCURRENTE:
    "Otra persona cambió el estado de este incidente al mismo tiempo. Actualizamos su estado; revísalo antes de intentarlo de nuevo.",
};

const MENSAJE_GENERICO = "No pudimos cambiar el estado del incidente. Inténtalo de nuevo.";

/** Texto fijo y comportamiento de la pantalla para cada respuesta de error. */
export function mensajeDeError(error: unknown): MensajeError {
  if (!(error instanceof ErrorEstadoIncidente)) {
    return { texto: MENSAJE_GENERICO, lugar: "dialogo", recargar: false };
  }
  if (error.estadoHttp === 409) {
    return {
      texto: (error.codigo && MENSAJES_409[error.codigo]) || "Cambió el estado de este incidente. Actualizamos su estado.",
      lugar: "lista",
      recargar: true,
    };
  }
  if (error.estadoHttp === 404) {
    return { texto: "No encontramos este incidente. Actualizamos la lista.", lugar: "lista", recargar: true };
  }
  if (error.estadoHttp === 403) {
    return { texto: "No tienes permiso para cambiar el estado de este incidente.", lugar: "dialogo", recargar: false };
  }
  if (error.estadoHttp === 422) {
    return { texto: "El motivo no es válido. Escribe entre 10 y 2000 caracteres.", lugar: "dialogo", recargar: false };
  }
  return { texto: MENSAJE_GENERICO, lugar: "dialogo", recargar: false };
}

/** Texto del aviso de éxito según la acción y el estado que devolvió el servidor. */
export function mensajeDeExito(accion: AccionEstado, resultado: DetalleEstado): string {
  if (accion === "reabrir") return "Incidente reabierto. El motivo quedó en la bitácora.";
  return resultado.decision_notificacion === "pendiente"
    ? "Incidente cerrado. Falta registrar la decisión de notificar."
    : "Incidente cerrado. El motivo quedó en la bitácora.";
}

/** Cierra o reabre el incidente con el motivo. Devuelve el estado nuevo o lanza ErrorEstadoIncidente. */
export async function cambiarEstado(
  rol: string,
  incidenteId: string,
  accion: AccionEstado,
  motivo: string,
): Promise<DetalleEstado> {
  const respuesta = await fetchAutenticado(
    `${RUTA}/${encodeURIComponent(incidenteId)}/${accion}`,
    { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ motivo: motivo.trim() }) },
    cabecerasComo(rol),
  );
  if (!respuesta.ok) {
    const cuerpo = (await respuesta.json().catch(() => null)) as { code?: unknown } | null;
    throw new ErrorEstadoIncidente(respuesta.status, typeof cuerpo?.code === "string" ? cuerpo.code : null);
  }
  return (await respuesta.json()) as DetalleEstado;
}
