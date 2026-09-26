import { sanitizarTextoDLP } from "@/lib/dlp";
import type { ConsultaCopiloto, EstadoCopiloto, FundamentoCopiloto, RespuestaCopiloto } from "@/types/copilot";

/** The browser never sends company names, documents or credentials. */
export function sanearCopiloto<T>(value: T): T {
  if (typeof value === "string") return sanitizarTextoDLP(value).textoSanitizado as T;
  if (Array.isArray(value)) return value.map(sanearCopiloto) as T;
  if (value && typeof value === "object") {
    return Object.fromEntries(Object.entries(value).map(([key, item]) => [key, sanearCopiloto(item)])) as T;
  }
  return value;
}

export function fuenteConsultable(fuente: FundamentoCopiloto): boolean {
  try {
    const url = new URL(fuente.url);
    return url.protocol === "https:" && /(^|\.)gob\.ec$/.test(url.hostname) &&
      Boolean(fuente.articulo && fuente.titulo && fuente.version);
  } catch { return false; }
}

export function respuestaVerificable(value: unknown): value is RespuestaCopiloto {
  if (!value || typeof value !== "object") return false;
  const r = value as RespuestaCopiloto;
  if (typeof r.respuesta !== "string" || !r.corpus_version || r.dlp_aplicado !== true ||
      !["local", "deepseek", "sin_fuente"].includes(r.modo) ||
      !Array.isArray(r.fundamentos) || !Array.isArray(r.planes) || !Array.isArray(r.advertencias)) return false;
  if (r.modo === "sin_fuente") return r.planes.length === 0;
  return r.fundamentos.length > 0 && r.fundamentos.every(fuenteConsultable) &&
    r.planes.every((p) => Number.isInteger(p.pregunta_id) && Array.isArray(p.pasos) &&
      Array.isArray(p.evidencias) && typeof p.responsable_sugerido === "string" &&
      typeof p.criterio_cierre === "string" && typeof p.seguimiento === "string" &&
      Array.isArray(p.fundamento) && p.fundamento.length > 0 && p.fundamento.every(fuenteConsultable));
}

export async function consultarCopiloto(consulta: ConsultaCopiloto, signal?: AbortSignal): Promise<RespuestaCopiloto> {
  const response = await fetch("/api/ai-copilot/consulta", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify(sanearCopiloto(consulta)), signal,
  });
  if (!response.ok) throw new Error("No se pudo consultar el asistente. Comprueba que el servicio esté disponible y vuelve a intentar.");
  const data: unknown = await response.json();
  if (!respuestaVerificable(data)) throw new Error("La respuesta no incluye fuentes verificables o protección DLP. No se mostrará como orientación jurídica.");
  return sanearCopiloto(data);
}

export async function estadoCopiloto(signal?: AbortSignal): Promise<EstadoCopiloto> {
  const response = await fetch("/api/ai-copilot/estado", { signal, cache: "no-store" });
  if (!response.ok) throw new Error("Servicio no disponible");
  return response.json();
}
