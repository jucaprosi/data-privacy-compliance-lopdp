/**
 * Cliente para los endpoints de aceptación (FIRMA-02).
 * Las rutas autenticadas usan fetchAutenticado; la ruta pública usa fetch nativo.
 */
import { fetchAutenticado } from "@/lib/auth";

const API = "/api/v1";

export interface InfoAceptacion {
  nombre_documento: string;
  organizacion: string;
  sha256: string;
}

export interface ResultadoAceptar {
  acuse_sha256: string;
}

export interface EnlaceGenerado {
  persona_id: string;
  url: string;
}

export interface SolicitudEnlaces {
  documento_id: string;
  persona_ids: string[];
  dias_vigencia: number;
}

export interface ItemAceptacion {
  id: string;
  documento_id: string;
  documento_sha256: string;
  persona_id: string;
  nombre: string;
  email: string;
  caduca_en: string;
  aceptado_en: string | null;
  ip: string | null;
  acuse_sha256: string | null;
  creado_en: string;
}

export interface ResultadoVerificar {
  coincide: boolean;
  tipo: "documento" | "acuse" | null;
}

export class ErrorAceptacion extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly code?: string,
  ) {
    super(message);
    this.name = "ErrorAceptacion";
  }
}

async function _parseError(res: Response): Promise<ErrorAceptacion> {
  const cuerpo = await res.json().catch(() => null);
  const detail = typeof cuerpo?.detail === "string" ? cuerpo.detail : res.statusText;
  return new ErrorAceptacion(detail, res.status, cuerpo?.code);
}

/** Información pública del enlace — sin autenticación. */
export async function obtenerInfoPublica(token: string): Promise<InfoAceptacion> {
  const res = await fetch(`${API}/aceptar/${token}`);
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** Acepta el enlace — sin autenticación. */
export async function aceptarEnlace(token: string): Promise<ResultadoAceptar> {
  const res = await fetch(`${API}/aceptar/${token}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ acepto: true }),
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}

/** Crea enlaces de aceptación — requiere autenticación. */
export async function crearEnlaces(solicitud: SolicitudEnlaces): Promise<EnlaceGenerado[]> {
  const res = await fetchAutenticado(`${API}/firma/aceptaciones`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(solicitud),
  });
  if (!res.ok) throw await _parseError(res);
  const datos = await res.json();
  return datos.enlaces;
}

/** Lista aceptaciones del tenant — requiere autenticación. */
export async function listarAceptaciones(documentoId?: string): Promise<ItemAceptacion[]> {
  const qs = documentoId ? `?documento_id=${encodeURIComponent(documentoId)}` : "";
  const res = await fetchAutenticado(`${API}/firma/aceptaciones${qs}`);
  if (!res.ok) throw await _parseError(res);
  const datos = await res.json();
  return datos.aceptaciones;
}

/** Verifica si un archivo coincide con un documento aprobado o acuse — requiere autenticación. */
export async function verificarDocumento(archivo: File): Promise<ResultadoVerificar> {
  const body = new FormData();
  body.append("archivo", archivo);
  const res = await fetchAutenticado(`${API}/firma/verificar`, {
    method: "POST",
    body,
  });
  if (!res.ok) throw await _parseError(res);
  return res.json();
}
