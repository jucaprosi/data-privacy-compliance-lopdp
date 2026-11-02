/**
 * Playwright: página pública /aceptar/<token> (FIRMA-02).
 *
 * Casos:
 * - Al pulsar «Acepto» el servidor registra la aceptación, la página muestra el acuse
 *   y el enlace deja de funcionar (410).
 */
import { expect, test } from "@playwright/test";

const BASE = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

/* Token ficticio para pruebas de interfaz sin base de datos real.
   El servidor de desarrollo devuelve respuestas mockeadas si FIRMA02_MOCK=true. */
const TOKEN_VIGENTE = process.env.FIRMA02_TOKEN_VIGENTE ?? "test-token-vigente-placeholder";
const TOKEN_CADUCADO = process.env.FIRMA02_TOKEN_CADUCADO ?? "test-token-caducado-placeholder";

test.describe("Página /aceptar/<token>", () => {
  test("muestra información del documento para un enlace vigente", async ({ page }) => {
    await page.route(`**/api/v1/aceptar/${TOKEN_VIGENTE}`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          nombre_documento: "Política de Privacidad v2.0",
          organizacion: "Empresa Demo SA",
          sha256: "a".repeat(64),
        }),
      }),
    );

    await page.goto(`${BASE}/aceptar/${TOKEN_VIGENTE}`);

    await expect(page.getByText("Política de Privacidad v2.0")).toBeVisible();
    await expect(page.getByText("Empresa Demo SA")).toBeVisible();
    await expect(page.getByTestId("btn-acepto")).toBeVisible();
  });

  test("al pulsar Acepto muestra el acuse y el enlace deja de funcionar", async ({ page }) => {
    let llamadas = 0;

    // Primera GET: enlace vigente.
    await page.route(`**/api/v1/aceptar/${TOKEN_VIGENTE}`, async (route) => {
      llamadas++;
      if (llamadas === 1) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            nombre_documento: "Política de Privacidad v2.0",
            organizacion: "Empresa Demo SA",
            sha256: "a".repeat(64),
          }),
        });
      } else {
        // Segunda llamada GET después de aceptar → 410.
        await route.fulfill({
          status: 410,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Enlace ya utilizado", code: "ACEPTACION_CADUCADA" }),
        });
      }
    });

    // POST: registrar aceptación.
    await page.route(`**/api/v1/aceptar/${TOKEN_VIGENTE}`, async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ acuse_sha256: "f".repeat(64) }),
        });
      } else {
        await route.fallback();
      }
    });

    await page.goto(`${BASE}/aceptar/${TOKEN_VIGENTE}`);
    await expect(page.getByTestId("btn-acepto")).toBeVisible();

    await page.getByTestId("btn-acepto").click();

    // El acuse aparece.
    await expect(page.getByTestId("acuse-ok")).toBeVisible();
    await expect(page.getByTestId("acuse-sha256")).toContainText("f".repeat(64));

    // El botón ya no está.
    await expect(page.getByTestId("btn-acepto")).not.toBeVisible();
  });

  test("un enlace caducado muestra el mensaje de enlace no disponible", async ({ page }) => {
    await page.route(`**/api/v1/aceptar/${TOKEN_CADUCADO}`, (route) =>
      route.fulfill({
        status: 410,
        contentType: "application/json",
        body: JSON.stringify({ detail: "El enlace de aceptación ha caducado.", code: "ACEPTACION_CADUCADA" }),
      }),
    );

    await page.goto(`${BASE}/aceptar/${TOKEN_CADUCADO}`);

    await expect(page.getByTestId("enlace-caducado")).toBeVisible();
    await expect(page.getByTestId("btn-acepto")).not.toBeVisible();
  });
});
