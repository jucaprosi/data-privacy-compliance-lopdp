/**
 * Cliente del resultado sellado del diagnóstico (DIAG-03).
 *
 * El DPO sella; el servidor usa las respuestas que tiene guardadas y su propio cálculo. Lo único
 * que se envía es el perfil de operación de la ficha, que el DPO confirma al sellar. El historial
 * lo consultan el DPO, el implementador, el coordinador y el administrador.
 */
import { fetchAutenticado } from "@/lib/auth";
import type { PerfilOperacion } from "@/lib/bancoPreguntas";
import type { IndicadoresSellados } from "./indicadores";
import { ROL_QUE_SELLA, cabecerasComo, rolParaLeer } from "./roles";

const RUTA = "/api/v1/diagnostico/resultados";

export interface RespuestaSellada {
  pregunta_id: number;
  control: string;
  dimension: string;
  estado: string;
  criticidad: number;
  nivel_declarado: number;
  nivel_sellado: number;
  con_documento: boolean;
}

export interface ResultadoSellado {
  id: string;
  secuencia: number;
  sellado_por: string;
  sellado_en: string;
  normativa: string;
  version_normativa: string;
  tamano: string;
  perfil: Partial<PerfilOperacion>;
  respuestas: RespuestaSellada[];
  indicadores: IndicadoresSellados;
  huella_anterior: string;
  huella: string;
}

export interface HistorialResultados {
  /** Del más reciente al más antiguo. */
  resultados: ResultadoSellado[];
  cadena_integra: boolean;
  primer_alterado: string | null;
  dpo_vigente: boolean;
}

async function errorDe(respuesta: Response, porDefecto: string): Promise<Error> {
  const cuerpo = (await respuesta.json().catch(() => null)) as { detail?: unknown } | null;
  const detalle = typeof cuerpo?.detail === "string" ? cuerpo.detail : porDefecto;
  return new Error(detalle);
}

export async function sellarDiagnostico(perfil: PerfilOperacion | undefined): Promise<ResultadoSellado> {
  const respuesta = await fetchAutenticado(
    RUTA,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ perfil: perfil ?? {} }),
    },
    cabecerasComo(ROL_QUE_SELLA)
  );
  if (!respuesta.ok) throw await errorDe(respuesta, "No se pudo sellar el diagnóstico.");
  return (await respuesta.json()) as ResultadoSellado;
}

export async function consultarHistorial(): Promise<HistorialResultados> {
  const rol = await rolParaLeer();
  if (!rol) throw new Error("Tu rol no consulta los resultados del diagnóstico.");
  const respuesta = await fetchAutenticado(RUTA, { method: "GET" }, cabecerasComo(rol));
  if (!respuesta.ok) throw await errorDe(respuesta, "No se pudo leer el historial de resultados.");
  return (await respuesta.json()) as HistorialResultados;
}
