/**
 * Arnés de interfaz de FE-07: inicio de sesión con Google y una sola identidad para todo el panel.
 *
 * Google se simula (ver utilesAuth.ts). El inicio de sesión real contra Google lo prueba el
 * propietario en local y en producción.
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";
import {
  BOTON_GOOGLE,
  CLAVE_SESION,
  TENANT_PRUEBA,
  credencialSimulada,
  esApi,
  fijarAjustes,
  googleSimulado,
  ruta,
  sembrarSesion,
  simularApi,
} from "./utilesAuth";
// === DEMO-00 ===
import { guardarSesion } from "../../src/lib/auth/sesion";
import { entornoEsDemo } from "../../src/lib/demo/cliente";
// === fin DEMO-00 ===

const cabecera = (peticion: Request, nombre: string) => peticion.headers()[nombre.toLowerCase()];

// === DEMO-00 ===
/**
 * Rutas de la API públicas a propósito: no llevan `Authorization`, ni siquiera con sesión. La lista
 * solo cambia con una ficha. Cualquier otra petición sin el token de la sesión hace fallar la prueba.
 */
const RUTAS_PUBLICAS: Record<string, string> = {
  "GET /api/v1/entorno":
    "EP-01: solo devuelve {entorno, datos_ficticios}; la entrada de la demo la consulta antes del login (DEMO-00).",
};
const clavePublica = (peticion: Request) => `${peticion.method()} ${new URL(peticion.url()).pathname}`;
// === fin DEMO-00 ===
const deRoles = (llamadas: Request[]) => llamadas.filter((l) => ruta(l.url()) === "/organizacion/me/roles");
const sesionGuardada = (page: Page) =>
  page.evaluate((clave) => window.sessionStorage.getItem(clave), CLAVE_SESION);

async function entrarConSesion(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
}

test.describe("Inicio de sesión con Google (FE-07)", () => {
  test("sin sesión, el panel lleva a /login y no llama a la API", async ({ page }) => {
    await fijarAjustes(page);
    await googleSimulado(page, credencialSimulada().token);
    const llamadas = await simularApi(page);

    await page.goto("/dashboard");

    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: "Plataforma LOPDP 360" })).toBeVisible();
    await expect(page.getByRole("button", { name: BOTON_GOOGLE })).toBeVisible();
    expect(llamadas.filter(esApi).map((l) => ruta(l.url()))).toEqual([]);
  });

  test("iniciar sesión entra al panel y el token queda solo en la sesión del navegador", async ({ page }) => {
    const credencial = credencialSimulada();
    await fijarAjustes(page);
    await googleSimulado(page, credencial.token);
    await simularApi(page);
    const consola: string[] = [];
    page.on("console", (m) => consola.push(m.text()));

    await page.goto("/login");
    await page.getByRole("button", { name: BOTON_GOOGLE }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    expect(JSON.parse((await sesionGuardada(page)) ?? "{}").token).toBe(credencial.token);
    expect(await page.evaluate((t) => JSON.stringify(window.localStorage).includes(t), credencial.token), "localStorage").toBe(false);
    expect(page.url(), "URL").not.toContain(credencial.token);
    expect(consola.join("\n"), "consola").not.toContain(credencial.token);
    await expect(page.getByTestId("sesion-activa")).toContainText(credencial.email);
  });

  test("una identificación que no es un token válido no inicia sesión", async ({ page }) => {
    await fijarAjustes(page);
    await googleSimulado(page, "esto-no-es-un-jwt");
    await simularApi(page);

    await page.goto("/login");
    await page.getByRole("button", { name: BOTON_GOOGLE }).click();

    await expect(page.getByTestId("login-error")).toBeVisible();
    await expect(page).toHaveURL(/\/login/);
    expect(await sesionGuardada(page)).toBeNull();
  });

  test("una identificación ya caducada no inicia sesión", async ({ page }) => {
    await fijarAjustes(page);
    await googleSimulado(page, credencialSimulada({ expiraEnSegundos: -60 }).token);
    await simularApi(page);

    await page.goto("/login");
    await page.getByRole("button", { name: BOTON_GOOGLE }).click();

    await expect(page.getByTestId("login-error")).toBeVisible();
    expect(await sesionGuardada(page)).toBeNull();
  });

  test("sin cliente de Google configurado, /login lo dice y no ofrece el botón", async ({ page }) => {
    await fijarAjustes(page, { modo: "oidc", clientId: null });
    await simularApi(page);

    await page.goto("/login");

    await expect(page.getByTestId("login-configuracion")).toContainText("NEXT_PUBLIC_GOOGLE_CLIENT_ID");
    await expect(page.getByTestId("login-boton-google")).toHaveCount(0);
  });

  test("sin NEXT_PUBLIC_TENANT_ID el inicio de sesión funciona: la organización sale de mis-organizaciones (FE-21)", async ({ page }) => {
    await fijarAjustes(page, { modo: "oidc", tenant: null });
    await googleSimulado(page, credencialSimulada().token);
    const llamadas = await simularApi(page);

    await page.goto("/login");
    await expect(page.getByTestId("login-configuracion")).toHaveCount(0);
    await page.getByRole("button", { name: BOTON_GOOGLE }).click();

    await expect(page).toHaveURL(/\/dashboard/);
    const consulta = llamadas.find((l) => ruta(l.url()) === "/organizacion/mis-organizaciones");
    expect(consulta, "se consultan las organizaciones de la persona").toBeTruthy();
    expect(cabecera(consulta!, "X-Tenant-ID"), "la consulta no lleva organización").toBeUndefined();
    await expect(page.getByTestId("organizacion-activa")).toContainText("Organización de prueba");
  });

  test("una sesión caducada se descarta y lleva a /login", async ({ page }) => {
    await fijarAjustes(page);
    await sembrarSesion(page, credencialSimulada({ expiraEnSegundos: -3600 }));
    await googleSimulado(page, credencialSimulada().token);
    const llamadas = await simularApi(page);

    await page.goto("/dashboard");

    await expect(page).toHaveURL(/\/login/);
    expect(llamadas.filter(esApi)).toEqual([]);
  });

  test("cerrar sesión limpia el navegador y el panel deja de abrirse", async ({ page }) => {
    await fijarAjustes(page);
    await sembrarSesion(page);
    await googleSimulado(page, credencialSimulada().token);
    await simularApi(page);

    await page.goto("/dashboard");
    await expect(page.getByTestId("sesion-activa")).toBeVisible();
    await page.getByRole("button", { name: "Cerrar sesión" }).click();

    await expect(page).toHaveURL(/\/login/);
    expect(await sesionGuardada(page)).toBeNull();
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/login/);
  });
});

test.describe("Identidad en las llamadas a la API (FE-07)", () => {
  test("la Hoja de Ruta no pide sus datos hasta abrirse, y los roles llevan el token de la sesión", async ({ page }) => {
    const credencial = credencialSimulada();
    const { token } = credencial;
    await fijarAjustes(page);
    await sembrarSesion(page, credencial);
    const llamadas = await simularApi(page, { roles: ["coordinador", "dpo"] });

    await entrarConSesion(page);
    // La ficha pide los roles para leer el tamaño de la organización (FE-08), pero sin abrir la Hoja de
    // Ruta no se toca ni su API ni la administración de la organización.
    const antes = llamadas.filter(esApi).map((l) => ruta(l.url()));
    expect(antes.filter((d) => d.startsWith("/roadmaps"))).toEqual([]);
    expect(antes.filter((d) => ["/organizacion/usuarios", "/organizacion/areas", "/organizacion/roles"].includes(d))).toEqual([]);
    const rolesAntes = deRoles(llamadas).length;

    await irASala(page, /^Hoja de Ruta/);
    // Al abrir la pestaña vuelve a pedirlos: es ella quien fija el rol activo del panel.
    await expect.poll(() => deRoles(llamadas).length).toBeGreaterThan(rolesAntes);

    const peticion = deRoles(llamadas)[0];
    expect(cabecera(peticion, "Authorization")).toBe(`Bearer ${token}`);
    expect(cabecera(peticion, "X-Tenant-ID")).toBe(TENANT_PRUEBA);
    expect(cabecera(peticion, "X-User-ID"), "en oidc no se envía X-User-ID").toBeUndefined();
    // La respuesta real del servidor trae {user_id, tenant_id, roles}: el selector de rol aparece.
    await expect(page.getByLabel("Seleccionar rol activo")).toBeVisible();
  });

  test("todos los clientes del panel envían el token y ninguno una identidad fija", async ({ page }) => {
    const credencial = credencialSimulada();
    const { token } = credencial;
    await fijarAjustes(page);
    await sembrarSesion(page, credencial);
    const llamadas = await simularApi(page);

    await entrarConSesion(page);
    // === FE-26 ===
    // Sin «Bóveda Evidencias»: el PMV no la ofrece en el menú (custodia física, solo EVYDENTIA).
    const salas = [/^Hoja de Ruta/, /Derechos ARCO/, /^Transferencias/, /Copiloto Mitigación/, /RAT Maestro/];
    // === fin FE-26 ===
    for (const sala of salas) {
      await irASala(page, sala);
    }
    await expect.poll(() => llamadas.filter(esApi).length).toBeGreaterThan(3);

    const api = llamadas.filter(esApi);
    const destinos = new Set(api.map((l) => ruta(l.url())));
    for (const esperado of ["/arco/solicitudes", "/terceros/garantias", "/ai/mitigaciones", "/organizacion/me/roles"]) {
      expect(destinos, `se esperaba una llamada a ${esperado}`).toContain(esperado);
    }
    for (const peticion of api) {
      const donde = `${peticion.method()} ${ruta(peticion.url())}`;
      // === DEMO-00 ===
      if (clavePublica(peticion) in RUTAS_PUBLICAS) {
        expect(cabecera(peticion, "Authorization"), `${donde}: ruta pública sin token`).toBeUndefined();
        continue;
      }
      // === fin DEMO-00 ===
      expect(cabecera(peticion, "Authorization"), `${donde}: Authorization`).toBe(`Bearer ${token}`);
      expect(cabecera(peticion, "X-Tenant-ID"), `${donde}: X-Tenant-ID`).toBe(TENANT_PRUEBA);
      expect(cabecera(peticion, "X-User-ID"), `${donde}: X-User-ID`).toBeUndefined();
      expect(cabecera(peticion, "Authorization"), `${donde}: token simulado`).not.toContain("jwt_mock");
    }
  });

  test("un 401 del servidor descarta la sesión y vuelve a pedir la identificación", async ({ page }) => {
    await fijarAjustes(page);
    await sembrarSesion(page);
    await googleSimulado(page, credencialSimulada().token);
    await simularApi(page, { estadoRoles: 401 });

    // La primera llamada con identidad (los roles que pide la ficha) ya recibe el 401.
    await page.goto("/");

    await expect(page).toHaveURL(/\/login\?motivo=expirada/);
    await expect(page.getByTestId("login-aviso")).toContainText("expiró");
    expect(await sesionGuardada(page)).toBeNull();
  });
});

test.describe("Modo de desarrollo con cabeceras (FE-07)", () => {
  test("en modo headers no se pide inicio de sesión y se envía la identidad de desarrollo", async ({ page }) => {
    await fijarAjustes(page, { modo: "headers", clientId: null, tenant: null });
    const llamadas = await simularApi(page);

    await page.goto("/login");
    await expect(page).toHaveURL(/\/dashboard/);

    await entrarConSesion(page);
    await irASala(page, /^Hoja de Ruta/);
    await expect.poll(() => deRoles(llamadas).length).toBeGreaterThan(0);

    const peticion = deRoles(llamadas)[0];
    expect(cabecera(peticion, "X-User-ID")).toBeTruthy();
    expect(cabecera(peticion, "X-Tenant-ID")).toBeTruthy();
    expect(cabecera(peticion, "Authorization")).toBeUndefined();
    await expect(page.getByTestId("sesion-activa")).toHaveCount(0);
  });
});

// === DEMO-00 ===
test.describe("Rutas públicas de la API (DEMO-00)", () => {
  type Llamada = { url: string; init: RequestInit };

  async function consultarEntorno(cuerpo: unknown): Promise<{ resultado: boolean; llamadas: Llamada[] }> {
    const almacen = new Map<string, string>();
    const sessionStorage = {
      getItem: (k: string) => almacen.get(k) ?? null,
      setItem: (k: string, v: string) => void almacen.set(k, v),
      removeItem: (k: string) => void almacen.delete(k),
    };
    const global = globalThis as unknown as Record<string, unknown>;
    const previos = { window: global.window, fetch: global.fetch };
    const llamadas: Llamada[] = [];
    global.window = { sessionStorage, location: { pathname: "/dashboard", search: "" }, __LOPDP_AUTH_PRUEBAS__: { modo: "oidc", tenant: TENANT_PRUEBA } };
    global.fetch = async (url: string, init: RequestInit = {}) => {
      llamadas.push({ url: String(url), init });
      return new Response(JSON.stringify(cuerpo), { status: 200, headers: { "Content-Type": "application/json" } });
    };
    try {
      expect(guardarSesion(credencialSimulada().token, { avisar: false }), "sesión sembrada").toBe(true);
      return { resultado: await entornoEsDemo(), llamadas };
    } finally {
      global.window = previos.window;
      global.fetch = previos.fetch;
    }
  }

  test("la lista de rutas públicas tiene un motivo por ruta", () => {
    expect(Object.keys(RUTAS_PUBLICAS)).toEqual(["GET /api/v1/entorno"]);
    for (const motivo of Object.values(RUTAS_PUBLICAS)) expect(motivo.trim()).not.toBe("");
  });

  test("entornoEsDemo pide /entorno sin Authorization aunque haya sesión", async () => {
    const { resultado, llamadas } = await consultarEntorno({ entorno: "demo", datos_ficticios: true });
    expect(resultado).toBe(true);
    expect(llamadas).toHaveLength(1);
    const [{ url, init }] = llamadas;
    expect(`${init.method ?? "GET"} ${url}`).toBe("GET /api/v1/entorno");
    expect(`GET ${url}` in RUTAS_PUBLICAS).toBe(true);
    const cabeceras = new Headers(init.headers);
    expect(cabeceras.get("Authorization")).toBeNull();
    expect(init.credentials).toBe("omit");
  });

  test("una respuesta de /entorno con otra clave no se acepta", async () => {
    const { resultado } = await consultarEntorno({ entorno: "demo", datos_ficticios: true, version: "x" });
    expect(resultado).toBe(false);
  });
});
// === fin DEMO-00 ===
