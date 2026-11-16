/**
 * Cliente de la papelera y de la exportación de la organización (ORG-20).
 *
 * Forma de las respuestas, tomada de `features/organizacion/services/{papelera,exportacion}_engine.py`:
 * GET /organizacion/papelera → `{registros: [{entidad, id, nombre, retirado_en}], entidades: [{entidad, etiqueta}]}`;
 * POST /organizacion/exportaciones → 202 `{id}`; GET /organizacion/exportaciones/{id} → `{estado, completa, url?,
 * sha256?, caduca_en?}`; 409 `EXPORTACION_EN_CURSO`. La papelera la usan `admin_organizacion` e `implementador`;
 * la exportación, solo `admin_organizacion`. La organización y la identidad salen de la sesión.
 */
import { fetchAutenticado } from "@/lib/auth";
import { requestJson } from "@/lib/roadmap/cliente";
import { ApiError } from "@/types/roadmap";
import type { OrganizacionRole } from "@/types/roadmap";

export interface RegistroPapelera {
  entidad: string;
  id: string;
  nombre: string;
  retirado_en: string;
}
export interface EntidadPapelera {
  entidad: string;
  etiqueta: string;
}
export interface Papelera {
  registros: RegistroPapelera[];
  entidades: EntidadPapelera[];
}
export type EstadoExportacion = "pendiente" | "lista" | "caducada";
export interface Exportacion {
  estado: EstadoExportacion;
  completa: boolean;
  url?: string;
  sha256?: string;
  caduca_en?: string;
}

export const puedeUsarPapelera = (rol: OrganizacionRole) => rol === "admin_organizacion" || rol === "implementador";
export const puedeExportar = (rol: OrganizacionRole) => rol === "admin_organizacion";

/** dd/mm/aaaa a partir de una fecha ISO; vacío si no se puede leer. */
export function fechaCorta(iso: string | undefined | null): string {
  if (!iso) return "";
  const f = new Date(iso);
  if (Number.isNaN(f.getTime())) return "";
  const dos = (n: number) => String(n).padStart(2, "0");
  return `${dos(f.getUTCDate())}/${dos(f.getUTCMonth() + 1)}/${f.getUTCFullYear()}`;
}

const conRol = (rol: OrganizacionRole) => ({ headers: { "X-Role": rol } });

export const papeleraApi = {
  async listar(rol: OrganizacionRole, entidad?: string): Promise<Papelera> {
    const consulta = entidad ? `?entidad=${encodeURIComponent(entidad)}` : "";
    const crudo = await requestJson<Partial<Papelera>>(`/organizacion/papelera${consulta}`, { method: "GET", ...conRol(rol) });
    return { registros: crudo?.registros ?? [], entidades: crudo?.entidades ?? [] };
  },
  async restaurar(entidad: string, id: string, rol: OrganizacionRole): Promise<void> {
    await requestJson<unknown>(
      `/organizacion/papelera/${encodeURIComponent(entidad)}/${encodeURIComponent(id)}/restaurar`,
      { method: "POST", ...conRol(rol) },
    );
  },
  async solicitarExportacion(rol: OrganizacionRole): Promise<{ id: string }> {
    return requestJson<{ id: string }>("/organizacion/exportaciones", { method: "POST", ...conRol(rol) });
  },
  async exportacion(id: string, rol: OrganizacionRole): Promise<Exportacion> {
    return requestJson<Exportacion>(`/organizacion/exportaciones/${encodeURIComponent(id)}`, { method: "GET", ...conRol(rol) });
  },
  /** Descarga el ZIP con la identidad de la sesión (un enlace simple no lleva el token). */
  async descargar(url: string, rol: OrganizacionRole): Promise<Blob> {
    const ruta = url.startsWith("/api/v1") ? url : `/api/v1${url}`;
    const respuesta = await fetchAutenticado(ruta, { method: "GET", headers: { "X-Role": rol } });
    if (!respuesta.ok) throw new ApiError(respuesta.status, "No pudimos descargar la exportación.");
    return respuesta.blob();
  },
};

export const esExportacionEnCurso = (err: unknown) => err instanceof ApiError && err.code === "EXPORTACION_EN_CURSO";
