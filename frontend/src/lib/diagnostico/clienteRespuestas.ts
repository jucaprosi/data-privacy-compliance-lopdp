/**
 * Cliente de las respuestas del diagnóstico guardadas en el servidor (DIAG-01).
 *
 * Usa requestJson, que añade la identidad de la sesión (cabeceras en modo headers, token en
 * oidc). El servidor es la fuente de verdad; el store solo guarda una caché local.
 */
import { requestJson } from "@/lib/roadmap/cliente";
import type { DimensionId } from "@/lib/dimensionesSGPDP";
import type { EstadoCumplimiento, RespuestaItemStore } from "@/store/useAuditStore";

export interface RespuestaServidor {
  pregunta_id: number;
  control: string;
  dimension: string;
  estado: EstadoCumplimiento;
  nivel_evidencia: number;
  criticidad: number;
  es_critica: boolean;
  riesgo_base: number;
}

const RUTA = "/diagnostico/respuestas";

/**
 * Solo se envían las respuestas propias con control y dimensión: las de referencia nunca.
 * `control` es el nombre del control del banco de preguntas; el banco no trae código P1-P73.
 */
export function aServidor(respuesta: RespuestaItemStore): RespuestaServidor | null {
  if (respuesta.esReferencia || !respuesta.control || !respuesta.dimensionId) return null;
  return {
    pregunta_id: respuesta.preguntaId,
    control: respuesta.control,
    dimension: respuesta.dimensionId,
    estado: respuesta.cumple,
    nivel_evidencia: respuesta.evidenciaNivel,
    criticidad: respuesta.criticidad ?? (respuesta.esCritica ? 5 : 3),
    es_critica: respuesta.esCritica,
    riesgo_base: respuesta.riesgoBase,
  };
}

export function desdeServidor(fila: RespuestaServidor): RespuestaItemStore {
  return {
    preguntaId: fila.pregunta_id,
    cumple: fila.estado,
    evidenciaNivel: fila.nivel_evidencia,
    esCritica: fila.es_critica,
    riesgoBase: fila.riesgo_base,
    criticidad: fila.criticidad,
    control: fila.control,
    dimensionId: fila.dimension as DimensionId,
    esReferencia: false,
  };
}

export async function cargarRespuestas(): Promise<RespuestaServidor[]> {
  return (await requestJson<{ respuestas: RespuestaServidor[] }>(RUTA)).respuestas;
}

export async function guardarRespuestas(respuestas: RespuestaServidor[]): Promise<RespuestaServidor[]> {
  return (await requestJson<{ respuestas: RespuestaServidor[] }>(RUTA, {
    method: "PUT",
    body: JSON.stringify({ respuestas }),
  })).respuestas;
}
