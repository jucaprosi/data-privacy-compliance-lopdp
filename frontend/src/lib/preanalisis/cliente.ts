// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasComo, rolParaResponder, rolesDelUsuario } from "@/lib/diagnostico/roles";
import type {
  ControlParaAnalisis,
  EstadoServicioIA,
  FragmentoDocumento,
  PreparacionDocumento,
  PropuestaIA,
  ResultadoAnalisis,
} from "@/lib/preanalisis/tipos";

const API_BASE_URL = "/api/v1";

const MENSAJE_SIN_CONEXION = "No se pudo contactar con el servicio de análisis (¿backend fuera de línea?).";

export class ErrorPreanalisis extends Error {
  readonly status: number;

  constructor(status: number, mensaje: string) {
    super(mensaje);
    this.name = "ErrorPreanalisis";
    this.status = status;
  }
}

function mensajePorEstado(status: number, detalle: string | null): string {
  switch (status) {
    case 413:
      return "El documento es demasiado grande para analizarse.";
    case 415:
      return "Este formato no puede analizarse automáticamente; respáldalo manualmente.";
    case 422:
      return "No se pudo leer el documento: parece dañado, protegido o sin texto.";
    case 502:
      return "El proveedor de IA falló al procesar la solicitud. Inténtalo de nuevo en unos minutos.";
    case 503:
      return "El servicio de análisis con IA no está disponible: no hay un proveedor configurado.";
    default:
      return detalle ?? `El servicio de análisis respondió con un error (${status}).`;
  }
}

async function extraerDetalle(respuesta: Response): Promise<string | null> {
  try {
    const cuerpo: unknown = await respuesta.json();
    if (cuerpo && typeof cuerpo === "object" && "detail" in cuerpo) {
      const { detail } = cuerpo as { detail: unknown };
      if (typeof detail === "string" && detail.trim()) return detail;
    }
  } catch {
    return null;
  }
  return null;
}

async function solicitar<T>(ruta: string, init: RequestInit, identidad?: Record<string, string>): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetchAutenticado(
      `${API_BASE_URL}${ruta}`,
      {
        ...init,
        headers: { ...(init.headers ?? {}) },
      },
      identidad
    );
  } catch {
    throw new ErrorPreanalisis(0, MENSAJE_SIN_CONEXION);
  }
  if (!respuesta.ok) {
    const detalle = await extraerDetalle(respuesta);
    throw new ErrorPreanalisis(respuesta.status, mensajePorEstado(respuesta.status, detalle));
  }
  try {
    return (await respuesta.json()) as T;
  } catch {
    throw new ErrorPreanalisis(respuesta.status, "La respuesta del servicio de análisis no es válida.");
  }
}

function textoOnull(valor: string | null | undefined): string | null {
  const limpio = typeof valor === "string" ? valor.trim() : "";
  return limpio === "" ? null : limpio;
}

/** País y región ciertos del estado, o null si falta alguno (falla cerrado, IA-15 §4 regla 3). */
export function destinoDelEstado(estado: EstadoServicioIA | null): { pais: string; region: string } | null {
  const pais = textoOnull(estado?.ubicacion);
  const region = textoOnull(estado?.region);
  return estado?.disponible && pais && region ? { pais, region } : null;
}

function esEcuador(pais: string): boolean {
  return pais.normalize("NFD").replace(/[̀-ͯ]/g, "").trim().toLowerCase() === "ecuador";
}

/** Aviso de envío completo (IA-15 §4), con destinatario, modelo, país y región del estado. Null si no hay destino. */
export function avisoDeEnvio(estado: EstadoServicioIA | null): string | null {
  const destino = destinoDelEstado(estado);
  if (!estado || !destino) return null;
  const quien = estado.proveedor && estado.modelo ? `a ${estado.proveedor} para procesarlos con el modelo ${estado.modelo}` : "al servicio de IA configurado";
  const fuera = esEcuador(destino.pais) ? "" : ", fuera de Ecuador";
  return `Estos fragmentos se envían ${quien}. Se procesan en ${destino.pais} (región ${destino.region})${fuera}.`;
}

/** Etiqueta corta del panel: «{destinatario} · {pais}, {region}». */
export function etiquetaDeDestino(estado: EstadoServicioIA | null): string | null {
  const destino = destinoDelEstado(estado);
  return estado?.proveedor && destino ? `${estado.proveedor} · ${destino.pais}, ${destino.region}` : null;
}

export async function consultarEstadoServicio(): Promise<EstadoServicioIA> {
  try {
    const estado = await solicitar<EstadoServicioIA>("/preanalisis/estado", { method: "GET" });
    return { ...estado, ubicacion: textoOnull(estado.ubicacion), region: textoOnull(estado.region) };
  } catch (error) {
    const motivo = error instanceof ErrorPreanalisis && error.status !== 0 ? error.message : MENSAJE_SIN_CONEXION;
    return { disponible: false, proveedor: null, modelo: null, motivo, ubicacion: null, region: null };
  }
}

export async function prepararDocumento(
  archivo: File,
  control: ControlParaAnalisis
): Promise<PreparacionDocumento> {
  const formulario = new FormData();
  formulario.append("archivo", archivo);
  formulario.append("control_id", String(control.control_id));
  formulario.append("control", control.control);
  formulario.append("enunciado", control.enunciado);
  formulario.append("evidencia_esperada", control.evidencia_esperada);
  return solicitar<PreparacionDocumento>("/preanalisis/preparar", { method: "POST", body: formulario });
}

/**
 * DIAG-07 R6: pide la propuesta quien responde (rol de `rolParaResponder`), con la dimensión de la
 * pregunta; el servidor exige `puede_escribir` y evidencia vinculada (403 y 409).
 */
export async function analizarControl(
  control: ControlParaAnalisis,
  fragmentos: FragmentoDocumento[],
  dimension = ""
): Promise<ResultadoAnalisis> {
  const rol = rolParaResponder(await rolesDelUsuario());
  return solicitar<ResultadoAnalisis>("/preanalisis/analizar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      control_id: control.control_id,
      control: control.control,
      enunciado: control.enunciado,
      evidencia_esperada: control.evidencia_esperada,
      referencia_normativa: control.referencia_normativa,
      fragmentos: fragmentos.map(({ texto, origen }) => ({ texto, origen })),
      dimension,
    }),
  }, rol ? cabecerasComo(rol) : undefined);
}

function nuevoId(): string {
  if (typeof crypto !== "undefined" && typeof crypto.randomUUID === "function") {
    return crypto.randomUUID();
  }
  return `prop-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function construirPropuesta(
  resultado: ResultadoAnalisis,
  evidencia: { id: string; codigo: string },
  preguntaId: number
): PropuestaIA {
  return {
    id: nuevoId(),
    preguntaId,
    evidenciaId: evidencia.id,
    evidenciaCodigo: evidencia.codigo,
    estado: resultado.estado,
    nivelEvidenciaMaximo: resultado.nivel_evidencia_maximo,
    citas: resultado.citas,
    citasDescartadas: resultado.citas_descartadas,
    razonamiento: resultado.razonamiento,
    limitaciones: resultado.limitaciones,
    modelo: resultado.modelo,
    generadaEn: new Date().toISOString(),
    decision: "pendiente",
  };
}
