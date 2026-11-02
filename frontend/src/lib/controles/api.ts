/**
 * Cliente HTTP de los controles periódicos (CAPA-02) y su semáforo.
 * Contrato: governance/especificaciones/CAPA-02.md §2 y §4.
 */
import { cabecerasDeRol, fetchAutenticado } from "@/lib/auth";

export type FrecuenciaControl = "mensual" | "trimestral" | "semestral" | "anual";
export type EstadoControl = "vigente" | "vencido" | "retirado";
export type Semaforo = "vigente" | "por_vencer" | "vencido" | "retirado";

export interface ControlPeriodico {
  id: string;
  nombre: string;
  control_ref: string | null;
  frecuencia: FrecuenciaControl;
  responsable_user_id: string;
  proxima_verificacion: string;
  estado: EstadoControl;
  hallazgo_vigente_id: string | null;
  ultima_verificacion_en: string | null;
}

export interface CrearControlPayload {
  nombre: string;
  control_ref?: string;
  frecuencia: FrecuenciaControl;
  responsable_user_id: string;
  proxima_verificacion: string;
}

export interface VerificarControlPayload {
  evidencia_sha256?: string;
  nota?: string;
}

export const DIAS_AVISO = 7;
const BASE = "/api/v1/auditoria-capa/controles";
const MS_POR_DIA = 86_400_000;

/** Fecha de hoy en Guayaquil (UTC-5, sin horario de verano), como en el servidor. */
export function hoyGuayaquil(ahora: Date = new Date()): string {
  return new Date(ahora.getTime() - 5 * 3_600_000).toISOString().slice(0, 10);
}

/** Días de `desde` a `hasta`, ambas en formato AAAA-MM-DD. */
export function diasEntre(desde: string, hasta: string): number {
  return Math.round((Date.parse(hasta) - Date.parse(desde)) / MS_POR_DIA);
}

export function semaforoDe(control: Pick<ControlPeriodico, "estado" | "proxima_verificacion">, hoy: string): Semaforo {
  if (control.estado === "retirado") return "retirado";
  const dias = diasEntre(hoy, control.proxima_verificacion);
  if (control.estado === "vencido" || dias < 0) return "vencido";
  return dias <= DIAS_AVISO ? "por_vencer" : "vigente";
}

function cabeceras(rol: string, userId: string): Record<string, string> {
  return { "Content-Type": "application/json", ...cabecerasDeRol(rol, userId) };
}

async function leer<T>(res: Response, mensajePorDefecto: string): Promise<T> {
  if (res.ok) return (await res.json()) as T;
  const cuerpo = (await res.json().catch(() => null)) as { detail?: unknown } | null;
  throw new Error(typeof cuerpo?.detail === "string" ? cuerpo.detail : mensajePorDefecto);
}

export async function listarControles(rol: string, userId: string): Promise<ControlPeriodico[]> {
  const res = await fetchAutenticado(BASE, { method: "GET", headers: cabeceras(rol, userId) });
  const datos = await leer<{ controles: ControlPeriodico[] }>(res, "No se pudieron cargar los controles.");
  return datos.controles;
}

export async function crearControl(
  payload: CrearControlPayload,
  rol: string,
  userId: string,
): Promise<ControlPeriodico> {
  const res = await fetchAutenticado(BASE, {
    method: "POST",
    headers: cabeceras(rol, userId),
    body: JSON.stringify(payload),
  });
  return leer(res, "No se pudo crear el control.");
}

export async function verificarControl(
  id: string,
  payload: VerificarControlPayload,
  rol: string,
  userId: string,
): Promise<ControlPeriodico> {
  const res = await fetchAutenticado(`${BASE}/${id}/verificaciones`, {
    method: "POST",
    headers: cabeceras(rol, userId),
    body: JSON.stringify(payload),
  });
  const datos = await leer<{ control: ControlPeriodico }>(res, "No se pudo registrar la verificación.");
  return datos.control;
}

export async function retirarControl(
  id: string,
  motivo: string,
  rol: string,
  userId: string,
): Promise<ControlPeriodico> {
  const res = await fetchAutenticado(`${BASE}/${id}/retirar`, {
    method: "POST",
    headers: cabeceras(rol, userId),
    body: JSON.stringify({ motivo }),
  });
  return leer(res, "No se pudo retirar el control.");
}

export async function vencerControles(rol: string, userId: string): Promise<void> {
  const res = await fetchAutenticado(`${BASE}/vencer`, { method: "POST", headers: cabeceras(rol, userId) });
  await leer(res, "No se pudieron revisar los vencimientos.");
}
