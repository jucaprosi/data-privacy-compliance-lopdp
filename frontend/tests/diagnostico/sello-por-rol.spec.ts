/**
 * DIAG-07 · §5: el botón de sellar depende de quién sella, de punta a punta en el lienzo del diagnóstico.
 * ¤diagnostico ¤dpo-independencia
 *
 * 1. El dpo ve «Sellar diagnóstico…» en el cierre, sella, y ningún control de respuesta está activo.
 * 2. El admin_organizacion responde (la respuesta llega al servidor) y no ve «Sellar diagnóstico…».
 * 3. Cada rol ve un solo aviso (role="note") con el texto de su caso y nunca «Modo lectura»; el auditor
 *    no ve ningún botón de responder ni de sellar; a 375 px la franja no desborda.
 *
 * Mutación documentada: atar el botón de `SelloPorEtapa` a quien responde (`puedeResponder`) hace
 * fallar la 1 (el dpo no lo ve) y la 2 (el administrador sí). API simulada en memoria: solo valores
 * generados.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala, responderControlActual } from "../utiles";
import { abrirCierreDelDiagnostico, filaDePrueba, simularApiDiagnostico } from "./simulador";

const AVISOS: Record<string, string> = {
  admin_organizacion:
    "Respondes las preguntas del diagnóstico. Cuando estén completas, el DPO las revisa y sella el diagnóstico.",
  dpo: "Revisas las respuestas y sellas el diagnóstico. Las respuestas las completa la organización; si algo no cuadra, puedes objetarlo.",
  auditor: "Puedes consultar el diagnóstico. Lo responde la organización y lo sella el DPO.",
};

async function abrirDiagnostico(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Normativa/);
}

test.describe("Sellar según quién sella (DIAG-07)", () => {
  test("el DPO ve «Sellar diagnóstico…», sella y no edita respuestas", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["dpo"], filas: [filaDePrueba(1)] });
    await abrirDiagnostico(page);
    const niveles = page.locator("[data-nivel]");
    await expect(niveles).toHaveCount(5);
    for (const nivel of await niveles.all()) await expect(nivel).toHaveAttribute("aria-disabled", "true");
    await niveles.nth(2).click({ force: true });
    expect(servidor.envios).toEqual([]);

    const cierre = await abrirCierreDelDiagnostico(context, page);
    await cierre.getByRole("button", { name: /^Sellar diagnóstico/ }).click();
    await expect.poll(() => servidor.cuerposSellado.length).toBe(1);
  });

  test("el administrador responde y no ve «Sellar diagnóstico…»", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["admin_organizacion"] });
    await abrirDiagnostico(page);
    await responderControlActual(page, 3);
    await expect.poll(() => servidor.filas.length).toBe(1);

    const cierre = await abrirCierreDelDiagnostico(context, page);
    await expect(cierre.getByTestId("etapa-diagnostico")).toBeVisible();
    await expect(cierre.getByRole("button", { name: /Sellar diagnóstico/ })).toHaveCount(0);
    expect(servidor.cuerposSellado).toEqual([]);
  });

  for (const [rol, texto] of Object.entries(AVISOS)) {
    test(`con ${rol} el aviso del lienzo es el de su caso`, async ({ page, context }) => {
      await simularApiDiagnostico(context, { roles: [rol], filas: [filaDePrueba(1)] });
      await abrirDiagnostico(page);
      const aviso = page.getByTestId("aviso-modo-diagnostico");
      await expect(aviso).toHaveAttribute("role", "note");
      await expect(aviso).toHaveText(texto);
      await expect(page.getByText(/Modo lectura/)).toHaveCount(0);
      if (rol === "auditor") {
        for (const nivel of await page.locator("[data-nivel]").all()) {
          await expect(nivel).toHaveAttribute("aria-disabled", "true");
        }
        const cierre = await abrirCierreDelDiagnostico(context, page);
        await expect(cierre.getByRole("button", { name: /Sellar diagnóstico/ })).toHaveCount(0);
      }
    });
  }

  test("a 375 px la franja del aviso no desborda", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"], filas: [filaDePrueba(1)] });
    await abrirDiagnostico(page);
    await page.setViewportSize({ width: 375, height: 812 });
    const aviso = page.getByTestId("aviso-modo-diagnostico");
    await expect(aviso).toBeVisible();
    const caja = await aviso.boundingBox();
    expect(caja !== null && caja.x >= 0 && caja.x + caja.width <= 375).toBe(true);
  });
});
