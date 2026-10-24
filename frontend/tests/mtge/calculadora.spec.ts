/**
 * MTGE-01: la calculadora de gran escala envía las seis variables de la Res. SPDP-SPD-2026-0005-R
 * al servidor y muestra su resultado; si el servidor falla, muestra el error y no inventa nada.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const RUTA = "**/api/v1/riesgos/mtge/evaluar";

async function abrirCalculadora(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Riesgos & MTGE/i);
  await expect(page.getByRole("region", { name: "Calculadora de gran escala" })).toBeVisible();
}

test.describe("Calculadora de gran escala (MTGE-01)", () => {
  test("envía las seis variables y los supuestos, y muestra el resultado del servidor", async ({ page }) => {
    let enviado: Record<string, unknown> | null = null;
    await page.route(RUTA, async (route) => {
      enviado = route.request().postDataJSON();
      await route.fulfill({
        json: {
          actividad_rat_id: "calculadora", puntaje_mtge: 13, es_gran_escala: true,
          criterio_activacion: "PUNTAJE_ART_10", supuestos_directos: [],
          desglose: { titulares: 3, volumen: 2, categorias: 2, frecuencia: 2, permanencia: 2, geografia: 2 },
          detona_eipd_obligatoria: true, detona_dpo_obligatorio: true, incluir_en_rat: true,
          medidas_reforzadas: true, rationale: "Gran escala: P = 13 alcanza el umbral de 6 (arts. 9 y 10)",
        },
      });
    });
    await abrirCalculadora(page);

    await page.getByLabel("Titulares únicos en 12 meses").fill("20000");
    await page.getByLabel("Tipos de datos por titular").fill("40");
    await page.getByLabel("Frecuencia").selectOption("CONTINUA");
    await page.getByLabel("Alcance geográfico").selectOption("NACIONAL");
    await page.getByLabel(/14\.3 Videovigilancia/).check();
    await page.getByRole("button", { name: "Calcular" }).click();

    await expect(page.getByTestId("mtge-veredicto")).toHaveText(/Gran escala/);
    await expect(page.getByTestId("mtge-puntaje")).toContainText("13");
    await expect(page.getByRole("row", { name: /Titulares en 12 meses/ })).toContainText("3");
    expect(enviado).toMatchObject({
      titulares_12_meses: 20000,
      tipos_datos_por_titular: 40,
      categorias_datos: "UNA_ESPECIAL",
      frecuencia: "CONTINUA",
      permanencia: "PROLONGADA",
      alcance: "NACIONAL",
      supuestos_directos: ["VIDEOVIGILANCIA_EN_ACCESO_PUBLICO"],
    });
  });

  test("si el servidor falla, muestra el error y no calcula en el navegador", async ({ page }) => {
    await page.route(RUTA, (route) => route.fulfill({ status: 500, json: { detail: "caído" } }));
    await abrirCalculadora(page);

    await page.getByRole("button", { name: "Calcular" }).click();

    const resultado = page.getByRole("region", { name: "Resultado del cálculo" });
    await expect(resultado.getByRole("alert")).toContainText("No se pudo calcular en el servidor");
    await expect(page.getByTestId("mtge-veredicto")).toHaveCount(0);
    await expect(page.getByTestId("mtge-puntaje")).toHaveCount(0);
  });

  test("la vista de la organización explica que el cálculo es por tratamiento", async ({ page }) => {
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Relacional|Gran escala/i);
    await expect(page.getByText(/se califica por tratamiento, no por organización/)).toBeVisible();
    await expect(page.getByText("10,000")).toHaveCount(0);
  });
});
