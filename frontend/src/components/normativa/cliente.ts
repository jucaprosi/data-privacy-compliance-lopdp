/**
 * Cliente del Centro de Vigilancia Normativa (NORM-02). El corpus es global: lo leen los roles de una
 * organización y lo dispara y revisa solo el operador de la plataforma. El servidor autoriza cada llamada;
 * aquí solo se decide qué identidad se envía y qué botones se muestran.
 */
import { cabecerasDeMiembro, cabecerasDePlataforma } from "@/lib/auth/cabeceras";
import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";
import { modoAutenticacion } from "@/lib/auth/modo";
import { leerSesionDeOperador } from "@/lib/auth/sesion";

const BASE = "/api/v1/normativa";

export type EstadoResolucion = "pendiente_revision" | "homologada" | "observada" | "vigente" | "reformada" | "derogada";
export type EstadoRevision = "vigente" | "observada" | "reformada" | "derogada";

export interface Resolucion {
  id: string;
  numero_resolucion: string;
  anio_emision: number;
  titulo: string;
  seccion_fuente: string;
  estado: EstadoResolucion;
  detectada_en: string;
}
export interface Pagina { total: number; pagina: number; por_pagina: number; items: Resolucion[] }
export interface VersionResolucion { id: string; archivo_sha256: string; detectada_en: string; motivo: string }
export interface DetalleResolucion extends Resolucion {
  organo_emisor: string | null;
  materia: string | null;
  url_fuente: string;
  revisada_por: string | null;
  revisada_en: string | null;
  nota_revision: string | null;
  versiones: VersionResolucion[];
}
export interface Corrida {
  id: string;
  origen: "programado" | "manual";
  estado: "ok" | "parcial" | "fallida";
  inicio: string;
  fin: string | null;
  nuevos: number;
  versiones_nuevas: number;
  errores: number;
}
export interface Filtros { numero: string; anio: string; q: string; organo: string; materia: string; estado: string }
export const SIN_FILTROS: Filtros = { numero: "", anio: "", q: "", organo: "", materia: "", estado: "" };

export class ErrorNormativa extends Error {
  constructor(readonly status: number, readonly codigo?: string) {
    super(codigo ?? `HTTP ${status}`);
  }
}

/** Operador de la plataforma: en "oidc", quien tiene sesión de operador; en "headers" (desarrollo), si se declara. */
export function esOperador(): boolean {
  if (modoAutenticacion() === "oidc") return leerSesionDeOperador() !== null;
  return process.env.NEXT_PUBLIC_OPERADOR_PLATAFORMA === "1";
}

function cabeceras(): Record<string, string> {
  return esOperador() ? cabecerasDePlataforma() : cabecerasDeMiembro();
}

async function pedir(ruta: string, init: RequestInit = {}): Promise<Response> {
  const respuesta = await fetchAutenticado(
    `${BASE}${ruta}`,
    { ...init, headers: { "Content-Type": "application/json", ...(init.headers ?? {}) } },
    cabeceras(),
  );
  if (!respuesta.ok) {
    let codigo: string | undefined;
    try {
      const cuerpo = (await respuesta.json()) as { detail?: { codigo?: string } };
      codigo = cuerpo?.detail?.codigo;
    } catch {
      // El texto del servidor nunca se muestra: solo su código.
    }
    throw new ErrorNormativa(respuesta.status, codigo);
  }
  return respuesta;
}

export async function listarResoluciones(f: Filtros, pagina: number): Promise<Pagina> {
  const p = new URLSearchParams({ pagina: String(pagina), por_pagina: "25" });
  for (const [k, v] of Object.entries(f)) if (v.trim()) p.set(k, v.trim());
  return (await pedir(`/resoluciones?${p}`)).json();
}
export async function detalleResolucion(id: string): Promise<DetalleResolucion> {
  return (await pedir(`/resoluciones/${encodeURIComponent(id)}`)).json();
}
/** El PDF llega por el backend con la identidad de la sesión; un iframe no manda cabeceras, así que va como blob. */
export async function bajarOriginal(id: string): Promise<Blob> {
  return (await pedir(`/resoluciones/${encodeURIComponent(id)}/original`)).blob();
}
export async function listarBitacora(): Promise<Corrida[]> {
  return (await pedir("/monitoreo")).json();
}
export async function buscarNovedades(): Promise<void> {
  await pedir("/monitoreo", { method: "POST" });
}
export async function registrarRevision(id: string, estado: EstadoRevision, nota: string): Promise<void> {
  await pedir(`/resoluciones/${encodeURIComponent(id)}/revision`, { method: "POST", body: JSON.stringify({ estado, nota }) });
}
