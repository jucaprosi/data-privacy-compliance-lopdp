/**
 * DIAG-14, reescrita por DIAG-07: quién puede guardar respuestas. ¤frontend-ide ¤rbac-tenant
 *
 * 1. Un implementador sin dominio asignado ve los botones de nivel y de evidencia con aria-disabled,
 *    un solo aviso («Solo consulta») y ninguna nota por pregunta; un clic no cambia el estado derivado.
 * 2. El DPO tampoco responde (revisa y sella): no ve el selector de nivel (R6) y la evidencia declarada
 *    está deshabilitada.
 * 3. El administrador responde: los controles funcionan.
 *
 * Mutación documentada: quitar aria-disabled de los botones hace fallar la prueba 1; volver a
 * `puedeSellar(roles)` en DiagnosticCanvas hace fallar la 2 y la 3.
 * API simulada en memoria: solo valores generados.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";
import { simularApiDiagnostico } from "./simulador";

async function abrirDiagnostico(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Normativa/);
}

async function comprobarDeshabilitado(page: Page) {
  const niveles = page.locator("[data-nivel]");
  const evidencias = page.locator("[data-evidencia]");
  await expect(niveles).toHaveCount(5);
  await expect(evidencias).toHaveCount(5);
  for (const grupo of [niveles, evidencias]) {
    for (let i = 0; i < 5; i++) {
      await expect(grupo.nth(i)).toHaveAttribute("aria-disabled", "true");
      await expect(grupo.nth(i)).toHaveCSS("border-top-style", "dashed");
    }
  }
  // Nunca dos notas a la vez: la franja del lienzo basta (UX/UI, DIAG-07).
  await expect(page.getByTestId("nota-solo-dpo-nivel")).toHaveCount(0);
  await expect(page.getByTestId("nota-solo-dpo-evidencia")).toHaveCount(0);
  await expect(page.getByRole("note")).toHaveCount(1);
  await expect(page.getByText("Ver como DPO")).toHaveCount(0);

  const estado = page.getByTestId("estado-derivado");
  const antes = await estado.textContent();
  await niveles.nth(2).click({ force: true });
  await evidencias.nth(3).click({ force: true });
  await expect(estado).toHaveText(antes ?? "");
  await expect(niveles.nth(2)).toHaveAttribute("aria-checked", "false");
}

test.describe("Quién guarda respuestas (DIAG-14 y DIAG-07)", () => {
  test("un implementador sin dominio asignado ve los controles deshabilitados y un solo aviso", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["implementador"] });
    await abrirDiagnostico(page);
    await comprobarDeshabilitado(page);
    await page.screenshot({ path: "test-results/diag07-implementador.png", fullPage: true });
  });

  test("el DPO no responde: no ve el selector de nivel y la evidencia declarada está deshabilitada", async ({ page, context }) => {
    // DIAG-07 R6 (§4): el DPO no ve el selector de nivel declarado; quien responde lo elige.
    const servidor = await simularApiDiagnostico(context, { roles: ["dpo"] });
    await abrirDiagnostico(page);
    await expect(page.getByTestId("aviso-modo-diagnostico")).toHaveAttribute("data-caso", "sella");
    await expect(page.locator("[data-nivel]")).toHaveCount(0);
    await expect(page.getByRole("radiogroup", { name: /Nivel de madurez/ })).toHaveCount(0);
    const evidencias = page.locator("[data-evidencia]");
    await expect(evidencias).toHaveCount(5);
    for (const evidencia of await evidencias.all()) await expect(evidencia).toHaveAttribute("aria-disabled", "true");
    await evidencias.nth(3).click({ force: true });
    await expect(page.getByTestId("nota-solo-dpo-nivel")).toHaveCount(0);
    expect(servidor.envios).toEqual([]);
  });

  test("el administrador responde: los controles funcionan y la nota no aparece", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["admin_organizacion"] });
    await abrirDiagnostico(page);

    const nivel = page.locator('[data-nivel="1"]');
    await expect(nivel).toHaveAttribute("aria-disabled", "false");
    await expect(nivel).toHaveCSS("border-top-style", "solid");
    await nivel.click();
    await expect(nivel).toHaveAttribute("aria-checked", "true");
    const evidencia = page.locator('[data-evidencia="2"]');
    await evidencia.click();
    await expect(evidencia).toHaveAttribute("aria-checked", "true");
  });
});
