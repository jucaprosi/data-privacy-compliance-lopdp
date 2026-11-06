/**
 * Semáforos de plazos del tablero (FE-24): solo de lo que ya tiene fecha en el servidor, es decir,
 * las tareas de la hoja de ruta con fecha de fin. Solicitudes, vulneraciones, revisiones,
 * contratos y documentos llegan con su propia tarea.
 */
import { fetchAutenticado } from "@/lib/auth";
import type { RoadmapResponse, RoadmapTask } from "@/types/roadmap";

export interface SemaforoPlazos {
  vencidas: number;
  proximas: number;
  enPlazo: number;
}

export const DIAS_PROXIMAS = 7;
const MS_DIA = 86_400_000;

export function tareasConFecha(response: RoadmapResponse): RoadmapTask[] {
  return response.waves.flatMap((w) => w.tasks ?? []).filter((t) => Boolean(t.end_date));
}

/** Clasifica las tareas abiertas con fecha de fin; las completadas no cuentan. */
export function clasificarPlazos(tareas: RoadmapTask[], hoy: Date = new Date()): SemaforoPlazos {
  const resultado: SemaforoPlazos = { vencidas: 0, proximas: 0, enPlazo: 0 };
  const inicioHoy = Date.UTC(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
  for (const t of tareas) {
    if (t.status === "completada" || !t.end_date) continue;
    const fin = Date.parse(t.end_date.slice(0, 10));
    if (Number.isNaN(fin)) continue;
    const dias = Math.floor((fin - inicioHoy) / MS_DIA);
    if (dias < 0) resultado.vencidas += 1;
    else if (dias <= DIAS_PROXIMAS) resultado.proximas += 1;
    else resultado.enPlazo += 1;
  }
  return resultado;
}

export async function cargarHojaDeRuta(roadmapId: string): Promise<RoadmapResponse> {
  const respuesta = await fetchAutenticado(`/api/v1/roadmaps/${encodeURIComponent(roadmapId)}`, { method: "GET" });
  if (!respuesta.ok) throw new Error("No se pudieron leer los plazos de la hoja de ruta.");
  return (await respuesta.json()) as RoadmapResponse;
}
