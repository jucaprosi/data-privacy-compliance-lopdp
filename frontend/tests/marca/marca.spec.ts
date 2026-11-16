/**
 * MARCA-04 · Nombre único EVYDENTIA en el frontend:
 * Paleta de comandos, reporte de assessment, página de plataforma y configuración de proyecto.
 */
import { expect, test } from "@playwright/test";

import { generarHtmlReporteAssessment } from "../../src/lib/reportes/generarReporteAssessment";
import type { CompanyData, ResultadoAssessment } from "../../src/store/useAuditStore";
import { abrirAppLimpia, configurarProyecto } from "../utiles";

test.describe("Nombre único EVYDENTIA (MARCA-04)", () => {
  test("la paleta de comandos muestra EVYDENTIA y no JUBYS", async ({ page }) => {
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad EVYDENTIA");

    await page.keyboard.press("Control+K");
    const buscador = page.getByPlaceholder(/Escribe un comando/i);
    await expect(buscador).toBeVisible();

    // Verificamos el pie de la paleta
    const pie = page.getByText(/cmdk · EVYDENTIA LOPDP 360/);
    await expect(pie).toBeVisible();

    // Verificamos el label accesible del elemento Command
    const cmdRoot = page.locator('[aria-label="Paleta de Comandos Universal EVYDENTIA LOPDP 360"]');
    await expect(cmdRoot).toBeVisible();

    // Aseguramos que la paleta no contenga texto visible ni atributo con JUBYS
    await expect(page.locator("text=/JUBYS/i")).toHaveCount(0);
    await expect(page.locator('[aria-label*="JUBYS" i]')).toHaveCount(0);

    await page.keyboard.press("Escape");
    await expect(buscador).toBeHidden();
  });

  test("la configuración del proyecto muestra placeholder con EVYDENTIA y no Jubys", async ({ page }) => {
    // Al abrir la app limpia, la pantalla inicial es la ficha de configuración
    await abrirAppLimpia(page);

    const inputRazonSocial = page.getByRole("textbox", { name: /Razón Social/i });
    await expect(inputRazonSocial).toBeVisible();
    await expect(inputRazonSocial).toHaveAttribute(
      "placeholder",
      "Ej. EVYDENTIA Cloud Solutions S.A.S."
    );
    const placeholder = await inputRazonSocial.getAttribute("placeholder");
    expect(placeholder).not.toMatch(/jubys/i);
  });

  test("la página de plataforma muestra valores de ejemplo neutros y no JUBYS", async ({ page }) => {
    await page.route("**/api/v1/plataforma/organizaciones**", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify([]),
      });
    });
    await page.goto("/plataforma");

    await expect(page.getByPlaceholder("Empresa Ejemplo")).toBeVisible();
    await expect(page.getByPlaceholder("Empresa Ejemplo S.A.")).toBeVisible();
    await expect(page.locator('[placeholder*="JUBYS" i]')).toHaveCount(0);
    await expect(page.locator("text=/JUBYS/i")).toHaveCount(0);
  });

  test("el generador del reporte de assessment incluye EVYDENTIA en el footer y no JUBYS", () => {
    const dummyResultado: ResultadoAssessment = {
      scorePonderado: 0,
      nivelTeorico: 0,
      nivelTeoricoEtiqueta: "Inicial",
      nivelAjustado: 0,
      nivelAjustadoEtiqueta: "Inicial",
      ajustePorBrechaEstructural: false,
      ajustePorEvidenciaInsuficiente: false,
      coberturaInsuficiente: false,
      dimensiones: [],
      brechas: [],
      brechasCriticas: 0,
      brechasAltas: 0,
      controlesEstructuralesDegradados: 0,
      controlesBloqueantesDegradados: 0,
      controlesSinEvidenciaSuficiente: 0,
      controlesEstructuralesEvaluados: [],
      totalEvaluados: 0,
      totalAplicables: 0,
      coberturaPorcentaje: 0,
      soloReferencia: false,
      respuestasPropias: 0,
      modo: "declarado",
      controlesConEvidenciaVinculada: 0,
    };
    const dummyCompany: CompanyData = {
      razonSocial: "Empresa de Prueba",
      sector: "Tecnología",
      tamano: "Mediana",
    };

    const html = generarHtmlReporteAssessment(dummyResultado, dummyResultado, dummyCompany);
    expect(html).toContain("EVYDENTIA · Plataforma LOPDP 360 — Reporte de Assessment de Madurez SGPDP");
    expect(html).not.toMatch(/JUBYS/i);
  });
});
