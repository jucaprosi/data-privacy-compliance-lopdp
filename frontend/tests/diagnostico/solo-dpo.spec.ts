/**
 * DIAG-14: solo el DPO asigna el nivel. ¤frontend-ide ¤rbac-tenant
 *
 * 1. Con un rol que no es DPO, los botones de nivel y de evidencia llevan aria-disabled, junto a cada
 *    grupo aparece la nota que nombra el rol y un clic no cambia el estado derivado.
 * 2. Con el DPO los controles funcionan y la nota no aparece.
 * 3. En la demo, el enlace de la nota pide la persona DPO.
 *
 * Mutación documentada: quitar aria-disabled de los botones hace fallar la prueba 1.
 * API simulada en memoria: solo valores generados.
 */
import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";
import { simularApiDiagnostico } from "./simulador";

const NOTA = "Solo el DPO puede asignar el nivel. Estás viendo como";

async function abrirDiagnostico(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Normativa/);
}

async function simularDemo(context: BrowserContext) {
  const personas = [
    { usuario_id: "persona-implementador", nombre: "Persona Uno", rol: "implementador", rol_etiqueta: "Implementador" },
    { usuario_id: "persona-dpo", nombre: "Persona Dos", rol: "dpo", rol_etiqueta: "DPO" },
  ];
  const pedidas: string[] = [];
  await context.route("**/api/v1/entorno", (route) => route.fulfill({ json: { entorno: "demo" } }));
  await context.route("**/api/v1/demo/estado", (route) =>
    route.fulfill({
      json: {
        demo: true,
        organizacion: { tenant_id: "tenant-demo-generado", nombre: "Organización Demo" },
        persona_activa: personas[0],
        personas,
        vence_en: null,
      },
    })
  );
  await context.route("**/api/v1/demo/persona", async (route) => {
    const { persona_usuario_id } = route.request().postDataJSON() as { persona_usuario_id: string };
    pedidas.push(persona_usuario_id);
    await route.fulfill({ json: { persona_activa: personas.find((p) => p.usuario_id === persona_usuario_id) } });
  });
  return pedidas;
}

test.describe("Solo el DPO asigna el nivel (DIAG-14)", () => {
  test("con un rol que no es DPO los controles se ven deshabilitados y explican por qué", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["implementador"] });
    await abrirDiagnostico(page);

    const niveles = page.locator("[data-nivel]");
    const evidencias = page.locator("[data-evidencia]");
    await expect(niveles).toHaveCount(5);
    await expect(evidencias).toHaveCount(5);
    for (const grupo of [niveles, evidencias]) {
      for (let i = 0; i < 5; i++) await expect(grupo.nth(i)).toHaveAttribute("aria-disabled", "true");
    }

    for (const id of ["nota-solo-dpo-nivel", "nota-solo-dpo-evidencia"]) {
      await expect(page.getByTestId(id)).toContainText(`${NOTA} Implementador.`);
    }
    await expect(page.getByText("Elige el nivel que describe")).toHaveCount(0);

    const estado = page.getByTestId("estado-derivado");
    const antes = await estado.textContent();
    await niveles.nth(2).click({ force: true });
    await evidencias.nth(3).click({ force: true });
    await expect(estado).toHaveText(antes ?? "");
    await expect(niveles.nth(2)).toHaveAttribute("aria-checked", "false");
    await expect(evidencias.nth(3)).toHaveAttribute("aria-checked", "false");
    await page.screenshot({ path: "test-results/diag14-no-dpo.png", fullPage: true });
  });

  test("con el DPO los controles funcionan y la nota no aparece", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await abrirDiagnostico(page);

    const nivel = page.locator('[data-nivel="1"]');
    await expect(nivel).toHaveAttribute("aria-disabled", "false");
    await nivel.click();
    await expect(nivel).toHaveAttribute("aria-checked", "true");
    await expect(page.getByTestId("estado-derivado")).not.toHaveText("");
    const evidencia = page.locator('[data-evidencia="2"]');
    await evidencia.click();
    await expect(evidencia).toHaveAttribute("aria-checked", "true");
    await expect(page.getByText(NOTA)).toHaveCount(0);
    await page.screenshot({ path: "test-results/diag14-dpo.png", fullPage: true });
  });

  test("en la demo, el enlace de la nota lleva a la persona DPO", async ({ page, context }) => {
    const pedidas = await simularDemo(context);
    await simularApiDiagnostico(context, { roles: ["implementador"] });
    await abrirDiagnostico(page);

    const enlace = page.getByTestId("nota-solo-dpo-nivel-ver-dpo");
    await expect(enlace).toHaveText("Ver como DPO");
    await enlace.click();
    await expect.poll(() => pedidas).toEqual(["persona-dpo"]);
  });
});
