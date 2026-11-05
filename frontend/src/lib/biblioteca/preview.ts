// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Cliente de la vista previa (BIB-206). El servidor arma la vista previa con la misma instantánea y modelo
 * de salida que el archivo; aquí solo se pide, se muestra y se emite si sigue vigente.
 */
import { cabecerasDeTenant, fetchAutenticado } from "@/lib/auth";
import type { FormatoGeneracion, Generacion, ModoGeneracion } from "@/lib/biblioteca/generacion";

export interface BloqueVista {
  tipo: "titulo" | "parrafo" | "lista" | "cita" | "tabla";
  texto: string;
  nivel: number;
  filas: string[][];
}

export interface VistaPrevia {
  borrador_id: string;
  revision: number;
  modo: ModoGeneracion;
  formato: FormatoGeneracion;
  estado: "borrador" | "para_revision";
  plantilla_sha256: string;
  instantanea_sha256: string;
  archivo_sha256: string;
  nombre_archivo: string;
  faltantes: string[];
  bloques: BloqueVista[];
}

export class VistaObsoleta extends Error {}

const RUTA = "/api/v1/biblioteca/preview/borradores";
const enc = encodeURIComponent;

async function leer<T>(respuesta: Response, porDefecto: string): Promise<T> {
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    const detalle = typeof datos?.detail === "string" ? datos.detail : porDefecto;
    if (respuesta.status === 409 && datos?.code === "BIB_PREVIEW_OBSOLETA") throw new VistaObsoleta(detalle);
    throw new Error(detalle);
  }
  return datos as T;
}

export async function previsualizar(borradorId: string, modo: ModoGeneracion,
  formato: FormatoGeneracion): Promise<VistaPrevia> {
  return leer(await fetchAutenticado(`${RUTA}/${enc(borradorId)}`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ modo, formato }),
    cache: "no-store",
  }, cabecerasDeTenant()), "No se pudo preparar la vista previa.");
}

export async function emitirDesdeVista(vista: VistaPrevia): Promise<Generacion> {
  return leer(await fetchAutenticado(`${RUTA}/${enc(vista.borrador_id)}/emitir`, {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ modo: vista.modo, formato: vista.formato, revision: vista.revision,
      instantanea_sha256: vista.instantanea_sha256 }),
  }, cabecerasDeTenant()), "No se pudo emitir el archivo.");
}
