/**
 * FE-16 con la evidencia física encendida (EVYDENTIA, FE-26): contraste de la carga de evidencias y de
 * la bóveda en ambos temas.
 *
 * Usa el ajuste de prueba `window.__LOPDP_EVIDENCIA_PRUEBAS__`, que solo existe fuera de producción,
 * y corre en el proyecto «desarrollo» (convención `*-activa.spec.ts`). Las pantallas del PMV están en
 * `colores-diagnostico.spec.ts`.
 */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";
import { comprobarPantalla, simularApi, TEMAS } from "./temas-diagnostico";

test.describe("FE-16: evidencias del diagnóstico visibles en ambos temas (EVYDENTIA)", () => {
  // === FE-26 ===
  test.beforeEach(async ({ context }) => {
    await context.addInitScript(() => {
      window.__LOPDP_EVIDENCIA_PRUEBAS__ = true;
    });
  });
  // === fin FE-26 ===

  for (const tema of TEMAS) {
    test(`${tema}: normativa con la carga de evidencias`, async ({ page }) => {
      await simularApi(page);
      await abrirAppLimpia(page);
      await configurarProyecto(page);
      await expect(page.getByText("Registro de Evidencias con Huella SHA-256")).toBeVisible();
      await comprobarPantalla(page, tema, "Normativa con carga de evidencias");
    });

    test(`${tema}: bóveda de evidencias`, async ({ page }) => {
      await simularApi(page);
      await abrirAppLimpia(page);
      await configurarProyecto(page);
      // Por el menú, no con irASala: la tabla de submenús se evalúa en el proceso de pruebas (Node), donde el
      // ajuste del navegador no existe y Biblioteca › Evidencias no figura.
      await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
      await page.getByRole("group", { name: "Submenús de Biblioteca" }).getByRole("button", { name: /^Evidencias/ }).click();
      await expect(page.getByRole("heading", { name: /Evidencias/ }).first()).toBeVisible();
      await comprobarPantalla(page, tema, "Bóveda de evidencias");
    });
  }
});
