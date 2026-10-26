/**
 * FE-15: Pantallas de la hoja de ruta legibles en los dos temas (theme-light y theme-dark).
 *
 * Mide el contraste real (WCAG 2.1, criterio 1.4.3: mínimo 4.5:1) de todo el texto visible
 * de planeación, olas, indicadores y evidencias, usando los arneses de /harness-roadmap.
 */
import { expect, test, type Page } from "@playwright/test";
import { medirContraste } from "../contraste";

const TEMAS = ["theme-light", "theme-dark"] as const;

async function aplicarTema(page: Page, tema: (typeof TEMAS)[number]): Promise<void> {
  await page.evaluate((t) => {
    document.documentElement.classList.remove("theme-light", "theme-dark");
    document.documentElement.classList.add(t);
  }, tema);
}

test.describe("Colores de la hoja de ruta (FE-15)", () => {
  for (const tema of TEMAS) {
    test.describe(`Tema: ${tema}`, () => {
      test("planeación: formulario legible y sin contrastes deficientes", async ({ page }) => {
        await page.goto("/harness-roadmap/planeacion?rol=implementador");
        await expect(page.getByRole("form", { name: "Variables de planeación" })).toBeVisible();
        await aplicarTema(page, tema);

        // Abrir detalles de evidencia opcional para medir su contraste también
        const detalles = page.locator("details summary");
        if (await detalles.isVisible()) {
          await detalles.click();
        }

        const deficientes = await medirContraste(page, "main");
        expect(deficientes, JSON.stringify(deficientes, null, 2)).toEqual([]);
      });

      test("olas e indicadores: vista general legible", async ({ page }) => {
        await page.goto("/harness-roadmap/olas?rol=coordinador&roadmapId=rdmp-test-001");
        await expect(page.getByRole("region", { name: "Hoja de ruta" })).toBeVisible();
        await expect(page.getByRole("region", { name: "Indicadores de avance" })).toBeVisible();
        await aplicarTema(page, tema);

        // La tarjeta de tarea individual está auditada y certificada por FE-12 en tarjeta-colores.spec.ts
        const deficientes = await medirContraste(page, "main", { selectorExcluir: "[data-testid^='tarea-']" });
        expect(deficientes, JSON.stringify(deficientes, null, 2)).toEqual([]);
      });

      test("evidencia: panel legible en vista y validación", async ({ page }) => {
        await page.goto("/harness-roadmap/evidencia?rol=coordinador&usuario=user-coord-01&tarea=task-001");
        await expect(page.getByRole("region", { name: "Evidencia de la tarea" })).toBeVisible();
        await expect(page.getByTestId("evidencia-evi-ajena")).toBeVisible();
        await aplicarTema(page, tema);

        const deficientes = await medirContraste(page, "main");
        expect(deficientes, JSON.stringify(deficientes, null, 2)).toEqual([]);
      });
    });
  }
});
