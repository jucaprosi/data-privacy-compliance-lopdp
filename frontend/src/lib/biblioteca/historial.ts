// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
import { httpBiblioteca } from "@/lib/biblioteca/http";

export type TipoEvento = "cambio" | "descarga" | "generacion" | "aprobacion" | "notificacion" | "reapertura" | "restauracion";
export interface EventoCronologia {
  id: string; tipo: TipoEvento; revision: number | null; actor_id: string;
  detalle: Record<string, unknown>; creado_en: string;
}
export interface ConservacionDocumento {
  documento_id: string; retenido_hasta: string | null; bloqueo_legal: boolean; motivo: string | null;
  politica_id: string | null; politica_aprobada: boolean; actualizado_por: string | null; actualizado_en: string | null;
}

const base = (id: string) => `/biblioteca/documentos/${encodeURIComponent(id)}`;
export const obtenerCronologia = (id: string) =>
  httpBiblioteca<EventoCronologia[]>(`${base(id)}/cronologia`);
export const obtenerConservacion = (id: string) =>
  httpBiblioteca<ConservacionDocumento>(`${base(id)}/conservacion`);
export const restaurarRevision = (id: string, revisionOrigen: number, motivo: string) =>
  httpBiblioteca(`${base(id)}/restauraciones`, {
    method: "POST", body: JSON.stringify({ revision_origen: revisionOrigen, motivo }),
  });
