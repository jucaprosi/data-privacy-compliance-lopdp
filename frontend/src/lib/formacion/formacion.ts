// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤evidencias ¤rbac-tenant
/**
 * Biblioteca de cliente para la sala Formación (FOR-01).
 */
import { fetchAutenticado } from "@/lib/auth";

export interface ContenidoFormativo {
  id: string;
  tenant_id: string;
  titulo: string;
  tipo: "pdf" | "video";
  referencia: string;
  creado_por: string;
  creado_en: string;
}

export interface PreguntaFormativa {
  id: string;
  orden: number;
  enunciado: string;
  opciones: string[];
  correcta?: number;
}

export interface AccionFormativa {
  id: string;
  tenant_id: string;
  contenido_id: string;
  nombre: string;
  inicio: string;
  fin: string;
  nota_minima: number;
  creado_por: string;
  total_participantes: number;
  terminados: number;
}

export interface ParticipanteAccion {
  id: string;
  persona_id: string;
  enviado_en: string;
  iniciado_en: string | null;
  terminado_en: string | null;
  nota: number | null;
  diploma_sha256: string | null;
}

export interface ExamenDetalle {
  accion: string;
  nota_minima: number;
  inicio: string;
  fin: string;
  iniciado_en: string | null;
  terminado_en: string | null;
  preguntas: PreguntaFormativa[];
}

export interface ExamenResultado {
  nota: number;
  aprobado: boolean;
  diploma_sha256?: string | null;
}

export interface CoberturaDatos {
  formadas: number;
  obligadas: number;
  cobertura: number;
}

export interface MiParticipacion {
  id: string;
  accion_id: string;
  accion_nombre: string;
  inicio: string;
  fin: string;
  nota_minima: number;
  enviado_en: string;
  iniciado_en: string | null;
  terminado_en: string | null;
  nota: number | null;
  diploma_sha256: string | null;
}

// 1. Contenidos
export async function listarContenidos(): Promise<ContenidoFormativo[]> {
  const res = await fetchAutenticado("/api/v1/formacion/contenidos", { method: "GET" });
  if (!res.ok) throw new Error("No pudimos cargar los contenidos formativos.");
  return res.json();
}

export async function crearContenido(payload: {
  titulo: string;
  tipo: "pdf" | "video";
  referencia: string;
}): Promise<ContenidoFormativo> {
  const res = await fetchAutenticado("/api/v1/formacion/contenidos", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("No pudimos crear el contenido formativo.");
  return res.json();
}

export async function listarPreguntas(contenidoId: string): Promise<PreguntaFormativa[]> {
  const res = await fetchAutenticado(`/api/v1/formacion/contenidos/${encodeURIComponent(contenidoId)}/preguntas`, {
    method: "GET",
  });
  if (!res.ok) throw new Error("No pudimos cargar las preguntas del contenido.");
  return res.json();
}

export async function crearPregunta(
  contenidoId: string,
  payload: { enunciado: string; opciones: string[]; correcta: number }
): Promise<PreguntaFormativa> {
  const res = await fetchAutenticado(`/api/v1/formacion/contenidos/${encodeURIComponent(contenidoId)}/preguntas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({}));
    if (res.status === 409 && errorJson.code === "PREGUNTAS_CONGELADAS") {
      throw new Error("El banco de preguntas se encuentra congelado porque ya existen participaciones iniciadas.");
    }
    throw new Error("No pudimos guardar la pregunta.");
  }
  return res.json();
}

// 2. Acciones
export async function listarAcciones(): Promise<AccionFormativa[]> {
  const res = await fetchAutenticado("/api/v1/formacion/acciones", { method: "GET" });
  if (!res.ok) throw new Error("No pudimos cargar las acciones formativas.");
  return res.json();
}

export async function crearAccion(payload: {
  contenido_id: string;
  nombre: string;
  inicio: string;
  fin: string;
  nota_minima: number;
}): Promise<AccionFormativa> {
  const res = await fetchAutenticado("/api/v1/formacion/acciones", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("No pudimos crear la acción formativa.");
  return res.json();
}

export async function listarParticipantesAccion(accionId: string): Promise<ParticipanteAccion[]> {
  const res = await fetchAutenticado(`/api/v1/formacion/acciones/${encodeURIComponent(accionId)}/participantes`, {
    method: "GET",
  });
  if (!res.ok) throw new Error("No pudimos cargar los participantes de la acción.");
  return res.json();
}

export async function anadirParticipantes(accionId: string, personaIds: string[]): Promise<void> {
  const res = await fetchAutenticado(`/api/v1/formacion/acciones/${encodeURIComponent(accionId)}/participantes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ persona_ids: personaIds }),
  });
  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({}));
    if (res.status === 409 && errorJson.code === "CONTENIDO_SIN_PREGUNTAS") {
      throw new Error("El contenido formativo no cuenta con preguntas en su banco de evaluación.");
    }
    throw new Error("No pudimos añadir los participantes.");
  }
}

// 3. Examen participante
export async function obtenerExamen(participacionId: string): Promise<ExamenDetalle> {
  const res = await fetchAutenticado(`/api/v1/formacion/participaciones/${encodeURIComponent(participacionId)}/examen`, {
    method: "GET",
  });
  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({}));
    if (res.status === 403 && errorJson.code === "PERSONA_NO_VINCULADA") {
      throw new Error("Tu correo no está registrado en el inventario de personas. Pide al administrador de tu organización que lo registre.");
    }
    throw new Error("No pudimos cargar la evaluación.");
  }
  return res.json();
}

export async function iniciarExamen(participacionId: string): Promise<{ iniciado_en: string }> {
  const res = await fetchAutenticado(`/api/v1/formacion/participaciones/${encodeURIComponent(participacionId)}/iniciar`, {
    method: "POST",
  });
  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({}));
    if (res.status === 409) {
      if (errorJson.code === "ACCION_FUERA_DE_FECHAS") {
        throw new Error("Esta formación se puede rendir solo dentro de las fechas programadas.");
      }
      if (errorJson.code === "EXAMEN_YA_RENDIDO") {
        throw new Error("Ya rendiste este examen.");
      }
    }
    throw new Error("No pudimos iniciar el examen. Inténtalo de nuevo.");
  }
  return res.json();
}

export async function enviarExamen(
  participacionId: string,
  respuestas: number[]
): Promise<ExamenResultado> {
  const res = await fetchAutenticado(`/api/v1/formacion/participaciones/${encodeURIComponent(participacionId)}/examen`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ respuestas }),
  });
  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({}));
    if (res.status === 409 && errorJson.code === "EXAMEN_YA_RENDIDO") {
      throw new Error("Ya rendiste este examen.");
    }
    if (res.status === 422 && errorJson.code === "RESPUESTAS_INCOMPLETAS") {
      throw new Error("Debes responder todas las preguntas.");
    }
    throw new Error("No pudimos enviar tus respuestas. Inténtalo de nuevo. Tu intento no se ha consumido.");
  }
  return res.json();
}

// 4. Mis participaciones
export async function listarMisParticipaciones(): Promise<MiParticipacion[]> {
  const res = await fetchAutenticado("/api/v1/formacion/mis-participaciones", { method: "GET" });
  if (!res.ok) return [];
  return res.json();
}

// 5. Cobertura
export async function obtenerCobertura(): Promise<CoberturaDatos> {
  const res = await fetchAutenticado("/api/v1/formacion/cobertura", { method: "GET" });
  if (!res.ok) throw new Error("No pudimos cargar la cobertura.");
  return res.json();
}
