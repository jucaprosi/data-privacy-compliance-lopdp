import type { TaskStatus } from "../../../../types/roadmap";
import type { OrigenHallazgo, TareaConOrigen } from "./tipos";

export type Vista = "lista" | "tablero" | "cronograma";

export const VISTAS: Array<{ id: Vista; etiqueta: string }> = [
  { id: "lista", etiqueta: "Lista" },
  { id: "tablero", etiqueta: "Tablero" },
  { id: "cronograma", etiqueta: "Cronograma" },
];

/** Orden de las columnas del tablero. */
export const ORDEN_ESTADOS: TaskStatus[] = ["pendiente", "en_progreso", "completada", "bloqueada"];

const ETIQUETA_ORIGEN: Record<OrigenHallazgo, string> = {
  diagnostico: "diagnóstico",
  auditoria: "auditoría",
  eipd: "EIPD",
  incidente: "incidente",
  tercero: "tercero",
  control_periodico: "control periódico",
};

export function etiquetaOrigen(origen: OrigenHallazgo): string {
  return ETIQUETA_ORIGEN[origen] ?? origen;
}

/** Fecha de hoy (AAAA-MM-DD) en Guayaquil, que es la que manda para decir si una tarea venció. */
export function hoyGuayaquil(ahora: Date = new Date()): string {
  return new Intl.DateTimeFormat("en-CA", {
    timeZone: "America/Guayaquil",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).format(ahora);
}

/** Vencida = no completada y con fecha de fin anterior a hoy (RM-22 R4). */
export function esVencida(tarea: TareaConOrigen, hoy: string): boolean {
  return tarea.status !== "completada" && Boolean(tarea.end_date) && (tarea.end_date as string) < hoy;
}

export function agruparPorEstado(tareas: TareaConOrigen[]): Record<TaskStatus, TareaConOrigen[]> {
  const grupos: Record<TaskStatus, TareaConOrigen[]> = { pendiente: [], en_progreso: [], completada: [], bloqueada: [] };
  for (const t of tareas) grupos[t.status].push(t);
  return grupos;
}

function dia(fecha: string): number {
  const [a, m, d] = fecha.split("-").map(Number);
  return Date.UTC(a, m - 1, d) / 86_400_000;
}

export interface BarraCronograma {
  tarea: TareaConOrigen;
  /** Porcentaje del eje, de 0 a 100. */
  izquierda: number;
  ancho: number;
}

export interface Cronograma {
  barras: BarraCronograma[];
  sinFecha: TareaConOrigen[];
  inicio: string | null;
  fin: string | null;
}

/** Una barra por tarea con inicio y fin; las demás van aparte, como «Sin fecha» (RM-22 R3). */
export function armarCronograma(tareas: TareaConOrigen[]): Cronograma {
  const conFechas = tareas
    .filter((t) => t.start_date && t.end_date)
    .sort((a, b) => (a.start_date as string).localeCompare(b.start_date as string) || a.id.localeCompare(b.id));
  const sinFecha = tareas.filter((t) => !(t.start_date && t.end_date));
  if (conFechas.length === 0) return { barras: [], sinFecha, inicio: null, fin: null };

  const desde = Math.min(...conFechas.map((t) => dia(t.start_date as string)));
  const hasta = Math.max(...conFechas.map((t) => Math.max(dia(t.end_date as string), dia(t.start_date as string))));
  const largo = Math.max(hasta - desde + 1, 1);
  const barras = conFechas.map((tarea) => {
    const ini = dia(tarea.start_date as string);
    const fin = Math.max(dia(tarea.end_date as string), ini);
    return { tarea, izquierda: ((ini - desde) / largo) * 100, ancho: ((fin - ini + 1) / largo) * 100 };
  });
  const iso = (d: number) => new Date(d * 86_400_000).toISOString().slice(0, 10);
  return { barras, sinFecha, inicio: iso(desde), fin: iso(hasta) };
}
