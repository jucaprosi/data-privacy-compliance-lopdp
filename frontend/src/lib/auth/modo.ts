/**
 * Modo de autenticación del frontend. Replica el del servidor (AUTH_MODE en app_core/security.py).
 *
 *  - "oidc": la identidad es el token de Google de la sesión; el servidor ignora cualquier X-User-ID.
 *  - "headers": identidad declarada por cabeceras. Es el modo de desarrollo y de las pruebas de
 *    interfaz; el servidor solo lo acepta si se configura AUTH_MODE=headers de forma explícita.
 *
 * Por defecto, un build de producción (`next build`: Vercel y `next start`) arranca en "oidc" y el
 * servidor de desarrollo (`next dev`) en "headers". `NEXT_PUBLIC_AUTH_MODE` fuerza cualquiera de los dos.
 * Un valor desconocido cae en "oidc": ante la duda, el modo seguro.
 */
import { leerOrganizacionActiva } from "./organizacion";

export type ModoAutenticacion = "oidc" | "headers";

/**
 * Ajustes que las pruebas de interfaz fijan desde el navegador (`addInitScript`), para ejercitar
 * "oidc" sin variables de entorno ni un segundo servidor. Solo existen fuera de producción: en un
 * build de producción `NODE_ENV` es una constante y esta lectura se elimina.
 */
export interface AjustesDePrueba {
  modo?: ModoAutenticacion;
  clientId?: string;
  tenant?: string;
}

declare global {
  interface Window {
    __LOPDP_AUTH_PRUEBAS__?: AjustesDePrueba;
  }
}

function ajustesDePrueba(): AjustesDePrueba {
  if (process.env.NODE_ENV === "production" || typeof window === "undefined") return {};
  return window.__LOPDP_AUTH_PRUEBAS__ ?? {};
}

export function modoAutenticacion(): ModoAutenticacion {
  const forzado = ajustesDePrueba().modo;
  if (forzado === "oidc" || forzado === "headers") return forzado;
  const configurado = (process.env.NEXT_PUBLIC_AUTH_MODE ?? "").trim().toLowerCase();
  if (configurado === "headers") return "headers";
  if (configurado === "") return process.env.NODE_ENV === "production" ? "oidc" : "headers";
  return "oidc";
}

/** Identificador de cliente OAuth de Google (público por diseño). Vacío si no se configuró. */
export function clientIdGoogle(): string {
  return (ajustesDePrueba().clientId ?? process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID ?? "").trim();
}

/** Tenant fijado por una prueba de interfaz; vacío si ninguna lo fijó (nunca en producción). */
export function tenantDePrueba(): string {
  return (ajustesDePrueba().tenant ?? "").trim();
}

/**
 * Tenant de la organización con la que se trabaja.
 *
 * En "oidc" es la organización elegida al iniciar sesión (FE-21), guardada con la sesión; ya no se
 * fija por despliegue y sin elegir no hay ninguna. En "headers" (desarrollo) se conserva
 * NEXT_PUBLIC_TENANT_ID o el tenant de demostración de siempre. Una prueba puede fijarlo.
 */
export function tenantConfigurado(): string {
  const prueba = tenantDePrueba();
  if (prueba) return prueba;
  if (modoAutenticacion() === "oidc") return leerOrganizacionActiva()?.tenant_id ?? "";
  return (process.env.NEXT_PUBLIC_TENANT_ID ?? "").trim() || "tenant-corp-demo";
}
