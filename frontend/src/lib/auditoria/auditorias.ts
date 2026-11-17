// ¤auditoria-capa ¤hallazgos
/**
 * Cliente TypeScript para el módulo de Auditorías con Grilla y Actas por Área (CAPA-04).
 */
import { fetchAutenticado } from "@/lib/auth";

export interface AuditoriaFila {
  id: string;
  area_id: string;
  control_ref: string;
  declarado: number;
  riesgo_inicial: number;
  verificado: number | null;
  evidencia_sha256: string | null;
  riesgo_final: number | null;
  revisado_por: string | null;
  hallazgo_id: string | null;
}

export interface AuditoriaActa {
  id: string;
  area_id: string;
  evidencia_id: string;
  acta_sha256: string;
  firmada_por: string;
  firmada_en: string;
}

export interface AuditoriaDetalle {
  id: string;
  tenant_id: string;
  nombre: string;
  alcance: string[];
  equipo: string[];
  estado: "abierta" | "cerrada";
  creado_por: string;
  creado_en: string;
  cerrada_en: string | null;
  filas: AuditoriaFila[];
  actas: AuditoriaActa[];
}

export interface AuditoriaResumen {
  id: string;
  tenant_id: string;
  nombre: string;
  alcance: string[];
  equipo: string[];
  estado: "abierta" | "cerrada";
  creado_por: string;
  creado_en: string;
  cerrada_en: string | null;
  total_controles: number;
  verificados: number;
}

export interface ActaContenido {
  area_id: string;
  acta_sha256: string;
  contenido: string;
}

export interface CierrePendiente {
  id: string;
  titulo: string;
  control_ref: string;
  severidad: string;
  estado: string;
  task_id: string | null;
  task_title: string | null;
  task_owner: string | null;
  completed_at: string | null;
}

export async function listarAuditorias(): Promise<AuditoriaResumen[]> {
  const res = await fetchAutenticado("/api/v1/auditoria-capa/auditorias", { method: "GET" });
  if (!res.ok) {
    throw new Error("No pudimos cargar las auditorías. Inténtalo de nuevo.");
  }
  const datos: unknown = await res.json();
  if (!Array.isArray(datos)) {
    throw new Error("No pudimos cargar las auditorías. Inténtalo de nuevo.");
  }
  return datos as AuditoriaResumen[];
}

export async function obtenerAuditoria(id: string): Promise<AuditoriaDetalle> {
  const res = await fetchAutenticado(`/api/v1/auditoria-capa/auditorias/${encodeURIComponent(id)}`, { method: "GET" });
  if (!res.ok) {
    throw new Error("No pudimos cargar la auditoría.");
  }
  return res.json();
}

export async function crearAuditoria(payload: {
  nombre: string;
  alcance: string[];
  equipo: string[];
}): Promise<AuditoriaDetalle> {
  const res = await fetchAutenticado("/api/v1/auditoria-capa/auditorias", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({}));
    if (res.status === 404 && errorJson.code === "DIAG_SIN_RESULTADO") {
      throw new Error("Aún no hay un diagnóstico sellado. Sella el diagnóstico antes de crear una auditoría.");
    }
    throw new Error("No pudimos crear la auditoría. Inténtalo de nuevo.");
  }
  return res.json();
}

export async function actualizarFilaAuditoria(
  auditoriaId: string,
  controlRef: string,
  payload: {
    verificado: number;
    riesgo_final: number;
    evidencia_sha256?: string | null;
  }
): Promise<AuditoriaFila> {
  const res = await fetchAutenticado(
    `/api/v1/auditoria-capa/auditorias/${encodeURIComponent(auditoriaId)}/filas/${encodeURIComponent(controlRef)}`,
    {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({}));
    if (res.status === 403 && errorJson.code === "AUDITOR_EJECUTOR") {
      throw new Error("No puedes verificar este control porque participaste en su ejecución. Lo verifica otra persona del equipo.");
    }
    throw new Error("No pudimos guardar este control. Inténtalo de nuevo.");
  }
  return res.json();
}

export async function levantarYFirmarActa(
  auditoriaId: string,
  areaId: string
): Promise<{ area_id: string; acta_sha256: string }> {
  const res = await fetchAutenticado(
    `/api/v1/auditoria-capa/auditorias/${encodeURIComponent(auditoriaId)}/areas/${encodeURIComponent(areaId)}/acta`,
    { method: "POST" }
  );
  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({}));
    if (res.status === 409) {
      if (errorJson.code === "AUDITORIA_INCOMPLETA") {
        throw new Error("Aún hay controles de esta área sin verificar. Complétalos antes de firmar el acta.");
      }
      if (errorJson.code === "ACTA_YA_FIRMADA") {
        throw new Error("El acta de esta área ya está firmada.");
      }
    }
    throw new Error("No pudimos firmar el acta. Sigue sin firmar.");
  }
  return res.json();
}

export async function obtenerActa(auditoriaId: string, areaId: string): Promise<ActaContenido> {
  const res = await fetchAutenticado(
    `/api/v1/auditoria-capa/auditorias/${encodeURIComponent(auditoriaId)}/areas/${encodeURIComponent(areaId)}/acta`,
    { method: "GET" }
  );
  if (!res.ok) {
    if (res.status === 404) {
      throw new Error("No encontramos el acta de esta área.");
    }
    throw new Error("No pudimos cargar el acta.");
  }
  return res.json();
}

export interface VerificacionCierreResponse {
  id: string;
  hallazgo_id: string;
  resultado: string;
  motivo: string;
}

export async function verificarCierreHallazgo(
  hallazgoId: string,
  payload: { resultado: "conforme" | "no_conforme"; motivo: string }
): Promise<VerificacionCierreResponse> {
  const res = await fetchAutenticado(
    `/api/v1/auditoria-capa/hallazgos/${encodeURIComponent(hallazgoId)}/verificar-cierre`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }
  );
  if (!res.ok) {
    const errorJson = await res.json().catch(() => ({}));
    if (res.status === 403 && errorJson.code === "AUDITOR_EJECUTOR") {
      throw new Error("No puedes verificar este control porque participaste en su ejecución. Lo verifica otra persona del equipo.");
    }
    if (res.status === 409 && errorJson.code === "ACCION_NO_CERRADA") {
      throw new Error(errorJson.detail || "La acción vinculada al hallazgo no ha sido completada o no tiene evidencia aprobada.");
    }
    throw new Error("No pudimos guardar la verificación. Inténtalo de nuevo.");
  }
  return res.json();
}

export async function listarCierresPendientes(): Promise<CierrePendiente[]> {
  const res = await fetchAutenticado("/api/v1/auditoria-capa/cierres-pendientes", { method: "GET" });
  if (!res.ok) {
    throw new Error("No pudimos cargar los cierres pendientes.");
  }
  return res.json();
}
