/**
 * Organización con la que se trabaja (FE-21).
 *
 * Una persona puede pertenecer a varias organizaciones como DPO o implementador (ORG-13). Al
 * iniciar sesión se consultan las suyas (`GET /organizacion/mis-organizaciones`) y la elegida queda
 * en `sessionStorage`, con la misma vida que el token: es la que llevan todas las peticiones en
 * `X-Tenant-ID`. La organización ya no se fija por despliegue.
 *
 * Con varias organizaciones, la credencial de Google queda «pendiente» (sin abrir la sesión) hasta
 * elegir: así nada se sincroniza con el servidor antes de saber con qué organización.
 */
const CLAVE_ACTIVA = "lopdp-organizacion-activa-v1";
const CLAVE_LISTA = "lopdp-mis-organizaciones-v1";
const CLAVE_PENDIENTE = "lopdp-credencial-pendiente-v1";
const RUTA = "/api/v1/organizacion/mis-organizaciones";
/** Pantalla donde se elige o se cambia de organización. */
export const RUTA_ORGANIZACIONES = "/organizaciones";

export interface Organizacion {
  tenant_id: string;
  nombre_comercial: string;
  roles: string[];
}

function almacen(): Storage | null {
  try {
    return typeof window !== "undefined" ? window.sessionStorage : null;
  } catch {
    return null;
  }
}

function leerJson<T>(clave: string): T | null {
  const bruto = almacen()?.getItem(clave);
  if (!bruto) return null;
  try {
    return JSON.parse(bruto) as T;
  } catch {
    almacen()?.removeItem(clave);
    return null;
  }
}

function esOrganizacion(valor: unknown): valor is Organizacion {
  const o = valor as Organizacion | null;
  return Boolean(o && typeof o.tenant_id === "string" && o.tenant_id && Array.isArray(o.roles));
}

export function leerOrganizacionActiva(): Organizacion | null {
  const org = leerJson<Organizacion>(CLAVE_ACTIVA);
  return esOrganizacion(org) ? org : null;
}

export function guardarOrganizacionActiva(org: Organizacion): void {
  almacen()?.setItem(CLAVE_ACTIVA, JSON.stringify(org));
}

/** Organizaciones de la persona, tal como las devolvió el servidor al iniciar sesión. */
export function leerMisOrganizaciones(): Organizacion[] {
  const lista = leerJson<unknown[]>(CLAVE_LISTA);
  return Array.isArray(lista) ? lista.filter(esOrganizacion) : [];
}

export function guardarMisOrganizaciones(lista: Organizacion[]): void {
  almacen()?.setItem(CLAVE_LISTA, JSON.stringify(lista));
}

export function leerCredencialPendiente(): string | null {
  return almacen()?.getItem(CLAVE_PENDIENTE) ?? null;
}

export function guardarCredencialPendiente(token: string): void {
  almacen()?.setItem(CLAVE_PENDIENTE, token);
}

/** Olvida organización activa, lista y credencial pendiente (al cerrar sesión). */
export function olvidarOrganizaciones(): void {
  const a = almacen();
  [CLAVE_ACTIVA, CLAVE_LISTA, CLAVE_PENDIENTE].forEach((clave) => a?.removeItem(clave));
}

export function olvidarCredencialPendiente(): void {
  almacen()?.removeItem(CLAVE_PENDIENTE);
}

/**
 * Consulta las organizaciones de la persona con su token. No envía organización ni rol: el
 * servidor solo devuelve las suyas.
 */
export async function consultarMisOrganizaciones(token: string): Promise<Organizacion[]> {
  const respuesta = await fetch(RUTA, { headers: { Authorization: `Bearer ${token}` } });
  if (!respuesta.ok) {
    throw new Error(`el servidor respondió ${respuesta.status}`);
  }
  const cuerpo = (await respuesta.json()) as { organizaciones?: unknown[] };
  return (cuerpo.organizaciones ?? []).filter(esOrganizacion);
}
