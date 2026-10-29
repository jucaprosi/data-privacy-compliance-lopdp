/**
 * FE-22 · Ctrl+K busca entre las pantallas de los nueve menús (especificación, R6).
 */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

test.describe("Ctrl+K sobre las pantallas de los nueve menús (FE-22)", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad FE-22");
    // Tras el alta la vista es el assessment: el menú abierto es Diagnóstico.
    await expect(barraDeMenus(page).locator('[aria-current="page"]')).toHaveText("Diagnóstico");
  });

  const buscador = (page: import("@playwright/test").Page) => page.getByPlaceholder(/Escribe un comando/i);

  test("encuentra una pantalla de otro menú, sin tildes, y Enter la abre", async ({ page }) => {
    await page.keyboard.press("Control+K");
    await buscador(page).fill("evaluacion de impacto");

    const opcion = page.getByRole("option", { name: /Riesgos y auditoría › Evaluaciones de impacto/ });
    await expect(opcion).toBeVisible();
    await expect(opcion).toHaveAttribute("data-selected", "true");

    await page.keyboard.press("Enter");
    await expect(buscador(page)).toBeHidden();
    await expect(page.getByText("mtge_relacional.adpa.view", { exact: true })).toBeVisible();
    await expect(barraDeMenus(page).locator('[aria-current="page"]')).toHaveText("Riesgos y auditoría");
  });

  test("busca también por el nombre del menú y Esc cierra sin navegar", async ({ page }) => {
    await page.keyboard.press("Control+K");
    await buscador(page).fill("OPERACION");
    await expect(page.getByRole("option", { name: /Operación › Solicitudes de titulares/ })).toBeVisible();
    await expect(page.getByRole("option", { name: /Operación › Vulneraciones/ })).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(buscador(page)).toBeHidden();
    await expect(page.getByText("diagnostico.adpa.view", { exact: true })).toBeVisible();
  });
});
