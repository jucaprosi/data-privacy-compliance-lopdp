/**
 * EVI-01b: la pantalla de evidencias guarda y comprueba los documentos en el servidor.
 *
 * Usa la subida firmada simulada de `../utiles` (única dueña de esos mocks) y el ajuste de prueba
 * `window.__LOPDP_EVIDENCIA_PRUEBAS__`, que solo existe fuera de producción (convención `*.spec.ts`
 * en `evidencias/`, proyecto «desarrollo»).
 *
 * Mutación documentada (EVI-01b): en `src/lib/evidencias/servidor.ts`, `subirDocumento` omite el tercer paso
 * (la llamada a `/subidas/confirmar`) y da el documento por registrado -> «el DPO sube y vincula» falla porque el
 * servidor simulado no tiene ningún documento y la pantalla no muestra «Registrado y comprobado en el servidor».
 */
import { expect, test } from "@playwright/test";

import { simularApiDiagnostico } from "../diagnostico/simulador";
import { abrirAppLimpia, configurarProyecto, simularSubidaFirmada } from "../utiles";

const PDF = { name: "politica-privacidad.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4 politica de privacidad") };

test.describe("Evidencias guardadas y comprobadas por el servidor (EVI-01b)", () => {
  test.beforeEach(async ({ context }) => {
    await context.addInitScript(() => {
      window.__LOPDP_EVIDENCIA_PRUEBAS__ = true;
    });
  });

  async function abrirCarga(page: import("@playwright/test").Page) {
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
    await expect(page.getByTestId("carga-evidencias")).toBeVisible();
  }

  test("el DPO sube un documento y lo vincula; tras recargar lo trae el servidor", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    const servidor = await simularSubidaFirmada(context);
    await abrirCarga(page);

    await page.locator('input[type="file"]').first().setInputFiles(PDF);
    await expect(page.getByTestId("evidencia-en-servidor")).toBeVisible();
    expect(servidor.documentos).toHaveLength(1);
    expect(servidor.subidasSinCabecera).toBe(0);

    await page.getByRole("combobox", { name: /Vincular EVD-.* a un control/ }).selectOption({ index: 1 });
    await expect.poll(() => servidor.documentos[0].controles_vinculados.length).toBe(1);

    // Otra carga de la página: el almacenamiento local se vacía y solo el servidor puede devolver el documento.
    await page.reload();
    await expect
      .poll(async () =>
        page.evaluate(() => {
          const crudo = window.localStorage.getItem("jubys-audit-storage");
          const evidencias = crudo ? (JSON.parse(crudo).state?.evidencias ?? []) : [];
          return evidencias.map((e: { nombreArchivo: string; enServidor?: boolean }) => [e.nombreArchivo, e.enServidor]);
        })
      )
      .toEqual([["politica-privacidad.pdf", true]]);
  });

  test("un error de subida se muestra tal cual y el documento no queda como guardado", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    const servidor = await simularSubidaFirmada(context, { error: "almacen-no-configurado" });
    await abrirCarga(page);

    await page.locator('input[type="file"]').first().setInputFiles(PDF);
    await expect(page.getByText("El almacén de documentos no está disponible en este entorno.")).toBeVisible();
    await expect(page.getByText("0 registradas").or(page.getByText(/No hay evidencias registradas/))).toBeVisible();
    await expect(page.getByTestId("evidencia-en-servidor")).toHaveCount(0);
    expect(servidor.documentos).toHaveLength(0);
  });

  test("si la huella del navegador no coincide, el servidor responde 422 y nada se registra", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    const servidor = await simularSubidaFirmada(context, { error: "huella-distinta" });
    await abrirCarga(page);

    await page.locator('input[type="file"]').first().setInputFiles(PDF);
    await expect(page.getByText(/no coincide con la del archivo guardado/)).toBeVisible();
    expect(servidor.confirmaciones).toBe(1);
    expect(servidor.documentos).toHaveLength(0);
    await expect(page.getByTestId("evidencia-en-servidor")).toHaveCount(0);
  });

  test("antes del sello del real, quien no es DPO no ve dónde subir", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["coordinador"] });
    await simularSubidaFirmada(context);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await expect(page.getByTestId("carga-evidencias")).toBeVisible();
    await expect(page.getByTestId("sin-permiso-subir")).toBeVisible();
    await expect(page.locator('input[type="file"]')).toHaveCount(0);
  });

  test("sellado el real, el DPO ya no ve dónde subir", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularSubidaFirmada(context, { etapa: "real" });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await expect(page.getByTestId("carga-evidencias")).toBeVisible();
    await expect(page.getByTestId("sin-permiso-subir")).toContainText("diagnóstico real sellado");
    await expect(page.locator('input[type="file"]')).toHaveCount(0);
  });
});
