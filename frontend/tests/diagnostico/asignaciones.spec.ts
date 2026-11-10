/**
 * DIAG-04: el administrador asigna los dominios del assessment a encargados del diagnóstico. ¤diagnostico-asignacion
 *
 * 1. Como administrador, elegir un encargado para D07 y volver a abrir la pantalla muestra su nombre; el
 *    servidor recibió solo el encargado (la identidad y la organización salen del token).
 * 2. Como implementador solo se lee: sin selectores, con el nombre genérico del encargado y el historial.
 *
 * Mutación documentada: quitar el selector del administrador hace fallar la prueba 1.
 * API simulada en memoria: solo valores generados.
 */
import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";
import { simularApiDiagnostico } from "./simulador";

const DIMENSIONES = Array.from({ length: 10 }, (_, i) => `D${String(i + 1).padStart(2, "0")}`);
const PERSONAS = [
  { id: "persona-uno", email: "uno@example.invalid", nombre: "Persona Uno", activo: true, roles: [{ role: "implementador" }] },
  { id: "persona-dpo", email: "dpo@example.invalid", nombre: "Persona DPO", activo: true, roles: [{ role: "dpo" }] },
];

async function simularAsignaciones(context: BrowserContext, roles: string[]) {
  await simularApiDiagnostico(context, { roles });
  const servidor = { vigente: new Map<string, string | null>(), puts: [] as { dimension: string; cuerpo: unknown }[] };
  await context.route("**/api/v1/organizacion/usuarios", (route) => route.fulfill({ json: PERSONAS }));
  await context.route("**/api/v1/diagnostico/asignaciones/*", async (route) => {
    const dimension = route.request().url().split("/").pop()!;
    const cuerpo = route.request().postDataJSON() as { responsable_user_id: string | null };
    servidor.puts.push({ dimension, cuerpo });
    servidor.vigente.set(dimension, cuerpo.responsable_user_id);
    await route.fulfill({ json: { dimension, nombre_dimension: dimension, responsable_user_id: cuerpo.responsable_user_id, asignado_en: "2026-11-09T10:00:00Z" } });
  });
  await context.route("**/api/v1/diagnostico/asignaciones/historial**", (route) =>
    route.fulfill({
      json: {
        historial: [...servidor.vigente].map(([dimension, responsable_user_id]) => ({
          dimension, responsable_user_id, asignado_por: "admin", asignado_en: "2026-11-09T10:00:00Z",
        })),
      },
    })
  );
  await context.route(/\/api\/v1\/diagnostico\/asignaciones$/, (route) =>
    route.fulfill({
      json: {
        asignaciones: DIMENSIONES.map((dimension) => ({
          dimension,
          nombre_dimension: `Dominio ${dimension}`,
          responsable_user_id: servidor.vigente.get(dimension) ?? null,
          asignado_en: null,
        })),
      },
    })
  );
  return servidor;
}

async function abrir(page: Page, submenu: string) {
  await barraDeMenus(page).getByRole("button", { name: "Diagnóstico", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Diagnóstico" }).getByRole("button", { name: new RegExp(`^${submenu}`) }).click();
}

test.describe("Asignación de dominios (DIAG-04)", () => {
  test("el administrador elige un encargado para D07 y el nombre sigue tras volver a abrir la pantalla", async ({ page, context }) => {
    const servidor = await simularAsignaciones(context, ["admin_organizacion"]);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await abrir(page, "Asignación");

    const selector = page.getByLabel("Encargado de D07");
    await expect(selector).toBeVisible();
    // El DPO no figura entre las personas elegibles.
    await expect(selector.locator("option", { hasText: "Persona DPO" })).toHaveCount(0);
    await selector.selectOption({ label: "Persona Uno" });
    await expect.poll(() => servidor.puts.length).toBe(1);
    expect(servidor.puts[0]).toEqual({ dimension: "D07", cuerpo: { responsable_user_id: "persona-uno" } });

    await abrir(page, "Reporte");
    await abrir(page, "Asignación");
    await expect(page.getByLabel("Encargado de D07")).toHaveValue("persona-uno");
    await expect(page.getByLabel("Encargado de D07").locator("option:checked")).toHaveText("Persona Uno");
  });

  test("un implementador consulta sin poder asignar y ve el historial", async ({ page, context }) => {
    const servidor = await simularAsignaciones(context, ["implementador"]);
    servidor.vigente.set("D03", "persona-uno");
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await abrir(page, "Asignación");

    await expect(page.getByTestId("asignacion-D03")).toBeVisible();
    await expect(page.getByTestId("asignacion-D03").getByText("Persona asignada")).toBeVisible();
    await expect(page.getByRole("combobox")).toHaveCount(0);
    await page.getByRole("button", { name: "Ver historial de asignaciones" }).click();
    await expect(page.getByTestId("historial-asignaciones").getByText(/D03 · asignado/)).toBeVisible();
  });
});
