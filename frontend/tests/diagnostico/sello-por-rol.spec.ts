/**
 * DIAG-07 · §5: el botón de sellar depende de quién sella, de punta a punta en el lienzo del diagnóstico.
 * ¤diagnostico ¤dpo-independencia
 *
 * 1. El dpo ve «Sellar diagnóstico…» en el cierre, sella, y ningún control de respuesta está activo.
 * 2. El admin_organizacion responde (la respuesta llega al servidor) y no ve «Sellar diagnóstico…».
 * 3. Cada rol ve un solo aviso (role="note") con el texto de su caso y nunca «Modo lectura»; el auditor
 *    ni «rol vigente»; el auditor no ve ningún botón de responder ni de sellar; el enlace del DPO lleva a
 *    Revisión del diagnóstico; a 375 px la franja no desborda.
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
    "Respondes las preguntas de tus dominios. Después, el DPO revisa las respuestas y sella el diagnóstico.",
  dpo:
    "Revisas y sellas el diagnósticoResponden el administrador y las personas asignadas a cada dominio. Revisa sus respuestas en Revisión del diagnóstico y sella cuando no queden objeciones abiertas.",
  auditor:
    "Solo consultaResponde cada pregunta la persona asignada a su dominio, y el DPO revisa y sella. Puedes consultar las respuestas y los resultados, pero no cambiarlos.",
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
      await expect(page.getByRole("note")).toHaveCount(1);
      await expect(page.getByText(/Modo lectura|rol vigente/)).toHaveCount(0);
      if (rol === "auditor") {
        for (const nivel of await page.locator("[data-nivel]").all()) {
          await expect(nivel).toHaveAttribute("aria-disabled", "true");
        }
        const cierre = await abrirCierreDelDiagnostico(context, page);
        await expect(cierre.getByRole("button", { name: /Sellar diagnóstico/ })).toHaveCount(0);
      }
    });
  }

  test("el enlace del aviso del DPO abre Revisión del diagnóstico", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"], filas: [filaDePrueba(1)] });
    await abrirDiagnostico(page);
    await page.getByRole("button", { name: "Ir a Revisión del diagnóstico" }).click();
    await expect(page.getByTestId("aviso-modo-diagnostico")).toHaveCount(0);
    await expect(page.getByText("Revisión del diagnóstico").first()).toBeVisible();
  });

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
