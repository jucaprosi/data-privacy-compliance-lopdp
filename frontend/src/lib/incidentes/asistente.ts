/**
 * Cliente del asistente de vulneración en ocho pasos (INC-02). Cada guardado es una versión nueva en
 * el servidor; aquí no se guarda nada en el navegador. Los plazos legales no se calculan.
 */
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasComo } from "./roles";

const RUTA = "/api/v1/incidentes";

export const NOMBRES_PASOS = [
  "Identificación",
  "Tratamientos afectados",
  "Titulares y datos",
  "Descripción y tipo",
  "Efectos y medidas",
  "Resolución",
  "Decisión de notificar",
  "Informes y notificación",
] as const;
export const TOTAL_PASOS = NOMBRES_PASOS.length;
export const JUSTIFICACION_MINIMA = 20;

export const ROLES_LECTURA = ["implementador", "coordinador", "dpo", "admin_organizacion"] as const;
export const ROLES_PASOS_PREVIOS = ["implementador", "coordinador"] as const;
export const ROLES_DECISION = ["implementador", "dpo"] as const;

export type Decision = "spdp" | "titulares" | "ambos" | "ninguno";
export type Destino = "spdp" | "titulares";

export interface SeccionAsistente {
  id: number;
  nombre: string;
  completa: boolean;
  datos: Record<string, unknown> | null;
}

export interface EstadoAsistente {
  seccion_actual: number;
  decision: Decision | null;
  secciones: SeccionAsistente[];
  informes: Destino[];
  notificados: Destino[];
}

export interface ResumenAsistente {
  seccion_actual: number;
  decision: Decision | null;
}

export interface InformeGenerado {
  sha256: string;
  evidencia_id: string;
}

export interface EvidenciaCustodiada {
  id: string;
  codigo: string;
  nombre: string;
  sha256: string;
}

/** Error con el código del catálogo y el detalle del servidor, para mostrar el texto fijo que toca. */
export class ErrorAsistente extends Error {
  constructor(
    public readonly status: number,
    public readonly codigo: string | null,
    public readonly detalle: string | null,
  ) {
    super(codigo ?? `HTTP ${status}`);
  }
}

async function error(respuesta: Response): Promise<ErrorAsistente> {
  const cuerpo = (await respuesta.json().catch(() => null)) as { code?: unknown; detail?: unknown } | null;
  return new ErrorAsistente(
    respuesta.status,
    typeof cuerpo?.code === "string" ? cuerpo.code : null,
    typeof cuerpo?.detail === "string" ? cuerpo.detail : null,
  );
}

async function pedir<T>(rol: string, ruta: string, init: RequestInit = {}): Promise<T> {
  const cabeceras = init.body ? { "Content-Type": "application/json" } : undefined;
  const respuesta = await fetchAutenticado(`${RUTA}${ruta}`, { ...init, headers: cabeceras }, cabecerasComo(rol));
  if (!respuesta.ok) throw await error(respuesta);
  return (await respuesta.json()) as T;
}

export function resumenAsistentes(rol: string): Promise<Record<string, ResumenAsistente>> {
  return pedir(rol, "/asistentes", { method: "GET" });
}

export function leerAsistente(rol: string, incidenteId: string): Promise<EstadoAsistente> {
  return pedir(rol, `/${encodeURIComponent(incidenteId)}/asistente`, { method: "GET" });
}

export function guardarSeccion(
  rol: string,
  incidenteId: string,
  seccion: number,
  datos: Record<string, unknown>,
): Promise<EstadoAsistente> {
  return pedir(rol, `/${encodeURIComponent(incidenteId)}/asistente/${seccion}`, {
    method: "PUT",
    body: JSON.stringify(datos),
  });
}

export function generarInforme(rol: string, incidenteId: string, destino: Destino): Promise<InformeGenerado> {
  return pedir(rol, `/${encodeURIComponent(incidenteId)}/informes`, {
    method: "POST",
    body: JSON.stringify({ destino }),
  });
}

export function registrarNotificacion(
  rol: string,
  incidenteId: string,
  destino: Destino,
  notificadoEn: string,
  evidenciaSha256: string,
): Promise<EstadoAsistente> {
  return guardarSeccion(rol, incidenteId, 8, {
    destino,
    notificado_en: notificadoEn,
    evidencia_sha256: evidenciaSha256,
  });
}

/** Evidencias ya custodiadas de la organización, para adjuntar a la notificación (no se sube nada aquí). */
export async function evidenciasCustodiadas(rol: string): Promise<EvidenciaCustodiada[]> {
  const respuesta = await fetchAutenticado("/api/v1/evidencias/documentos", { method: "GET" }, cabecerasComo(rol));
  if (!respuesta.ok) throw await error(respuesta);
  const cuerpo = (await respuesta.json()) as {
    documentos: { id: string; codigo: string; nombre_archivo: string; sha256_hash: string }[];
  };
  return cuerpo.documentos.map((d) => ({ id: d.id, codigo: d.codigo, nombre: d.nombre_archivo, sha256: d.sha256_hash }));
}

/** Informes que pide la decisión; «No notificar» no pide ninguno. */
export function destinosDe(decision: Decision | null): Destino[] {
  if (decision === "spdp") return ["spdp"];
  if (decision === "titulares") return ["titulares"];
  if (decision === "ambos") return ["spdp", "titulares"];
  return [];
}
