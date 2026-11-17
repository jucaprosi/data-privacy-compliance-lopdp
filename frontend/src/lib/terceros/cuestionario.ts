/**
 * Cliente de la API para Cuestionario de Garantías de Encargados (TER-02).
 */
import { fetchAutenticado } from "@/lib/auth";

export interface PreguntaCuestionario {
  id: string;
  enunciado: string;
  tipo: "si_no" | "si_no_evidencia" | "texto" | "fecha" | "texto_evidencia";
  obligatoria: boolean;
  cita: string;
  condicional?: string | null;
}

export interface CuestionarioResumen {
  id: string;
  tercero_id: string;
  version_cuestionario: string;
  estado: "enviado" | "respondido" | "conforme" | "correccion" | "rechazado";
  caduca_en?: string | null;
  proxima_revision?: string | null;
  creado_en?: string | null;
  revisado_en?: string | null;
  comentario_revision?: string | null;
  informe_sha256?: string | null;
}

export interface CuestionarioPublicoInfo {
  id: string;
  tenant_id: string;
  organizacion: string;
  caduca_en: string;
  version_cuestionario: string;
  preguntas: PreguntaCuestionario[];
}

export interface RevisionPayload {
  decision: "conforme" | "correccion" | "rechazado";
  comentario?: string | null;
  proxima_revision?: string | null;
}

const API_BASE = "/api/v1";

export async function crearEnlaceCuestionario(
  terceroId: string,
  diasVigencia: number = 7,
): Promise<{ id: string; url: string; caduca_en: string; token?: string }> {
  const res = await fetchAutenticado(`${API_BASE}/terceros/${encodeURIComponent(terceroId)}/cuestionarios`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ dias_vigencia: diasVigencia }),
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.detail || "No pudimos crear el enlace. Inténtalo de nuevo.");
  }
  return await res.json();
}

export async function listarCuestionariosTercero(terceroId: string): Promise<CuestionarioResumen[]> {
  const res = await fetchAutenticado(`${API_BASE}/terceros/${encodeURIComponent(terceroId)}/cuestionarios`);
  if (!res.ok) {
    throw new Error("No pudimos cargar los cuestionarios.");
  }
  return await res.json();
}

export async function revisarCuestionario(
  cuestionarioId: string,
  payload: RevisionPayload,
): Promise<{ estado: string; informe_sha256?: string; url_nueva?: string }> {
  const res = await fetchAutenticado(`${API_BASE}/terceros/cuestionarios/${encodeURIComponent(cuestionarioId)}/revision`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.detail || "No pudimos guardar la revisión. Inténtalo de nuevo.");
  }
  return await res.json();
}

// Métodos públicos (sin autenticación)
export async function obtenerCuestionarioPublico(token: string): Promise<CuestionarioPublicoInfo> {
  const res = await fetch(`${API_BASE}/publico/proveedor/${encodeURIComponent(token)}`);
  if (!res.ok) {
    throw new Error(res.status === 404 || res.status === 410 ? "CODIGO_ENLACE_NO_VALIDO" : `HTTP_${res.status}`);
  }
  return await res.json();
}

export async function enviarRespuestasPublico(
  token: string,
  respuestas: Record<string, unknown>,
  archivos: { pregunta_id: string; file: File }[],
): Promise<{ estado: string }> {
  const formData = new FormData();
  formData.append("respuestas", JSON.stringify(respuestas));
  for (const a of archivos) {
    formData.append("archivos", a.file, `${a.pregunta_id}_${a.file.name}`);
  }

  const res = await fetch(`${API_BASE}/publico/proveedor/${encodeURIComponent(token)}`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const cuerpo = await res.json().catch(() => null);
    throw new Error(cuerpo?.detail || "No pudimos enviar tus respuestas. Tus datos siguen en esta página; inténtalo de nuevo.");
  }
  return await res.json();
}
