/**
 * Cliente tipado del centro de conocimiento (REG-02). Solo lee el corpus versionado de `regulacion_rag`.
 * Contrato: governance/especificaciones/REG-02.md §2.
 */
import { fetchAutenticado } from "@/lib/auth";

export interface ArticuloNormativa {
  fuente: string;
  articulo: string;
  titulo: string;
  texto: string;
  version: string;
}

export interface CitaNormativa {
  fuente: string;
  articulo: string;
  version: string;
}

export interface AyudaConCita {
  texto: string;
  cita: CitaNormativa;
}

/** La ayuda cita el corpus o no existe: no hay un tercer caso (INV_LOPDP_AI_RAG_STRICT_CITATION). */
export type ResultadoAyuda = { estado: "con_cita"; ayuda: AyudaConCita } | { estado: "sin_fuente" };

export interface ConsultaAyuda {
  controlRef?: string;
  articulo?: string;
}

const BASE = "/api/v1/conocimiento";

export async function buscarNormativa(fuente: string, q: string): Promise<ArticuloNormativa[]> {
  const params = new URLSearchParams();
  if (fuente) params.set("fuente", fuente);
  if (q.trim()) params.set("q", q.trim());
  const res = await fetchAutenticado(`${BASE}/normativa?${params.toString()}`);
  if (!res.ok) throw new Error(`No se pudo consultar la normativa (HTTP ${res.status}).`);
  const cuerpo = (await res.json()) as { articulos?: ArticuloNormativa[] };
  return cuerpo.articulos ?? [];
}

export async function obtenerAyuda({ controlRef, articulo }: ConsultaAyuda): Promise<ResultadoAyuda> {
  const params = new URLSearchParams();
  if (controlRef) params.set("control_ref", controlRef);
  else if (articulo) params.set("articulo", articulo);
  const res = await fetchAutenticado(`${BASE}/ayuda?${params.toString()}`);
  if (res.status === 404) return { estado: "sin_fuente" };
  if (!res.ok) throw new Error(`No se pudo consultar la ayuda (HTTP ${res.status}).`);
  const ayuda = (await res.json()) as Partial<AyudaConCita>;
  // Defensa en el cliente: un texto sin cita completa nunca se muestra.
  const cita = ayuda.cita;
  if (!ayuda.texto || !cita?.fuente || !cita.articulo || !cita.version) return { estado: "sin_fuente" };
  return { estado: "con_cita", ayuda: ayuda as AyudaConCita };
}

/** «Art. 7 LOPDP»: artículo y fuente, tal como se lee en la ley. */
export function etiquetaCita(cita: Pick<CitaNormativa, "fuente" | "articulo">): string {
  return `${cita.articulo} ${cita.fuente}`;
}
