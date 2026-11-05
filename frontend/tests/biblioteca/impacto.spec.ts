// ¤adpa ¤arbitro
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

async function abrir(page: Page) {
  await page.addInitScript(() => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "org-bib304" }; });
  await page.route(/\/api\/v1\/biblioteca\/impactos(?:\?.*)?$/, (route) => route.fulfill({ json: [{
    id: "exp-1", impacto_id: "imp-1", codigo: "AVISO-PRIVACIDAD", version: "2.0",
    decision: "pendiente", motivo: null, documentos_afectados: 2, decidente_id: null, decidido_en: null,
  }] }));
  await page.route("**/api/v1/biblioteca/impactos/exp-1/decision", async (route) => {
    const cuerpo = route.request().postDataJSON();
    expect(cuerpo).toEqual({ decision: "actualizar", motivo: "Cambio normativo revisado" });
    await route.fulfill({ json: { id: "exp-1", ...cuerpo } });
  });
  await page.route("**/api/v1/biblioteca/documentos**", (route) => route.fulfill({ json: [] }));
  await abrirAppLimpia(page); await configurarProyecto(page, "Entidad BIB-304");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" }).getByRole("button", { name: /^Documentos y plantillas/ }).click();
}

test("registra actualizar con motivo sin editar el documento aprobado", async ({ page }) => {
  await abrir(page);
  const impacto = page.getByTestId("impacto-documental");
  await expect(impacto).toContainText("AVISO-PRIVACIDAD");
  await impacto.getByRole("textbox", { name: "Motivo" }).fill("Cambio normativo revisado");
  await impacto.getByRole("button", { name: "Actualizar", exact: true }).click();
  await expect(impacto).toBeVisible();
});
