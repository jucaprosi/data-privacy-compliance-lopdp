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

/**
 * Tenant de la organización de la sesión.
 *
 * En "oidc" sale solo de la configuración (NEXT_PUBLIC_TENANT_ID) y no hay valor por defecto: una
 * organización por despliegue. Elegir entre varias exige un servicio de «mis organizaciones» que la
 * API aún no ofrece. En "headers" (desarrollo) se conserva el tenant de demostración de siempre.
 */
export function tenantConfigurado(): string {
  const configurado = (ajustesDePrueba().tenant ?? process.env.NEXT_PUBLIC_TENANT_ID ?? "").trim();
  if (configurado) return configurado;
  return modoAutenticacion() === "headers" ? "tenant-corp-demo" : "";
}
