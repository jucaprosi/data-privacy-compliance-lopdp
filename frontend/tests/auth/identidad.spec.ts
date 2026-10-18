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

const cabecera = (peticion: Request, nombre: string) => peticion.headers()[nombre.toLowerCase()];
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

  test("sin tenant configurado, /login lo dice (en oidc no hay tenant por defecto)", async ({ page }) => {
    await fijarAjustes(page, { modo: "oidc", tenant: null });
    await simularApi(page);

    await page.goto("/login");

    await expect(page.getByTestId("login-configuracion")).toContainText("NEXT_PUBLIC_TENANT_ID");
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
    const { token } = credencialSimulada();
    await fijarAjustes(page);
    await sembrarSesion(page, credencialSimulada());
    const llamadas = await simularApi(page, { roles: ["encargado", "dpo"] });

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
    const { token } = credencialSimulada();
    await fijarAjustes(page);
    await sembrarSesion(page, credencialSimulada());
    const llamadas = await simularApi(page);

    await entrarConSesion(page);
    for (const sala of [/^Hoja de Ruta/, /Derechos ARCO/, /^Transferencias/, /Copiloto Mitigación/, /Bóveda Evidencias/, /RAT Maestro/]) {
      await irASala(page, sala);
    }
    await expect.poll(() => llamadas.filter(esApi).length).toBeGreaterThan(3);

    const api = llamadas.filter(esApi);
    const destinos = new Set(api.map((l) => ruta(l.url())));
    for (const esperado of ["/arco/solicitudes", "/terceros", "/ai/mitigaciones", "/organizacion/me/roles"]) {
      expect(destinos, `se esperaba una llamada a ${esperado}`).toContain(esperado);
    }
    for (const peticion of api) {
      const donde = `${peticion.method()} ${ruta(peticion.url())}`;
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
