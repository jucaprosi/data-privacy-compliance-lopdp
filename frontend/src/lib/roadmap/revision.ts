import { fetchAutenticado } from "@/lib/auth";
import { getIdentityHeaders } from "@/lib/roadmap/cliente";

export interface EstadoRevision {
  status: string;
  generado_por: string | null;
  generado_por_nombre: string | null;
  generado_en: string | null;
  revisado_por: string | null;
  revisado_por_nombre: string | null;
  revisado_en: string | null;
  puede_activar: boolean;
  es_autor: boolean;
  etiqueta: string | null;
}

export interface RespuestaActivacion {
  status: string;
  revisado_por: string | null;
  revisado_por_nombre?: string | null;
  revisado_en: string | null;
}

export class ErrorRevision extends Error {
  readonly status: number;
  readonly codigo?: string;

  constructor(status: number, codigo?: string) {
    super(`Error ${status}`);
    this.name = "ErrorRevision";
    this.status = status;
    this.codigo = codigo;
  }
}

async function leerCodigo(respuesta: Response): Promise<string | undefined> {
  try {
    const cuerpo = (await respuesta.clone().json()) as { code?: unknown; codigo?: unknown };
    if (typeof cuerpo?.code === "string") return cuerpo.code;
    if (typeof cuerpo?.codigo === "string") return cuerpo.codigo;
  } catch {
    // Respuesta sin JSON o sin código estructurado.
  }
  return undefined;
}

export async function obtenerRevision(roadmapId: string): Promise<EstadoRevision | null> {
  const respuesta = await fetchAutenticado(
    `/api/v1/roadmaps/${encodeURIComponent(roadmapId)}/revision`,
    { method: "GET" },
    getIdentityHeaders(),
  );
  if (respuesta.status === 404) return null;
  if (!respuesta.ok) throw new ErrorRevision(respuesta.status, await leerCodigo(respuesta));
  return (await respuesta.json()) as EstadoRevision;
}

export async function activarHojaRuta(roadmapId: string): Promise<RespuestaActivacion> {
  const respuesta = await fetchAutenticado(
    `/api/v1/roadmaps/${encodeURIComponent(roadmapId)}/activar`,
    { method: "POST" },
    getIdentityHeaders(),
  );
  if (!respuesta.ok) throw new ErrorRevision(respuesta.status, await leerCodigo(respuesta));
  return (await respuesta.json()) as RespuestaActivacion;
}

export async function descargarInformePdf(
  roadmapId: string,
): Promise<{ blob: Blob; revisionHeader: string | null }> {
  const respuesta = await fetchAutenticado(
    `/api/v1/roadmaps/${encodeURIComponent(roadmapId)}/informe.pdf`,
    { method: "GET" },
    getIdentityHeaders(),
  );
  if (!respuesta.ok) throw new ErrorRevision(respuesta.status, await leerCodigo(respuesta));
  return {
    blob: await respuesta.blob(),
    revisionHeader: respuesta.headers.get("X-Roadmap-Revision"),
  };
}

export function mensajeErrorActivacion(err: unknown): { mensaje: string; recargar: boolean } {
  if (err instanceof ErrorRevision) {
    if (err.status === 409 && err.codigo === "REVISION_MISMA_PERSONA") {
      return {
        mensaje: "No puedes activar una hoja de ruta que generaste tú. Debe activarla otra persona.",
        recargar: false,
      };
    }
    if (err.status === 409 && err.codigo === "HOJA_YA_ACTIVA") {
      return {
        mensaje: "Otra persona ya activó esta hoja de ruta. Actualizamos su estado.",
        recargar: true,
      };
    }
    if (err.status === 403) {
      return {
        mensaje: "Solo un coordinador o el DPO pueden activar la hoja de ruta.",
        recargar: false,
      };
    }
    if (err.status === 404) {
      return {
        mensaje: "No encontramos esta hoja de ruta. Vuelve a cargar la página.",
        recargar: false,
      };
    }
  }
  return {
    mensaje: "No pudimos activar la hoja de ruta. Inténtalo de nuevo.",
    recargar: false,
  };
}

export function mensajeErrorInforme(err: unknown): string {
  if (err instanceof ErrorRevision && err.status === 409 && err.codigo === "HOJA_PENDIENTE_DE_REVISION") {
    return "Esta hoja de ruta está pendiente de revisión. El informe se podrá descargar cuando se active.";
  }
  return "No pudimos descargar el informe. Inténtalo de nuevo.";
}

export function formatearFechaRevision(iso: string | null | undefined): string | null {
  if (!iso) return null;
  const fecha = new Date(iso);
  if (Number.isNaN(fecha.getTime())) return null;
  return new Intl.DateTimeFormat("es-EC", {
    day: "numeric",
    month: "long",
    year: "numeric",
  }).format(fecha);
}
