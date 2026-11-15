// ¤inteligencia-normativa ¤copiloto-ia ¤dpo-independencia
// ¤¤qa-engineer
/**
 * NORM-03 · pestaña «Impacto» del detalle de una norma, contra el backend real (API-01).
 *
 * Necesita la pestaña montada en el panel de NORM-02 y una API con una resolución, el modelo simulado en el servidor
 * (el único doble) y dos personas de la organización: DPO (`NORM03_USUARIO_DPO`) y administración
 * (`NORM03_USUARIO_ADMIN`). Sin `NORM03_BACKEND_REAL=1` se omite: no hay nada que simular en el navegador.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const TENANT = process.env.NORM03_TENANT ?? "n03-e2e-org";
const NUMERO = process.env.NORM03_NUMERO ?? "SPDP-N03-2026";

test.beforeEach(() => {
  test.skip(!process.env.NORM03_BACKEND_REAL, "Necesita el backend real sembrado para NORM-03.");
});

async function abrirImpacto(page: Page) {
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, TENANT);
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad NORM-03");
  await barraDeMenus(page).getByRole("button", { name: "Conocimiento", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Conocimiento" })
    .getByRole("button", { name: /^Vigilancia normativa/ }).click();
  await page.getByRole("table", { name: "Catálogo de normas" }).getByRole("button", { name: new RegExp(NUMERO) }).click();
  const panel = page.getByRole("dialog");
  await panel.getByRole("tab", { name: "Impacto" }).click();
  return panel.getByRole("tabpanel", { name: "Impacto" });
}

test.describe("Impacto normativo (backend real)", () => {
  test("avisa que la propuesta es de una IA, la analiza y el DPO la acepta con nota", async ({ page }) => {
    const impacto = await abrirImpacto(page);
    await expect(impacto.getByRole("note")).toContainText("generó una IA");

    await impacto.getByRole("button", { name: "Analizar impacto en mi organización" }).click();
    const analisis = impacto.getByRole("article").first();
    await expect(analisis).toContainText("Pendiente de decisión");
    await expect(analisis).toContainText("Cita:");

    await analisis.getByRole("button", { name: "Aceptar" }).click();
    const formulario = impacto.getByRole("form", { name: "Aceptar la propuesta" });
    await formulario.getByRole("button", { name: /^Confirmar/ }).click();
    await expect(formulario.getByRole("alert")).toContainText("nota");

    await formulario.getByLabel("Nota de la decisión").fill("Revisado por el DPO contra el texto.");
    await formulario.getByRole("button", { name: /^Confirmar/ }).click();
    await expect(analisis).toContainText("Aceptada");
    await expect(analisis).toContainText("Nota del DPO");
  });

  test("quien no es DPO no ve Aceptar ni Rechazar", async ({ page }) => {
    test.skip(!process.env.NORM03_SOLO_ADMIN, "Requiere el servidor del frontend con el rol de administración.");
    const impacto = await abrirImpacto(page);
    await expect(impacto.getByRole("article").first()).toContainText("Pendiente de decisión");
    await expect(impacto.getByRole("button", { name: "Aceptar" })).toHaveCount(0);
    await expect(impacto.getByRole("button", { name: "Rechazar" })).toHaveCount(0);
  });
});
