// ¤adpa ¤rbac-tenant
/** Cliente de vínculos de un documento con tratamientos, controles y tareas (BIB-402). */
import { cabecerasDeTenant, fetchAutenticado } from "@/lib/auth";

export type TipoVinculo = "tratamiento" | "control" | "tarea";

export interface Vinculo {
  id: string;
  documento_id: string;
  tipo: TipoVinculo;
  ref: string;
  estado: "vigente" | "revisar";
  creado_por: string;
  creado_en: string;
}

export interface EntradaVinculos {
  tratamientos: string[];
  controles: string[];
  tareas: string[];
}

export interface DocumentoVinculado {
  documento_id: string;
  codigo: string;
  nombre: string;
  estado_documento: string;
  estado: "vigente" | "revisar";
}

export const ROLES_QUE_VINCULAN = ["implementador", "coordinador"] as const;

const ruta = (documentoId: string) =>
  `/api/v1/biblioteca/documentos/${encodeURIComponent(documentoId)}/vinculos`;

async function json<T>(respuesta: Response, aviso: string): Promise<T> {
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    const detalle = cuerpo?.detail;
    throw new Error(typeof detalle === "string" ? detalle : detalle?.message ?? aviso);
  }
  return cuerpo as T;
}

export async function listarVinculos(documentoId: string): Promise<Vinculo[]> {
  const r = await fetchAutenticado(ruta(documentoId), { cache: "no-store" }, cabecerasDeTenant());
  return (await json<{ vinculos: Vinculo[] }>(r, "No se pudieron consultar los vínculos.")).vinculos;
}

export async function guardarVinculos(documentoId: string, entrada: EntradaVinculos): Promise<Vinculo[]> {
  const r = await fetchAutenticado(ruta(documentoId), {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(entrada),
  }, cabecerasDeTenant());
  return (await json<{ vinculos: Vinculo[] }>(r, "No se pudieron guardar los vínculos.")).vinculos;
}

export async function documentosDeTratamiento(tratamientoId: string): Promise<DocumentoVinculado[]> {
  const r = await fetchAutenticado(
    `/api/v1/biblioteca/tratamientos/${encodeURIComponent(tratamientoId)}/documentos`,
    { cache: "no-store" }, cabecerasDeTenant());
  return json<DocumentoVinculado[]>(r, "No se pudieron consultar los documentos del tratamiento.");
}

/** Roles vigentes en la organización activa; el servidor vuelve a comprobarlos en cada escritura. */
export async function misRoles(): Promise<string[]> {
  try {
    const r = await fetchAutenticado("/api/v1/organizacion/me/roles", { cache: "no-store" }, cabecerasDeTenant());
    if (!r.ok) return [];
    const cuerpo = await r.json();
    return Array.isArray(cuerpo) ? cuerpo.map((x: { role?: string }) => String(x?.role ?? "")) : [];
  } catch {
    return [];
  }
}

export function puedeVincular(roles: readonly string[]): boolean {
  return roles.some((r) => (ROLES_QUE_VINCULAN as readonly string[]).includes(r));
}

export function separarVinculos(vinculos: Vinculo[]): EntradaVinculos {
  const de = (tipo: TipoVinculo) => vinculos.filter((v) => v.tipo === tipo).map((v) => v.ref);
  return { tratamientos: de("tratamiento"), controles: de("control"), tareas: de("tarea") };
}
