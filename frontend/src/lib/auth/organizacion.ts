// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
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

// === FE-29 ===
/**
 * Por qué no se pudieron consultar las organizaciones (FE-29 R2). Se decide por el `code` estable del
 * servidor, nunca por el texto de `detail` (R1):
 * - `no_registrado`: 403 `USUARIO_NO_REGISTRADO`;
 * - `vinculada_otra`: 403 `CUENTA_VINCULADA_OTRA_IDENTIDAD`;
 * - `sin_permiso`: cualquier otro 403;
 * - `sesion`: 401;
 * - `servidor`: 5xx, otro estado o un cuerpo ilegible;
 * - `red`: `fetch` lanzó (sin conexión o petición abortada).
 */
export type TipoErrorDeAcceso = "no_registrado" | "vinculada_otra" | "sin_permiso" | "sesion" | "servidor" | "red";

export class ErrorDeAcceso extends Error {
  constructor(
    readonly estado: number | null,
    readonly codigo: string | null,
    readonly tipo: TipoErrorDeAcceso,
  ) {
    super(tipo);
    this.name = "ErrorDeAcceso";
  }
}

const TIPO_POR_CODIGO: Record<string, TipoErrorDeAcceso> = {
  USUARIO_NO_REGISTRADO: "no_registrado",
  CUENTA_VINCULADA_OTRA_IDENTIDAD: "vinculada_otra",
};

/** Clasifica una respuesta que no es 200 (R2). `codigo` es undefined si el cuerpo no se pudo leer. */
export function clasificarRespuesta(estado: number, codigo: string | null | undefined): TipoErrorDeAcceso {
  if (estado === 401) return "sesion";
  if (estado >= 500 || codigo === undefined) return "servidor";
  if (estado === 403) return (codigo && TIPO_POR_CODIGO[codigo]) || "sin_permiso";
  return "servidor";
}

/** El `code` del cuerpo; null si el cuerpo es JSON sin código y undefined si no es JSON legible. */
async function leerCodigo(respuesta: Response): Promise<string | null | undefined> {
  try {
    const cuerpo = (await respuesta.json()) as { code?: unknown } | null;
    return typeof cuerpo?.code === "string" ? cuerpo.code : null;
  } catch {
    return undefined;
  }
}
// === fin FE-29 ===

/**
 * Consulta las organizaciones de la persona con su token. No envía organización ni rol: el
 * servidor solo devuelve las suyas. Si no puede, lanza `ErrorDeAcceso` (FE-29).
 */
export async function consultarMisOrganizaciones(token: string): Promise<Organizacion[]> {
  let respuesta: Response;
  try {
    respuesta = await fetch(RUTA, { headers: { Authorization: `Bearer ${token}` } });
  } catch {
    throw new ErrorDeAcceso(null, null, "red");
  }
  if (!respuesta.ok) {
    const codigo = await leerCodigo(respuesta);
    throw new ErrorDeAcceso(respuesta.status, codigo ?? null, clasificarRespuesta(respuesta.status, codigo));
  }
  let cuerpo: { organizaciones?: unknown[] };
  try {
    cuerpo = (await respuesta.json()) as { organizaciones?: unknown[] };
  } catch {
    throw new ErrorDeAcceso(respuesta.status, null, "servidor");
  }
  return (Array.isArray(cuerpo?.organizaciones) ? cuerpo.organizaciones : []).filter(esOrganizacion);
}
