// ¤adpa ¤rbac-tenant
// ¤¤frontend-architect
/**
 * Cliente de API para plantillas de la cuenta profesional (BIB-401).
 *
 * Utiliza fetchAutenticado para las llamadas al backend y resuelve
 * los roles del usuario mediante /organizacion/me/roles.
 */
import { fetchAutenticado } from "@/lib/auth/fetchAutenticado";

/** Fallo al hablar con la API: lleva solo el código HTTP; el texto que ve la persona lo fija la vista (nunca el del servidor). */
export class ErrorPlantillasCuenta extends Error {
  constructor(public readonly estado: number) {
    super(`plantillas-cuenta: HTTP ${estado}`);
    this.name = "ErrorPlantillasCuenta";
  }
}

const API_BASE = "/api/v1/biblioteca/plantillas-cuenta";
const ROLES_URL = "/api/v1/organizacion/me/roles";

export interface PlantillaCuenta {
  id: string;
  cuenta_id: string;
  maestra_codigo: string;
  maestra_version: string;
  contenido_key?: string | null;
  contenido?: string | null;
  marca?: Record<string, unknown> | null;
  estado: "vigente" | "desactualizada" | "retirada";
  creado_por: string;
  creado_en: string;
  actualizado_en: string;
}

export interface DiffMaestra {
  maestra_vigente: string;
  cambios: string[];
}

export interface PlantillaCuentaCreate {
  maestra_codigo: string;
  marca?: Record<string, unknown>;
  contenido?: string;
}

export interface PlantillaCuentaUpdate {
  contenido?: string;
  marca?: Record<string, unknown>;
  estado?: string;
}

export interface RespuestaRoles {
  user_id: string;
  tenant_id: string;
  roles: string[];
}

/** Consulta los roles del usuario autenticado en la organización activa. */
export async function obtenerRolesUsuario(): Promise<string[]> {
  try {
    const res = await fetchAutenticado(ROLES_URL);
    if (!res.ok) return [];
    const data: RespuestaRoles = await res.json();
    return data.roles || [];
  } catch {
    return [];
  }
}

/** Determina si el usuario actual cuenta con rol 'implementador'. */
export async function esImplementador(): Promise<boolean> {
  const roles = await obtenerRolesUsuario();
  return roles.includes("implementador");
}

/** Lista las copias de plantilla pertenecientes a la cuenta profesional. */
export async function listarPlantillasCuenta(): Promise<PlantillaCuenta[]> {
  const res = await fetchAutenticado(API_BASE);
  if (!res.ok) throw new ErrorPlantillasCuenta(res.status);
  return res.json();
}

/** Obtiene una copia de plantilla de cuenta por ID. */
export async function obtenerPlantillaCuenta(id: string): Promise<PlantillaCuenta> {
  const res = await fetchAutenticado(`${API_BASE}/${id}`);
  if (!res.ok) throw new ErrorPlantillasCuenta(res.status);
  return res.json();
}

/** Crea una nueva copia de plantilla de cuenta desde una maestra publicada. */
export async function crearPlantillaCuenta(entrada: PlantillaCuentaCreate): Promise<PlantillaCuenta> {
  const res = await fetchAutenticado(API_BASE, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entrada),
  });
  if (!res.ok) throw new ErrorPlantillasCuenta(res.status);
  return res.json();
}

/** Actualiza contenido o marca de la copia de cuenta. */
export async function actualizarPlantillaCuenta(
  id: string,
  entrada: PlantillaCuentaUpdate,
): Promise<PlantillaCuenta> {
  const res = await fetchAutenticado(`${API_BASE}/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(entrada),
  });
  if (!res.ok) throw new ErrorPlantillasCuenta(res.status);
  return res.json();
}

/** Obtiene la diferencia textual entre la copia y la maestra vigente. */
export async function obtenerDiffMaestra(id: string): Promise<DiffMaestra> {
  const res = await fetchAutenticado(`${API_BASE}/${id}/diff`);
  if (!res.ok) throw new ErrorPlantillasCuenta(res.status);
  return res.json();
}

/** Aplica la versión más reciente de la maestra publicada a la copia de cuenta. */
export async function aplicarMaestra(id: string): Promise<PlantillaCuenta> {
  const res = await fetchAutenticado(`${API_BASE}/${id}/aplicar-maestra`, {
    method: "POST",
  });
  if (!res.ok) throw new ErrorPlantillasCuenta(res.status);
  return res.json();
}
