/**
 * DIAG-07: el administrador ve los controles de respuesta habilitados y guarda; el implementador sin
 * dominio asignado los ve deshabilitados. ¤diagnostico ¤dpo-independencia
 *
 * Mutación documentada: volver a `puedeSellar(roles)` en DiagnosticCanvas deshabilita los controles
 * del administrador y la primera prueba falla; enviar `X-Role: dpo` en `guardarRespuestas` hace fallar
 * la comprobación del rol enviado. API simulada en memoria: solo valores generados.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";
import { simularApiDiagnostico } from "./simulador";

async function abrirDiagnostico(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Normativa/);
}

test.describe("Guardar como administrador (DIAG-07)", () => {
  test("el administrador responde y la respuesta llega al servidor con su rol", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["admin_organizacion"] });
    const rolesEnviados: string[] = [];
    page.on("request", (req) => {
      if (req.method() === "PUT" && req.url().includes("/api/v1/diagnostico/respuestas")) {
        rolesEnviados.push(req.headers()["x-role"] ?? "");
      }
    });
    await abrirDiagnostico(page);

    const nivel = page.locator('[data-nivel="3"]');
    await expect(nivel).toHaveAttribute("aria-disabled", "false");
    await nivel.click();
    await page.locator('[data-evidencia="2"]').click();
    await expect.poll(() => servidor.envios.length).toBeGreaterThan(0);
    expect(rolesEnviados.every((rol) => rol === "admin_organizacion")).toBe(true);
  });

  test("el implementador sin dominio asignado ve los controles deshabilitados", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["implementador"] });
    await abrirDiagnostico(page);
    const nivel = page.locator('[data-nivel="3"]');
    await expect(nivel).toHaveAttribute("aria-disabled", "true");
    await nivel.click({ force: true });
    expect(servidor.envios).toHaveLength(0);
  });
});
