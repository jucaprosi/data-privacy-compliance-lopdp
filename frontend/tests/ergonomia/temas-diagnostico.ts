/**
 * Contraste del diagnóstico en ambos temas (FE-16): API simulada y medición por pantalla.
 *
 * La comparten `colores-diagnostico.spec.ts` y `colores-diagnostico-activa.spec.ts` (FE-26). Este
 * archivo no declara pruebas.
 */
import { expect, type Page } from "@playwright/test";

import { medirContraste } from "../contraste";

export const TEMAS = ["theme-light", "theme-dark"] as const;

export async function simularApi(page: Page): Promise<void> {
  await page.route("**/api/**", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ success: true }) }),
  );
}

export async function comprobarPantalla(page: Page, tema: (typeof TEMAS)[number], pantalla: string, selector = "main > div.flex-1"): Promise<void> {
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
