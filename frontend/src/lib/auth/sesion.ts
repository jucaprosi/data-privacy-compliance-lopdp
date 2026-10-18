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

/** Sesión vigente, o null. Una sesión caducada se descarta al leerla. */
export function leerSesion(): Sesion | null {
  const bruto = almacen()?.getItem(CLAVE);
  if (!bruto) return null;
  try {
    const sesion = JSON.parse(bruto) as Sesion;
    if (typeof sesion.token === "string" && typeof sesion.exp === "number" && !haCaducado(sesion.exp)) {
      return sesion;
    }
  } catch {
    // contenido corrupto: se trata como ausente
  }
  almacen()?.removeItem(CLAVE);
  return null;
}

/** Guarda la sesión a partir del token de Google. Devuelve false si el token no es utilizable. */
export function guardarSesion(token: string): boolean {
  const credencial = leerCredencial(token);
  if (!credencial || haCaducado(credencial.exp)) return false;
  const sesion: Sesion = { token, ...credencial };
  try {
    almacen()?.setItem(CLAVE, JSON.stringify(sesion));
  } catch {
    return false;
  }
  notificar(sesion);
  return true;
}

export function cerrarSesion(): void {
  almacen()?.removeItem(CLAVE);
  notificar(null);
}

export function suscribirSesion(oyente: Oyente): () => void {
  oyentes.add(oyente);
  return () => {
    oyentes.delete(oyente);
  };
}
