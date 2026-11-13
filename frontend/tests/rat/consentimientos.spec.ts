/**
 * RAT-07 (governance/especificaciones/RAT-07.md §4 y §5).
 *
 * Con la API simulada: registrar un consentimiento sube el total y no aparece ningún campo de identidad;
 * a 375 px no hay desplazamiento horizontal; el DPO solo lee.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const FICHA = {
  id: "rat-1",
  codigo: "RAT-001",
  nombre: "Historia clínica",
  area_responsable: "Salud",
  finalidad: "Atención",
  base_legal: "CONSENTIMIENTO",
  categorias_titulares: ["PACIENTES"],
  datos_sensibles: false,
  volumen_titulares_estimado: 100,
  transferencia_internacional: false,
  requiere_eipd: false,
  es_gran_escala: false,
};
const COLECTIVO = {
  id: "col-1",
  tratamiento_id: "rat-1",
  nombre: "Socios",
  base_legitimacion: "CONSENTIMIENTO",
  texto_version: "v1",
};

async function abrirTitulares(page: Page, rol: string) {
  const envios: unknown[] = [];
  const registros: { id: string; colectivo_id: string; fecha: string; canal: string; cantidad: number; texto_version: string | null }[] = [];
  await page.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { user_id: "u-1", tenant_id: "t-1", roles: [{ role: rol }] } }),
  );
  await page.route("**/api/v1/rat/plantillas", (route) => route.fulfill({ json: { plantillas: [] } }));
  await page.route("**/api/v1/rat/actividades", (route) =>
    route.fulfill({ json: { total: 1, actividades: [FICHA] } }),
  );
  await page.route("**/api/v1/rat/rat-1/colectivos", (route) => route.fulfill({ json: { colectivos: [COLECTIVO] } }));
  await page.route("**/api/v1/rat/colectivos/col-1/consentimientos**", async (route) => {
    if (route.request().method() === "POST") {
      const cuerpo = route.request().postDataJSON();
      envios.push(cuerpo);
      registros.push({ id: `r-${registros.length}`, colectivo_id: "col-1", ...cuerpo });
      await route.fulfill({ status: 201, json: registros[registros.length - 1] });
      return;
    }
    await route.fulfill({ json: { registros, total: registros.reduce((s, r) => s + r.cantidad, 0) } });
  });
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Consultorio de prueba");
  await irASala(page, /RAT Maestro/);
  await page.getByRole("button", { name: "Ver titulares de Historia clínica" }).click();
  const panel = page.getByRole("region", { name: "Titulares de Historia clínica" });
  await panel.getByRole("button", { name: "Ver registros de Socios" }).click();
  return { panel, envios };
}

test.describe("Colectivos y consentimientos agregados (RAT-07)", () => {
  test("registrar un consentimiento sube el total y no pide ningún dato de identidad", async ({ page }) => {
    const { panel, envios } = await abrirTitulares(page, "coordinador");
    await expect(panel.getByRole("note")).toHaveText(
      "Aquí solo se registran cantidades por fecha y canal. No se guardan datos de los titulares.",
    );
    await expect(panel.getByText("Aún no hay registros para este colectivo.")).toBeVisible();

    await panel.getByLabel("Fecha", { exact: true }).fill("2026-11-01");
    await panel.getByLabel("Canal").selectOption("presencial");
    await panel.getByLabel("Cantidad").fill("10");
    await panel.getByRole("button", { name: "Registrar" }).click();
    await expect(panel.getByRole("status").filter({ hasText: "Total: 10" })).toBeVisible();
    await panel.getByLabel("Cantidad").fill("5");
    await panel.getByRole("button", { name: "Registrar" }).click();
    await expect(panel.getByRole("status").filter({ hasText: "Total: 15" })).toBeVisible();
    await expect(panel.getByRole("status").filter({ hasText: "Registro guardado. Total actualizado." })).toBeVisible();

    await expect(panel.getByRole("table", { name: "Registros de Socios" }).getByRole("row")).toHaveCount(3);
    expect(envios).toEqual([
      { fecha: "2026-11-01", canal: "presencial", cantidad: 10, texto_version: null },
      { fecha: "2026-11-01", canal: "presencial", cantidad: 5, texto_version: null },
    ]);
    for (const nombre of [/nombre del titular/i, /c[eé]dula/i, /correo/i, /tel[eé]fono del titular/i]) {
      await expect(panel.getByLabel(nombre)).toHaveCount(0);
    }
  });

  test("una cantidad que no es mayor que cero se rechaza con su mensaje", async ({ page }) => {
    const { panel, envios } = await abrirTitulares(page, "implementador");
    await panel.getByLabel("Fecha", { exact: true }).fill("2026-11-01");
    await panel.getByLabel("Cantidad").fill("0");
    await panel.getByRole("button", { name: "Registrar" }).click();
    await expect(panel.getByText("Escribe una cantidad mayor que cero.")).toBeVisible();
    expect(envios).toEqual([]);
  });

  test("el DPO solo lee: sin formularios de escritura", async ({ page }) => {
    const { panel } = await abrirTitulares(page, "dpo");
    await expect(panel.getByRole("button", { name: "Registrar" })).toHaveCount(0);
    await expect(panel.getByRole("button", { name: "Nuevo colectivo" })).toHaveCount(0);
    await expect(panel.getByText("Aún no hay registros para este colectivo.")).toBeVisible();
  });

  test("a 375 px no hay desplazamiento horizontal", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    const { panel } = await abrirTitulares(page, "coordinador");
    await expect(panel).toBeVisible();
    const ancho = await page.evaluate(() => ({ doc: document.documentElement.scrollWidth, vista: window.innerWidth }));
    expect(ancho.doc).toBeLessThanOrEqual(ancho.vista);
  });
});
