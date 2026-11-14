/**
 * DLP-01: descubrimiento de datos en una muestra. La API se simula: del servidor solo llegan tipos y
 * conteos. Se comprueba que, tras el resultado, ningún nodo del DOM conserva un valor de la muestra y que
 * los errores se muestran con textos fijos, nunca con el texto del servidor.
 */
import { expect, test, type BrowserContext } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const CEDULA = "3000000004"; // ficticia, válida por Módulo 10
const CORREO = "titular.ficticio@correo.invalid";
const MUESTRA = `Socio 1; ${CEDULA}; ${CORREO}\nSocio 2; sin datos`;

async function simularApi(
  context: BrowserContext,
  { roles, rechazo }: { roles: string[]; rechazo?: { status: number; detail: unknown } }
) {
  const servidor = { cuerpos: [] as Record<string, unknown>[], vinculos: [] as Record<string, unknown>[] };
  await context.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { roles: roles.map((role) => ({ role })) } })
  );
  await context.route("**/api/v1/rat/actividades", (route) =>
    route.fulfill({ json: { actividades: [{ id: "rat-1", codigo: "RAT-001", nombre: "Gestión de socios" }] } })
  );
  await context.route("**/api/v1/dlp-discovery/escaneos", (route) => route.fulfill({ json: { escaneos: [] } }));
  await context.route("**/api/v1/dlp-discovery/escanear-muestra", async (route) => {
    servidor.cuerpos.push(route.request().postDataJSON() as Record<string, unknown>);
    if (rechazo) {
      await route.fulfill({ status: rechazo.status, json: { detail: rechazo.detail } });
      return;
    }
    await route.fulfill({
      status: 201,
      json: {
        id: "esc-1", fuente_nombre: "Base de socios", limite_muestra: 1000, filas_evaluadas: 2,
        infotypes_detectados: { EC_CEDULA_MOD10: 1, EMAIL: 1, SALUD: 1 }, contiene_datos_sensibles: true,
        actividad_rat_id: null, creado_por: "u-1", creado_en: new Date().toISOString(),
      },
    });
  });
  await context.route("**/api/v1/dlp-discovery/escaneos/*/vincular-rat", async (route) => {
    servidor.vinculos.push(route.request().postDataJSON() as Record<string, unknown>);
    await route.fulfill({ json: { escaneo_id: "esc-1", actividad_rat_id: "rat-1", actividad_nombre: "Gestión de socios" } });
  });
  return servidor;
}

async function abrir(page: import("@playwright/test").Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Descubrimiento de datos/);
}

test.describe("Descubrimiento de datos (DLP-01)", () => {
  test("el resultado solo muestra tipos y conteos; la muestra desaparece del DOM", async ({ page, context }) => {
    const servidor = await simularApi(context, { roles: ["coordinador"] });
    await abrir(page);
    await expect(page.getByRole("note")).toContainText("No guardamos la muestra ni los valores encontrados");
    await page.getByLabel("Nombre de la fuente").fill("Base de socios");
    await page.getByLabel("Muestra", { exact: true }).fill(MUESTRA);
    await expect(page.getByText("2 de 1000 filas")).toBeVisible();
    await page.getByRole("button", { name: "Escanear muestra" }).click();

    await expect(page.getByRole("heading", { name: "Resultado del escaneo" })).toBeFocused();
    await expect(page.getByText("La muestra se borró de esta pantalla.")).toBeVisible();
    const resultado = page.getByRole("region", { name: "Resultado del escaneo" });
    await expect(resultado).toContainText("Cédulas de identidad");
    await expect(resultado).toContainText("Posibles datos de salud");
    await expect(resultado).toContainText("puede dar falsos positivos");
    await expect(resultado).not.toContainText("EC_CEDULA_MOD10");

    const html = await page.content();
    const valores = await page.locator("input, textarea").evaluateAll((els) =>
      els.map((e) => (e as HTMLInputElement).value)
    );
    for (const valor of [CEDULA, CORREO]) {
      expect(html).not.toContain(valor);
      expect(valores.join(" ")).not.toContain(valor);
    }
    expect(servidor.cuerpos[0].filas).toEqual([`Socio 1; ${CEDULA}; ${CORREO}`, "Socio 2; sin datos"]);

    await page.getByLabel("Actividad de tratamiento").selectOption("rat-1");
    await page.getByLabel("Vincular correos electrónicos").check();
    await page.getByRole("button", { name: "Vincular al registro de actividades" }).click();
    await expect(page.getByText("Categorías vinculadas a Gestión de socios.")).toBeVisible();
    expect(servidor.vinculos).toEqual([{ actividad_rat_id: "rat-1", infotypes: ["EMAIL"] }]);
  });

  test("un error nunca muestra el texto del servidor", async ({ page, context }) => {
    await simularApi(context, {
      roles: ["implementador"],
      rechazo: { status: 500, detail: `fallo con ${CEDULA}` },
    });
    await abrir(page);
    await page.getByLabel("Nombre de la fuente").fill("Base");
    await page.getByLabel("Muestra", { exact: true }).fill(MUESTRA);
    await page.getByRole("button", { name: "Escanear muestra" }).click();
    await expect(page.getByRole("alert").filter({ hasText: /muestra/ })).toHaveText("No pudimos escanear la muestra. Inténtalo de nuevo.");
    await expect(page.locator("body")).not.toContainText(`fallo con ${CEDULA}`);
  });

  test("el tope de filas usa el texto fijo", async ({ page, context }) => {
    await simularApi(context, {
      roles: ["coordinador"],
      rechazo: { status: 422, detail: { codigo: "DLP_MUESTRA_EXCEDE_LIMITE", mensaje: "x" } },
    });
    await abrir(page);
    await page.getByLabel("Nombre de la fuente").fill("Base");
    await page.getByLabel("Muestra", { exact: true }).fill(MUESTRA);
    await page.getByRole("button", { name: "Escanear muestra" }).click();
    await expect(page.getByRole("alert").filter({ hasText: /muestra/ })).toHaveText(
      "La muestra supera el máximo de 1000 filas. Reduce la muestra e inténtalo de nuevo."
    );
  });

  test("el DPO consulta y no escanea", async ({ page, context }) => {
    await simularApi(context, { roles: ["dpo"] });
    await abrir(page);
    await expect(page.getByText("Aún no hay escaneos.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Escanear muestra" })).toHaveCount(0);
  });
});
