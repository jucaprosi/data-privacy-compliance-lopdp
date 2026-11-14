/** Textos y tonos de las etiquetas de estado (UX/UI NORM-02). Siempre con texto; el color solo refuerza. */
import type { Corrida, EstadoResolucion } from "./cliente";

export const ESTADO_RESOLUCION: Record<EstadoResolucion, { texto: string; clase: string }> = {
  pendiente_revision: { texto: "Pendiente de revisión", clase: "" },
  homologada: { texto: "Homologada", clase: "" },
  vigente: { texto: "Vigente", clase: "badge-render-success" },
  observada: { texto: "Con observaciones", clase: "badge-render-warning" },
  reformada: { texto: "Reformada", clase: "badge-render-warning" },
  derogada: { texto: "Derogada", clase: "opacity-70" },
};

export const ESTADO_CORRIDA: Record<Corrida["estado"], { texto: string; clase: string }> = {
  ok: { texto: "Completada", clase: "badge-render-success" },
  parcial: { texto: "Completada con avisos", clase: "badge-render-warning" },
  fallida: { texto: "Fallida", clase: "badge-render-danger" },
};

export const MENSAJES: Record<string, string> = {
  NORMATIVA_NOTA_OBLIGATORIA: "Escribe una nota.",
  NORMATIVA_ESTADO_NO_PERMITIDO: "Ese estado no se puede registrar.",
  NORMATIVA_ORIGINAL_NO_DISPONIBLE: "El documento no está disponible por ahora.",
  NORMATIVA_RESOLUCION_NO_ENCONTRADA: "La norma ya no está en el catálogo.",
};

export const OPCIONES_REVISION = [
  { valor: "vigente", texto: "Vigente" },
  { valor: "observada", texto: "Con observaciones" },
  { valor: "reformada", texto: "Reformada" },
  { valor: "derogada", texto: "Derogada" },
] as const;

export function fechaCorta(iso: string | null): string {
  return iso ? new Date(iso).toLocaleDateString("es-EC", { year: "numeric", month: "short", day: "numeric" }) : "—";
}
