// ¤arbitro
// ¤¤qa-engineer
/**
 * BIB-118 · Menú «Administración editorial» por capacidades (API simulada; el GET real lo acredita
 * `tests/test_bib118_capacidades_mias.py`). Criterios 1-4 de UX_BIBLIOTECA_CAPACIDADES_EDITORIALES.md §4.
 *
 * MUTACIÓN DECISIVA: en `src/components/layout/menus/BIB-118.ts` cambiar el predicado por
 * `visible: () => true` hace fallar «sin capacidades el submenú no existe, ni en Ctrl+K».
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib118";

async function abrir(page: Page, capacidades: string[], editorial: "ok" | "403" = "ok") {
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, ORGANIZACION);
  await page.route("**/api/v1/**", (ruta) => ruta.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/capacidades/mias", (ruta) => ruta.fulfill({ json: { capacidades } }));
  await page.route("**/api/v1/biblioteca/editorial", (ruta) =>
    editorial === "403"
      ? ruta.fulfill({ status: 403, json: { code: "BIB_SIN_CAPACIDAD", detail: "No tienes capacidad editorial asignada." } })
      : ruta.fulfill({ json: { actor_id: "editor", capacidades, versiones: [], revisiones: [] } }));
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-118");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  return page.getByRole("group", { name: "Submenús de Biblioteca" });
}

async function abrirEditorial(page: Page, capacidades: string[], editorial: "ok" | "403" = "ok") {
  const submenus = await abrir(page, capacidades, editorial);
  await submenus.getByRole("button", { name: /^Administración editorial/ }).click();
  return page.getByRole("main", { name: "Administración editorial" });
}

test.describe("Biblioteca: Administración editorial por capacidades (BIB-118, API simulada)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("sin capacidades el submenú no existe, ni en Ctrl+K", async ({ page }) => {
    const submenus = await abrir(page, []);
    await expect(submenus.getByRole("button", { name: /^Documentos y plantillas/ })).toBeVisible();
    await expect(submenus.getByRole("button", { name: /^Administración editorial/ })).toHaveCount(0);
    await page.keyboard.press("Control+k");
    await page.keyboard.type("Administración editorial");
    await expect(page.getByRole("option", { name: /Administración editorial/ })).toHaveCount(0);
  });

  test("con «editor» el submenú existe y la cabecera muestra solo «Editor»", async ({ page }) => {
    const vista = await abrirEditorial(page, ["editor"]);
    const lista = vista.getByRole("list", { name: "Tus permisos editoriales" });
    await expect(lista.getByRole("listitem")).toHaveText(["Editor"]);
    await expect(vista.getByText(/^Recuerda:/)).toHaveCount(0);
  });

  test("con editor y revisor técnico aparece la línea «Recuerda…»", async ({ page }) => {
    const vista = await abrirEditorial(page, ["editor", "revisor_tecnico"]);
    await expect(vista.getByRole("list", { name: "Tus permisos editoriales" }).getByRole("listitem"))
      .toHaveText(["Editor", "Revisor técnico"]);
    await expect(vista.getByText("Recuerda: no puedes revisar ni publicar las versiones que tú creaste.")).toBeVisible();
  });

  test("si la vista responde 403 se muestra el estado vacío", async ({ page }) => {
    const vista = await abrirEditorial(page, ["publicador"], "403");
    await expect(vista.getByRole("status").filter({ hasText: "No tienes permisos editoriales en la Biblioteca" }))
      .toHaveText("No tienes permisos editoriales en la Biblioteca. Los asigna el equipo de la plataforma.");
  });
});

test.describe("Sin contexto de capacidades (BIB-118, FE-22 R4)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("mientras carga, los demás submenús siguen igual y solo se oculta el que tiene predicado", async ({ page }) => {
    await page.addInitScript((tenant) => {
      window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
    }, ORGANIZACION);
    await page.route("**/api/v1/**", (ruta) => ruta.fulfill({ status: 503, json: { detail: "API simulada" } }));
    await page.route("**/api/v1/biblioteca/capacidades/mias", () => new Promise(() => {}));  // nunca responde
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad BIB-118");
    for (const menu of ["Inicio", "Diagnóstico", "Inventario", "Biblioteca"]) {
      await expect(barraDeMenus(page).getByRole("button", { name: menu, exact: true })).toBeVisible();
    }
    await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
    const submenus = page.getByRole("group", { name: "Submenús de Biblioteca" });
    await expect(submenus.getByRole("button", { name: /^Documentos y plantillas/ })).toBeVisible();
    await expect(submenus.getByRole("button", { name: /^Administración editorial/ })).toHaveCount(0);
  });
});
