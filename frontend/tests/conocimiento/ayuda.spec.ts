/** REG-02 · Ayuda contextual: el «?» muestra la cita «Art. … LOPDP» o dice que no hay fuente en el corpus. */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";
import { instalarApiConocimiento } from "./apiSimulada";

test.describe("Conocimiento › Ayuda (REG-02)", () => {
  test.beforeEach(async ({ page }) => {
    await instalarApiConocimiento(page);
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad REG-02");
    await irASala(page, /^Ayuda/);
  });

  test("al abrir el «?» de un control con fuente se ve la cita del artículo", async ({ page }) => {
    await page.getByRole("button", { name: "Ayuda sobre el control" }).click();
    const panel = page.getByRole("dialog", { name: "Base legal" });
    await expect(panel).toContainText("Art. 7 LOPDP");
    await expect(panel).toContainText("lopdp-rg-2026-09-20.1");
    await expect(panel).not.toContainText("Sin fuente en el corpus");
  });

  test("un control sin fuente muestra «sin fuente en el corpus» y ningún texto", async ({ page }) => {
    await page.getByLabel(/Control \(p\. ej\. P12\)/).fill("P999");
    await page.getByRole("button", { name: "Ayuda sobre el control" }).click();
    const panel = page.getByRole("dialog", { name: "Base legal" });
    await expect(panel).toContainText("Sin fuente en el corpus");
    await expect(panel).not.toContainText("Art.");
  });
});
