/**
 * FE-22 · NIIF 18 no entra en los nueve menús: conserva su navegación propia (R5).
 */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

test("con NIIF 18 no aparecen los nueve menús y sí la navegación NIIF", async ({ page }) => {
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad FE-22");
  await expect(barraDeMenus(page)).toBeVisible();

  await page.locator("#selector-normativa").selectOption("NIIF");
  const confirmacion = page.getByRole("alertdialog");
  if (await confirmacion.count()) {
    await confirmacion.getByRole("button", { name: "Cambiar normativa" }).click();
  }
  await expect(page.locator("#selector-normativa")).toHaveValue("NIIF");

  await expect(barraDeMenus(page)).toHaveCount(0);
  await expect(page.getByRole("group", { name: /^Submenús de / })).toHaveCount(0);
  for (const sala of [/Ingesta de Balance/, /Matriz Reclasificación/, /Visor Doctrinal/]) {
    await expect(page.getByRole("button", { name: sala })).toBeVisible();
  }

  await page.getByRole("button", { name: /Ingesta de Balance/ }).click();
  await expect(page.getByText("niif_ingesta.adpa.view", { exact: true })).toBeVisible();
});
