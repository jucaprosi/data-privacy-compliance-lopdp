/**
 * Objeciones del DPO a las respuestas del diagnóstico y datos de la revisión (DIAG-07).
 *
 * El DPO objeta una respuesta con un motivo; la objeción queda abierta hasta que quien respondió
 * vuelve a guardar la pregunta. Con objeciones abiertas no se sella. Los errores se muestran con
 * textos fijos por código: nunca el texto del servidor.
 */
import { fetchAutenticado } from "@/lib/auth";
import { ROL_QUE_SELLA, cabecerasComo, rolParaLeer } from "./roles";

const RUTA_OBJECIONES = "/api/v1/diagnostico/objeciones";
const RUTA_REVISION = "/api/v1/diagnostico/revision";

export const LONGITUD_MINIMA_MOTIVO = 20;

export interface Objecion {
  id: string;
  pregunta_id: number;
  motivo: string;
  objetado_por: string;
  objetado_en: string;
  resuelta_en: string | null;
}

/** Una fila de la grilla: lo declarado y el nivel de evidencia que calcula el servidor al sellar. */
export interface FilaRevision {
  pregunta_id: number;
  control: string;
  dimension: string;
  estado: string;
  nivel_asignado: number | null;
  nivel_evidencia: number;
  no_aplica: boolean;
  justificacion_no_aplica: string | null;
  con_documento: boolean;
  nivel_calculado: number;
}

const MENSAJES: Record<string, string> = {
  OBJECION_DUPLICADA: "Esa pregunta ya tiene una objeción abierta.",
  OBJECIONES_ABIERTAS: "Hay objeciones abiertas: no se puede sellar todavía.",
};

const MENSAJE_GENERICO = "No se pudo completar la operación. Inténtalo de nuevo.";

export function motivoSuficiente(motivo: string): boolean {
  return motivo.trim().length >= LONGITUD_MINIMA_MOTIVO;
}

export function abiertas(objeciones: readonly Objecion[]): Objecion[] {
  return objeciones.filter((o) => o.resuelta_en === null);
}

/** La objeción abierta de cada pregunta (solo hay una por pregunta). */
export function abiertaPorPregunta(objeciones: readonly Objecion[]): Map<number, Objecion> {
  return new Map(abiertas(objeciones).map((o) => [o.pregunta_id, o]));
}

/** Línea que explica por qué no se puede sellar; null si no hay objeciones abiertas. */
export function textoBloqueoSello(n: number): string | null {
  if (n <= 0) return null;
  if (n === 1) return "Hay 1 objeción abierta. Se resuelve cuando quien respondió vuelve a guardar la respuesta.";
  return `Hay ${n} objeciones abiertas. Se resuelven cuando quien respondió vuelve a guardar las respuestas.`;
}

async function errorDe(respuesta: Response): Promise<Error> {
  const cuerpo = (await respuesta.json().catch(() => null)) as { code?: unknown } | null;
  const codigo = typeof cuerpo?.code === "string" ? cuerpo.code : "";
  return new Error(MENSAJES[codigo] ?? MENSAJE_GENERICO);
}

export async function cargarObjeciones(soloAbiertas = false): Promise<Objecion[]> {
  const rol = await rolParaLeer();
  if (!rol) return [];
  const ruta = soloAbiertas ? `${RUTA_OBJECIONES}?abiertas=true` : RUTA_OBJECIONES;
  const respuesta = await fetchAutenticado(ruta, { method: "GET" }, cabecerasComo(rol));
  if (!respuesta.ok) throw await errorDe(respuesta);
  return ((await respuesta.json()) as { objeciones: Objecion[] }).objeciones;
}

export async function objetar(preguntaId: number, motivo: string): Promise<Objecion> {
  const respuesta = await fetchAutenticado(
    RUTA_OBJECIONES,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ pregunta_id: preguntaId, motivo: motivo.trim() }),
    },
    cabecerasComo(ROL_QUE_SELLA)
  );
  if (!respuesta.ok) throw await errorDe(respuesta);
  return (await respuesta.json()) as Objecion;
}

export async function cargarRevision(): Promise<FilaRevision[]> {
  const respuesta = await fetchAutenticado(RUTA_REVISION, { method: "GET" }, cabecerasComo(ROL_QUE_SELLA));
  if (!respuesta.ok) throw await errorDe(respuesta);
  return ((await respuesta.json()) as { filas: FilaRevision[] }).filas;
}
