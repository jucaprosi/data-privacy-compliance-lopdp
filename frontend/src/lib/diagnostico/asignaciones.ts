/**
 * Cliente de la asignación de dominios del assessment a encargados del diagnóstico (DIAG-04).
 *
 * Asigna el administrador de la organización; implementador, coordinador y DPO consultan. Cada llamada
 * declara el rol con el que se actúa y el servidor lo verifica (ver roles.ts). La identidad y la
 * organización salen de la sesión, nunca del cuerpo.
 */
import { requestJson } from "@/lib/roadmap/cliente";

export const ROL_QUE_ASIGNA = "admin_organizacion";
const ROLES_QUE_LEEN = ["admin_organizacion", "implementador", "coordinador", "dpo", "responsable_area"] as const;
const ROLES_CON_HISTORIAL = ["implementador", "coordinador", "dpo"] as const;

export interface AsignacionDominio {
  dimension: string;
  nombre_dimension: string;
  responsable_user_id: string | null;
  /** Solo el nombre. La clave no existe para quien no lo recibe; es nula si el encargado ya no tiene rol vigente. */
  responsable_nombre?: string | null;
  asignado_en: string | null;
}

export interface MovimientoAsignacion {
  dimension: string;
  responsable_user_id: string | null;
  responsable_nombre?: string | null;
  asignado_por: string;
  asignado_en: string;
}

export interface PersonaEncargable {
  id: string;
  nombre: string;
  roles: string[];
}

export function rolParaAsignaciones(roles: readonly string[]): string | null {
  return ROLES_QUE_LEEN.find((rol) => roles.includes(rol)) ?? null;
}

export function rolParaHistorial(roles: readonly string[]): string | null {
  return ROLES_CON_HISTORIAL.find((rol) => roles.includes(rol)) ?? null;
}

export function puedeAsignar(roles: readonly string[]): boolean {
  return roles.includes(ROL_QUE_ASIGNA);
}

export async function cargarAsignaciones(rol: string): Promise<AsignacionDominio[]> {
  return (await requestJson<{ asignaciones: AsignacionDominio[] }>("/diagnostico/asignaciones", {
    headers: { "X-Role": rol },
  })).asignaciones;
}

export async function asignarDominio(dimension: string, responsableUserId: string | null): Promise<AsignacionDominio> {
  return requestJson<AsignacionDominio>(`/diagnostico/asignaciones/${encodeURIComponent(dimension)}`, {
    method: "PUT",
    headers: { "X-Role": ROL_QUE_ASIGNA },
    body: JSON.stringify({ responsable_user_id: responsableUserId }),
  });
}

export async function cargarHistorial(rol: string, dimension?: string): Promise<MovimientoAsignacion[]> {
  const consulta = dimension ? `?dimension=${encodeURIComponent(dimension)}` : "";
  return (await requestJson<{ historial: MovimientoAsignacion[] }>(`/diagnostico/asignaciones/historial${consulta}`, {
    headers: { "X-Role": rol },
  })).historial;
}

interface UsuarioOrganizacion {
  id: string;
  nombre: string;
  roles: { role: string }[];
}

/** Personas con rol vigente en la organización, sin quien solo es DPO (el servidor lo rechazaría). */
export async function cargarPersonasEncargables(): Promise<PersonaEncargable[]> {
  const usuarios = await requestJson<UsuarioOrganizacion[]>("/organizacion/usuarios", {
    headers: { "X-Role": ROL_QUE_ASIGNA },
  });
  return usuarios
    .map((u) => ({ id: u.id, nombre: u.nombre, roles: u.roles.map((r) => r.role) }))
    .filter((p) => p.roles.some((rol) => rol !== "dpo"));
}
