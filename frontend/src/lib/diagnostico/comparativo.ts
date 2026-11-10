/**
 * Cliente del comparativo del diagnóstico de prueba con el real (DIAG-06). Solo lectura: la
 * comparación la calcula el servidor (features/diagnostico/services/comparativo_engine.py).
 * Sin cifra única: cada dimensión se compara con la suya.
 */
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasComo, rolParaLeer } from "./roles";

const RUTA = "/api/v1/diagnostico/comparativo";

export interface SelloResumen {
  id: string;
  tipo: "prueba" | "real";
  sellado_en: string;
}

export interface ControlBrecha {
  pregunta_id: number;
  control: string;
  dimension: string;
  criticidad: number;
}

export interface FilaDimension {
  dimension: string;
  nombre: string;
  nivel_base: number | null;
  nivel_actual: number | null;
  diferencia_nivel: number | null;
  cerradas: number;
  nuevas: number;
  siguen: number;
}

export interface ComparativoDiagnostico {
  comparable: boolean;
  motivo: string | null;
  codigo_motivo?: "sin_real" | "sin_sellos" | null;
  linea_base: SelloResumen | null;
  actual: SelloResumen | null;
  por_dimension: FilaDimension[];
  brechas: { cerradas: ControlBrecha[]; nuevas: ControlBrecha[]; siguen: ControlBrecha[] };
}

export function tendencia(diferencia: number | null): "mejora" | "empeora" | "igual" | "sin_dato" {
  if (diferencia === null) return "sin_dato";
  return diferencia > 0 ? "mejora" : diferencia < 0 ? "empeora" : "igual";
}

export async function consultarComparativo(): Promise<ComparativoDiagnostico> {
  const rol = await rolParaLeer();
  if (!rol) throw new Error("Tu rol no consulta el comparativo del diagnóstico.");
  const respuesta = await fetchAutenticado(RUTA, { method: "GET" }, cabecerasComo(rol));
  if (!respuesta.ok) {
    const cuerpo = (await respuesta.json().catch(() => null)) as { detail?: unknown } | null;
    throw new Error(typeof cuerpo?.detail === "string" ? cuerpo.detail : "No se pudo leer el comparativo.");
  }
  return (await respuesta.json()) as ComparativoDiagnostico;
}
