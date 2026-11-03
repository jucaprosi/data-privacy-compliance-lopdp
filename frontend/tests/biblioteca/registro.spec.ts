// ¤adpa ¤frontend-ide
// ¤¤qa-engineer
/**
 * BIB-111 · Registro de vistas de Biblioteca. Una vista registrada en la ranura de una pestaña
 * sustituye al vacío; sin registro, el vacío de BIB-101 se mantiene, en la vista completa y en el
 * panel. API simulada. Las vistas de prueba se fijan desde el navegador y solo existen fuera de
 * producción (`lib/biblioteca/registro.ts`).
 *
 * Pendiente del coordinador: añadir esta prueba a `SOLO_DESARROLLO` de `playwright.config.ts` (fuera
 * de la `propiedad` de BIB-111). Hasta entonces, en CI cae en el proyecto «produccion» y se omite;
 * en local corre contra `next dev`.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib111";
const VACIO_DOCUMENTOS = "Todavía no hay documentos de la organización";
const VACIO_PLANTILLAS = "El catálogo de plantillas aún no está disponible";

async function prepararSesion(page: Page, vistas: Array<{ ranura: string; texto: string }>) {
  await page.addInitScript(
    ({ tenant, vistasDePrueba }) => {
      window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
      (window as unknown as Record<string, unknown>).__LOPDP_VISTAS_BIBLIOTECA_PRUEBAS__ = vistasDePrueba;
    },
    { tenant: ORGANIZACION, vistasDePrueba: vistas },
  );
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
}

async function abrirBiblioteca(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-111");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page
    .getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ })
    .click();
  return page.getByRole("region", { name: "Biblioteca", exact: true });
}

test.describe("Biblioteca: registro de vistas (BIB-111, API simulada)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("sin vistas registradas se mantiene el vacío de cada pestaña", async ({ page }) => {
    await prepararSesion(page, []);
    const vista = await abrirBiblioteca(page);

    await expect(vista.getByRole("tabpanel")).toContainText(VACIO_DOCUMENTOS);
    await vista.getByRole("tab", { name: "Plantillas" }).click();
    await expect(vista.getByRole("tabpanel")).toContainText(VACIO_PLANTILLAS);
  });

  test("una vista registrada sustituye al vacío de su ranura y no toca la otra pestaña", async ({ page }) => {
    await prepararSesion(page, [{ ranura: "pestana:documentos", texto: "Vista registrada de documentos" }]);
    const vista = await abrirBiblioteca(page);

    await expect(vista.getByRole("tabpanel")).toContainText("Vista registrada de documentos");
    await expect(vista.getByRole("tabpanel")).not.toContainText(VACIO_DOCUMENTOS);

    await vista.getByRole("tab", { name: "Plantillas" }).click();
    await expect(vista.getByRole("tabpanel")).toContainText(VACIO_PLANTILLAS);
    await expect(vista.getByTestId("vista-prueba-pestana:documentos")).toHaveCount(0);
  });

  test("el panel lateral monta la misma vista registrada", async ({ page }) => {
    await prepararSesion(page, [{ ranura: "pestana:plantillas", texto: "Vista registrada de plantillas" }]);
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad BIB-111");

    await page.getByTestId("boton-biblioteca").click();
    const panel = page.getByRole("dialog", { name: "Panel de Biblioteca" });
    await expect(panel.getByRole("tabpanel")).toContainText(VACIO_DOCUMENTOS);
    await panel.getByRole("tab", { name: "Plantillas" }).click();
    await expect(panel.getByRole("tabpanel")).toContainText("Vista registrada de plantillas");
    await expect(panel.getByRole("tabpanel")).not.toContainText(VACIO_PLANTILLAS);
  });
});
