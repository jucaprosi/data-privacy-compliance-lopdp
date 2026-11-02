// ¤adpa ¤rbac-tenant
// ¤¤developer-architect
/**
 * Contexto de Biblioteca (BIB-101): con qué organización se trabaja y cómo se pide al servidor.
 *
 * D2 (2026-10-27): el PMV usa la organización de la sesión. El frontend nunca la pone en la URL ni
 * en el cuerpo: viaja solo en las cabeceras de identidad (`cabecerasDeTenant`), y el servidor la
 * autoriza contra la membresía del usuario verificado. Una organización ajena se rechaza allí, no aquí.
 */
import { cabecerasDeTenant, fetchAutenticado, tenantConfigurado } from "@/lib/auth";

export type PestanaBiblioteca = "documentos" | "plantillas";

export const PESTANAS: ReadonlyArray<{ id: PestanaBiblioteca; nombre: string }> = [
  { id: "documentos", nombre: "Documentos de la organización" },
  { id: "plantillas", nombre: "Plantillas" },
];

/** Contador del botón fijo (`GET /documentos/pendientes`, contrato de `docs/biblioteca-pmv.md`). */
export interface Pendientes {
  borrador: number;
  en_revision: number;
  por_vencer: number;
  vencidos: number;
  total: number;
}

/**
 * Resultado de pedir los pendientes. `no_disponible`: el servidor aún no ofrece la ruta (la crea
 * BIB-107); el botón funciona igual, sin contador. `denegado`: el servidor rechazó la organización.
 */
export type ResultadoPendientes =
  | { estado: "listo"; pendientes: Pendientes }
  | { estado: "no_disponible" }
  | { estado: "denegado"; mensaje: string }
  | { estado: "error"; mensaje: string };

export const RUTA_PENDIENTES = "/api/v1/biblioteca/documentos/pendientes";

/** Organización de la sesión; vacío si todavía no se eligió ninguna. */
export function organizacionDeLaSesion(): string {
  return tenantConfigurado();
}

function esPendientes(valor: unknown): valor is Pendientes {
  const p = valor as Pendientes | null;
  return Boolean(p) && ["borrador", "en_revision", "por_vencer", "vencidos", "total"]
    .every((campo) => Number.isInteger((p as unknown as Record<string, unknown>)[campo]));
}

export async function consultarPendientes(): Promise<ResultadoPendientes> {
  let respuesta: Response;
  try {
    respuesta = await fetchAutenticado(RUTA_PENDIENTES, { cache: "no-store" }, cabecerasDeTenant());
  } catch {
    return { estado: "error", mensaje: "No se pudo consultar Biblioteca." };
  }
  const cuerpo = await respuesta.json().catch(() => null);
  if (respuesta.status === 404 || respuesta.status === 405 || respuesta.status === 501) {
    return { estado: "no_disponible" };
  }
  if (respuesta.status === 401 || respuesta.status === 403) {
    return {
      estado: "denegado",
      mensaje: typeof cuerpo?.detail === "string" ? cuerpo.detail : "No tienes acceso a la Biblioteca de esta organización.",
    };
  }
  if (!respuesta.ok || !esPendientes(cuerpo)) {
    return { estado: "error", mensaje: "No se pudo consultar Biblioteca." };
  }
  return { estado: "listo", pendientes: cuerpo };
}
