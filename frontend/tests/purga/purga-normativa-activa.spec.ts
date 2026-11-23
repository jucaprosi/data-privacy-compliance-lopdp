// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// === FE-26 ===
// Estas pruebas suben evidencias al diagnóstico (custodia física, EVYDENTIA): encienden el ajuste de
// prueba `window.__LOPDP_EVIDENCIA_PRUEBAS__`, que solo existe fuera de producción, y corren en el
// proyecto «desarrollo» (convención `*-activa.spec.ts`). El PMV no monta la carga (pmv/sin-subida.spec.ts).
// === fin FE-26 ===
import { expect, test, type Browser, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, simularSubidaFirmada, type SubidaFirmadaSimulada } from "../utiles";

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

async function simularApi(page: Page, rol = "dpo", servidor = false): Promise<SubidaFirmadaSimulada> {
  const almacen = await simularSubidaFirmada(page);
  await page.route("**/api/v1/**", async (route) => {
    const ruta = new URL(route.request().url()).pathname;
    // La evidencia la atiende la subida firmada simulada: así el administrador lee lo que vinculó el DPO.
    if (servidor && ruta.includes("/evidencias/")) {
      await route.fallback();
      return;
    }
    // DIAG-07 R6: el DPO sube y vincula la evidencia; quien responde pide el preanálisis.
    if (ruta.endsWith("/organizacion/me/roles")) {
      await route.fulfill({ json: { roles: [{ role: rol }] } });
      return;
    }
    if (ruta.endsWith("/preanalisis/estado")) {
      await route.fulfill({ json: { disponible: true, proveedor: "simulado", modelo: "qa-08", motivo: null, ubicacion: "Estados Unidos", region: "us" } });
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
  return almacen;
}

async function subir(page: Page, archivo: typeof PDF): Promise<void> {
  await page.locator('input[type="file"]').first().setInputFiles(archivo);
  // El título solo lo lleva la evidencia registrada; el nombre sale también, un instante, en la fila
  // de «calculando huella…», y getByText daría violación de modo estricto, que no se reintenta.
  await expect(page.getByTitle(archivo.name, { exact: true })).toBeVisible();
}

/**
 * Nombres del registro de evidencias persistido. DIAG-07 R6: el administrador no ve la lista de evidencias
 * (la carga es del DPO), así que la conservación y la purga se comprueban en el registro mismo.
 */
function registro(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const crudo = window.localStorage.getItem("jubys-audit-storage");
    const evidencias = crudo ? (JSON.parse(crudo).state?.evidencias ?? []) : [];
    return evidencias.map((e: { nombreArchivo: string }) => e.nombreArchivo);
  });
}

/**
 * DIAG-07 R6, un rol por sesión: el DPO sube y vincula la evidencia; el administrador, en su sesión, la lee
 * del servidor y pide la propuesta de la IA. Devuelve la página del administrador.
 */
async function prepararEscenario(dpo: Page, browser: Browser): Promise<Page> {
  const almacen = await simularApi(dpo, "dpo", true);
  await abrirAppLimpia(dpo);
  await configurarProyecto(dpo, "Entidad QA-08");
  await expect(dpo.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
  await dpo.getByTestId("carga-evidencia-dpo").locator('input[type="file"]').first().setInputFiles(PDF);
  await expect.poll(() => almacen.documentos[0]?.controles_vinculados.length ?? 0).toBeGreaterThan(0);

  const contextoAdmin = await browser.newContext();
  await contextoAdmin.addInitScript(() => {
    window.__LOPDP_EVIDENCIA_PRUEBAS__ = true;
  });
  const inicial = await contextoAdmin.newPage();
  await simularApi(inicial, "admin_organizacion", true);
  await abrirAppLimpia(inicial);
  await configurarProyecto(inicial, "Entidad QA-08");
  await inicial.close();
  // Pestaña nueva del mismo contexto: la ficha persiste y el registro se lee del servidor.
  const page = await contextoAdmin.newPage();
  await simularApi(page, "admin_organizacion", true);
  await page.route("**/api/v1/evidencias/documentos", (route) =>
    route.request().method() === "GET" ? route.fulfill({ json: { total: almacen.documentos.length, documentos: almacen.documentos } }) : route.fallback()
  );
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
  const alerta = page.getByRole("button", { name: "Cerrar alerta" });
  // La alerta se monta tras hidratar: se espera un momento antes de decidir que no está.
  await alerta.waitFor({ state: "visible", timeout: 5000 }).catch(() => undefined);
  if (await alerta.isVisible()) await alerta.click();

  // La propuesta pertenece a la evidencia: así la misma transición comprueba
  // que la purga cubre ambos registros y no solamente la lista visible.
  await page.getByRole("button", { name: "Analizar con IA" }).first().click();
  await page.getByLabel("Volver a presentar el archivo").setInputFiles(PDF);
  await page.getByRole("dialog", { name: "Confirmar envío al modelo de IA" }).getByRole("button", { name: "Enviar y analizar" }).click();
  await expect(page.getByText("Propuesta de la IA", { exact: true })).toBeVisible();
  return page;
}

test.describe("purga al cambiar de normativa", () => {
  // === FE-26 ===
  test.beforeEach(async ({ context }) => {
    await context.addInitScript(() => {
      window.__LOPDP_EVIDENCIA_PRUEBAS__ = true;
    });
  });
  // === fin FE-26 ===
  test("cancelar conserva evidencia y propuesta; confirmar las elimina sin reaparición", async ({ page: dpo, browser }) => {
    test.slow(); // Dos sesiones de navegador en una prueba.
    const page = await prepararEscenario(dpo, browser);

    await page.locator("#selector-normativa").selectOption("NIIF");
    const confirmacion = page.getByRole("alertdialog");
    await expect(confirmacion).toContainText("eliminará las evidencias registradas");
    await confirmacion.getByRole("button", { name: "Cancelar" }).click();
    await expect(page.locator("#selector-normativa")).toHaveValue("LOPDP");
    await expect.poll(() => registro(page)).toEqual([PDF.name]);
    await expect(page.getByText("Propuesta de la IA", { exact: true })).toBeVisible();

    await page.locator("#selector-normativa").selectOption("NIIF");
    await page.getByRole("alertdialog").getByRole("button", { name: "Cambiar normativa" }).click();
    await expect(page.locator("#selector-normativa")).toHaveValue("NIIF");
    await expect.poll(() => registro(page)).toEqual([]);
    await expect(page.getByText("Propuesta de la IA", { exact: true })).toHaveCount(0);

    // abrirAppLimpia instala un init script que borra storage en cada carga;
    // abrir otra pestaña del mismo contexto simula la recarga sin falsear la
    // persistencia que precisamente queremos comprobar.
    const recargada = await page.context().newPage();
    await simularApi(recargada, "admin_organizacion", true);
    await recargada.goto("/");
    await expect(recargada.locator("#selector-normativa")).toHaveValue("NIIF");
    await recargada.locator("#selector-normativa").selectOption("LOPDP");
    await expect(recargada.locator("#selector-normativa")).toHaveValue("LOPDP");
    await expect.poll(() => registro(recargada)).toEqual([]);
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
