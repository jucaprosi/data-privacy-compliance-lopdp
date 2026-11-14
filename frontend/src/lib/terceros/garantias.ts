/**
 * Cliente de contrato y garantía de terceros con hallazgos automáticos (TER-01).
 *
 * Contrato: governance/especificaciones/TER-01.md §2. Los textos que ve la persona son fijos por
 * caso (revisión UX/UI): nunca se muestra el texto del servidor.
 */
import { fetchAutenticado } from "@/lib/auth";
import { cabecerasComo, rolesDelUsuario } from "@/lib/diagnostico/roles";

/** Rol con el que se actúa en Terceros: el que más puede de los que tiene la persona (el servidor lo comprueba). */
const ORDEN_ROLES = ["implementador", "coordinador", "dpo", "admin_organizacion", "auditor"] as const;

async function cabeceras(): Promise<Record<string, string>> {
  const roles = await rolesDelUsuario().catch(() => [] as string[]);
  const rol = ORDEN_ROLES.find((r) => roles.includes(r));
  if (!rol) throw new Error("sin-rol");
  return cabecerasComo(rol);
}

export type RolTercero = "ENCARGADO" | "SUBENCARGADO" | "DESTINATARIO";
export type TipoGarantia =
  | "nivel_adecuado"
  | "clausulas_tipo"
  | "normas_corporativas"
  | "autorizacion_spdp"
  | "caso_excepcional";
export type Criticidad = "baja" | "media" | "alta";

export interface HallazgoTercero {
  id: string;
  origen_ref: string;
  estado: string;
  regla: "contrato" | "garantia";
}

export interface TerceroGarantias {
  id: string;
  nombre: string;
  rol: RolTercero;
  pais: string | null;
  contrato_sha256: string | null;
  contrato_vigente_hasta: string | null;
  garantia_tipo: TipoGarantia | null;
  garantia_sha256: string | null;
  criticidad: Criticidad | null;
  proxima_revision: string | null;
  hallazgos: HallazgoTercero[];
}

export interface PermisosTerceros {
  gestionar: boolean;
  evaluar: boolean;
}

export interface EntradaGarantias {
  rol?: RolTercero;
  pais?: string | null;
  contrato_sha256?: string | null;
  contrato_vigente_hasta?: string | null;
  garantia_tipo?: TipoGarantia | null;
  garantia_sha256?: string | null;
  criticidad?: Criticidad | null;
  proxima_revision?: string | null;
}

export const ROLES: Record<RolTercero, string> = {
  ENCARGADO: "Encargado",
  SUBENCARGADO: "Subencargado",
  DESTINATARIO: "Destinatario",
};

export const TIPOS_GARANTIA: Record<TipoGarantia, string> = {
  nivel_adecuado: "País con nivel adecuado",
  clausulas_tipo: "Cláusulas contractuales tipo",
  normas_corporativas: "Normas corporativas vinculantes",
  autorizacion_spdp: "Autorización de la Autoridad",
  caso_excepcional: "Caso excepcional",
};

export const CRITICIDADES: Record<Criticidad, string> = { baja: "Baja", media: "Media", alta: "Alta" };

/** Países ofrecidos en el selector; el código ISO se guarda por detrás. */
export const CODIGOS_PAIS = [
  "EC", "AR", "BR", "CA", "CL", "CN", "CO", "DE", "ES", "FR", "GB", "IE", "IN", "IT",
  "JP", "MX", "NL", "PA", "PE", "PT", "SG", "US", "UY",
] as const;

export function nombrePais(codigo: string): string {
  try {
    return new Intl.DisplayNames(["es"], { type: "region" }).of(codigo) ?? codigo;
  } catch {
    return codigo;
  }
}

export const TEXTOS = {
  cargando: "Cargando terceros…",
  errorCarga: "No pudimos cargar los terceros. Inténtalo de nuevo.",
  errorGuardar: "No pudimos guardar las garantías. Inténtalo de nuevo.",
  errorEvaluar: "No pudimos evaluar los terceros. Inténtalo de nuevo.",
  sinContrato: "Sin contrato",
  vencido: "Vencido",
  sinGarantia: "Sin garantía registrada",
  hallazgoGarantia: "Hallazgo crítico: transferencia sin garantía registrada",
  hallazgoContrato: "Hallazgo alto: encargado sin contrato",
} as const;

export function formatearFecha(iso: string): string {
  const [a, m, d] = iso.split("-");
  return `${d}/${m}/${a}`;
}

export function textoContrato(t: TerceroGarantias, hoy: string): string {
  if (!t.contrato_sha256) return TEXTOS.sinContrato;
  if (t.contrato_vigente_hasta && t.contrato_vigente_hasta < hoy) return TEXTOS.vencido;
  return t.contrato_vigente_hasta ? `Vigente hasta ${formatearFecha(t.contrato_vigente_hasta)}` : "Registrado";
}

export function textoGarantia(t: TerceroGarantias): string {
  return t.garantia_tipo && t.garantia_sha256 ? TIPOS_GARANTIA[t.garantia_tipo] : TEXTOS.sinGarantia;
}

export function textoEvaluacion(creados: number, cerrados: number): string {
  const c = creados === 1 ? "1 hallazgo creado" : `${creados} hallazgos creados`;
  const k = cerrados === 1 ? "1 cerrado" : `${cerrados} cerrados`;
  return `Evaluación terminada: ${c} y ${k}.`;
}

export async function cargarTerceros(): Promise<{ terceros: TerceroGarantias[]; permisos: PermisosTerceros }> {
  const res = await fetchAutenticado("/api/v1/terceros/garantias", {}, await cabeceras());
  if (!res.ok) throw new Error("carga");
  return (await res.json()) as { terceros: TerceroGarantias[]; permisos: PermisosTerceros };
}

export async function guardarGarantias(id: string, entrada: EntradaGarantias): Promise<TerceroGarantias> {
  const res = await fetchAutenticado(`/api/v1/terceros/${encodeURIComponent(id)}/garantias`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entrada),
  }, await cabeceras());
  if (!res.ok) throw new Error("guardar");
  return (await res.json()) as TerceroGarantias;
}

export async function evaluarTerceros(): Promise<{ hallazgos_creados: number; cerrados: number }> {
  const res = await fetchAutenticado("/api/v1/terceros/evaluar", { method: "POST" }, await cabeceras());
  if (!res.ok) throw new Error("evaluar");
  return (await res.json()) as { hallazgos_creados: number; cerrados: number };
}
