/**
 * RAT-02: la plantilla de salud aparece solo si el servidor la ofrece, se carga con confirmación
 * explícita y envía exactamente las actividades elegidas.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const PLANTILLA = {
  sector: "salud",
  version: "2026-06-01",
  fuente: "MATRIZ_RAT_Consultorio_Medico_SALUDATA (3).xlsx",
  actividades: [
    { codigo: "SALUD-001", nombre: "Admisión y registro de pacientes", finalidad: "Identificar al paciente", actor_sugerido: "recepción" },
    { codigo: "SALUD-003", nombre: "Atención médica e historia clínica", finalidad: "Registrar la atención", actor_sugerido: "médico responsable" },
  ],
};

async function abrirRat(page: Page, plantillas: unknown[]) {
  const envios: unknown[] = [];
  await page.route("**/api/v1/rat/plantillas", (route) => route.fulfill({ json: { plantillas } }));
  await page.route("**/api/v1/rat/plantillas/*/aplicar", async (route) => {
    envios.push(route.request().postDataJSON());
    await route.fulfill({ json: { sector: "salud", creadas: ["SALUD-003"], omitidas: [] } });
  });
  await page.route("**/api/v1/rat/actividades", (route) => route.fulfill({ json: { actividades: [] } }));
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Consultorio de prueba");
  await irASala(page, /RAT Maestro/);
  return envios;
}

test.describe("Plantilla de salud del RAT (RAT-02)", () => {
  test("se elige qué cargar y solo se envían las actividades marcadas", async ({ page }) => {
    const envios = await abrirRat(page, [PLANTILLA]);
    const seccion = page.getByRole("region", { name: "Plantilla de salud" });
    await expect(seccion).toBeVisible();

    await seccion.getByRole("button", { name: "Cargar plantilla de salud" }).click();
    const cargar = seccion.getByRole("button", { name: /Cargar \d+ actividades en el RAT/ });
    await expect(cargar).toBeDisabled();

    await seccion.getByLabel(/Atención médica e historia clínica/).check();
    await cargar.click();

    await expect.poll(() => envios).toEqual([{ codigos: ["SALUD-003"] }]);
    await expect(seccion.getByRole("status")).toContainText("Se cargaron 1 actividades");
  });

  test("sin plantilla para el sector de la organización no se muestra nada", async ({ page }) => {
    await abrirRat(page, []);
    await expect(page.getByRole("region", { name: "Plantilla de salud" })).toHaveCount(0);
  });
});
