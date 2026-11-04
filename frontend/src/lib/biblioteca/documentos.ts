// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Documentos de la organización (BIB-113): cliente frontend de las tres rutas del contrato
 * de `docs/biblioteca-pmv.md` apartado c:
 * - GET /api/v1/biblioteca/documentos?estado=&origen= (5)
 * - GET /api/v1/biblioteca/documentos/{id} (6)
 * - GET /api/v1/biblioteca/documentos/pendientes (9)
 *
 * La organización viaja exclusivamente en las cabeceras de identidad (`cabecerasDeTenant`),
 * nunca en la URL ni en el cuerpo. Distingue `listo`, `no_disponible` (404, 405 o 501),
 * `denegado` (401, 403) y `error`. Para `obtenerDocumento`, un 404 de documento ajeno o no
 * existente se entrega como `no_encontrado`.
 */
import { cabecerasDeTenant, fetchAutenticado } from "@/lib/auth";
import type { Pendientes, ResultadoPendientes } from "@/lib/biblioteca/contexto";

export const RUTA_DOCUMENTOS = "/api/v1/biblioteca/documentos";
export const RUTA_PENDIENTES = "/api/v1/biblioteca/documentos/pendientes";

export type OrigenDocumento = "plantilla" | "propio" | "subido";
export type EstadoDocumento = "borrador" | "en_revision" | "aprobado" | "vencido";

export interface DocumentoResumen {
  id: string;
  codigo: string;
  nombre: string;
  origen: OrigenDocumento;
  plantilla_version: string | null;
  estado: EstadoDocumento;
  editado: boolean;
  proxima_revision: string;
  revision: number;
  creado_por?: string;
  creado_en?: string;
  actualizado_en?: string;
}

export interface Documento extends DocumentoResumen {
  plantilla_id: string | null;
  contenido_markdown: string;
  variables_faltantes: string[];
  aprobado_por: string | null;
  aprobado_en: string | null;
  sha256: string;
  fecha_emision?: string;
  tarea_hoja_ruta_id?: string | null;
}

export interface FiltrosDocumentos {
  estado: EstadoDocumento | "";
  origen: OrigenDocumento | "";
}

export const SIN_FILTROS_DOCUMENTOS: FiltrosDocumentos = {
  estado: "",
  origen: "",
};

export const ORIGENES: ReadonlyArray<{ id: OrigenDocumento; nombre: string; etiqueta: string }> = [
  { id: "plantilla", nombre: "Plantilla", etiqueta: "basado en plantilla" },
  { id: "propio", nombre: "Propio", etiqueta: "propio" },
  { id: "subido", nombre: "Subido", etiqueta: "subido" },
];

export const ESTADOS_DOCUMENTO: ReadonlyArray<{ id: EstadoDocumento; nombre: string }> = [
  { id: "borrador", nombre: "Borrador" },
  { id: "en_revision", nombre: "En revisión" },
  { id: "aprobado", nombre: "Aprobado" },
  { id: "vencido", nombre: "Vencido" },
];

export const ETIQUETAS_ORIGEN: Record<OrigenDocumento, string> = {
  plantilla: "basado en plantilla",
  propio: "propio",
  subido: "subido",
};

export const ETIQUETAS_ESTADO: Record<EstadoDocumento, string> = {
  borrador: "Borrador",
  en_revision: "En revisión",
  aprobado: "Aprobado",
  vencido: "Vencido",
};

export type ResultadoDocumentos =
  | { estado: "listo"; documentos: DocumentoResumen[] }
  | { estado: "no_disponible" }
  | { estado: "denegado"; mensaje: string }
  | { estado: "error"; mensaje: string };

export type ResultadoDocumento =
  | { estado: "listo"; documento: Documento }
  | { estado: "no_encontrado"; mensaje: string }
  | { estado: "no_disponible" }
  | { estado: "denegado"; mensaje: string }
  | { estado: "error"; mensaje: string };

export function hayFiltrosDocumentos(filtros: FiltrosDocumentos): boolean {
  return filtros.estado !== "" || filtros.origen !== "";
}

export function consultaDocumentosDe(filtros: FiltrosDocumentos): string {
  const parametros = new URLSearchParams();
  if (filtros.estado) parametros.set("estado", filtros.estado);
  if (filtros.origen) parametros.set("origen", filtros.origen);
  const texto = parametros.toString();
  return texto ? `?${texto}` : "";
}

function esDocumentoResumen(valor: unknown): valor is DocumentoResumen {
  const d = valor as Partial<DocumentoResumen> | null;
  return (
    Boolean(d) &&
    typeof d?.id === "string" &&
    typeof d?.codigo === "string" &&
    typeof d?.nombre === "string" &&
    typeof d?.origen === "string" &&
    typeof d?.estado === "string" &&
    typeof d?.editado === "boolean" &&
    typeof d?.proxima_revision === "string" &&
    typeof d?.revision === "number"
  );
}

function esDocumento(valor: unknown): valor is Documento {
  const d = valor as Partial<Documento> | null;
  return (
    esDocumentoResumen(valor) &&
    typeof d?.contenido_markdown === "string" &&
    Array.isArray(d?.variables_faltantes) &&
    typeof d?.sha256 === "string"
  );
}

function esPendientes(valor: unknown): valor is Pendientes {
  const p = valor as Pendientes | null;
  return (
    Boolean(p) &&
    ["borrador", "en_revision", "por_vencer", "vencidos", "total"].every((campo) =>
      Number.isInteger((p as unknown as Record<string, unknown>)[campo])
    )
  );
}

export async function consultarDocumentos(
  filtros: FiltrosDocumentos = SIN_FILTROS_DOCUMENTOS
): Promise<ResultadoDocumentos> {
  let respuesta: Response;
  try {
    respuesta = await fetchAutenticado(
      `${RUTA_DOCUMENTOS}${consultaDocumentosDe(filtros)}`,
      { cache: "no-store" },
      cabecerasDeTenant()
    );
  } catch {
    return { estado: "error", mensaje: "No hay conexión con el servidor." };
  }
  const cuerpo = await respuesta.json().catch(() => null);
  if (
    respuesta.status === 404 ||
    respuesta.status === 405 ||
    respuesta.status === 501 ||
    respuesta.status === 503 ||
    cuerpo?.detail === "API simulada"
  ) {
    return { estado: "no_disponible" };
  }
  if (respuesta.status === 401 || respuesta.status === 403) {
    return {
      estado: "denegado",
      mensaje:
        typeof cuerpo?.detail === "string"
          ? cuerpo.detail
          : "No tienes acceso a los documentos de esta organización.",
    };
  }
  if (!respuesta.ok || !Array.isArray(cuerpo) || !cuerpo.every(esDocumentoResumen)) {
    return {
      estado: "error",
      mensaje: "El servidor no pudo entregar los documentos de la organización.",
    };
  }
  return { estado: "listo", documentos: cuerpo };
}

export async function obtenerDocumento(id: string): Promise<ResultadoDocumento> {
  if (!id) {
    return { estado: "error", mensaje: "Identificador de documento no especificado." };
  }
  let respuesta: Response;
  try {
    respuesta = await fetchAutenticado(
      `${RUTA_DOCUMENTOS}/${encodeURIComponent(id)}`,
      { cache: "no-store" },
      cabecerasDeTenant()
    );
  } catch {
    return { estado: "error", mensaje: "No hay conexión con el servidor." };
  }
  const cuerpo = await respuesta.json().catch(() => null);
  if (respuesta.status === 404) {
    return {
      estado: "no_encontrado",
      mensaje:
        typeof cuerpo?.detail === "string"
          ? cuerpo.detail
          : "No se encontró el documento en tu organización.",
    };
  }
  if (
    respuesta.status === 405 ||
    respuesta.status === 501 ||
    respuesta.status === 503 ||
    cuerpo?.detail === "API simulada"
  ) {
    return { estado: "no_disponible" };
  }
  if (respuesta.status === 401 || respuesta.status === 403) {
    return {
      estado: "denegado",
      mensaje:
        typeof cuerpo?.detail === "string"
          ? cuerpo.detail
          : "No tienes acceso al documento solicitado.",
    };
  }
  if (!respuesta.ok || !esDocumento(cuerpo)) {
    return {
      estado: "error",
      mensaje: "No se pudo obtener el detalle del documento.",
    };
  }
  return { estado: "listo", documento: cuerpo };
}

export async function consultarPendientesDocumentos(): Promise<ResultadoPendientes> {
  let respuesta: Response;
  try {
    respuesta = await fetchAutenticado(
      RUTA_PENDIENTES,
      { cache: "no-store" },
      cabecerasDeTenant()
    );
  } catch {
    return { estado: "error", mensaje: "No se pudo consultar Biblioteca." };
  }
  const cuerpo = await respuesta.json().catch(() => null);
  if (
    respuesta.status === 404 ||
    respuesta.status === 405 ||
    respuesta.status === 501 ||
    respuesta.status === 503 ||
    cuerpo?.detail === "API simulada"
  ) {
    return { estado: "no_disponible" };
  }
  if (respuesta.status === 401 || respuesta.status === 403) {
    return {
      estado: "denegado",
      mensaje:
        typeof cuerpo?.detail === "string"
          ? cuerpo.detail
          : "No tienes acceso a la Biblioteca de esta organización.",
    };
  }
  if (!respuesta.ok || !esPendientes(cuerpo)) {
    return { estado: "error", mensaje: "No se pudo consultar Biblioteca." };
  }
  return { estado: "listo", pendientes: cuerpo };
}
