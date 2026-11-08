/**
 * Cliente de las respuestas del diagnóstico guardadas en el servidor (DIAG-01).
 *
 * Usa requestJson, que añade la identidad de la sesión (cabeceras en modo headers, token en
 * oidc). El servidor es la fuente de verdad; el store solo guarda una caché local.
 *
 * DIAG-03: solo el DPO responde; los demás roles consultan. Cada llamada declara el rol con el que
 * se actúa (roles.ts) y el servidor lo verifica.
 *
 * DIAG-05: «no aplica» viaja con su justificación; sin una de al menos 10 caracteres no se envía
 * (el servidor la rechazaría con 422). El autor no se envía: lo fija el servidor desde el token.
 */
import { leerSesion, modoAutenticacion } from "@/lib/auth";
import { requestJson } from "@/lib/roadmap/cliente";
import { ROL_QUE_SELLA, puedeSellar, rolParaLeer, rolesDelUsuario } from "./roles";
import { estadoDerivado } from "./escala";
import type { DimensionId } from "@/lib/dimensionesSGPDP";
import type { EstadoCumplimiento, RespuestaItemStore } from "@/store/useAuditStore";

export interface RespuestaServidor {
  pregunta_id: number;
  control: string;
  dimension: string;
  /** Entrada: nivel asignado SMARTCIDI 1 a 5 (null = pendiente). */
  nivel_asignado: number | null;
  /** Dato derivado: lo devuelve el servidor y no se envía (DIAG-08 R3). */
  estado?: EstadoCumplimiento;
  nivel_evidencia: number;
  criticidad: number;
  es_critica: boolean;
  riesgo_base: number;
  no_aplica?: boolean;
  justificacion_no_aplica?: string | null;
  /** Dato del servidor: quién justificó el «no aplica»; nunca se envía. */
  justificado_por?: string | null;
}

/** Campos de «no aplica» que acompañan a una respuesta del store (DIAG-05). */
export interface JustificacionNoAplica {
  noAplica?: boolean;
  justificacionNoAplica?: string | null;
  justificadoPor?: string | null;
}

export const LONGITUD_MINIMA_JUSTIFICACION = 10;

export function justificacionSuficiente(texto: string | null | undefined): boolean {
  return (texto ?? "").trim().length >= LONGITUD_MINIMA_JUSTIFICACION;
}

const RUTA = "/diagnostico/respuestas";

/**
 * Solo se envían las respuestas propias con control y dimensión: las de referencia nunca.
 * `control` es el nombre del control del banco de preguntas; el banco no trae código P1-P73.
 */
export function aServidor(respuesta: RespuestaItemStore): RespuestaServidor | null {
  // Sin nivel asignado no hay nada que enviar: la pregunta sigue pendiente (DIAG-09 R5).
  if (respuesta.esReferencia || !respuesta.control || !respuesta.dimensionId) return null;
  if (respuesta.nivelAsignado == null) return null;
  const { noAplica, justificacionNoAplica } = respuesta as RespuestaItemStore & JustificacionNoAplica;
  // Un «no aplica» sin justificación suficiente se queda en el navegador hasta completarla.
  if (noAplica && !justificacionSuficiente(justificacionNoAplica)) return null;
  return {
    pregunta_id: respuesta.preguntaId,
    control: respuesta.control,
    dimension: respuesta.dimensionId,
    nivel_asignado: respuesta.nivelAsignado,
    nivel_evidencia: respuesta.evidenciaNivel,
    criticidad: respuesta.criticidad ?? (respuesta.esCritica ? 5 : 3),
    es_critica: respuesta.esCritica,
    riesgo_base: respuesta.riesgoBase,
    no_aplica: Boolean(noAplica),
    justificacion_no_aplica: noAplica ? (justificacionNoAplica ?? "").trim() : null,
  };
}

export function desdeServidor(fila: RespuestaServidor): RespuestaItemStore & JustificacionNoAplica {
  return {
    preguntaId: fila.pregunta_id,
    nivelAsignado: fila.nivel_asignado ?? null,
    cumple: fila.estado ?? estadoDerivado(fila.nivel_asignado),
    evidenciaNivel: fila.nivel_evidencia,
    esCritica: fila.es_critica,
    riesgoBase: fila.riesgo_base,
    criticidad: fila.criticidad,
    control: fila.control,
    dimensionId: fila.dimension as DimensionId,
    esReferencia: false,
    noAplica: Boolean(fila.no_aplica),
    justificacionNoAplica: fila.justificacion_no_aplica ?? null,
    justificadoPor: fila.justificado_por ?? null,
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
