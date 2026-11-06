/**
 * Sesión del navegador: el token de identidad de Google y poco más.
 *
 * Dónde se guarda y por qué: en `sessionStorage`. Desaparece al cerrar la pestaña, no se comparte
 * entre pestañas y el navegador nunca lo envía solo (a diferencia de una cookie, no hay CSRF). Su
 * riesgo es el de cualquier almacenamiento legible por script (XSS), que se acota con la política de
 * seguridad de contenido (SEC-06) y con la vida corta del token (en torno a una hora). No se usa
 * `localStorage`: persistiría días después de cerrar el navegador.
 *
 * El token nunca va en la URL ni en consola. Aquí solo se LEE su carga útil para mostrar el correo y
 * saber cuándo caduca; la verificación (firma, emisor, audiencia) es del servidor.
 */
import { modoAutenticacion, tenantDePrueba } from "./modo";
import { leerOrganizacionActiva, olvidarOrganizaciones } from "./organizacion";

const CLAVE = "lopdp-sesion-v1";
/** Margen para no enviar un token a punto de caducar. */
const MARGEN_SEGUNDOS = 30;

export interface Sesion {
  token: string;
  email: string;
  nombre: string;
  /** Instante de caducidad, en segundos desde 1970 (claim `exp`). */
  exp: number;
}

type Oyente = (sesion: Sesion | null) => void;
const oyentes = new Set<Oyente>();

function almacen(): Storage | null {
  try {
    return typeof window !== "undefined" ? window.sessionStorage : null;
  } catch {
    return null; // navegación privada o almacenamiento bloqueado
  }
}

function base64UrlADecodificado(parte: string): string {
  const base64 = parte.replace(/-/g, "+").replace(/_/g, "/");
  const relleno = base64 + "=".repeat((4 - (base64.length % 4)) % 4);
  const binario = atob(relleno);
  const bytes = Uint8Array.from(binario, (c) => c.charCodeAt(0));
  return new TextDecoder().decode(bytes);
}

/** Lee la carga útil del token SIN verificarlo. Devuelve null si no tiene forma de JWT con `exp`. */
export function leerCredencial(token: string): Omit<Sesion, "token"> | null {
  const partes = token.split(".");
  if (partes.length !== 3) return null;
  try {
    const carga = JSON.parse(base64UrlADecodificado(partes[1])) as Record<string, unknown>;
    if (typeof carga.exp !== "number") return null;
    const email = typeof carga.email === "string" ? carga.email : "";
    const nombre = typeof carga.name === "string" ? carga.name : email;
    return { email, nombre, exp: carga.exp };
  } catch {
    return null;
  }
}

export function haCaducado(exp: number, ahoraMs: number = Date.now()): boolean {
  return exp - MARGEN_SEGUNDOS <= Math.floor(ahoraMs / 1000);
}

function notificar(sesion: Sesion | null): void {
  oyentes.forEach((oyente) => oyente(sesion));
}

/**
 * Sesión vigente, o null. Una sesión caducada se descarta al leerla. En "oidc" la sesión va unida a
 * una organización elegida (FE-21): una sesión sin organización (por ejemplo, abierta antes de
 * existir la elección) también se descarta y se vuelve a iniciar.
 */
export function leerSesion(): Sesion | null {
  const bruto = almacen()?.getItem(CLAVE);
  if (!bruto) return null;
  try {
    const sesion = JSON.parse(bruto) as Sesion;
    const conOrganizacion = modoAutenticacion() !== "oidc" || Boolean(tenantDePrueba() || leerOrganizacionActiva());
    if (typeof sesion.token === "string" && typeof sesion.exp === "number" && !haCaducado(sesion.exp) && conOrganizacion) {
      return sesion;
    }
  } catch {
    // contenido corrupto: se trata como ausente
  }
  almacen()?.removeItem(CLAVE);
  return null;
}

// === ORG-21 ===
/**
 * Sesión del operador de la plataforma sin organización (ORG-21), en su propia clave. `leerSesion`
 * descarta y borra toda sesión sin organización activa (FE-21), y la llaman stores globales en
 * cualquier página: guardada en `CLAVE` desaparecería al llegar a /plataforma. En esta clave el
 * resto de la aplicación no la ve, y las demás pantallas siguen sin sesión para el operador.
 */
const CLAVE_OPERADOR = "lopdp-sesion-operador-v1";

function sesionVigente(bruto: string | null | undefined): Sesion | null {
  if (!bruto) return null;
  try {
    const sesion = JSON.parse(bruto) as Sesion;
    if (typeof sesion.token === "string" && typeof sesion.exp === "number" && !haCaducado(sesion.exp)) return sesion;
  } catch {
    // contenido corrupto: se trata como ausente
  }
  return null;
}

/** Guarda la sesión del operador sin organización. Devuelve false si el token no es utilizable. */
export function guardarSesionDeOperador(token: string): boolean {
  const credencial = leerCredencial(token);
  if (!credencial || haCaducado(credencial.exp)) return false;
  try {
    almacen()?.setItem(CLAVE_OPERADOR, JSON.stringify({ token, ...credencial }));
  } catch {
    return false;
  }
  return true;
}

/**
 * Sesión vigente para hablar con `/api/v1/plataforma`, o null: la del operador sin organización o,
 * si no la hay, la sesión normal (un operador que sí pertenece a una organización). Comprueba forma
 * y caducidad, sin exigir organización activa. Solo la usa `cabecerasDePlataforma`; el servidor
 * decide en cada ruta con `verificar_operador`.
 */
export function leerSesionDeOperador(): Sesion | null {
  return sesionVigente(almacen()?.getItem(CLAVE_OPERADOR)) ?? sesionVigente(almacen()?.getItem(CLAVE));
}

function olvidarSesionDeOperador(): void {
  almacen()?.removeItem(CLAVE_OPERADOR);
}
// === fin ORG-21 ===

/**
 * Guarda la sesión a partir del token de Google. Devuelve false si el token no es utilizable.
 * Con `avisar: false` no despierta a quienes escuchan la sesión: se usa justo antes de recargar
 * la página, para que nada se sincronice con datos de la organización anterior.
 */
export function guardarSesion(token: string, { avisar = true }: { avisar?: boolean } = {}): boolean {
  const credencial = leerCredencial(token);
  if (!credencial || haCaducado(credencial.exp)) return false;
  const sesion: Sesion = { token, ...credencial };
  try {
    almacen()?.setItem(CLAVE, JSON.stringify(sesion));
  } catch {
    return false;
  }
  if (avisar) notificar(sesion);
  return true;
}

export function cerrarSesion(): void {
  almacen()?.removeItem(CLAVE);
  // === ORG-21 ===
  olvidarSesionDeOperador();
  // === fin ORG-21 ===
  olvidarOrganizaciones();
  notificar(null);
}

export function suscribirSesion(oyente: Oyente): () => void {
  oyentes.add(oyente);
  return () => {
    oyentes.delete(oyente);
  };
}
