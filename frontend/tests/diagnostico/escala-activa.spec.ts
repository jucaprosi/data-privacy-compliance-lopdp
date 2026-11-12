/**
 * DIAG-09 con la evidencia física encendida (EVYDENTIA, FE-26): la propuesta de la IA sobre un archivo
 * subido a la carga de evidencias marca el rango del estado y deja el nivel sin elegir.
 *
 * Usa el ajuste de prueba `window.__LOPDP_EVIDENCIA_PRUEBAS__`, que solo existe fuera de producción,
 * y corre en el proyecto «desarrollo» (convención `*-activa.spec.ts`). El resto de la escala está en
 * `escala.spec.ts`.
 */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, responderControlActual, simularSubidaFirmada } from "../utiles";
import { simularRespuestasDiagnostico08 } from "./respuestas08";
import { simularApiDiagnostico } from "./simulador";

test.describe("Escala SMARTCIDI con evidencia física (DIAG-09, EVYDENTIA)", () => {
  // === FE-26 ===
  test.beforeEach(async ({ context }) => {
    await context.addInitScript(() => {
      window.__LOPDP_EVIDENCIA_PRUEBAS__ = true;
    });
  });
  // === fin FE-26 ===

  test("propuesta de la IA: el nivel queda sin elegir y el rango del estado queda marcado", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularRespuestasDiagnostico08(context);
    await simularSubidaFirmada(context);
    await page.route("**/api/v1/preanalisis/**", async (route) => {
      const ruta = new URL(route.request().url()).pathname;
      if (ruta.endsWith("/preanalisis/estado")) {
        await route.fulfill({ json: { disponible: true, proveedor: "simulado", modelo: "qa-09", motivo: null } });
      } else if (ruta.endsWith("/preanalisis/preparar")) {
        await route.fulfill({
          json: {
            formato: "pdf",
            caracteres_totales: 49,
            fragmentos: [{ texto: "politica de privacidad y tratamiento", origen: "p. 1", relevancia: 1 }],
            pii_enmascarada: 0,
            advertencias: [],
          },
        });
      } else if (ruta.endsWith("/preanalisis/analizar")) {
        await route.fulfill({
          json: {
            estado: "Parcial",
            nivel_evidencia_maximo: 1,
            citas: [{ fragmento: "politica de privacidad y tratamiento", motivo: "Sustento simulado" }],
            citas_descartadas: 0,
            razonamiento: "La evidencia simulada sustenta el control en parte.",
            limitaciones: [],
            modelo: "qa-09",
          },
        });
      } else {
        await route.fallback();
      }
    });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
    await page.locator('input[type="file"]').first().setInputFiles({
      name: "politica-privacidad.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("%PDF-1.4 politica de privacidad y tratamiento"),
    });
    await page.locator("select").nth(1).selectOption("1");
    await page.getByRole("button", { name: "Analizar con IA" }).first().click();
    await page
      .getByRole("dialog", { name: "Confirmar envío al modelo de IA" })
      .getByRole("button", { name: "Enviar y analizar" })
      .click();
    await expect(page.getByText("Propuesta de la IA", { exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Aceptar propuesta" }).click();

    const niveles = page.getByRole("radiogroup", { name: /Nivel de madurez/ });
    await expect(niveles.getByRole("radio").first()).toBeVisible();
    // Parcial = niveles 2 y 3: ninguno elegido, los dos marcados y los demás sin marca.
    await expect(niveles.getByRole("radio", { checked: true })).toHaveCount(0);
    await expect(niveles.locator("[data-sugerido]")).toHaveCount(2);
    await expect(niveles.locator('[data-nivel="2"]')).toHaveAttribute("data-sugerido", "true");
    await expect(niveles.locator('[data-nivel="3"]')).toHaveAttribute("data-sugerido", "true");
    await expect(page.getByTestId("rango-sugerido")).toContainText("entre 2 y 3");
    await expect(page.getByTestId("estado-derivado")).toHaveText("Pendiente");

    await responderControlActual(page, 3);
    await expect(niveles.locator('[data-nivel="3"]')).toHaveAttribute("aria-checked", "true");
  });
});
