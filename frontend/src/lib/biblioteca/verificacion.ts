// ¤adpa ¤rbac-tenant
import { cabecerasDeTenant, fetchAutenticado } from "@/lib/auth";

export type Veredicto = "conforme" | "no_conforme" | "pendiente" | "sin_requisito";

export interface Evidencia {
  id: string;
  accion_id: string;
  titulo: string;
  version: string;
  sha256: string;
  clasificacion: string;
  permisos: string[];
  fecha: string;
  control_ref: string | null;
  documento_id: string | null;
  documento_revision: number | null;
  creado_por: string;
  creado_en: string;
}

export interface Verificacion {
  id: string;
  accion_id: string;
  evidencia_id: string;
  criterio: string;
  evidencia_legible: boolean;
  resultado: "conforme" | "no_conforme";
  eficacia_requerida: boolean;
  eficacia_conforme: boolean | null;
  revisor: string;
  fecha: string;
  observaciones: string | null;
  creado_en: string;
}

export interface Expediente {
  accion_id: string;
  veredicto: Veredicto;
  evidencias: Evidencia[];
  verificaciones: Verificacion[];
}

export interface NuevaEvidencia {
  titulo: string;
  version: string;
  sha256: string;
  clasificacion: "publica" | "interna" | "confidencial" | "restringida";
  permisos: string[];
  fecha: string;
  documento_id?: string;
  documento_revision?: number;
}

export interface NuevaVerificacion {
  evidencia_id: string;
  criterio: string;
  evidencia_legible: boolean;
  resultado: "conforme" | "no_conforme";
  eficacia_requerida: boolean;
  eficacia_conforme: boolean | null;
  fecha: string;
  observaciones?: string;
}

const ruta = (accionId: string) =>
  `/api/v1/biblioteca/verificaciones/acciones/${encodeURIComponent(accionId)}`;

async function json<T>(respuesta: Response): Promise<T> {
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new Error(cuerpo?.detail ?? "No se pudo actualizar la verificación.");
  return cuerpo as T;
}

export async function obtenerExpediente(accionId: string): Promise<Expediente> {
  return json(await fetchAutenticado(ruta(accionId), { cache: "no-store" }, cabecerasDeTenant()));
}

export async function registrarEvidencia(accionId: string, entrada: NuevaEvidencia): Promise<Evidencia> {
  return json(await fetchAutenticado(`${ruta(accionId)}/evidencias`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(entrada),
  }, cabecerasDeTenant()));
}

export async function registrarVerificacion(accionId: string, entrada: NuevaVerificacion): Promise<Expediente> {
  return json(await fetchAutenticado(`${ruta(accionId)}/verificaciones`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(entrada),
  }, cabecerasDeTenant()));
}

/** SHA-256 del archivo en el navegador; el hash prueba integridad, no legibilidad ni revisión. */
export async function huellaDeArchivo(archivo: Blob): Promise<string> {
  const resumen = await crypto.subtle.digest("SHA-256", await archivo.arrayBuffer());
  return Array.from(new Uint8Array(resumen)).map((b) => b.toString(16).padStart(2, "0")).join("");
}

export const TEXTO_VEREDICTO: Record<Veredicto, string> = {
  conforme: "Conforme: la acción puede cerrarse",
  no_conforme: "No conforme: la acción sigue abierta",
  pendiente: "Pendiente de verificación: el cierre está bloqueado",
  sin_requisito: "Sin evidencia registrada",
};
