/**
 * Utilidades de las pruebas de inicio de sesión (FE-07).
 *
 * No hay Google real: la credencial es un JWT con la forma correcta y firma inventada, porque el
 * navegador solo lee su carga útil (correo y caducidad) y la verificación es del servidor. El script
 * de Google Identity Services se sustituye por uno que pinta un botón y entrega esa credencial.
 *
 * Las pruebas fijan el modo, el cliente de Google y el tenant desde el navegador
 * (`window.__LOPDP_AUTH_PRUEBAS__`, que solo existe fuera de producción), así el mismo servidor de
 * desarrollo sirve a las pruebas en modo "headers" y en "oidc".
 */
import { type Page, type Request, type Route } from "@playwright/test";

export const CLIENT_ID_PRUEBA = "cliente-de-prueba.apps.googleusercontent.com";
export const TENANT_PRUEBA = "tenant-de-prueba";
export const CLAVE_SESION = "lopdp-sesion-v1";
export const BOTON_GOOGLE = "Continuar con Google (simulado)";

const base64url = (objeto: unknown) => Buffer.from(JSON.stringify(objeto)).toString("base64url");

export interface OpcionesCredencial {
  email?: string;
  nombre?: string;
  /** Segundos hasta que caduca; negativo = ya caducada. */
  expiraEnSegundos?: number;
}

export function credencialSimulada({ email = "ana@empresa.test", nombre = "Ana Prueba", expiraEnSegundos = 3600 }: OpcionesCredencial = {}) {
  const exp = Math.floor(Date.now() / 1000) + expiraEnSegundos;
  const token = [
    base64url({ alg: "RS256", typ: "JWT" }),
    base64url({ iss: "https://accounts.google.com", aud: CLIENT_ID_PRUEBA, sub: "sub-ana", email, email_verified: true, name: nombre, exp }),
    "firma-simulada",
  ].join(".");
  return { token, email, nombre, exp };
}

/** Fija el modo "oidc" (o "headers"), el cliente de Google y el tenant antes de que cargue la app. */
export async function fijarAjustes(
  page: Page,
  ajustes: { modo: "oidc" | "headers"; clientId?: string | null; tenant?: string | null } = { modo: "oidc" },
): Promise<void> {
  await page.addInitScript(
    (a) => {
      window.__LOPDP_AUTH_PRUEBAS__ = { modo: a.modo, clientId: a.clientId, tenant: a.tenant } as never;
    },
    {
      modo: ajustes.modo,
      clientId: ajustes.clientId === undefined ? CLIENT_ID_PRUEBA : ajustes.clientId ?? "",
      tenant: ajustes.tenant === undefined ? TENANT_PRUEBA : ajustes.tenant ?? "",
    },
  );
}

/**
 * Deja una sesión ya iniciada en el navegador. Se siembra una sola vez por pestaña: si la prueba
 * cierra la sesión, una recarga no la resucita.
 */
export async function sembrarSesion(page: Page, credencial = credencialSimulada()): Promise<void> {
  await page.addInitScript(
    ({ clave, sesion }) => {
      if (window.sessionStorage.getItem("__sesion_sembrada")) return;
      window.sessionStorage.setItem(clave, JSON.stringify(sesion));
      window.sessionStorage.setItem("__sesion_sembrada", "1");
    },
    { clave: CLAVE_SESION, sesion: credencial },
  );
}

/** Sustituye el script de Google por uno que entrega `credencial` al pulsar su botón. */
export async function googleSimulado(page: Page, credencial: string): Promise<void> {
  const script = `
    window.__credencialSimulada = ${JSON.stringify(credencial)};
    window.google = { accounts: { id: {
      initialize(opciones) { window.__gsi = opciones; },
      renderButton(elemento) {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.textContent = ${JSON.stringify(BOTON_GOOGLE)};
        boton.onclick = () => window.__gsi.callback({ credential: window.__credencialSimulada });
        elemento.appendChild(boton);
      },
      disableAutoSelect() {},
    } } };
  `;
  await page.route("https://accounts.google.com/gsi/client", (route: Route) =>
    route.fulfill({ status: 200, contentType: "text/javascript", body: script }),
  );
}

export const ruta = (url: string) => new URL(url).pathname.replace(/^\/api\/v1/, "");
export const esApi = (peticion: Request) => new URL(peticion.url()).pathname.startsWith("/api/v1");

export interface OrganizacionSimulada {
  tenant_id: string;
  nombre_comercial: string;
  roles: string[];
}

export const ORGANIZACION_PRUEBA: OrganizacionSimulada = {
  tenant_id: TENANT_PRUEBA,
  nombre_comercial: "Organización de prueba",
  roles: ["implementador"],
};

export interface EscenarioApi {
  /** Estado con el que responde /organizacion/me/roles; 200 por defecto. */
  estadoRoles?: number;
  roles?: string[];
  /** Lo que responde /organizacion/mis-organizaciones (FE-21); una organización por defecto. */
  organizaciones?: OrganizacionSimulada[];
}

/**
 * Simula la API: registra cada llamada y responde lo mínimo. Lo no previsto devuelve 404 con
 * `NOT_MOCKED` y queda registrado, para que ninguna petición pase inadvertida.
 */
export async function simularApi(
  page: Page,
  { estadoRoles = 200, roles = ["implementador"], organizaciones = [ORGANIZACION_PRUEBA] }: EscenarioApi = {},
): Promise<Request[]> {
  const llamadas: Request[] = [];
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    llamadas.push(peticion);
    const destino = ruta(peticion.url());
    const json = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (destino === "/organizacion/mis-organizaciones") return json(200, { organizaciones });
    if (destino === "/organizacion/me/roles") {
      if (estadoRoles !== 200) return json(estadoRoles, { detail: "Token de identidad inválido o caducado.", code: "AUTH", action_required: null });
      return json(200, { roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })) });
    }
    if (["/organizacion/usuarios", "/organizacion/areas", "/organizacion/roles"].includes(destino)) return json(200, []);
    if (["/arco/solicitudes", "/terceros", "/ai/mitigaciones"].includes(destino)) return json(200, []);
    return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
  });
  return llamadas;
}
