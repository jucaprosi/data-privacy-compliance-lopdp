import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto } from "../utiles";

const PDF = {
  name: "politica-privacidad.pdf",
  mimeType: "application/pdf",
  buffer: Buffer.from("%PDF-1.4 politica de privacidad y tratamiento"),
};

const XLSX = {
  name: "balance-niif.xlsx",
  mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  buffer: Buffer.from("PK\u0003\u0004 balance de comprobacion"),
};

async function simularApi(page: Page): Promise<void> {
  await page.route("**/api/v1/**", async (route) => {
    const ruta = new URL(route.request().url()).pathname;
    // Desde DIAG-03 solo el DPO responde, sube evidencia y pide el preanálisis.
    if (ruta.endsWith("/organizacion/me/roles")) {
      await route.fulfill({ json: { roles: [{ role: "dpo" }] } });
      return;
    }
    if (ruta.endsWith("/preanalisis/estado")) {
      await route.fulfill({ json: { disponible: true, proveedor: "simulado", modelo: "qa-08", motivo: null } });
      return;
    }
    if (ruta.endsWith("/preanalisis/preparar")) {
      await route.fulfill({
        json: {
          formato: "pdf",
          caracteres_totales: 49,
          fragmentos: [{ texto: "politica de privacidad y tratamiento", origen: "p. 1", relevancia: 1 }],
          pii_enmascarada: 0,
          advertencias: [],
        },
      });
      return;
    }
    if (ruta.endsWith("/preanalisis/analizar")) {
      await route.fulfill({
        json: {
          estado: "Conforme",
          nivel_evidencia_maximo: 1,
          citas: [{ fragmento: "politica de privacidad y tratamiento", motivo: "Sustento documental simulado" }],
          citas_descartadas: 0,
          razonamiento: "La evidencia simulada sustenta el control.",
          limitaciones: [],
          modelo: "qa-08",
        },
      });
      return;
    }
    await route.fulfill({ status: 404, json: { detail: "Ruta no simulada por QA-08" } });
  });
}

async function subir(page: Page, archivo: typeof PDF): Promise<void> {
  await page.locator('input[type="file"]').first().setInputFiles(archivo);
  await expect(page.getByText(archivo.name, { exact: true })).toBeVisible();
}

async function prepararEscenario(page: Page): Promise<void> {
  await simularApi(page);
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad QA-08");
  await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
  await subir(page, PDF);

  // La propuesta pertenece a la evidencia: así la misma transición comprueba
  // que la purga cubre ambos registros y no solamente la lista visible.
  await page.locator("select").nth(1).selectOption("1");
  await page.getByRole("button", { name: "Analizar con IA" }).first().click();
  await page.getByRole("dialog", { name: "Confirmar envío al modelo de IA" }).getByRole("button", { name: "Enviar y analizar" }).click();
  await expect(page.getByText("Propuesta de la IA", { exact: true })).toBeVisible();
}

test.describe("purga al cambiar de normativa", () => {
  test("cancelar conserva evidencia y propuesta; confirmar las elimina sin reaparición", async ({ page }) => {
    await prepararEscenario(page);

    await page.locator("#selector-normativa").selectOption("NIIF");
    const confirmacion = page.getByRole("alertdialog");
    await expect(confirmacion).toContainText("eliminará las evidencias registradas");
    await confirmacion.getByRole("button", { name: "Cancelar" }).click();
    await expect(page.locator("#selector-normativa")).toHaveValue("LOPDP");
    await expect(page.getByText(PDF.name, { exact: true }).first()).toBeVisible();
    await expect(page.getByText("Propuesta de la IA", { exact: true })).toBeVisible();

    await page.locator("#selector-normativa").selectOption("NIIF");
    await page.getByRole("alertdialog").getByRole("button", { name: "Cambiar normativa" }).click();
    await expect(page.locator("#selector-normativa")).toHaveValue("NIIF");
    await expect(page.getByText(PDF.name, { exact: true })).toHaveCount(0);
    await expect(page.getByText("Propuesta de la IA", { exact: true })).toHaveCount(0);

    // abrirAppLimpia instala un init script que borra storage en cada carga;
    // abrir otra pestaña del mismo contexto simula la recarga sin falsear la
    // persistencia que precisamente queremos comprobar.
    const recargada = await page.context().newPage();
    await simularApi(recargada);
    await recargada.goto("/");
    await expect(recargada.locator("#selector-normativa")).toHaveValue("NIIF");
    await recargada.locator("#selector-normativa").selectOption("LOPDP");
    await expect(recargada.getByText(PDF.name, { exact: true })).toHaveCount(0);
    await expect(recargada.getByText("Propuesta de la IA", { exact: true })).toHaveCount(0);
  });

  test("la lista blanca cambia con la normativa activa", async ({ page }) => {
    await simularApi(page);
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad formatos QA-08");
    await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();

    await subir(page, PDF);
    await page.locator("#selector-normativa").selectOption("NIIF");
    await page.getByRole("alertdialog").getByRole("button", { name: "Cambiar normativa" }).click();

    await page.locator('input[type="file"]').first().setInputFiles(PDF);
    await expect(page.getByText(/Formato no admitido en politica-privacidad\.pdf/)).toBeVisible();
    await expect(page.getByText(PDF.name, { exact: true })).toHaveCount(0);

    await subir(page, XLSX);
  });
});
