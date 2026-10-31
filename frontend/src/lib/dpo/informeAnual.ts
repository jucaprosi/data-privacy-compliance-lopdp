/**
 * Cliente HTTP tipado del informe anual del DPO y de la inscripción ante la SPDP (DPO-02).
 * Solo fetchAutenticado; la organización y la identidad las resuelve el servidor, no el cuerpo.
 */
import { cabecerasDeRol, cabecerasDeTenant, fetchAutenticado } from "@/lib/auth";

export interface ResumenInformeDpo {
  total_actuaciones: number;
  consultas_atendidas: number;
  dictamenes: number;
  escalamientos: number;
  con_acuse_de_direccion: number;
  sin_acuse_de_direccion: number;
}

export interface ActuacionInformeDpo {
  id: string;
  tipo: string;
  asunto: string;
  fecha_emision: string;
  acuse_recibo_alta_direccion: boolean;
}

export interface InscripcionResumenDpo {
  inscrito: boolean;
  fecha_inscripcion: string | null;
  numero_tramite: string | null;
}

export interface InformeAnualDpo {
  tenant_id: string;
  anio: number;
  generado_at: string;
  resumen: ResumenInformeDpo;
  actuaciones_por_tipo: Record<string, number>;
  actuaciones: ActuacionInformeDpo[];
  inscripcion_spdp: InscripcionResumenDpo | null;
  cadena: {
    huella: string;
    integra: boolean;
    dictamen_alterado: string | null;
    total_en_cadena: number;
  };
}

export interface InscripcionSpdp {
  id: string;
  inscrito: boolean;
  fecha_inscripcion: string | null;
  numero_tramite: string | null;
  registrado_por: string;
  registrado_at: string | null;
}

export interface InscripcionesSpdp {
  tenant_id: string;
  vigente: InscripcionSpdp | null;
  historial: InscripcionSpdp[];
}

export interface RegistrarInscripcionPayload {
  inscrito: boolean;
  fecha_inscripcion?: string | null;
  numero_tramite?: string | null;
}

function cabeceras(rol?: string, userId?: string): Record<string, string> {
  return {
    "Content-Type": "application/json",
    ...(rol ? cabecerasDeRol(rol, userId || "") : cabecerasDeTenant()),
  };
}

async function extraerError(res: Response, porDefecto: string): Promise<Error> {
  const cuerpo = (await res.json().catch(() => null)) as { detail?: unknown } | null;
  const detalle =
    typeof cuerpo?.detail === "string" ? cuerpo.detail : res.statusText || porDefecto;
  return new Error(`HTTP ${res.status}: ${detalle}`);
}

/** Genera el informe del año (solo el rol dpo; el servidor responde 403 a los demás). */
export async function generarInformeAnualDpo(
  anio: number,
  rol = "dpo",
  userId?: string,
): Promise<InformeAnualDpo> {
  const res = await fetchAutenticado("/api/v1/dpo/informe-anual", {
    method: "POST",
    headers: cabeceras(rol, userId),
    body: JSON.stringify({ anio }),
  });
  if (!res.ok) throw await extraerError(res, "No se pudo generar el informe anual.");
  return (await res.json()) as InformeAnualDpo;
}

/** Consulta el informe del año (cualquier rol con membresía activa). */
export async function consultarInformeAnualDpo(
  anio: number,
  rol?: string,
  userId?: string,
): Promise<InformeAnualDpo> {
  const res = await fetchAutenticado(`/api/v1/dpo/informe-anual?anio=${encodeURIComponent(String(anio))}`, {
    method: "GET",
    headers: cabeceras(rol, userId),
  });
  if (!res.ok) throw await extraerError(res, "No se pudo consultar el informe anual.");
  return (await res.json()) as InformeAnualDpo;
}

/** Descarga el documento del informe (la huella de la cadena va en su pie). */
export async function descargarInformeAnualDpo(
  anio: number,
  rol?: string,
  userId?: string,
): Promise<{ nombre: string; contenido: Blob }> {
  const res = await fetchAutenticado(
    `/api/v1/dpo/informe-anual/documento?anio=${encodeURIComponent(String(anio))}`,
    { method: "GET", headers: cabeceras(rol, userId) },
  );
  if (!res.ok) throw await extraerError(res, "No se pudo descargar el informe anual.");
  return { nombre: `informe-dpo-${anio}.md`, contenido: await res.blob() };
}

export async function consultarInscripcionSpdp(
  rol?: string,
  userId?: string,
): Promise<InscripcionesSpdp> {
  const res = await fetchAutenticado("/api/v1/dpo/inscripcion", {
    method: "GET",
    headers: cabeceras(rol, userId),
  });
  if (!res.ok) throw await extraerError(res, "No se pudo consultar la inscripción ante la SPDP.");
  return (await res.json()) as InscripcionesSpdp;
}

export async function registrarInscripcionSpdp(
  payload: RegistrarInscripcionPayload,
  rol = "admin_organizacion",
  userId?: string,
): Promise<InscripcionSpdp> {
  const res = await fetchAutenticado("/api/v1/dpo/inscripcion", {
    method: "POST",
    headers: cabeceras(rol, userId),
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw await extraerError(res, "No se pudo registrar la inscripción.");
  return (await res.json()) as InscripcionSpdp;
}
