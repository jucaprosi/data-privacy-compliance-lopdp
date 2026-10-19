/**
 * Arnés de interfaz de FE-02: formulario de variables de planeación y generación.
 *
 * Monta PlaneacionForm en la ruta de pruebas /harness-roadmap/planeacion, que instala el
 * servidor simulado de FE-01. Parámetros de la ruta: rol, latencia (ms) y fallo=1.
 */
import { expect, test, type Page } from "@playwright/test";

const RUTA = "/harness-roadmap/planeacion";

async function abrir(page: Page, consulta = ""): Promise<void> {
  await page.goto(`${RUTA}${consulta}`);
  await expect(page.getByRole("form", { name: "Variables de planeación" })).toBeVisible();
}

async function completarVariablesValidas(page: Page): Promise<void> {
  await page.getByLabel(/Plazo en meses/).fill("6");
  await page.getByLabel(/Presupuesto/).fill("15000");
  await page.getByLabel(/Moneda/).fill("USD");
  await page.getByLabel(/^Equipo/).fill("DPO\nIngeniera de seguridad");
  await page.getByLabel(/Delegado de protección de datos/).fill("María Pérez");
}

test.describe("Formulario de planeación (FE-02)", () => {
  test("campos obligatorios vacíos o fuera de rango muestran su mensaje y no generan", async ({ page }) => {
    await abrir(page);
    await page.getByLabel(/Plazo en meses/).fill("2");
    await page.getByRole("button", { name: "Generar hoja de ruta" }).click();

    await expect(page.getByText("El plazo debe estar entre 3 y 12 meses.")).toBeVisible();
    await expect(page.getByText("Indica el presupuesto disponible.")).toBeVisible();
    await expect(page.getByText("Indica al menos un miembro del equipo, uno por línea.")).toBeVisible();
    await expect(page.getByText("Indica quién ejerce como delegado de protección de datos.")).toBeVisible();
    await expect(page.getByTestId("progreso-mensaje")).toHaveCount(0);
    await expect(page.getByTestId("roadmap-id")).toHaveCount(0);

    // Al corregir un campo, su mensaje desaparece sin esperar a otro envío.
    await page.getByLabel(/Presupuesto/).fill("1000");
    await expect(page.getByText("Indica el presupuesto disponible.")).toHaveCount(0);
  });

  test("un presupuesto negativo y una moneda mal escrita se rechazan", async ({ page }) => {
    await abrir(page);
    await completarVariablesValidas(page);
    await page.getByLabel(/Presupuesto/).fill("-5");
    await page.getByLabel(/Moneda/).fill("US");
    await page.getByRole("button", { name: "Generar hoja de ruta" }).click();

    await expect(page.getByText("El presupuesto no puede ser negativo.")).toBeVisible();
    await expect(page.getByText(/código de tres letras, por ejemplo USD/)).toBeVisible();
    await expect(page.getByTestId("roadmap-id")).toHaveCount(0);
  });

  test("la generación muestra un progreso que avisa de la espera y termina con la hoja de ruta", async ({ page }) => {
    await abrir(page, "?latencia=9500");
    await completarVariablesValidas(page);
    await page.getByRole("button", { name: "Generar hoja de ruta" }).click();

    const progreso = page.getByTestId("progreso-mensaje");
    await expect(progreso).toContainText("Preparando el análisis");
    await expect(page.getByRole("button", { name: "Generando…" })).toBeDisabled();
    // Mientras dura, el formulario no admite cambios que desalineen lo que se está generando.
    await expect(page.getByLabel(/Presupuesto/)).toBeDisabled();
    // La espera real es de 20 a 90 s: el mensaje tiene que cambiar, no quedarse mudo.
    await expect(progreso).toContainText("hasta 90 segundos", { timeout: 12_000 });

    await expect(page.getByTestId("roadmap-id")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("roadmap-id")).toHaveText(/^rm-/);
    await expect(progreso).toHaveCount(0);
  });

  test("si la generación falla muestra código y acción, y permite reintentar hasta lograrlo", async ({ page }) => {
    await abrir(page, "?fallo=1");
    await completarVariablesValidas(page);
    await page.getByRole("button", { name: "Generar hoja de ruta" }).click();

    await expect(page.getByTestId("error-mensaje")).toHaveText("El modelo no respondió a tiempo.");
    await expect(page.getByTestId("error-codigo")).toHaveText("GENERATION_FAILED");
    await expect(page.getByTestId("error-accion")).toHaveText("retry_generation");
    await expect(page.getByTestId("roadmap-id")).toHaveCount(0);

    await page.getByRole("button", { name: /Reintentar generación/ }).click();
    await expect(page.getByTestId("roadmap-id")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByTestId("error-mensaje")).toHaveCount(0);
  });

  for (const rol of ["dpo", "coordinador", "responsable_area"]) {
    test(`el rol ${rol} ve el formulario en solo lectura y con la explicación`, async ({ page }) => {
      await abrir(page, `?rol=${rol}`);

      await expect(page.getByRole("note")).toContainText("Solo el rol implementador puede generar");
      await expect(page.getByLabel(/Presupuesto/)).toBeDisabled();
      await expect(page.getByLabel(/^Equipo/)).toBeDisabled();
      await expect(page.getByRole("button", { name: "Generar hoja de ruta" })).toBeDisabled();
    });
  }

  test("ninguna pantalla muestra tokens de gobernanza", async ({ page }) => {
    await abrir(page);
    const texto = await page.locator("body").innerText();
    expect(texto).not.toMatch(/[¤¦]/);
  });
});
