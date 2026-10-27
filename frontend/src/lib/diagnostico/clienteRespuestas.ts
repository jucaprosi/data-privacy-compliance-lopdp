/**
 * Cliente de las respuestas del diagnóstico guardadas en el servidor (DIAG-01).
 *
 * Usa requestJson, que añade la identidad de la sesión (cabeceras en modo headers, token en
 * oidc). El servidor es la fuente de verdad; el store solo guarda una caché local.
 *
 * DIAG-03: solo el DPO responde; los demás roles consultan. Cada llamada declara el rol con el que
 * se actúa (roles.ts) y el servidor lo verifica.
 */
import { leerSesion, modoAutenticacion } from "@/lib/auth";
import { requestJson } from "@/lib/roadmap/cliente";
import { ROL_QUE_SELLA, puedeSellar, rolParaLeer, rolesDelUsuario } from "./roles";
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

/**
 * Hay identidad con la que llamar a la API: en modo headers siempre (desarrollo); en oidc, solo con
 * una sesión de Google vigente. Sin sesión no se llama a la API (FE-07: el panel lleva a /login).
 */
export function hayIdentidadParaApi(): boolean {
  return modoAutenticacion() === "headers" || leerSesion() !== null;
}

export async function cargarRespuestas(): Promise<RespuestaServidor[]> {
  const rol = await rolParaLeer();
  if (!rol) throw new Error("Tu rol no consulta el diagnóstico de la organización.");
  return (await requestJson<{ respuestas: RespuestaServidor[] }>(RUTA, { headers: { "X-Role": rol } }))
    .respuestas;
}

/** Solo el DPO responde: con otro rol no se envía nada y se explica por qué. */
export async function guardarRespuestas(respuestas: RespuestaServidor[]): Promise<RespuestaServidor[]> {
  if (!puedeSellar(await rolesDelUsuario())) {
    throw new Error("Solo el DPO responde el diagnóstico; tus respuestas no se guardan en el servidor.");
  }
  return (await requestJson<{ respuestas: RespuestaServidor[] }>(RUTA, {
    method: "PUT",
    headers: { "X-Role": ROL_QUE_SELLA },
    body: JSON.stringify({ respuestas }),
  })).respuestas;
}
