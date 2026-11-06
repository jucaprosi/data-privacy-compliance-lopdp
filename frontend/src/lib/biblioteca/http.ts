// ¤adpa ¤rbac-tenant
// ¤¤developer-architect
/**
 * Cliente común Biblioteca: identidad del miembro, roles por ruta y errores del servidor.
 *
 * BIB-115: las rutas de Biblioteca resuelven al usuario con `get_context` (`api/rbac.py`), que exige
 * `X-Tenant-ID` y `X-Role` (y `X-User-ID` en modo "headers"). Toda petición de Biblioteca arma su
 * identidad con `cabecerasDeMiembro`; solo la administración editorial, que es global, usa la de plataforma.
 */
import {
  cabecerasDeMiembro,
  cabecerasDePlataforma,
  SinRolPermitido,
  type CabecerasIdentidad,
} from "@/lib/auth/cabeceras";
import { fetchAutenticado } from "@/lib/auth";

/** Roles de cada `require_role` de `api/routers/biblioteca_*.py`. Si el router cambia, cambia aquí. */
export const ROLES_EDITORES = ["admin_organizacion", "dpo", "coordinador", "implementador"] as const;
export const ROLES_GESTION_DOCUMENTAL = ["admin_organizacion", "implementador", "coordinador"] as const;
export const ROLES_DECIDIR_IMPACTO = ["admin_organizacion", "coordinador", "dpo"] as const;
export const ROLES_APORTAR_EVIDENCIA = ["admin_organizacion", "implementador", "coordinador", "responsable_area"] as const;
export const ROLES_REVISAR_EVIDENCIA = ["admin_organizacion", "coordinador", "dpo"] as const;
// Vínculos: `ROLES_QUE_VINCULAN` en `vinculos.ts`.

export class ErrorBiblioteca extends Error {
  constructor(public codigo: string, mensaje: string, public estado: number) { super(mensaje); }
}

interface ErrorDeValidacion { loc?: unknown[]; msg?: string }

/**
 * Mensaje legible de una respuesta de error: el `detail` del servidor si es texto, su `message` si
 * es un objeto, o la cabecera que falta si FastAPI rechazó la petición (422) por una cabecera.
 */
export function mensajeDelServidor(cuerpo: unknown, porDefecto: string): string {
  const detalle = (cuerpo as { detail?: unknown } | null)?.detail;
  if (typeof detalle === "string" && detalle) return detalle;
  if (Array.isArray(detalle)) {
    const cabecera = (detalle as ErrorDeValidacion[]).find((e) => e?.loc?.[0] === "header");
    if (cabecera) return `Falta la cabecera ${String(cabecera.loc?.[1] ?? "")}`.trim();
    const primero = (detalle as ErrorDeValidacion[])[0];
    if (typeof primero?.msg === "string") return primero.msg;
  }
  const mensaje = (detalle as { message?: unknown } | null)?.message;
  return typeof mensaje === "string" && mensaje ? mensaje : porDefecto;
}

/**
 * Si la respuesta es un rechazo de identidad (401, 403, o 422 por una cabecera de identidad),
 * devuelve el mensaje que debe verse; si no, `null`.
 */
export function rechazoDeIdentidad(estado: number, cuerpo: unknown, porDefecto: string): string | null {
  if (estado === 401 || estado === 403) return mensajeDelServidor(cuerpo, porDefecto);
  if (estado !== 422) return null;
  const mensaje = mensajeDelServidor(cuerpo, "");
  return mensaje.startsWith("Falta la cabecera") ? mensaje : null;
}

/** Mensaje de un fallo previo al envío por falta de rol; `null` si el fallo es de otro tipo. */
export function falloDeRol(error: unknown): string | null {
  return error instanceof SinRolPermitido ? error.message : null;
}

const RUTAS_DE_PLATAFORMA = /^\/biblioteca\/editorial(\/|$|\?)/;

/** Roles que admite cada escritura servida por `httpBiblioteca` (método y ruta sin `/api/v1`). */
const ROLES_POR_RUTA: ReadonlyArray<{ metodo: string; ruta: RegExp; roles: readonly string[] }> = [
  { metodo: "POST", ruta: /^\/biblioteca\/documentos$/, roles: ROLES_GESTION_DOCUMENTAL },
  { metodo: "POST", ruta: /^\/biblioteca\/plantillas\/[^/]+\/copias$/, roles: ROLES_EDITORES },
  { metodo: "POST", ruta: /^\/biblioteca\/documentos\/[^/]+\/(restauraciones|eventos)$/, roles: ROLES_GESTION_DOCUMENTAL },
  { metodo: "PUT", ruta: /^\/biblioteca\/documentos\/[^/]+\/conservacion$/, roles: ROLES_GESTION_DOCUMENTAL },
  { metodo: "PUT", ruta: /^\/biblioteca\/impactos\/[^/]+\/decision$/, roles: ROLES_DECIDIR_IMPACTO },
  { metodo: "*", ruta: /^\/biblioteca\/fuentes\//, roles: ROLES_EDITORES },
];

/** Identidad de una ruta de Biblioteca (sin `/api/v1`); lanza `SinRolPermitido` si no hay rol válido. */
export function identidadPara(ruta: string, metodo = "GET"): CabecerasIdentidad {
  if (RUTAS_DE_PLATAFORMA.test(ruta)) return cabecerasDePlataforma();
  const camino = ruta.split("?")[0];
  const regla = ROLES_POR_RUTA.find((r) => (r.metodo === "*" || r.metodo === metodo.toUpperCase()) && r.ruta.test(camino));
  return cabecerasDeMiembro(regla?.roles);
}

export async function httpBiblioteca<T>(ruta: string, init: RequestInit = {}): Promise<T> {
  let identidad: CabecerasIdentidad;
  try {
    identidad = identidadPara(ruta, init.method);
  } catch (error) {
    const mensaje = falloDeRol(error);
    if (mensaje) throw new ErrorBiblioteca("BIB_SIN_ROL", mensaje, 403);
    throw error;
  }
  const respuesta = await fetchAutenticado(`/api/v1${ruta}`, {
    ...init, cache: "no-store",
    headers: { "Content-Type": "application/json", ...init.headers },
  }, identidad);
  const cuerpo = await respuesta.json().catch(() => null);
  if (!respuesta.ok) {
    throw new ErrorBiblioteca(cuerpo?.code ?? "BIB_ERROR_HTTP",
      mensajeDelServidor(cuerpo, "No se pudo completar la operación."), respuesta.status);
  }
  return cuerpo as T;
}
