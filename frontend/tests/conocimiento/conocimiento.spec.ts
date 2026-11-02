/** REG-02 · Menú 8 «Conocimiento»: tres pantallas nuevas, cada una montada en su submenú. */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, barraDeMenus, configurarProyecto, irASala } from "../utiles";
import { instalarApiConocimiento } from "./apiSimulada";

test.describe("Menú Conocimiento (REG-02)", () => {
  test.beforeEach(async ({ page }) => {
    await instalarApiConocimiento(page);
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad REG-02");
  });

  test("el menú muestra Normativa Ecuador, Resúmenes y guías y Ayuda", async ({ page }) => {
    await barraDeMenus(page).getByRole("button", { name: "Conocimiento", exact: true }).click();
    const grupo = page.getByRole("group", { name: "Submenús de Conocimiento" });
    for (const nombre of ["Normativa Ecuador", "Resúmenes y guías", "Ayuda"]) {
      await expect(grupo.getByRole("button", { name: new RegExp(`^${nombre}`) })).toBeVisible();
    }
  });

  test("Normativa Ecuador lista artículos con fuente y versión, y filtra por texto y fuente", async ({ page }) => {
    await irASala(page, /Normativa Ecuador/);
    const lista = page.getByRole("list", { name: "Artículos del corpus" });
    await expect(lista.getByRole("listitem")).toHaveCount(3);
    await expect(lista).toContainText("Art. 7 LOPDP");
    await expect(lista).toContainText("lopdp-rg-2026-09-20.1");

    await page.getByLabel("Buscar en la normativa").fill("derechos");
    await expect(lista.getByRole("listitem")).toHaveCount(2);

    await page.getByLabel("Fuente").selectOption("Reglamento");
    await expect(lista.getByRole("listitem")).toHaveCount(1);
    await expect(lista).toContainText("Art. 15 Reglamento General a la LOPDP");

    await page.getByLabel("Buscar en la normativa").fill("zzz");
    await expect(page.getByText("Sin fuente en el corpus para esa búsqueda.")).toBeVisible();
  });

  test("Resúmenes y guías agrupa los resúmenes por fuente, cada uno con su cita", async ({ page }) => {
    await irASala(page, /Resúmenes y guías/);
    await expect(page.getByRole("list", { name: "Resúmenes de LOPDP" }).getByRole("listitem")).toHaveCount(2);
    await expect(page.getByRole("list", { name: "Resúmenes de Reglamento General a la LOPDP" })).toContainText("Art. 15 Reglamento General a la LOPDP");
  });
});
