import { expect, test, type Page } from "@playwright/test";

async function abrirLimpio(page: Page): Promise<void> {
  await page.route("**/api/**", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ success: true, respuestas: [] }),
  }));
  await page.goto("/");
  await page.evaluate(() => localStorage.clear());
  await page.reload();
  await expect(page.locator("#panel-dock-izquierdo")).toBeVisible();
}

async function ancho(page: Page): Promise<number> {
  const caja = await page.locator("#panel-dock-izquierdo").boundingBox();
  expect(caja).not.toBeNull();
  return caja!.width;
}

test.describe("Persistencia de preferencias de interfaz", () => {
  test("conserva el tamaño del panel tras recargar", async ({ page }) => {
    await abrirLimpio(page);
    const separador = page.getByTitle("Arrastra para redimensionar el panel").first();
    const asa = await separador.boundingBox();
    expect(asa).not.toBeNull();

    await page.mouse.move(asa!.x + asa!.width / 2, asa!.y + asa!.height / 2);
    await page.mouse.down();
    await page.mouse.move(asa!.x + 90, asa!.y + asa!.height / 2, { steps: 8 });
    await page.mouse.up();
    const redimensionado = await ancho(page);

    await page.reload();
    await expect.poll(() => ancho(page)).toBeGreaterThanOrEqual(redimensionado - 2);
    expect(await ancho(page)).toBeLessThanOrEqual(redimensionado + 2);
  });

  test("conserva el tema oscuro tras recargar", async ({ page }) => {
    await abrirLimpio(page);
    await page.getByTitle("Cambiar a tema oscuro").click();
    await expect(page.locator(".app-frame-canvas")).toHaveClass(/theme-dark/);

    await page.reload();
    await expect(page.locator(".app-frame-canvas")).toHaveClass(/theme-dark/);
    await expect(page.getByTitle("Cambiar a tema claro")).toBeVisible();
  });

  test("un navegador limpio usa tema claro y distribución predeterminada", async ({ page }) => {
    await abrirLimpio(page);
    await expect(page.locator(".app-frame-canvas")).toHaveClass(/theme-light/);
    await expect(page.getByTitle("Cambiar a tema oscuro")).toBeVisible();

    const grupo = await page.locator("#dashboard-paneles-v1").boundingBox();
    expect(grupo).not.toBeNull();
    // 18 % del grupo; los separadores entre paneles restan unos píxeles al ancho medido.
    expect(Math.abs((await ancho(page)) - grupo!.width * 0.18)).toBeLessThanOrEqual(4);
  });
});
