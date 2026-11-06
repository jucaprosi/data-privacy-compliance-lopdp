// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Cliente de BIB-207: guardado con revisión esperada y trabajos de generación idempotentes.
 * El servidor decide tenant, permisos, conflictos y estados; aquí solo se pide, se consulta y se reintenta.
 */
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasDeMiembro } from "@/lib/auth/cabeceras";
import { mensajeDelServidor, ROLES_EDITORES } from "@/lib/biblioteca/http";
import type { FormatoGeneracion, ModoGeneracion } from "@/lib/biblioteca/generacion";

export type EstadoTrabajo = "pendiente" | "generando" | "listo" | "fallido";
export type Valor = string | number | boolean | null | string[];

export interface Trabajo {
  id: string;
  borrador_id: string;
  revision_borrador: number;
  clave: string;
  modo: ModoGeneracion;
  formato: FormatoGeneracion;
  estado: EstadoTrabajo;
  intentos: number;
  generacion_id: string | null;
  error_codigo: string | null;
  error_detalle: string | null;
  creado_por: string;
  creado_en: string;
  actualizado_en: string;
  vencido: boolean;
}

export interface CampoBorrador { clave: string; etiqueta: string; tipo: "texto" | "si_no" | "lista" }
export interface BorradorEditable {
  id: string;
  codigo: string;
  revision: number;
  contexto: Record<string, Valor>;
  campos: CampoBorrador[];
}

export interface Diferencia { clave: string; mio: Valor | null; vigente: Valor | null }
export interface Conflicto {
  borrador_id: string;
  revision_esperada: number;
  revision_vigente: number;
  contexto_vigente: Record<string, Valor>;
  fecha_vigente: string;
  diferencias: Diferencia[];
}

export type ResultadoGuardado = { ok: true; revision: number } | { ok: false; conflicto: Conflicto };

export const ETIQUETAS_ESTADO: Record<EstadoTrabajo, string> = {
  pendiente: "Pendiente", generando: "Generando", listo: "Listo", fallido: "Fallido",
};

const RUTA = "/api/v1/biblioteca/trabajos";
const enc = encodeURIComponent;

async function leer<T>(respuesta: Response, porDefecto: string): Promise<T> {
  const datos = await respuesta.json().catch(() => null);
  if (!respuesta.ok) throw new Error(mensajeDelServidor(datos, porDefecto));
  return datos as T;
}

/** Clave de idempotencia nueva por petición del usuario; un reintento de red reutiliza la misma. */
export function nuevaClave(): string {
  const c = globalThis.crypto;
  return c?.randomUUID ? c.randomUUID() : `k-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`;
}

export function estadoVisible(t: Trabajo): string {
  return t.vencido ? "Fallido (tiempo agotado)" : ETIQUETAS_ESTADO[t.estado];
}

export function reintentable(t: Trabajo): boolean {
  return t.estado === "fallido" || t.vencido;
}

export async function obtenerBorrador(id: string): Promise<BorradorEditable> {
  return leer(await fetchAutenticado(`/api/v1/biblioteca/borradores/${enc(id)}`, { cache: "no-store" },
    cabecerasDeMiembro(ROLES_EDITORES)), "No se pudo cargar el borrador.");
}

export async function guardarConRevision(id: string, revision: number,
  contexto: Record<string, Valor>): Promise<ResultadoGuardado> {
  const respuesta = await fetchAutenticado(`${RUTA}/borradores/${enc(id)}`, {
    method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ revision, contexto }),
  }, cabecerasDeMiembro(ROLES_EDITORES));
  if (respuesta.status === 409) {
    const datos = await respuesta.json().catch(() => null);
    if (datos?.conflicto) return { ok: false, conflicto: datos.conflicto as Conflicto };
  }
  const guardado = await leer<{ revision: number }>(respuesta, "No se pudo guardar el borrador.");
  return { ok: true, revision: guardado.revision };
}

export async function listarTrabajos(borradorId: string): Promise<Trabajo[]> {
  return leer(await fetchAutenticado(`${RUTA}/borradores/${enc(borradorId)}`, { cache: "no-store" },
    cabecerasDeMiembro(ROLES_EDITORES)), "No se pudieron cargar los trabajos de generación.");
}

export async function solicitarTrabajo(borradorId: string, modo: ModoGeneracion, formato: FormatoGeneracion,
  clave: string): Promise<Trabajo> {
  return leer(await fetchAutenticado(`${RUTA}/borradores/${enc(borradorId)}/generaciones`, {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ modo, formato, clave }),
  }, cabecerasDeMiembro(ROLES_EDITORES)), "No se pudo pedir la generación.");
}

export async function obtenerTrabajo(id: string): Promise<Trabajo> {
  return leer(await fetchAutenticado(`${RUTA}/${enc(id)}`, { cache: "no-store" }, cabecerasDeMiembro(ROLES_EDITORES)),
    "No se pudo consultar el trabajo.");
}

export async function reintentarTrabajo(id: string): Promise<Trabajo> {
  return leer(await fetchAutenticado(`${RUTA}/${enc(id)}/reintentar`, { method: "POST" }, cabecerasDeMiembro(ROLES_EDITORES)),
    "No se pudo reintentar el trabajo.");
}
