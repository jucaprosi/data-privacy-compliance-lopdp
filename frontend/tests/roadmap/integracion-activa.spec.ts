/**
 * FE-06 con la evidencia física encendida (EVYDENTIA, FE-26): la «Custodia de Evidencias» del panel.
 *
 * Usa el ajuste de prueba `window.__LOPDP_EVIDENCIA_PRUEBAS__`, que solo existe fuera de producción
 * (src/lib/config/evidenciaFisica.ts): este archivo corre en el proyecto «desarrollo» por la
 * convención `*-activa.spec.ts`. El caso por omisión del PMV está en `integracion.spec.ts`.
 */
import { expect, test } from "@playwright/test";

import { entrarEnHojaDeRuta, prepararApi, ruta, subvista, type Rol } from "./panel";

const ROLES: Rol[] = ["implementador", "admin_organizacion", "coordinador", "dpo", "responsable_area"];

test.describe("Custodia de evidencias en el panel de la Hoja de Ruta (FE-06, EVYDENTIA)", () => {
  test.beforeEach(async ({ context }) => {
    await context.addInitScript(() => {
      window.__LOPDP_EVIDENCIA_PRUEBAS__ = true;
    });
  });

  for (const rol of ROLES) {
    test(`el rol ${rol} ve la subvista de custodia`, async ({ page }) => {
      await prepararApi(page, { roles: [rol] });
      await entrarEnHojaDeRuta(page);

      await expect(subvista(page, "Olas & Tareas")).toBeVisible();
      await expect(subvista(page, "Custodia de Evidencias")).toBeVisible();
    });
  }

  test("sin tarea elegida la custodia lo explica y no pide datos de demostración", async ({ page }) => {
    const llamadas = await prepararApi(page, { roles: ["implementador"] });
    await entrarEnHojaDeRuta(page);

    await subvista(page, "Custodia de Evidencias").click();
    await expect(page.getByTestId("roadmap-sin-tarea")).toBeVisible();

    const destinos = llamadas.map((l) => ruta(l.url()));
    expect(destinos.filter((d) => d.includes("rm-demo-001") || d.includes("task-001"))).toEqual([]);
    expect(destinos.filter((d) => d.startsWith("/roadmaps"))).toEqual([]);
  });

  test("la custodia no muestra tokens de gobernanza", async ({ page }) => {
    await prepararApi(page, { roles: ["admin_organizacion", "implementador"] });
    await entrarEnHojaDeRuta(page);

    await subvista(page, "Custodia de Evidencias").click();
    const texto = await page.locator("main, body").first().innerText();
    expect(texto).not.toMatch(/[¤¦]/);
  });
});
