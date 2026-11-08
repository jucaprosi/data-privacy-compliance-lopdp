// ¤arbitro
// ¤¤qa-engineer
/**
 * BIB-119 · Capacidades editoriales: recarga y cambio de persona u organización (API simulada, `/mias`
 * retrasada). Pruebas 1-7 de governance/tareas/BIB-119.md.
 *
 * Mutaciones ejecutadas (BIB-119.md):
 * - M1 `contextoVisibilidad()` en el efecto de page.tsx: fallan la 2 y la 3. La 1 sigue en verde, porque la
 *   vista se pinta con el hook aunque el efecto no se vuelva a ejecutar; la ficha esperaba la 1.
 * - M2 corregir la vista con `null`: falla la 1.
 * - M3 clave sin persona en useCapacidadesEditoriales.ts: falla la 6.
 * - M4 sin contador de generación: falla la 4.
 * - M5 aviso también cuando la petición falla: falla la 7.
 */
import { expect, test, type Page } from "@playwright/test";
import { barraDeMenus, configurarProyecto } from "../utiles";

const ORG_A = "org-prueba-bib119-a";
const ORG_B = "org-prueba-bib119-b";
const PERSONA = "evydentia.demo.persona";
const AVISO = "No tienes permisos editoriales en la Biblioteca. Te llevamos al tablero.";

type Respuesta = { capacidades?: string[]; estado?: number; demora?: number };

/** `responder(n, tenant, persona)` decide la respuesta de la n-ésima llamada a `/mias`. */
async function preparar(page: Page, responder: (n: number, tenant: string, persona: string) => Respuesta) {
  const llamadas: string[] = [];
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = window.__LOPDP_AUTH_PRUEBAS__ ?? { modo: "headers", tenant };
    // Limpia el almacenamiento persistente solo en la primera carga: una recarga lo conserva.
    if (!sessionStorage.getItem("bib119-limpio")) {
      localStorage.clear();
      sessionStorage.setItem("bib119-limpio", "1");
    }
    // Rastro de si el panel llegó a pintarse en algún momento.
    new MutationObserver(() => {
      if (document.body?.innerText.includes("dashboard.adpa.view")) sessionStorage.setItem("bib119-paso-panel", "1");
    }).observe(document, { subtree: true, childList: true, characterData: true });
  }, ORG_A);
  await page.route("**/api/v1/**", (ruta) => ruta.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/editorial", (ruta) =>
    ruta.fulfill({ json: { actor_id: "editor", capacidades: ["editor"], versiones: [], revisiones: [] } }));
  await page.route("**/api/v1/biblioteca/capacidades/mias", async (ruta) => {
    const tenant = ruta.request().headers()["x-tenant-id"] ?? "";
    const persona = await page.evaluate((c) => sessionStorage.getItem(c) ?? "", PERSONA).catch(() => "");
    llamadas.push(`${tenant}|${persona}`);
    const r = responder(llamadas.length, tenant, persona);
    await new Promise((fin) => setTimeout(fin, r.demora ?? 1000));
    await ruta.fulfill(r.estado ? { status: r.estado, json: { detail: "Fallo simulado" } }
      : { json: { capacidades: r.capacidades ?? [] } }).catch(() => {});
  });
  await page.goto("/");
  await expect(page.getByRole("textbox", { name: /Razón Social/ })).toBeVisible();
  await configurarProyecto(page, "Entidad BIB-119");
  return llamadas;
}

const submenus = (page: Page) => page.getByRole("group", { name: "Submenús de Biblioteca" });

async function abrirBiblioteca(page: Page) {
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  return submenus(page);
}

async function entrarEnEditorial(page: Page) {
  await (await abrirBiblioteca(page)).getByRole("button", { name: /^Administración editorial/ }).click();
  await expect(page.getByRole("main", { name: "Administración editorial" })).toBeVisible();
}

const pasoPorPanel = (page: Page) => page.evaluate(() => sessionStorage.getItem("bib119-paso-panel") === "1");
const marcarSinPanel = (page: Page) => page.evaluate(() => sessionStorage.removeItem("bib119-paso-panel"));
const enPanel = (page: Page) => expect(page.getByText("dashboard.adpa.view")).toBeVisible();

test.describe("Biblioteca: capacidades editoriales al recargar y cambiar de persona (BIB-119)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("1 · recargar con capacidad muestra la carga y luego la vista, sin pasar por el panel", async ({ page }) => {
    await preparar(page, () => ({ capacidades: ["editor"] }));
    await entrarEnEditorial(page);
    await marcarSinPanel(page);
    await page.reload();
    await expect(page.getByRole("status").filter({ hasText: "Cargando la administración editorial…" }))
      .toHaveAttribute("aria-busy", "true");
    await expect(page.getByRole("main", { name: "Administración editorial" })).toBeVisible();
    expect(await pasoPorPanel(page)).toBe(false);
  });

  test("2 · recargar sin capacidades termina en el panel con el aviso", async ({ page }) => {
    await preparar(page, (n) => ({ capacidades: n === 1 ? ["editor"] : [] }));
    await entrarEnEditorial(page);
    await page.reload();
    await enPanel(page);
    await expect(page.getByRole("status").filter({ hasText: AVISO })).toHaveText(AVISO);
  });

  test("3 · cambiar de organización sin recargar quita el submenú, también en Ctrl+K, y saca de la vista", async ({ page }) => {
    await preparar(page, (_n, tenant) => ({ capacidades: tenant === ORG_A ? ["editor"] : [], demora: 300 }));
    await entrarEnEditorial(page);
    await page.evaluate((t) => { window.__LOPDP_AUTH_PRUEBAS__!.tenant = t; }, ORG_B);
    await abrirBiblioteca(page);
    await enPanel(page);
    await abrirBiblioteca(page);
    await expect(submenus(page).getByRole("button", { name: /^Administración editorial/ })).toHaveCount(0);
    await page.keyboard.press("Control+k");
    await page.keyboard.type("Administración editorial");
    await expect(page.getByRole("option", { name: /Administración editorial/ })).toHaveCount(0);
  });

  test("4 · la respuesta tardía de A no le muestra el menú a B", async ({ page }) => {
    test.setTimeout(90_000);
    // La respuesta de A tarda más que todo el alta del proyecto: llega cuando ya se cambió a B.
    const llamadas = await preparar(page, (_n, tenant) => tenant === ORG_A
      ? { capacidades: ["editor"], demora: 20000 } : { capacidades: [], demora: 100 });
    const inicio = Date.now();
    await page.evaluate((t) => { window.__LOPDP_AUTH_PRUEBAS__!.tenant = t; }, ORG_B);
    await abrirBiblioteca(page);
    await expect.poll(() => llamadas.some((l) => l.startsWith(ORG_B))).toBe(true);
    await page.waitForTimeout(Math.max(0, 21000 - (Date.now() - inicio)));
    await abrirBiblioteca(page);
    await expect(submenus(page).getByRole("button", { name: /^Documentos y plantillas/ })).toBeVisible();
    await expect(submenus(page).getByRole("button", { name: /^Administración editorial/ })).toHaveCount(0);
  });

  test("5 · cambiar de organización con la misma persona vuelve a pedir /mias", async ({ page }) => {
    const llamadas = await preparar(page, () => ({ capacidades: ["editor"], demora: 100 }));
    await abrirBiblioteca(page);
    await expect.poll(() => llamadas.length).toBeGreaterThanOrEqual(1);
    const antes = llamadas.length;
    await page.evaluate((t) => { window.__LOPDP_AUTH_PRUEBAS__!.tenant = t; }, ORG_B);
    await abrirBiblioteca(page);
    await expect.poll(() => llamadas.length).toBe(antes + 1);
    expect(llamadas.at(-1)).toContain(ORG_B);
  });

  test("6 · en la demo, cambiar solo de persona vuelve a pedir /mias", async ({ page }) => {
    const llamadas = await preparar(page, () => ({ capacidades: ["editor"], demora: 100 }));
    await abrirBiblioteca(page);
    await expect.poll(() => llamadas.length).toBeGreaterThanOrEqual(1);
    const antes = llamadas.length;
    await page.evaluate((c) => sessionStorage.setItem(c, JSON.stringify({ usuario_id: "demo-persona-2", rol: "dpo" })), PERSONA);
    await abrirBiblioteca(page);
    await expect.poll(() => llamadas.length).toBe(antes + 1);
    expect(llamadas.at(-1)).toContain(ORG_A);
  });

  test("7 · si /mias falla no se muestra el aviso de salida", async ({ page }) => {
    await preparar(page, (n) => (n === 1 ? { capacidades: ["editor"] } : { estado: 500 }));
    await entrarEnEditorial(page);
    await page.reload();
    await enPanel(page);
    await expect(page.getByText(AVISO)).toHaveCount(0);
  });
});
