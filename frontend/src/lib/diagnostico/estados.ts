/**
 * Cliente de los estados del diagnóstico, el assessment actual (DIAG-12). El DPO emite un estado a
 * partir del diagnóstico real; los demás roles consultan. La suma y la comparación las calcula el
 * servidor (features/diagnostico/services/estados_engine.py). Sin cifra única de avance.
 */
import { fetchAutenticado } from "@/lib/auth";
import type { ComparativoDiagnostico } from "./comparativo";
import type { IndicadoresSellados } from "./indicadores";
import { ROL_QUE_SELLA, cabecerasComo, rolParaLeer } from "./roles";

const RUTA = "/api/v1/diagnostico/estados";

export interface EstadoDiagnostico {
  id: string;
  secuencia: number;
  emitido_por: string;
  fecha_corte: string;
  resultado_real_id: string;
  escala: string;
  tareas: { tarea_id: string; control_ref: string }[];
  indicadores: IndicadoresSellados;
  huella_anterior: string;
  huella: string;
}

export interface HistorialEstados {
  /** Del más reciente al más antiguo. */
  estados: EstadoDiagnostico[];
  cadena_integra: boolean;
  primer_alterado: string | null;
}

export type ComparacionEstado = "real" | "anterior";

export type ComparativoEstado = ComparativoDiagnostico & { con: ComparacionEstado };

/** Error de la API con el código de negocio del servidor, para mostrar un texto fijo por código. */
export class ErrorEstados extends Error {
  constructor(mensaje: string, readonly codigo: string | null) {
    super(mensaje);
  }
}

async function errorDe(respuesta: Response, porDefecto: string): Promise<ErrorEstados> {
  const cuerpo = (await respuesta.json().catch(() => null)) as { detail?: unknown; code?: unknown } | null;
  return new ErrorEstados(
    typeof cuerpo?.detail === "string" ? cuerpo.detail : porDefecto,
    typeof cuerpo?.code === "string" ? cuerpo.code : null
  );
}

export async function consultarEstados(): Promise<HistorialEstados> {
  const rol = await rolParaLeer();
  if (!rol) throw new Error("Tu rol no consulta los estados del diagnóstico.");
  const respuesta = await fetchAutenticado(RUTA, { method: "GET" }, cabecerasComo(rol));
  if (!respuesta.ok) throw await errorDe(respuesta, "No se pudieron leer los estados.");
  return (await respuesta.json()) as HistorialEstados;
}

export async function emitirEstado(): Promise<EstadoDiagnostico> {
  const respuesta = await fetchAutenticado(RUTA, { method: "POST" }, cabecerasComo(ROL_QUE_SELLA));
  if (!respuesta.ok) throw await errorDe(respuesta, "No se pudo emitir el estado.");
  return (await respuesta.json()) as EstadoDiagnostico;
}

export async function compararEstado(id: string, con: ComparacionEstado): Promise<ComparativoEstado> {
  const rol = await rolParaLeer();
  if (!rol) throw new Error("Tu rol no consulta los estados del diagnóstico.");
  const respuesta = await fetchAutenticado(
    `${RUTA}/${encodeURIComponent(id)}/comparativo?con=${con}`,
    { method: "GET" },
    cabecerasComo(rol)
  );
  if (!respuesta.ok) throw await errorDe(respuesta, "No se pudo comparar el estado.");
  return (await respuesta.json()) as ComparativoEstado;
}
