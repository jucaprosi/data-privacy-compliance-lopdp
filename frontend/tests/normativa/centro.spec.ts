// ¤vigilancia-spdp ¤navegacion-menus
// ¤¤qa-engineer
/**
 * NORM-02 · Centro de Vigilancia Normativa contra el backend real, sin datos simulados (API-01).
 *
 * Necesita la API sembrada por `servidor_e2e.py` y dos servidores de desarrollo del frontend con la API detrás:
 *   - operador:  NEXT_PUBLIC_USER_EMAIL=operador@plataforma.test NEXT_PUBLIC_OPERADOR_PLATAFORMA=1  (PLAYWRIGHT_BASE_URL)
 *   - miembro:   NEXT_PUBLIC_USER_ID=n02-e2e-miembro NEXT_PUBLIC_USER_ROLE=implementador            (NORM02_URL_MIEMBRO)
 * Sin `NORM02_BACKEND_REAL=1` se omite: no hay nada que simular.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const TENANT = "n02-e2e-org";

test.beforeEach(() => {
  test.skip(!process.env.NORM02_BACKEND_REAL, "Necesita el backend real sembrado (servidor_e2e.py).");
});

async function abrirCentro(page: Page, base?: string) {
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, TENANT);
  if (base) await page.goto(base);
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad NORM-02");
  await barraDeMenus(page).getByRole("button", { name: "Conocimiento", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Conocimiento" })
    .getByRole("button", { name: /^Vigilancia normativa/ }).click();
  return page.getByRole("region", { name: "Vigilancia normativa" });
}

test.describe("Vigilancia normativa (backend real)", () => {
  test("recorre el catálogo, filtra por año y abre el visor del documento", async ({ page }) => {
    const centro = await abrirCentro(page);
    const tabla = centro.getByRole("table", { name: "Catálogo de normas" });
    await expect(tabla).toContainText("SPDP-SPD-2026-0005-R");
    await expect(centro.getByRole("status").first()).toContainText("3 normas");

    const filtros = centro.getByRole("search", { name: "Filtrar normas" });
    await filtros.getByLabel("Año").fill("2026");
    await filtros.getByRole("button", { name: "Filtrar" }).click();
    await expect(centro.getByRole("status").first()).toContainText("1 normas");
    await expect(tabla).not.toContainText("SPDP-SPD-2024-0001-R");

    const fila = tabla.getByRole("button", { name: "SPDP-SPD-2026-0005-R" });
    await fila.click();
    const panel = page.getByRole("dialog");
    await expect(panel.getByRole("heading", { level: 3 })).toContainText("SPDP-SPD-2026-0005-R/2026");
    await expect(panel.locator('iframe[title="Documento: SPDP-SPD-2026-0005-R/2026"]')).toBeVisible();
    await expect(panel.getByRole("link", { name: "Abrir el documento en otra pestaña" })).toBeVisible();

    // Escape cierra el panel y devuelve el foco a la fila que lo abrió.
    await page.keyboard.press("Escape");
    await expect(panel).toHaveCount(0);
    await expect(fila).toBeFocused();
  });

  test("el operador dispara la búsqueda y registra una revisión con nota", async ({ page }) => {
    const centro = await abrirCentro(page);
    await centro.getByRole("tab", { name: "Bitácora" }).click();
    await centro.getByRole("button", { name: "Buscar novedades ahora" }).click();
    await expect(centro.getByRole("status").last()).toContainText("Búsqueda terminada", { timeout: 20_000 });

    await centro.getByRole("tab", { name: "Catálogo" }).click();
    await centro.getByRole("table", { name: "Catálogo de normas" }).getByRole("button", { name: "SPDP-SPD-2025-0002-R" }).click();
    const panel = page.getByRole("dialog");
    await panel.getByRole("button", { name: "Registrar revisión" }).click();
    await panel.getByRole("button", { name: "Guardar revisión" }).click();
    await expect(panel.getByRole("alert")).toContainText("Escribe una nota.");
    await panel.getByLabel("Nota").fill("Cotejada con el Registro Oficial.");
    await panel.getByRole("button", { name: "Guardar revisión" }).click();
    await expect(panel).toContainText("Estado: Vigente");
    await expect(panel).toContainText("Cotejada con el Registro Oficial.");
  });

  test("un rol de la organización no ve los botones del operador", async ({ page }) => {
    test.skip(!process.env.NORM02_URL_MIEMBRO, "Necesita el servidor del frontend con la identidad de un miembro.");
    const centro = await abrirCentro(page, process.env.NORM02_URL_MIEMBRO);
    await centro.getByRole("tab", { name: "Bitácora" }).click();
    await expect(centro.getByRole("button", { name: "Buscar novedades ahora" })).toHaveCount(0);
    await centro.getByRole("tab", { name: "Catálogo" }).click();
    await centro.getByRole("table", { name: "Catálogo de normas" }).getByRole("button").first().click();
    await expect(page.getByRole("dialog").getByRole("button", { name: "Registrar revisión" })).toHaveCount(0);
  });

  test("a 375 px no hay desplazamiento horizontal y ningún texto lleva rastros internos", async ({ page }) => {
    const centro = await abrirCentro(page);
    // La navegación se recorre en escritorio; el ancho de teléfono se mide sobre la pantalla ya abierta.
    await page.setViewportSize({ width: 375, height: 812 });
    await expect(centro.getByRole("status").first()).toContainText("normas");
    const ancho = await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);
    expect(ancho).toBe(true);
    const texto = await centro.innerText();
    expect(texto).not.toMatch(/[¤¦]/);
  });
});
