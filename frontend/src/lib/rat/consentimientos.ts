/**
 * Cliente HTTP de colectivos de titulares y consentimientos agregados (RAT-07).
 * Contrato: governance/especificaciones/RAT-07.md §2. Nunca datos de un titular individual.
 */
import { cabecerasDeRol, fetchAutenticado } from "@/lib/auth";

export interface Colectivo {
  id: string;
  tratamiento_id: string;
  nombre: string;
  base_legitimacion: string;
  texto_version: string | null;
}

export interface RegistroConsentimiento {
  id: string;
  colectivo_id: string;
  fecha: string;
  canal: string;
  cantidad: number;
  texto_version: string | null;
}

export interface RegistrosDeColectivo {
  registros: RegistroConsentimiento[];
  total: number;
}

export interface ColectivoEntrada {
  nombre: string;
  base_legitimacion: string;
  texto_version: string | null;
}

export interface RegistroEntrada {
  fecha: string;
  canal: string;
  cantidad: number;
  texto_version: string | null;
}

/** Mismas etiquetas que usa el RAT para la base de legitimación. */
export const BASES_LEGITIMACION: { valor: string; etiqueta: string }[] = [
  { valor: "CONSENTIMIENTO", etiqueta: "Consentimiento" },
  { valor: "OBLIGACION_LEGAL", etiqueta: "Obligación legal" },
  { valor: "CUMPLIMIENTO_CONTRATO", etiqueta: "Cumplimiento de contrato" },
  { valor: "PROTECCION_INTERES_VITAL", etiqueta: "Protección de interés vital" },
  { valor: "INTERES_LEGITIMO", etiqueta: "Interés legítimo" },
  { valor: "MISION_INTERES_PUBLICO", etiqueta: "Misión de interés público" },
];

export const CANALES: { valor: string; etiqueta: string }[] = [
  { valor: "web", etiqueta: "Web" },
  { valor: "presencial", etiqueta: "Presencial" },
  { valor: "telefono", etiqueta: "Teléfono" },
  { valor: "otro", etiqueta: "Otro" },
];

export const ROLES_ESCRITURA = ["implementador", "coordinador", "admin_organizacion"];
export const ROLES_LECTURA = [...ROLES_ESCRITURA, "dpo", "responsable_area"];

/** Error con mensaje ya redactado para la persona usuaria; nunca el texto del servidor. */
export class ErrorConsentimientos extends Error {
  constructor(
    mensaje: string,
    readonly estado: number,
  ) {
    super(mensaje);
  }
}

const BASE = "/api/v1/rat";
const MENSAJE_404 = "No encontramos este tratamiento o colectivo. Vuelve a cargar la página.";
const MENSAJE_GENERICO = "No pudimos guardar los cambios. Inténtalo de nuevo.";
const MENSAJE_422 = "Revisa los datos del formulario.";

async function leer<T>(res: Response): Promise<T> {
  if (res.ok) return (await res.json()) as T;
  if (res.status === 404) throw new ErrorConsentimientos(MENSAJE_404, 404);
  if (res.status === 422) throw new ErrorConsentimientos(MENSAJE_422, 422);
  throw new ErrorConsentimientos(MENSAJE_GENERICO, res.status);
}

function cabeceras(rol: string, userId: string): Record<string, string> {
  return { "Content-Type": "application/json", ...cabecerasDeRol(rol, userId) };
}

export async function listarColectivos(ratId: string, rol: string, userId: string): Promise<Colectivo[]> {
  const res = await fetchAutenticado(`${BASE}/${ratId}/colectivos`, { method: "GET", headers: cabeceras(rol, userId) });
  return (await leer<{ colectivos: Colectivo[] }>(res)).colectivos;
}

export async function crearColectivo(ratId: string, datos: ColectivoEntrada, rol: string, userId: string): Promise<Colectivo> {
  const res = await fetchAutenticado(`${BASE}/${ratId}/colectivos`, {
    method: "POST",
    headers: cabeceras(rol, userId),
    body: JSON.stringify(datos),
  });
  return leer(res);
}

export async function editarColectivo(id: string, datos: ColectivoEntrada, rol: string, userId: string): Promise<Colectivo> {
  const res = await fetchAutenticado(`${BASE}/colectivos/${id}`, {
    method: "PUT",
    headers: cabeceras(rol, userId),
    body: JSON.stringify(datos),
  });
  return leer(res);
}

export async function registrarConsentimiento(
  colectivoId: string,
  datos: RegistroEntrada,
  rol: string,
  userId: string,
): Promise<RegistroConsentimiento> {
  const res = await fetchAutenticado(`${BASE}/colectivos/${colectivoId}/consentimientos`, {
    method: "POST",
    headers: cabeceras(rol, userId),
    body: JSON.stringify(datos),
  });
  return leer(res);
}

export async function consultarConsentimientos(
  colectivoId: string,
  rol: string,
  userId: string,
  desde?: string,
  hasta?: string,
): Promise<RegistrosDeColectivo> {
  const parametros = new URLSearchParams();
  if (desde) parametros.set("desde", desde);
  if (hasta) parametros.set("hasta", hasta);
  const consulta = parametros.toString();
  const res = await fetchAutenticado(`${BASE}/colectivos/${colectivoId}/consentimientos${consulta ? `?${consulta}` : ""}`, {
    method: "GET",
    headers: cabeceras(rol, userId),
  });
  return leer(res);
}
