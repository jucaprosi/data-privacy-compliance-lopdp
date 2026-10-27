import { expect, test, type Page } from "@playwright/test";

import { medirContraste } from "../contraste";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const TEMAS = ["theme-light", "theme-dark"] as const;

async function simularApi(page: Page): Promise<void> {
  await page.route("**/api/**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ success: true }) }),
  );
}

async function comprobarPantalla(page: Page, tema: (typeof TEMAS)[number], pantalla: string, selector = "main > div.flex-1"): Promise<void> {
  const marco = page.locator(".app-frame-canvas");
  if (tema === "theme-dark" && await marco.evaluate((el) => !el.classList.contains("theme-dark"))) {
    await page.getByTitle("Cambiar a tema oscuro").click();
  }
  await expect(marco).toHaveClass(new RegExp(tema));
  // El marco anima el cambio de tema durante 200 ms; medir en mitad de la transición falsea el ratio.
  await page.waitForTimeout(300);
  const deficientes = await medirContraste(page, selector);
  expect(deficientes, `${pantalla} en ${tema}: ${JSON.stringify(deficientes, null, 2)}`).toEqual([]);
}

test.describe("FE-16: texto visible del diagnóstico en ambos temas", () => {
  for (const tema of TEMAS) {
    test(`${tema}: ficha y perfil de operación`, async ({ page }) => {
      await simularApi(page);
      await abrirAppLimpia(page);
      await expect(page.getByRole("textbox", { name: /Razón Social/ })).toBeVisible();
      await expect(page.getByRole("radiogroup").first()).toBeVisible();
      await comprobarPantalla(page, tema, "Ficha organizacional");
    });

    test(`${tema}: selector, evidencias, controles y preanálisis`, async ({ page }) => {
      await simularApi(page);
      await abrirAppLimpia(page);
      await configurarProyecto(page);
      await expect(page.locator("#selector-normativa")).toBeVisible();
      await expect(page.getByText(/Progreso: Pregunta/)).toBeVisible();
      await comprobarPantalla(page, tema, "Normativa y diagnóstico");
    });

    test(`${tema}: resultado, bóveda de evidencias y reportes`, async ({ page }) => {
      await simularApi(page);
      await abrirAppLimpia(page);
      await configurarProyecto(page);
      await irASala(page, /Dashboard Central/);
      await page.getByRole("tab", { name: "Informe", exact: true }).click();
      await expect(page.getByRole("tabpanel", { name: "Informe" })).toBeVisible();
      await comprobarPantalla(page, tema, "Resultado del assessment", "#panel-informe");

      await irASala(page, /Bóveda Evidencias/);
      await expect(page.getByRole("heading", { name: /Evidencias/ }).first()).toBeVisible();
      await comprobarPantalla(page, tema, "Bóveda de evidencias");

      await irASala(page, /Reportes PDF/);
      await expect(page.getByRole("heading", { name: /Reportes/ }).first()).toBeVisible();
      await comprobarPantalla(page, tema, "Reportes");
    });
  }
});
