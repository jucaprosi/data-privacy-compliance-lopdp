// ¤riesgos-eipd ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Cliente de la evaluación de impacto guiada (MTGE-03). Llama a la API por fetchAutenticado y
 * resuelve los roles con /organizacion/me/roles; el servidor vuelve a comprobarlos en cada escritura.
 */
import { cabecerasDeTenant, fetchAutenticado } from "@/lib/auth";

const BASE = "/api/v1/eipd";

export type NivelRiesgo = "bajo" | "medio" | "alto";
export type Decision = "aceptar" | "medidas" | "consulta_previa";

export interface PuntoCorregir {
  id: string;
  texto: string;
  hallazgo_id: string | null;
}

export interface Eipd {
  id: string;
  tratamiento_id: string;
  obligatoria: boolean;
  obligatoria_por_ley: boolean;
  motivo_obligatoriedad: string;
  paso_actual: number;
  consulta_titulares: string | null;
  ciclo_vida: { fases: string[]; amenazas: string[] } | null;
  necesidad: string | null;
  riesgo_inherente: NivelRiesgo | null;
  riesgo_residual: NivelRiesgo | null;
  decision: Decision | null;
  decision_texto: string | null;
  informe_sha256: string | null;
  cerrada_en: string | null;
  creado_en: string;
  puntos: PuntoCorregir[];
}

export interface Catalogos {
  fases: Record<string, string>;
  amenazas: Record<string, string>;
}

export interface Tratamiento {
  id: string;
  nombre: string;
}

/** Fallo de la API: solo el código HTTP y el `code` de negocio; el texto lo fija la vista. */
export class ErrorEipd extends Error {
  constructor(public readonly estado: number, public readonly codigo: string | null) {
    super(`eipd: HTTP ${estado}${codigo ? ` ${codigo}` : ""}`);
    this.name = "ErrorEipd";
  }
}

/** Mensajes fijos por código; nunca se muestra el texto del servidor. */
export const MENSAJES_ERROR: Record<string, string> = {
  EIPD_OBLIGATORIA: "La ley exige esta evaluación para este tratamiento; no puede marcarse como no obligatoria.",
  EIPD_SIN_DECISION: "Con riesgo residual alto, elige una decisión antes de cerrar.",
  EIPD_PASO_INCOMPLETO: "Completa los pasos 1 a 7 antes de cerrar la evaluación.",
  EIPD_CERRADA: "La evaluación está cerrada y ya no se puede modificar.",
  EIPD_NO_ENCONTRADA: "No se encontró la evaluación.",
  EIPD_TRATAMIENTO_NO_ENCONTRADO: "No se encontró el tratamiento en el registro de actividades.",
  EIPD_PASO_INVALIDO: "Revisa los datos de este paso.",
  EIPD_CUSTODIA_NO_DISPONIBLE: "Aún no se puede guardar el informe; la evaluación sigue abierta.",
};
export const MENSAJE_GENERICO = "No se pudo completar la operación. Intenta de nuevo.";

export function mensajeDeError(error: unknown): string {
  if (error instanceof ErrorEipd) {
    if (error.codigo && MENSAJES_ERROR[error.codigo]) return MENSAJES_ERROR[error.codigo];
    if (error.estado === 403) return "Tu rol no permite esta acción.";
  }
  return MENSAJE_GENERICO;
}

async function pedir<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  const r = await fetchAutenticado(ruta, { cache: "no-store", ...init }, cabecerasDeTenant());
  if (!r.ok) {
    let codigo: string | null = null;
    try {
      const cuerpo = await r.json();
      codigo = typeof cuerpo?.code === "string" ? cuerpo.code : null;
    } catch {
      codigo = null;
    }
    throw new ErrorEipd(r.status, codigo);
  }
  return (await r.json()) as T;
}

function json(metodo: string, cuerpo?: unknown): RequestInit {
  return {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: cuerpo === undefined ? undefined : JSON.stringify(cuerpo),
  };
}

export const listarEipd = () => pedir<Eipd[]>(BASE);
export const obtenerEipd = (id: string) => pedir<Eipd>(`${BASE}/${encodeURIComponent(id)}`);
export const crearEipd = (tratamientoId: string) => pedir<Eipd>(BASE, json("POST", { tratamiento_id: tratamientoId }));
export const guardarPaso = (id: string, n: number, cuerpo: Record<string, unknown>) =>
  pedir<Eipd>(`${BASE}/${encodeURIComponent(id)}/paso/${n}`, json("PUT", cuerpo));
export const cerrarEipd = (id: string) =>
  pedir<{ informe_sha256: string }>(`${BASE}/${encodeURIComponent(id)}/cerrar`, json("POST"));
export const informeEipd = (id: string) =>
  pedir<{ informe: Record<string, unknown>; informe_sha256: string; integro: boolean }>(
    `${BASE}/${encodeURIComponent(id)}/informe`);
export const catalogosEipd = () => pedir<Catalogos>(`${BASE}/catalogos`);

export async function listarTratamientos(): Promise<Tratamiento[]> {
  const cuerpo = await pedir<{ actividades: Tratamiento[] }>("/api/v1/rat/actividades");
  return (cuerpo.actividades ?? []).map((a) => ({ id: a.id, nombre: a.nombre }));
}

export async function misRolesEipd(): Promise<string[]> {
  try {
    const r = await fetchAutenticado("/api/v1/organizacion/me/roles", { cache: "no-store" }, cabecerasDeTenant());
    if (!r.ok) return [];
    const cuerpo = await r.json();
    const lista = Array.isArray(cuerpo) ? cuerpo : Array.isArray(cuerpo?.roles) ? cuerpo.roles : [];
    return lista.map((x: unknown) => (typeof x === "string" ? x : String((x as { role?: string })?.role ?? "")));
  } catch {
    return [];
  }
}

export const ROLES_ESCRITURA = ["implementador", "coordinador"] as const;
export const puedeEditar = (roles: readonly string[]) =>
  roles.some((r) => (ROLES_ESCRITURA as readonly string[]).includes(r));
export const puedeCerrar = (roles: readonly string[]) => roles.includes("implementador");

/** La decisión es obligatoria para cerrar solo con residual alto (R3). */
export const cierreBloqueado = (residual: NivelRiesgo | null, decision: Decision | null) =>
  residual === "alto" && decision === null;

export const NIVELES: Record<NivelRiesgo, string> = { bajo: "Bajo", medio: "Medio", alto: "Alto" };
export const DECISIONES: Record<Decision, string> = {
  aceptar: "Aceptar el riesgo",
  medidas: "Aplicar nuevas medidas",
  consulta_previa: "Consultar a la Autoridad antes del tratamiento",
};
