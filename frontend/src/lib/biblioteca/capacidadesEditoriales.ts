// ¤adpa
// ¤¤frontend-architect
/**
 * BIB-118 · Capacidades editoriales propias: `GET /api/v1/biblioteca/capacidades/mias`. Sin respaldo a
 * `listarEditorial`. Un error devuelve `[]`: el menú se oculta y la autorización sigue en el servidor.
 */
import { httpBiblioteca } from "@/lib/biblioteca/http";

export const ETIQUETAS_CAPACIDAD = {
  editor: "Editor",
  revisor_tecnico: "Revisor técnico",
  revisor_juridico: "Revisor jurídico",
  publicador: "Publicador",
} as const;
export type CapacidadEditorial = keyof typeof ETIQUETAS_CAPACIDAD;

export async function leerMisCapacidades(): Promise<string[]> {
  try {
    const { capacidades } = await httpBiblioteca<{ capacidades: string[] }>("/biblioteca/capacidades/mias");
    return Array.isArray(capacidades) ? capacidades : [];
  } catch {
    return [];
  }
}
