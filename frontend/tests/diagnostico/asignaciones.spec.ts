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
  const recibeNombre = !roles.includes("responsable_area");
  await simularApiDiagnostico(context, { roles });
  const servidor = { vigente: new Map<string, string | null>(), puts: [] as { dimension: string; cuerpo: unknown }[], rechazar: false };
  await context.route("**/api/v1/organizacion/usuarios", (route) => route.fulfill({ json: PERSONAS }));
  await context.route("**/api/v1/diagnostico/asignaciones/*", async (route) => {
    const dimension = route.request().url().split("/").pop()!;
    const cuerpo = route.request().postDataJSON() as { responsable_user_id: string | null };
    servidor.puts.push({ dimension, cuerpo });
    if (servidor.rechazar) {
      await route.fulfill({ status: 422, json: { detail: "texto del servidor", code: "ENCARGADO_ES_DPO" } });
      return;
    }
    servidor.vigente.set(dimension, cuerpo.responsable_user_id);
    await route.fulfill({ json: { dimension, nombre_dimension: dimension, responsable_user_id: cuerpo.responsable_user_id, asignado_en: "2026-11-09T10:00:00Z" } });
  });
  await context.route("**/api/v1/diagnostico/asignaciones/historial**", (route) =>
    route.fulfill({
      json: {
        historial: [...servidor.vigente].map(([dimension, responsable_user_id]) => ({
          dimension, responsable_user_id, responsable_nombre: PERSONAS.find((p) => p.id === responsable_user_id)?.nombre ?? null, asignado_por: "admin", asignado_en: "2026-11-09T10:00:00Z",
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
          ...(recibeNombre
            ? { responsable_nombre: PERSONAS.find((p) => p.id === servidor.vigente.get(dimension))?.nombre ?? null }
            : {}),
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
    await expect(page.getByTestId("asignacion-D03").getByText("Persona Uno")).toBeVisible();
    await expect(page.getByRole("combobox")).toHaveCount(0);
    await page.getByRole("button", { name: "Ver historial de asignaciones" }).click();
    await expect(page.getByTestId("historial-asignaciones").getByText(/D03 · asignado a Persona Uno/)).toBeVisible();
    const texto = await page.getByTestId("asignacion-dominios").innerText();
    expect(texto).not.toMatch(/DIAG-|ENCARGADO_|persona-uno/);
  });

  test("un responsable de área ve «Asignado» y no el nombre", async ({ page, context }) => {
    const servidor = await simularAsignaciones(context, ["responsable_area"]);
    servidor.vigente.set("D03", "persona-uno");
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await abrir(page, "Asignación");

    await expect(page.getByTestId("asignacion-D03").getByText("Asignado", { exact: true })).toBeVisible();
    await expect(page.getByTestId("asignacion-dominios").getByText("Persona Uno")).toHaveCount(0);
    await expect(page.getByRole("combobox")).toHaveCount(0);
    await expect(page.getByTestId("asignacion-D01").getByText("Sin asignar")).toBeVisible();
    await expect(page.getByTestId("asignacion-D03").getByLabel("Encargado de D03: asignado")).toBeVisible();
    await expect(page.getByText("Solo quien administra")).toHaveCount(0);
  });

  test("un rechazo del servidor muestra su texto y el selector vuelve al valor anterior", async ({ page, context }) => {
    const servidor = await simularAsignaciones(context, ["admin_organizacion"]);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await abrir(page, "Asignación");

    await page.getByLabel("Encargado de D02").selectOption({ label: "Persona Uno" });
    await expect(page.getByTestId("asignacion-dominios").getByRole("status")).toHaveText("Asignación guardada.");
    servidor.rechazar = true;
    await page.getByLabel("Encargado de D02").selectOption({ value: "" });
    await expect(page.getByTestId("asignacion-dominios").getByRole("alert")).toHaveText("El DPO revisa y sella el diagnóstico, pero no lo responde. Elige a otra persona.");
    await expect(page.getByLabel("Encargado de D02")).toHaveValue("persona-uno");
    expect(await page.getByTestId("asignacion-dominios").innerText()).not.toMatch(/DIAG-|ENCARGADO_|persona-uno/);
  });
});
