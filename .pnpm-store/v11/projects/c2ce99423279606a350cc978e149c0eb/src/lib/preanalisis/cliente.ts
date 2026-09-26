import type {
  ControlParaAnalisis,
  EstadoServicioIA,
  FragmentoDocumento,
  PreparacionDocumento,
  PropuestaIA,
  ResultadoAnalisis,
} from "@/lib/preanalisis/tipos";

const API_BASE_URL = "/api/v1";
const CABECERA_TENANT = { "X-Tenant-ID": "tenant-corp-demo" };

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

async function solicitar<T>(ruta: string, init: RequestInit): Promise<T> {
  let respuesta: Response;
  try {
    respuesta = await fetch(`${API_BASE_URL}${ruta}`, {
      ...init,
      headers: { ...CABECERA_TENANT, ...(init.headers ?? {}) },
    });
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

export async function consultarEstadoServicio(): Promise<EstadoServicioIA> {
  try {
    return await solicitar<EstadoServicioIA>("/preanalisis/estado", { method: "GET" });
  } catch (error) {
    const motivo = error instanceof ErrorPreanalisis && error.status !== 0 ? error.message : MENSAJE_SIN_CONEXION;
    return { disponible: false, proveedor: null, modelo: null, motivo };
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

export async function analizarControl(
  control: ControlParaAnalisis,
  fragmentos: FragmentoDocumento[]
): Promise<ResultadoAnalisis> {
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
    }),
  });
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
