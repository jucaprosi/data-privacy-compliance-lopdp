/**
 * Arnés de pruebas E2E para Gestión de Formación (FOR-01).
 *
 * Verifica:
 * 1. Acceso a "Formación" con tablist de tres paneles (Cobertura, Acciones, Contenidos).
 * 2. Cálculo de cobertura sobre personas activas del inventario (progressbar y texto).
 * 3. Paneles de contenidos y acciones formativas.
 * 4. Doctrina 1: Prohibida la palabra "certificado" o "diploma".
 */
import { expect, test } from "@playwright/test";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

test.describe("FOR-01: Gestión de Formación, Acciones y Cobertura", () => {
  test.beforeEach(async ({ page }) => {
    await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
    await abrirAppLimpia(page);
    await configurarProyecto(page);
  });

  test("tablist de formación, visualización de cobertura y paneles de administración", async ({ page }) => {
    // Interceptar llamadas de API de formación
    await page.route("**/api/v1/formacion/**", async (route) => {
      const url = route.request().url();
      const metodo = route.request().method();

      if (url.includes("/cobertura") && metodo === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            obligadas: 4,
            formadas: 2,
            cobertura: 0.5,
          }),
        });
      }

      if (url.includes("/acciones") && metodo === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              id: "acc-1",
              nombre: "Capacitación Anual LOPDP",
              contenido_id: "cont-1",
              contenido_titulo: "Guía de Seguridad",
              inicio: "2026-01-01",
              fin: "2026-12-31",
              nota_minima: 75,
              total_participantes: 4,
              terminados: 2,
            },
          ]),
        });
      }

      if (url.includes("/contenidos") && metodo === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify([
            {
              id: "cont-1",
              titulo: "Guía de Seguridad",
              tipo: "pdf",
              url: "https://ejemplo.com/guia.pdf",
              documento_id: null,
              creado_en: "2026-11-01T10:00:00Z",
              total_preguntas: 5,
            },
          ]),
        });
      }

      return route.continue();
    });

    await irASala(page, /^Formación/);

    // Verificar main y tablist
    const main = page.getByRole("main", { name: "Formación" });
    await expect(main).toBeVisible();

    const tablist = page.getByRole("tablist", { name: "Formación" });
    await expect(tablist).toBeVisible();

    // Pestañas
    const tabCobertura = page.getByRole("tab", { name: "Cobertura" });
    const tabAcciones = page.getByRole("tab", { name: "Acciones" });
    const tabContenidos = page.getByRole("tab", { name: "Contenidos" });

    await expect(tabCobertura).toBeVisible();
    await expect(tabAcciones).toBeVisible();
    await expect(tabContenidos).toBeVisible();

    // Cobertura activa por defecto
    await expect(page.getByRole("heading", { name: "Cobertura de formación" })).toBeVisible();
    await expect(page.getByText("2 de 4 personas formadas")).toBeVisible();
    await expect(page.getByText("50 %")).toBeVisible();

    const progressbar = page.getByRole("progressbar", { name: "Personas formadas" });
    await expect(progressbar).toBeVisible();
    await expect(progressbar).toHaveAttribute("aria-valuetext", "2 de 4");

    // Navegar a Acciones
    await tabAcciones.click();
    await expect(page.getByText("Capacitación Anual LOPDP")).toBeVisible();
    await expect(page.getByText("Del 2026-01-01 al 2026-12-31")).toBeVisible();

    // Navegar a Contenidos
    await tabContenidos.click();
    await expect(page.getByText("Guía de Seguridad")).toBeVisible();

    // Doctrina 1: En ningún texto visible debe existir certificado ni diploma
    const htmlContenido = await page.content();
    expect(htmlContenido.toLowerCase()).not.toContain("certificado");
    expect(htmlContenido.toLowerCase()).not.toContain("diploma");
  });
});
