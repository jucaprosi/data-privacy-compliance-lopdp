/**
 * DER-01 · Cliente de la verificación de identidad y de la respuesta a una solicitud de titular.
 *
 * La respuesta envía solo `{modelo_id, variables, resultado}`: el hash de la evidencia lo calcula el
 * servidor y nunca sale de aquí. Los mensajes de error son fijos por código; no se muestra el texto del
 * servidor. Sin plazos: el semáforo llega con REG-01.
 */
import { fetchAutenticado } from "@/lib/auth";
import { rolesDelUsuario } from "@/lib/incidentes/roles";

const RUTA = "/api/v1/derechos";

export const ROLES_VERIFICAN = ["coordinador", "responsable_area", "admin_organizacion", "implementador"] as const;
export const ROLES_RESPONDEN = ["admin_organizacion", "implementador"] as const;

export type MetodoIdentidad = "documento" | "correo" | "presencial";
export type ResultadoRespuesta = "concedido" | "parcial" | "denegado";

export const METODOS: ReadonlyArray<{ valor: MetodoIdentidad; etiqueta: string }> = [
  { valor: "documento", etiqueta: "Documento de identidad" },
  { valor: "correo", etiqueta: "Correo electrónico verificado" },
  { valor: "presencial", etiqueta: "Presencial" },
];

/** Las etiquetas de la queja cambian; los valores que viajan son los mismos tres. */
export function etiquetasDeResultado(derecho: string): Record<ResultadoRespuesta, string> {
  return derecho === "QUEJA"
    ? { concedido: "Atendida", parcial: "Atendida en parte", denegado: "No atendida" }
    : { concedido: "Concedida", parcial: "Parcial", denegado: "Denegada" };
}

export const ETIQUETA_VARIABLE: Record<string, string> = {
  organizacion: "Organización",
  nombre_titular: "Nombre del titular",
  fecha_solicitud: "Fecha de la solicitud",
  numero_solicitud: "Número de la solicitud",
  fecha_respuesta: "Fecha de la respuesta",
  contacto_dpo: "Contacto del DPO",
  actuacion: "Acción realizada",
  motivo: "Motivo",
};

export const etiquetaDeVariable = (nombre: string): string => ETIQUETA_VARIABLE[nombre] ?? nombre;

export interface ModeloRespuesta {
  id: string;
  derecho: string;
  resultado: ResultadoRespuesta;
  texto: string;
  variables: string[];
}

export interface FichaSolicitud {
  id: string;
  derecho: string;
  estado: string;
  identidad_verificada_en: string | null;
  identidad_metodo: MetodoIdentidad | null;
  identidad_verificada_por: string | null;
  identidad_verificada_por_nombre: string | null;
  resultado: ResultadoRespuesta | null;
  respondida_en: string | null;
  evidencia_respuesta_hash: string | null;
}

export type ErrorRespuesta = { codigo: string; mensaje: string };

const MENSAJE_POR_CODIGO: Record<string, string> = {
  IDENTIDAD_NO_VERIFICADA: "Antes de responder, verifica la identidad del titular.",
  SOLICITUD_RESPONDIDA: "Esta solicitud ya tiene una respuesta registrada. Actualizamos la ficha.",
  VARIABLES_INCOMPLETAS: "Faltan datos en la respuesta. Revisa la vista previa.",
  RESPUESTA_SIN_EVIDENCIA: "No pudimos guardar la respuesta como evidencia, así que no se registró. Inténtalo de nuevo.",
};
const MENSAJE_VALIDACION = "No pudimos registrar la respuesta. Vuelve a cargar la página e inténtalo de nuevo.";
const MENSAJE_PERMISO = "No tienes permiso para esta acción.";
const MENSAJE_GENERICO = "No pudimos guardar los cambios. Inténtalo de nuevo.";

export async function errorDe(respuesta: Response): Promise<ErrorRespuesta> {
  let codigo = "";
  try {
    const cuerpo = (await respuesta.clone().json()) as { code?: string; codigo?: string };
    codigo = cuerpo.code ?? cuerpo.codigo ?? "";
  } catch {
    /* sin cuerpo legible: se decide por el estado */
  }
  if (MENSAJE_POR_CODIGO[codigo]) return { codigo, mensaje: MENSAJE_POR_CODIGO[codigo] };
  if (respuesta.status === 403) return { codigo: "PERMISO", mensaje: MENSAJE_PERMISO };
  if (respuesta.status === 422) return { codigo: "VALIDACION", mensaje: MENSAJE_VALIDACION };
  return { codigo: codigo || "ERROR", mensaje: MENSAJE_GENERICO };
}

export class FalloRespuesta extends Error {
  constructor(public readonly detalle: ErrorRespuesta) {
    super(detalle.mensaje);
  }
}

async function pedir<T>(ruta: string, init?: RequestInit): Promise<T> {
  const respuesta = await fetchAutenticado(`${RUTA}${ruta}`, init);
  if (!respuesta.ok) throw new FalloRespuesta(await errorDe(respuesta));
  return (await respuesta.json()) as T;
}

const JSON_POST = (cuerpo: unknown): RequestInit => ({
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(cuerpo),
});

export const cargarFicha = (id: string) => pedir<FichaSolicitud>(`/solicitudes/${encodeURIComponent(id)}`);

export async function cargarModelos(derecho: string, resultado: ResultadoRespuesta): Promise<ModeloRespuesta[]> {
  const q = new URLSearchParams({ derecho, resultado });
  return (await pedir<{ modelos: ModeloRespuesta[] }>(`/modelos?${q}`)).modelos;
}

export const verificarIdentidad = (id: string, metodo: MetodoIdentidad) =>
  pedir<FichaSolicitud>(`/solicitudes/${encodeURIComponent(id)}/verificar-identidad`, JSON_POST({ metodo }));

/** Envía solo modelo, variables y resultado. */
export const registrarRespuesta = (
  id: string,
  entrada: { modelo_id: string; variables: Record<string, string>; resultado: ResultadoRespuesta },
) =>
  pedir<{ evidencia_respuesta_hash: string }>(
    `/solicitudes/${encodeURIComponent(id)}/respuesta`,
    JSON_POST({ modelo_id: entrada.modelo_id, variables: entrada.variables, resultado: entrada.resultado }),
  );

/** Texto plano con las variables resueltas; la que falta o está vacía queda como «[Falta: etiqueta]». */
export function vistaPrevia(texto: string, valores: Record<string, string>): { texto: string; faltan: string[] } {
  const faltan: string[] = [];
  const resuelto = texto.replace(/\{([a-z_][a-z0-9_]*)\}/g, (_m, nombre: string) => {
    const valor = (valores[nombre] ?? "").trim();
    if (valor) return valor;
    if (!faltan.includes(nombre)) faltan.push(nombre);
    return `[Falta: ${etiquetaDeVariable(nombre)}]`;
  });
  return { texto: resuelto, faltan };
}

export const huellaCorta = (hash: string): string => hash.slice(0, 8);

export interface PermisosDeRespuesta {
  puedeVerificar: boolean;
  puedeResponder: boolean;
}

export async function permisosDelUsuario(): Promise<PermisosDeRespuesta> {
  const roles = await rolesDelUsuario();
  return {
    puedeVerificar: ROLES_VERIFICAN.some((r) => roles.includes(r)),
    puedeResponder: ROLES_RESPONDEN.some((r) => roles.includes(r)),
  };
}

/** Documento custodiado con esa huella: la evidencia de la respuesta (misma lista que el módulo de evidencias). */
export async function documentoDeLaRespuesta(hash: string): Promise<string | null> {
  const respuesta = await fetchAutenticado("/api/v1/evidencias/documentos");
  if (!respuesta.ok) return null;
  const { documentos } = (await respuesta.json()) as { documentos: Array<{ id: string; sha256: string }> };
  return documentos.find((d) => d.sha256 === hash)?.id ?? null;
}

export async function descargarRespuesta(documentoId: string): Promise<void> {
  const respuesta = await fetchAutenticado(`/api/v1/evidencias/documentos/${encodeURIComponent(documentoId)}/archivo`);
  if (!respuesta.ok) throw new FalloRespuesta(await errorDe(respuesta));
  const url = URL.createObjectURL(await respuesta.blob());
  const enlace = document.createElement("a");
  enlace.href = url;
  enlace.download = "respuesta.txt";
  enlace.click();
  URL.revokeObjectURL(url);
}
