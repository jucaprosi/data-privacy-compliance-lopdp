/**
 * EP-02 · Aviso fijo del entorno y `noindex` fuera de producción (PRD §5.5 y §5.6.1.6).
 *
 * `GET /api/v1/entorno` se simula: manda el servidor, no la variable de compilación.
 * `robots.txt` y la meta `robots` dependen de `NEXT_PUBLIC_APP_ENV`, que el servidor de pruebas
 * hereda de este proceso; sin la variable, el frontend es desarrollo.
 */
import { expect, test, type Page } from "@playwright/test";

const COMPILADO = process.env.NEXT_PUBLIC_APP_ENV ?? "development";
const PRODUCCION = COMPILADO === "production";

async function simularEntorno(page: Page, entorno: string | null): Promise<void> {
  // En desarrollo el aviso solo consulta al servidor si el arnés lo pide.
  await page.addInitScript(() => {
    (window as unknown as { __LOPDP_ENTORNO_PRUEBAS__?: boolean }).__LOPDP_ENTORNO_PRUEBAS__ = true;
  });
  await page.route("**/api/v1/entorno", (ruta) =>
    entorno === null
      ? ruta.fulfill({ status: 503, body: "" })
      : ruta.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ entorno, datos_ficticios: entorno === "pruebas" || entorno === "demo" }),
        }),
  );
}

const aviso = (page: Page) => page.getByTestId("aviso-entorno");

test.describe("Aviso de entorno", () => {
  for (const ruta of ["/login", "/"]) {
    test(`con pruebas aparece en ${ruta}`, async ({ page }) => {
      await simularEntorno(page, "pruebas");
      await page.goto(ruta);
      await expect(aviso(page)).toBeVisible();
      await expect(aviso(page)).toHaveAttribute("role", "status");
      await expect(aviso(page)).toContainText("Entorno de pruebas · datos ficticios");
      await expect(aviso(page)).not.toContainText("¤");
      await expect(aviso(page).locator("[data-slot=organizacion]")).toHaveCount(1);
    });
  }

  test("con demo muestra la variante ámbar", async ({ page }) => {
    await simularEntorno(page, "demo");
    await page.goto("/login");
    await expect(aviso(page)).toContainText("Demostración · datos ficticios");
    await expect(aviso(page)).toHaveAttribute("data-entorno", "demo");
    await expect(aviso(page)).toHaveCSS("background-color", "rgb(255, 244, 214)");
  });

  test("con pruebas el fondo es azul pizarra", async ({ page }) => {
    await simularEntorno(page, "pruebas");
    await page.goto("/login");
    await expect(aviso(page)).toHaveCSS("background-color", "rgb(232, 238, 247)");
  });

  test("en producción no aparece", async ({ page }) => {
    await simularEntorno(page, "production");
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await expect(aviso(page)).toHaveCount(0);
  });

  test("si la llamada falla no aparece", async ({ page }) => {
    await simularEntorno(page, null);
    await page.goto("/login");
    await page.waitForLoadState("networkidle");
    await expect(aviso(page)).toHaveCount(0);
  });

  test("en pantalla estrecha sigue visible", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await simularEntorno(page, "pruebas");
    await page.goto("/login");
    await expect(aviso(page)).toBeVisible();
    await expect(aviso(page)).toContainText("Pruebas · ficticio");
  });
});

test.describe("Indexación", () => {
  test(`robots.txt según el entorno compilado (${COMPILADO})`, async ({ request }) => {
    const res = await request.get("/robots.txt");
    expect(res.ok()).toBeTruthy();
    const cuerpo = await res.text();
    if (PRODUCCION) expect(cuerpo).not.toMatch(/Disallow:\s*\/\s*$/m);
    else expect(cuerpo).toMatch(/Disallow:\s*\/\s*$/m);
  });

  test(`meta robots según el entorno compilado (${COMPILADO})`, async ({ page }) => {
    await page.goto("/login");
    const meta = page.locator('meta[name="robots"]');
    if (PRODUCCION) await expect(meta).toHaveCount(0);
    else await expect(meta).toHaveAttribute("content", /noindex.*nofollow/);
  });
});
