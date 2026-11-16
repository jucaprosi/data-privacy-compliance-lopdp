/**
 * Arnés de interfaz de RM-25c: primera validación del coordinador y validación final del DPO.
 *
 * Monta EvidenciaPanel en /harness-roadmap/evidencia. Datos sembrados en task-002: evi-ajena (subida por
 * user-resp-01) y evi-propia (subida por user-enc-01, el usuario por defecto). Casos del arnés: `conprimera`
 * (evi-ajena ya tiene la primera validación de un coordinador), `primera409` y `validada`.
 *
 * Mutaciones ejecutadas (cada una dejó el spec en rojo y se restauró):
 * - EvidenciaPanel: `aria-disabled={!evidencia.primera_validacion_por || bloqueada}` por `aria-disabled={false}`
 *   -> «el DPO no puede usar «Validación final» sin primera validación».
 * - EvidenciaPanel: mostrar «Primera validación» también al DPO (`rol === "coordinador"` por `rol !== "responsable_area"`)
 *   -> «solo el coordinador ve «Primera validación»».
 * - EvidenciaPanel: `mensajeDePrimeraValidacion` devuelve `err.message` -> «un error muestra el mensaje fijo, no el del servidor».
 */
import { expect, test, type Page } from "@playwright/test";

const RUTA = "/harness-roadmap/evidencia";

async function abrir(page: Page, consulta = ""): Promise<void> {
  await page.goto(`${RUTA}${consulta}`);
  await expect(page.getByRole("region", { name: "Evidencia de la tarea" })).toBeVisible();
  await expect(page.getByTestId("evidencia-evi-ajena")).toBeVisible();
}

const evidencia = (page: Page, id: string) => page.getByTestId(`evidencia-${id}`);
const DPO = "&rol=dpo&usuario=user-dpo-01";

test.describe("Doble validación de la evidencia (RM-25c)", () => {
  test("el coordinador ve «Primera validación» y la registra con su rol en el historial", async ({ page }) => {
    await abrir(page, "?rol=coordinador&usuario=user-enc-01");
    const ajena = evidencia(page, "evi-ajena");

    await expect(ajena.getByRole("button", { name: "Primera validación" })).toBeEnabled();
    await ajena.getByRole("button", { name: "Primera validación" }).click();

    const historial = ajena.getByRole("list", { name: "Historial de validación" });
    await expect(historial).toContainText("user-enc-01 · Coordinador · Primera validación");
    await expect(ajena.getByRole("button", { name: "Primera validación" })).toHaveCount(0);
  });

  test("solo el coordinador ve «Primera validación»", async ({ page }) => {
    for (const consulta of [DPO, "&rol=implementador&usuario=user-impl-01", "&rol=responsable_area&usuario=user-resp-01"]) {
      await abrir(page, `?x=1${consulta}`);
      await expect(page.getByTestId("evidencia-evi-ajena").or(page.getByTestId("sin-evidencia"))).toBeVisible();
      await expect(page.getByRole("button", { name: "Primera validación" })).toHaveCount(0);
    }
    // Aserción positiva previa: el coordinador sí lo ve con los mismos datos.
    await abrir(page, "?rol=coordinador&usuario=user-enc-01");
    await expect(page.getByRole("button", { name: "Primera validación" }).first()).toBeVisible();
  });

  test("el coordinador no hace la primera validación de lo que subió él", async ({ page }) => {
    await abrir(page, "?rol=coordinador&usuario=user-enc-01");
    await expect(evidencia(page, "evi-propia").getByRole("button", { name: "Primera validación" })).toBeDisabled();
    await expect(evidencia(page, "evi-ajena").getByRole("button", { name: "Primera validación" })).toBeEnabled();
  });

  test("el DPO no puede usar «Validación final» sin primera validación", async ({ page }) => {
    await abrir(page, `?x=1${DPO}`);
    const ajena = evidencia(page, "evi-ajena");
    const final = ajena.getByRole("button", { name: "Validación final" });

    await expect(final).toBeVisible();
    await expect(final).toHaveAttribute("aria-disabled", "true");
    await expect(ajena).toContainText("Disponible cuando el coordinador haga la primera validación");
    await final.click({ force: true }); // aria-disabled no impide el clic: la pantalla debe ignorarlo
    await expect(ajena.getByRole("button", { name: "Confirmar aprobación" })).toHaveCount(0);
  });

  test("con primera validación, el DPO usa «Validación final» y queda en el historial", async ({ page }) => {
    await abrir(page, `?fallo=conprimera${DPO}`);
    const ajena = evidencia(page, "evi-ajena");
    const final = ajena.getByRole("button", { name: "Validación final" });

    await expect(final).toHaveAttribute("aria-disabled", "false");
    await expect(ajena).not.toContainText("Disponible cuando el coordinador haga la primera validación");
    await expect(ajena.getByRole("list", { name: "Historial de validación" })).toContainText(
      "user-enc-02 · Coordinador · Primera validación · 10/11/2026",
    );
    await final.click();
    await ajena.getByRole("button", { name: "Confirmar aprobación" }).click();
    await expect(page.getByTestId("validacion-evi-ajena")).toContainText("Aprobada");
    await expect(ajena.getByRole("list", { name: "Historial de validación" })).toContainText("user-dpo-01");
    await expect(ajena.getByRole("list", { name: "Historial de validación" })).toContainText("Validación final");
  });

  test("el historial muestra el rol de cada validación", async ({ page }) => {
    await abrir(page, `?fallo=validada${DPO}`);
    const historial = evidencia(page, "evi-ajena").getByRole("list", { name: "Historial de validación" });
    await expect(historial.getByRole("listitem")).toHaveCount(2);
    await expect(historial).toContainText("user-enc-02 · Coordinador · Primera validación · 10/11/2026");
    await expect(historial).toContainText("user-dpo-01 · DPO · Validación final · 11/11/2026");
  });

  test("un error muestra el mensaje fijo, no el del servidor", async ({ page }) => {
    await abrir(page, "?fallo=primera409&rol=coordinador&usuario=user-enc-01");
    const ajena = evidencia(page, "evi-ajena");
    await ajena.getByRole("button", { name: "Primera validación" }).click();

    const aviso = page.getByTestId("error-primera-evi-ajena");
    await expect(aviso).toHaveText("Esta evidencia ya tiene su primera validación. Actualiza la lista para verla.");
    await expect(aviso).not.toContainText("Ya registrada.");
    // La persona puede reintentar y el segundo intento sí se registra.
    await ajena.getByRole("button", { name: "Primera validación" }).click();
    await expect(ajena.getByRole("list", { name: "Historial de validación" })).toContainText("Primera validación");
  });
});
