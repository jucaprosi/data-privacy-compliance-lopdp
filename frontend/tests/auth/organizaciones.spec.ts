/**
 * Arnés de FE-21: quien pertenece a varias organizaciones elige con cuál trabajar y puede cambiar.
 *
 * Google y la API se simulan (utilesAuth.ts). Sin tenant fijado por la prueba, la organización sale
 * de `/organizacion/mis-organizaciones` (ORG-13), como en producción.
 *
 * Pruebas de mutación (FE-21), ejecutadas y restauradas:
 *  - `tenantConfigurado()` (lib/auth/modo.ts) devolviendo la primera organización de la lista en
 *    lugar de la activa: al cambiar a B las peticiones siguen llevando A, y «A → B → A» falla en
 *    «todas las peticiones llevan la organización nueva».
 *  - `cambiarDeOrganizacion` sin `guardarOrganizacionActiva`: «A → B → A» falla porque el
 *    encabezado sigue en A.
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import { configurarProyecto } from "../utiles";
import {
  BOTON_GOOGLE,
  CLAVE_SESION,
  credencialSimulada,
  fijarAjustes,
  googleSimulado,
  ruta,
  simularApi,
  type OrganizacionSimulada,
} from "./utilesAuth";

const A: OrganizacionSimulada = { tenant_id: "tenant-a", nombre_comercial: "Cooperativa Andina", roles: ["dpo"] };
const B: OrganizacionSimulada = { tenant_id: "tenant-b", nombre_comercial: "Banco Bolívar", roles: ["implementador", "dpo"] };
const EMPRESA_A = "Empresa A S.A.";
const EMPRESA_B = "Empresa B S.A.";
const dpo = credencialSimulada({ email: "dpo@externo.test", nombre: "DPO Externo" });

const tenantDe = (peticion: Request) => peticion.headers()["x-tenant-id"];
const fichaGuardada = (page: Page) =>
  page.evaluate(() => JSON.parse(window.localStorage.getItem("jubys-audit-storage") ?? "{}")?.state?.companyData?.razonSocial ?? "");

async function iniciar(page: Page, organizaciones: OrganizacionSimulada[]): Promise<Request[]> {
  await fijarAjustes(page, { modo: "oidc", tenant: null });
  await googleSimulado(page, dpo.token);
  const llamadas = await simularApi(page, { organizaciones, roles: ["dpo"] });
  await page.goto("/login");
  await page.getByRole("button", { name: BOTON_GOOGLE }).click();
  return llamadas;
}

async function elegir(page: Page, org: OrganizacionSimulada) {
  await expect(page).toHaveURL(/\/organizaciones/);
  await page.getByRole("button", { name: new RegExp(org.nombre_comercial) }).click();
}

async function cambiarA(page: Page, org: OrganizacionSimulada, decision: "Guardar y cambiar" | "Descartar y cambiar") {
  await page.getByRole("link", { name: "Cambiar organización" }).click();
  await elegir(page, org);
  await page.getByRole("alertdialog").getByRole("button", { name: decision }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await expect(page.getByTestId("organizacion-activa")).toContainText(org.nombre_comercial);
}

test.describe("Elegir y cambiar de organización (FE-21)", () => {
  test("sin organizaciones: lo dice y no abre el panel", async ({ page }) => {
    const llamadas = await iniciar(page, []);

    await expect(page.getByTestId("login-error")).toContainText("Tu cuenta no pertenece a ninguna organización; pide una invitación.");
    await expect(page).toHaveURL(/\/login/);
    expect(await page.evaluate((c) => window.sessionStorage.getItem(c), CLAVE_SESION)).toBeNull();
    expect(llamadas.map((l) => ruta(l.url()))).toEqual(["/organizacion/mis-organizaciones"]);
  });

  test("con una: entra directo y no ofrece cambiar", async ({ page }) => {
    await iniciar(page, [A]);

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByTestId("organizacion-activa")).toContainText(A.nombre_comercial);
    await expect(page.getByRole("link", { name: "Cambiar organización" })).toHaveCount(0);
  });

  test("con varias: elige antes de abrir la sesión y antes de hablar con ninguna organización", async ({ page }) => {
    const llamadas = await iniciar(page, [A, B]);

    await expect(page).toHaveURL(/\/organizaciones/);
    const lista = page.getByRole("list", { name: "Tus organizaciones" });
    await expect(lista).toContainText(A.nombre_comercial);
    await expect(lista).toContainText("Implementador, DPO");
    expect(await page.evaluate((c) => window.sessionStorage.getItem(c), CLAVE_SESION), "sin sesión todavía").toBeNull();
    expect(llamadas.filter((l) => tenantDe(l)), "ninguna petición con organización antes de elegir").toEqual([]);

    await elegir(page, B);
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByTestId("organizacion-activa")).toContainText(B.nombre_comercial);
    await expect(page.getByRole("link", { name: "Cambiar organización" })).toBeVisible();
    await expect.poll(() => llamadas.filter((l) => tenantDe(l)).length).toBeGreaterThan(0);
    expect(new Set(llamadas.filter((l) => tenantDe(l)).map(tenantDe))).toEqual(new Set([B.tenant_id]));
  });

  test("A → B → A: cada organización ve solo lo suyo, las peticiones llevan la nueva y A se recupera", async ({ page }) => {
    const llamadas = await iniciar(page, [A, B]);
    await elegir(page, A);
    await expect(page).toHaveURL(/\/dashboard/);
    await configurarProyecto(page, EMPRESA_A);

    const antesDeB = llamadas.length;
    await cambiarA(page, B, "Guardar y cambiar");
    await expect.poll(() => llamadas.slice(antesDeB).filter((l) => tenantDe(l)).length).toBeGreaterThan(0);
    const enB = llamadas.slice(antesDeB).filter((l) => tenantDe(l));
    expect(new Set(enB.map(tenantDe)), "todas las peticiones llevan la organización nueva").toEqual(new Set([B.tenant_id]));
    expect(enB.some((l) => (l.postData() ?? "").includes(EMPRESA_A)), "nada de A se envía en B").toBe(false);
    expect(await fichaGuardada(page), "B no muestra la ficha de A").not.toBe(EMPRESA_A);
    await expect(page.getByText(EMPRESA_A)).toHaveCount(0);

    await configurarProyecto(page, EMPRESA_B);
    const antesDeA = llamadas.length;
    await cambiarA(page, A, "Guardar y cambiar");
    expect(await fichaGuardada(page), "al volver, A recupera lo trabajado").toBe(EMPRESA_A);
    await expect.poll(() => llamadas.slice(antesDeA).filter((l) => tenantDe(l)).length).toBeGreaterThan(0);
    expect(new Set(llamadas.slice(antesDeA).filter((l) => tenantDe(l)).map(tenantDe))).toEqual(new Set([A.tenant_id]));
  });

  test("con cambios sin guardar ofrece guardar o descartar; descartar no los lleva a ninguna parte", async ({ page }) => {
    await iniciar(page, [A, B]);
    await elegir(page, A);
    await expect(page).toHaveURL(/\/dashboard/);
    await configurarProyecto(page, EMPRESA_A);

    await page.getByRole("link", { name: "Cambiar organización" }).click();
    await elegir(page, B);
    const dialogo = page.getByRole("alertdialog");
    await expect(dialogo).toContainText("Tienes cambios sin guardar");
    await expect(dialogo.getByRole("button", { name: "Guardar y cambiar" })).toBeVisible();
    await dialogo.getByRole("button", { name: "Cancelar" }).click();
    await expect(dialogo).toHaveCount(0);
    await expect(page).toHaveURL(/\/organizaciones/);

    await elegir(page, B);
    await page.getByRole("alertdialog").getByRole("button", { name: "Descartar y cambiar" }).click();
    await expect(page).toHaveURL(/\/dashboard/);
    expect(await fichaGuardada(page), "lo descartado no llega a B").not.toBe(EMPRESA_A);

    await page.getByRole("link", { name: "Cambiar organización" }).click();
    await elegir(page, A);
    await expect(page).toHaveURL(/\/dashboard/);
    expect(await fichaGuardada(page), "y tampoco quedó en A").not.toBe(EMPRESA_A);
  });
});
