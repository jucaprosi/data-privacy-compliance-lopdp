import { expect, test } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";
import { comprobarPantalla, simularApi, TEMAS } from "./temas-diagnostico";

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

    // === FE-26 ===
    // Sin la bóveda de evidencias: el PMV no la ofrece (colores-diagnostico-activa.spec.ts la mide).
    test(`${tema}: resultado y reportes`, async ({ page }) => {
    // === fin FE-26 ===
      await simularApi(page);
      await abrirAppLimpia(page);
      await configurarProyecto(page);
      await irASala(page, /Dashboard Central/);
      await page.getByRole("tab", { name: "Informe", exact: true }).click();
      await expect(page.getByRole("tabpanel", { name: "Informe" })).toBeVisible();
      await comprobarPantalla(page, tema, "Resultado del assessment", "#panel-informe");

      await irASala(page, /Reportes PDF/);
      await expect(page.getByRole("heading", { name: /Reportes/ }).first()).toBeVisible();
      await comprobarPantalla(page, tema, "Reportes");
    });
  }
});
