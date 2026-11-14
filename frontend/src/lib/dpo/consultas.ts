/**
 * Cliente HTTP tipado de las consultas de la organización al DPO (DPO-03).
 * Solo fetchAutenticado; la organización y la identidad las resuelve el servidor, no el cuerpo.
 */
import { cabecerasDeRol, fetchAutenticado } from "@/lib/auth";

export type EstadoConsulta = "abierta" | "respondida" | "cerrada";

export interface MensajeConsulta {
  secuencia: number;
  autor_rol: string;
  autor_nombre: string | null;
  es_mio: boolean;
  texto: string;
  creado_en: string;
}

export interface ConsultaDpo {
  id: string;
  asunto: string;
  estado: EstadoConsulta;
  creado_en: string;
  cerrada_en: string | null;
  huella_hilo: string | null;
  mensajes: MensajeConsulta[];
}

/** Error de la API con el estado HTTP y el código de negocio, para elegir el texto fijo de la pantalla. */
export class ErrorConsultas extends Error {
  constructor(
    public readonly estado: number,
    public readonly codigo: string | null,
  ) {
    super(`HTTP ${estado}${codigo ? ` ${codigo}` : ""}`);
    this.name = "ErrorConsultas";
  }
}

/** Etiquetas de rol de la plataforma, para el hilo («Delegado de protección de datos · …»). */
export const ETIQUETA_ROL: Record<string, string> = {
  dpo: "DPO",
  coordinador: "Coordinador",
  admin_organizacion: "Administrador de la organización",
  responsable_area: "Responsable de área",
  implementador: "Implementador",
  auditor: "Auditor",
};

const BASE = "/api/v1/dpo/consultas";

function cabeceras(rol: string, userId?: string): Record<string, string> {
  return { "Content-Type": "application/json", ...cabecerasDeRol(rol, userId || "") };
}

async function fallo(res: Response): Promise<ErrorConsultas> {
  const cuerpo = (await res.json().catch(() => null)) as { code?: unknown } | null;
  return new ErrorConsultas(res.status, typeof cuerpo?.code === "string" ? cuerpo.code : null);
}

export async function listarConsultas(rol: string, userId?: string, estado?: EstadoConsulta): Promise<ConsultaDpo[]> {
  const url = estado ? `${BASE}?estado=${encodeURIComponent(estado)}` : BASE;
  const res = await fetchAutenticado(url, { method: "GET", headers: cabeceras(rol, userId) });
  if (!res.ok) throw await fallo(res);
  return ((await res.json()) as { consultas: ConsultaDpo[] }).consultas;
}

export async function crearConsulta(rol: string, userId: string | undefined, asunto: string, texto: string): Promise<ConsultaDpo> {
  const res = await fetchAutenticado(BASE, {
    method: "POST",
    headers: cabeceras(rol, userId),
    body: JSON.stringify({ asunto, texto }),
  });
  if (!res.ok) throw await fallo(res);
  return (await res.json()) as ConsultaDpo;
}

export async function enviarMensaje(rol: string, userId: string | undefined, consultaId: string, texto: string): Promise<MensajeConsulta> {
  const res = await fetchAutenticado(`${BASE}/${encodeURIComponent(consultaId)}/mensajes`, {
    method: "POST",
    headers: cabeceras(rol, userId),
    body: JSON.stringify({ texto }),
  });
  if (!res.ok) throw await fallo(res);
  return (await res.json()) as MensajeConsulta;
}

/** Solo el rol dpo; el servidor responde 403 a los demás. */
export async function responderYCerrar(userId: string | undefined, consultaId: string, respuesta: string): Promise<ConsultaDpo> {
  const res = await fetchAutenticado(`${BASE}/${encodeURIComponent(consultaId)}/cerrar`, {
    method: "POST",
    headers: cabeceras("dpo", userId),
    body: JSON.stringify({ respuesta }),
  });
  if (!res.ok) throw await fallo(res);
  return (await res.json()) as ConsultaDpo;
}
