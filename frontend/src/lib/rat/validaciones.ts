/**
 * Cliente HTTP de las validaciones y versiones de una ficha del RAT (RAT-05).
 * Contrato: governance/especificaciones/RAT-05.md §2.
 */
import { cabecerasDeRol, fetchAutenticado } from "@/lib/auth";

export interface ReglaValidacion {
  codigo: string;
  cumple: boolean;
  mensaje: string;
}

export interface ValidacionesFicha {
  reglas: ReglaValidacion[];
  hallazgo_id: string | null;
}

export interface VersionFicha {
  numero: number;
  creado_por: string | null;
  creado_en: string;
}

/** Literales a) a g) del art. 26 LOPDP (Registro Oficial 459, 26-may-2021). */
export const CONDICIONES_HABILITANTES: { valor: string; etiqueta: string }[] = [
  { valor: "CONSENTIMIENTO_EXPLICITO", etiqueta: "a) Consentimiento explícito del titular" },
  { valor: "LABORAL_SEGURIDAD_SOCIAL", etiqueta: "b) Derecho laboral y de seguridad y protección social" },
  { valor: "INTERESES_VITALES", etiqueta: "c) Protección de intereses vitales" },
  { valor: "DATOS_PUBLICOS", etiqueta: "d) Datos hechos manifiestamente públicos por el titular" },
  { valor: "ORDEN_JUDICIAL", etiqueta: "e) Orden de autoridad judicial" },
  { valor: "ARCHIVO_INVESTIGACION_ESTADISTICA", etiqueta: "f) Archivo, investigación o fines estadísticos" },
  { valor: "SALUD_SEGUN_LEY", etiqueta: "g) Datos de salud sujetos a las disposiciones de la ley" },
];

const BASE = "/api/v1/rat";

async function leer<T>(res: Response, mensajePorDefecto: string): Promise<T> {
  if (res.ok) return (await res.json()) as T;
  const cuerpo = (await res.json().catch(() => null)) as { detail?: unknown } | null;
  throw new Error(typeof cuerpo?.detail === "string" ? cuerpo.detail : mensajePorDefecto);
}

function cabeceras(rol: string, userId: string): Record<string, string> {
  return { "Content-Type": "application/json", ...cabecerasDeRol(rol, userId) };
}

export async function obtenerValidaciones(ratId: string, rol: string, userId: string): Promise<ValidacionesFicha> {
  const res = await fetchAutenticado(`${BASE}/${ratId}/validaciones`, { method: "GET", headers: cabeceras(rol, userId) });
  return leer(res, "No se pudieron cargar las validaciones.");
}

export async function listarVersiones(ratId: string, rol: string, userId: string): Promise<VersionFicha[]> {
  const res = await fetchAutenticado(`${BASE}/${ratId}/versiones`, { method: "GET", headers: cabeceras(rol, userId) });
  const datos = await leer<{ versiones: VersionFicha[] }>(res, "No se pudieron cargar las versiones.");
  return datos.versiones;
}

export async function leerVersion(
  ratId: string,
  numero: number,
  rol: string,
  userId: string,
): Promise<Record<string, unknown>> {
  const res = await fetchAutenticado(`${BASE}/${ratId}/versiones/${numero}`, { method: "GET", headers: cabeceras(rol, userId) });
  return leer(res, "No se pudo leer la versión.");
}

/** Declara la condición habilitante: es un guardado de la ficha, y solo lo hace el coordinador. */
export async function guardarCondicion(ratId: string, condicion: string, rol: string, userId: string): Promise<void> {
  const res = await fetchAutenticado(`${BASE}/actividades/${ratId}`, {
    method: "PATCH",
    headers: cabeceras(rol, userId),
    body: JSON.stringify({ condicion_habilitante: condicion }),
  });
  await leer(res, "No se pudo guardar la condición habilitante.");
}
