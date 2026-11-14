/**
 * DIAG-07: Diagnóstico › Revisión del DPO. ¤diagnostico ¤dpo-independencia
 *
 * 1. Con una objeción abierta en la 12, «Sellar el diagnóstico» se anuncia deshabilitado y explica por
 *    qué; la fila 12 muestra «Objetada» con el motivo a la vista (sin hover).
 * 2. El DPO objeta con el diálogo: el contador, el error con menos de 20 caracteres y el aviso final.
 * 3. Cuando quien respondió vuelve a guardar la 12, sale del recuento y se puede sellar.
 * 4. A 375 px no hay desplazamiento horizontal de la página; sin marcas de gobernanza en la interfaz.
 *
 * Mutación documentada: quitar `aria-disabled` del botón de sellar (o no contar las objeciones abiertas)
 * hace fallar la prueba 1. API simulada en memoria: solo valores generados.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, abrirSubmenu, configurarProyecto } from "../utiles";
import { filaDePrueba, simularApiDiagnostico } from "./simulador";

const MOTIVO = "La evidencia declarada no respalda el nivel indicado.";
const REVISION = { menu: "dpo", nombre: "Revisión del diagnóstico" } as const;

async function abrirRevision(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await abrirSubmenu(page, REVISION as never);
  await expect(page.getByRole("heading", { name: "Revisión del diagnóstico" })).toBeVisible();
}

test.describe("Revisión del diagnóstico (DIAG-07)", () => {
  test("con una objeción abierta, sellar está deshabilitado y la fila muestra el motivo", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["dpo"], filas: [filaDePrueba(12), filaDePrueba(13)] });
    servidor.objeciones.push({
      id: "objecion-previa",
      pregunta_id: 12,
      motivo: MOTIVO,
      objetado_por: "usuario-prueba",
      objetado_en: "2026-10-28T10:30:00+00:00",
      resuelta_en: null,
    });
    await abrirRevision(page);

    const fila = page.getByTestId("fila-revision-12");
    await expect(fila.getByText("Objetada")).toBeVisible();
    await expect(fila.getByText(`Motivo: ${MOTIVO}`)).toBeVisible();

    const sellar = page.getByTestId("sellar-desde-revision");
    await expect(sellar).toHaveAttribute("aria-disabled", "true");
    await expect(sellar).toHaveAccessibleDescription(
      "Hay 1 objeción abierta. Se resuelve cuando quien respondió vuelve a guardar la respuesta."
    );
    await sellar.click({ force: true }); // aria-disabled: el clic no sella
    expect(servidor.cuerposSellado).toHaveLength(0);

    // Quien respondió vuelve a guardar la 12: sale del recuento y se puede sellar.
    servidor.objeciones[0].resuelta_en = "2026-10-28T11:00:00+00:00";
    // Se sale y se vuelve a la revisión (el menú DPO sigue abierto): la grilla recarga del servidor.
    const dock = page.getByRole("group", { name: "Submenús de DPO" });
    await dock.getByRole("button", { name: /^Panel del DPO/ }).click();
    await dock.getByRole("button", { name: /^Revisión del diagnóstico/ }).click();
    await expect(page.getByRole("heading", { name: "Revisión del diagnóstico" })).toBeVisible();
    await expect(page.getByTestId("bloqueo-sello")).toHaveCount(0);
    await expect(page.getByTestId("sellar-desde-revision")).toHaveAttribute("aria-disabled", "false");
    await page.getByTestId("sellar-desde-revision").click();
    await expect.poll(() => servidor.cuerposSellado.length).toBe(1);
  });

  test("el DPO objeta con el diálogo y la fila queda objetada", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"], filas: [filaDePrueba(12)] });
    await abrirRevision(page);

    await page.getByRole("button", { name: "Objetar la pregunta P12" }).click();
    const dialogo = page.getByRole("dialog", { name: "Objetar la respuesta de P12" });
    await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
    const motivo = dialogo.getByLabel("Motivo de la objeción");
    await motivo.fill("corto");
    await expect(dialogo.getByText("5 de 20 caracteres como mínimo")).toBeVisible();
    await dialogo.getByRole("button", { name: "Objetar la respuesta" }).click();
    await expect(dialogo.getByText("Explica el motivo con al menos 20 caracteres.")).toBeVisible();

    await motivo.fill(MOTIVO);
    await dialogo.getByRole("button", { name: "Objetar la respuesta" }).click();
    await expect(dialogo).toHaveCount(0);
    await expect(page.getByRole("status").filter({ hasText: "Objeción registrada." })).toBeVisible();
    await expect(page.getByTestId("fila-revision-12").getByText("Objetada")).toBeVisible();
    await expect(page.getByTestId("sellar-desde-revision")).toHaveAttribute("aria-disabled", "true");
  });

  test("a 375 px no hay desplazamiento horizontal y no hay marcas de gobernanza", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"], filas: [filaDePrueba(12)] });
    await abrirRevision(page);
    await page.setViewportSize({ width: 375, height: 812 });
    await expect(page.getByTestId("grilla-revision")).toBeVisible();
    const desborda = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(desborda).toBe(false);
    const texto = await page.locator("body").innerText();
    expect(texto).not.toMatch(/[¤¦]/);
  });
});
