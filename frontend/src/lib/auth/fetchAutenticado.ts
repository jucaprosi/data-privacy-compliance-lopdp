/**
 * `fetch` con la identidad de la sesión y manejo único del 401.
 *
 * Un 401 en modo "oidc" significa que el token de Google caducó (dura en torno a una hora) o dejó de
 * valer: se descarta la sesión y se vuelve a pedir la identificación. En "headers" no hay sesión que
 * descartar y el 401 se devuelve tal cual.
 */
import { cabecerasDeTenant, type CabecerasIdentidad } from "./cabeceras";
import { modoAutenticacion } from "./modo";
import { cerrarSesion } from "./sesion";
// === DEMO-04 ===
import { cabecerasDeDemo } from "./cabeceras";
import { avisarDemoVencida } from "@/lib/demo/estado";

/** 401 con `codigo = DEMO_VENCIDA`: la demo terminó; se muestra su pantalla, no /login. */
async function esDemoVencida(respuesta: Response): Promise<boolean> {
  try {
    const cuerpo = (await respuesta.clone().json()) as { codigo?: string; detail?: { codigo?: string } };
    return (cuerpo?.codigo ?? cuerpo?.detail?.codigo) === "DEMO_VENCIDA";
  } catch {
    return false;
  }
}
// === fin DEMO-04 ===

export const RUTA_LOGIN = "/login";

/** Descarta la sesión y lleva a /login. No hace nada si ya se está en /login. */
export function alExpirarLaSesion(): void {
  if (modoAutenticacion() !== "oidc") return;
  cerrarSesion();
  if (typeof window !== "undefined" && !window.location.pathname.startsWith(RUTA_LOGIN)) {
    window.location.assign(`${RUTA_LOGIN}?motivo=expirada`);
  }
}

export async function fetchAutenticado(
  input: RequestInfo | URL,
  init: RequestInit = {},
  cabeceras: CabecerasIdentidad = cabecerasDeTenant(),
): Promise<Response> {
  const propias = (init.headers ?? {}) as Record<string, string>;
  // === DEMO-04 ===
  const demo = cabecerasDeDemo();
  const respuesta = await fetch(input, { ...init, headers: { ...cabeceras, ...demo, ...propias } });
  if (respuesta.status === 401 && (await esDemoVencida(respuesta))) {
    avisarDemoVencida();
    return respuesta;
  }
  // === fin DEMO-04 ===
  if (respuesta.status === 401) alExpirarLaSesion();
  return respuesta;
}
