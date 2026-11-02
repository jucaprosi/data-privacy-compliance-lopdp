/**
 * RAT-06 (governance/especificaciones/RAT-06.md §4 y §5).
 *
 * Con la API simulada: «Exportar XLSX» descarga un archivo `.xlsx` y muestra la huella; sin fichas se ve el motivo;
 * el rol que no exporta no ve los botones.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const HUELLA = "a".repeat(64);

async function abrirRat(page: Page, rol: string) {
  await page.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { user_id: "u-1", tenant_id: "t-1", roles: [{ role: rol }] } }),
  );
  await page.route("**/api/v1/rat/plantillas", (route) => route.fulfill({ json: { plantillas: [] } }));
  await page.route("**/api/v1/rat/actividades", (route) => route.fulfill({ json: { total: 0, actividades: [] } }));
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Consultorio de prueba");
  await irASala(page, /RAT Maestro/);
}

test.describe("Exportación del RAT (RAT-06)", () => {
  test("Exportar XLSX descarga un archivo .xlsx y muestra la huella", async ({ page }) => {
    await page.route("**/api/v1/rat/exportar?formato=xlsx", (route) =>
      route.fulfill({
        body: "contenido",
        contentType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers: {
          "Content-Disposition": 'attachment; filename="rat-t-1-2026-11-01.xlsx"',
          "X-Huella-SHA256": HUELLA,
        },
      }),
    );
    await abrirRat(page, "dpo");
    const seccion = page.getByRole("region", { name: "Exportar" });
    const descarga = page.waitForEvent("download");
    await seccion.getByRole("button", { name: "Exportar XLSX" }).click();
    expect((await descarga).suggestedFilename()).toBe("rat-t-1-2026-11-01.xlsx");
    await expect(seccion.getByRole("status")).toContainText(HUELLA);
  });

  test("sin fichas vigentes muestra el motivo y no descarga", async ({ page }) => {
    await page.route("**/api/v1/rat/exportar?formato=pdf", (route) =>
      route.fulfill({ status: 409, json: { detail: "No hay fichas vigentes que exportar.", code: "RAT_VACIO" } }),
    );
    await abrirRat(page, "coordinador");
    const seccion = page.getByRole("region", { name: "Exportar" });
    await seccion.getByRole("button", { name: "Exportar PDF" }).click();
    await expect(seccion.getByRole("alert")).toContainText("No hay fichas vigentes");
  });

  test("el rol sin permiso no ve la exportación", async ({ page }) => {
    await abrirRat(page, "responsable_area");
    await expect(page.getByRole("heading", { name: /RAT Maestro/ })).toBeVisible();
    await expect(page.getByRole("button", { name: "Exportar XLSX" })).toHaveCount(0);
  });
});
