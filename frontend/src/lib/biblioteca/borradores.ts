// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Cliente de borradores de documentos (BIB-114, contrato de `docs/biblioteca-pmv.md` §c):
 *  - `POST /biblioteca/documentos`: crea un borrador desde plantilla con variables de contexto.
 *  - `GET /biblioteca/documentos/{id}`: obtiene el borrador y su estado actual.
 *  - `PATCH /biblioteca/documentos/{id}`: guarda cambios con control optimista de revisión (`revision`).
 *
 * Sigue los mismos cuatro estados de `contexto.ts`: «listo», «no_disponible» (404/405/501),
 * «denegado» (401/403) y «error». Para guardado, un 409 se entrega como «conflicto».
 */
import { cabecerasDeTenant, fetchAutenticado } from "@/lib/auth";

export interface Documento {
  id: string;
  codigo: string;
  nombre: string;
  origen: "plantilla" | "propio" | "subido";
  plantilla_id: string | null;
  plantilla_version: string | null;
  contenido_markdown: string;
  variables_faltantes: string[];
  editado: boolean;
  estado: "borrador" | "en_revision" | "aprobado" | "vencido";
  aprobado_por?: string | null;
  aprobado_en?: string | null;
  sha256?: string;
  fecha_emision?: string;
  proxima_revision?: string;
  revision: number;
  creado_por?: string;
  creado_en?: string;
  actualizado_en?: string;
  tarea_hoja_ruta_id?: string | null;
}

export type TipoVariableContexto = "texto" | "si_no" | "lista";

export interface VariableContexto {
  clave: string;
  etiqueta: string;
  tipo?: TipoVariableContexto;
  obligatoria?: boolean;
}

export interface EntradaCrearDocumento {
  plantilla_id: string;
  fecha_emision?: string;
  contexto?: Record<string, string | string[]>;
  tarea_hoja_ruta_id?: string | null;
}

export interface EntradaCambiarDocumento {
  contenido_markdown: string;
  revision: number;
}

export type ResultadoDocumento =
  | { estado: "listo"; documento: Documento }
  | { estado: "no_disponible" }
  | { estado: "denegado"; mensaje: string }
  | { estado: "error"; mensaje: string };

export type ResultadoGuardarDocumento =
  | { estado: "listo"; documento: Documento }
  | { estado: "conflicto"; mensaje: string }
  | { estado: "no_disponible" }
  | { estado: "denegado"; mensaje: string }
  | { estado: "error"; mensaje: string };

const RUTA_DOCUMENTOS = "/api/v1/biblioteca/documentos";

const REGEX_FALTA = /⟦falta:\s*([^⟧]+)⟧/g;

/** Extrae las claves de variables que aún están marcadas como faltantes en el texto Markdown. */
export function extraerVariablesFaltantes(markdown: string): string[] {
  const faltantes: string[] = [];
  let coincidencia: RegExpExecArray | null;
  REGEX_FALTA.lastIndex = 0;
  while ((coincidencia = REGEX_FALTA.exec(markdown)) !== null) {
    const clave = coincidencia[1].trim();
    if (clave && !faltantes.includes(clave)) {
      faltantes.push(clave);
    }
  }
  return faltantes;
}

/** Llama a POST /biblioteca/documentos para crear un borrador desde plantilla. */
export async function crearDocumento(entrada: EntradaCrearDocumento): Promise<ResultadoDocumento> {
  let respuesta: Response;
  try {
    respuesta = await fetchAutenticado(
      RUTA_DOCUMENTOS,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(entrada),
        cache: "no-store",
      },
      cabecerasDeTenant(),
    );
  } catch {
    return { estado: "error", mensaje: "No se pudo conectar con el servidor para crear el documento." };
  }
  const cuerpo = await respuesta.json().catch(() => null);
  if (respuesta.status === 404 || respuesta.status === 405 || respuesta.status === 501) {
    return { estado: "no_disponible" };
  }
  if (respuesta.status === 401 || respuesta.status === 403) {
    return {
      estado: "denegado",
      mensaje: typeof cuerpo?.detail === "string" ? cuerpo.detail : "No tienes permiso para crear documentos en esta organización.",
    };
  }
  if (!respuesta.ok || !cuerpo || typeof cuerpo.id !== "string") {
    return {
      estado: "error",
      mensaje: typeof cuerpo?.detail === "string" ? cuerpo.detail : "No se pudo crear el documento.",
    };
  }
  return { estado: "listo", documento: cuerpo as Documento };
}

/** Llama a GET /biblioteca/documentos/{id} para obtener el documento. */
export async function obtenerDocumento(id: string): Promise<ResultadoDocumento> {
  let respuesta: Response;
  try {
    respuesta = await fetchAutenticado(
      `${RUTA_DOCUMENTOS}/${encodeURIComponent(id)}`,
      { cache: "no-store" },
      cabecerasDeTenant(),
    );
  } catch {
    return { estado: "error", mensaje: "No se pudo conectar con el servidor." };
  }
  const cuerpo = await respuesta.json().catch(() => null);
  if (respuesta.status === 404 || respuesta.status === 405 || respuesta.status === 501) {
    return { estado: "no_disponible" };
  }
  if (respuesta.status === 401 || respuesta.status === 403) {
    return {
      estado: "denegado",
      mensaje: typeof cuerpo?.detail === "string" ? cuerpo.detail : "No tienes acceso a este documento.",
    };
  }
  if (!respuesta.ok || !cuerpo || typeof cuerpo.id !== "string") {
    return {
      estado: "error",
      mensaje: typeof cuerpo?.detail === "string" ? cuerpo.detail : "No se pudo obtener el documento.",
    };
  }
  return { estado: "listo", documento: cuerpo as Documento };
}

/**
 * Guarda cambios en el borrador con PATCH /biblioteca/documentos/{id}.
 * Control de concurrencia: si `revision` no coincide con la del servidor, responde 409 (conflicto).
 */
export async function guardarDocumento(
  id: string,
  cambio: EntradaCambiarDocumento,
): Promise<ResultadoGuardarDocumento> {
  let respuesta: Response;
  try {
    respuesta = await fetchAutenticado(
      `${RUTA_DOCUMENTOS}/${encodeURIComponent(id)}`,
      {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(cambio),
        cache: "no-store",
      },
      cabecerasDeTenant(),
    );
  } catch {
    return { estado: "error", mensaje: "Error de red: no se pudo guardar el borrador." };
  }
  const cuerpo = await respuesta.json().catch(() => null);
  if (respuesta.status === 409) {
    return {
      estado: "conflicto",
      mensaje:
        typeof cuerpo?.detail === "string"
          ? cuerpo.detail
          : "Conflicto de edición: la revisión del documento está desfasada.",
    };
  }
  if (respuesta.status === 404 || respuesta.status === 405 || respuesta.status === 501) {
    return { estado: "no_disponible" };
  }
  if (respuesta.status === 401 || respuesta.status === 403) {
    return {
      estado: "denegado",
      mensaje: typeof cuerpo?.detail === "string" ? cuerpo.detail : "No tienes permiso para editar este documento.",
    };
  }
  if (!respuesta.ok || !cuerpo || typeof cuerpo.id !== "string") {
    return {
      estado: "error",
      mensaje: typeof cuerpo?.detail === "string" ? cuerpo.detail : "No se pudo guardar el documento.",
    };
  }
  return { estado: "listo", documento: cuerpo as Documento };
}
