/**
 * CON-01: conservación de datos. La API se simula. Se comprueban el semáforo con tres fechas, que registrar
 * exige marcar la casilla, que un segundo registro usa el texto fijo del código 409, que el DPO no ve botones,
 * que ningún texto dice que la plataforma suprime, elimina o bloquea datos, y que a 375 px no hay desplazamiento.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, abrirSubmenu, barraDeMenus, configurarProyecto, submenuPorNombre } from "../utiles";
import { credencialSimulada, fijarAjustes, ruta, sembrarSesion } from "../auth/utilesAuth";

const ISO = (dias: number) => new Date(Date.now() + dias * 86_400_000).toISOString().slice(0, 10);

function politica(id: string, dias: number, extra: Record<string, unknown> = {}) {
  return {
    id, actividad_rat_id: "rat-1", plazo_meses: 24, accion_vencimiento: "BLOQUEO",
    fecha_proxima_revision: ISO(dias), estado: "ACTIVA", acta_ejecucion_hash: null, ...extra,
  };
}

async function simularApi(page: Page, { roles, ejecucion }: { roles: string[]; ejecucion?: { status: number; code: string } }) {
  await page.route("**/api/v1/**", async (route) => {
    const destino = ruta(route.request().url());
    const json = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });
    if (destino === "/organizacion/me/roles") {
      return json(200, { user_id: "u", tenant_id: "t-prueba", roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })) });
    }
    if (destino === "/rat/actividades") {
      return json(200, { actividades: [{ id: "rat-1", codigo: "RAT-001", nombre: "Nómina" }] });
    }
    if (destino === "/conservacion/politicas" && route.request().method() === "GET") {
      return json(200, [politica("p-vigente", 90), politica("p-por-vencer", 10), politica("p-vencida", -2)]);
    }
    if (/^\/conservacion\/politicas\/[^/]+\/ejecutar$/.test(destino)) {
      if (ejecucion) return json(ejecucion.status, { detail: "texto del servidor", code: ejecucion.code, action_required: null });
      return json(200, politica("p-vencida", -2, { estado: "BLOQUEADA", acta_ejecucion_hash: "ab12cd34" + "0".repeat(56) }));
    }
    return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
  });
}

async function abrir(page: Page, roles: string[], ejecucion?: { status: number; code: string }) {
  await fijarAjustes(page);
  await sembrarSesion(page, credencialSimulada());
  await simularApi(page, { roles, ejecucion });
  await abrirAppLimpia(page);
  if (!(await barraDeMenus(page).getByRole("button", { name: "Inventario", exact: true }).isVisible())) {
    await configurarProyecto(page, "Entidad CON-01");
  }
  await abrirSubmenu(page, submenuPorNombre(/Conservación de datos/)!);
}

test.describe("Conservación de datos (CON-01)", () => {
  test("el semáforo distingue vigente, por vencer y vencida", async ({ page }) => {
    await abrir(page, ["admin_organizacion"]);
    const tabla = page.getByRole("table", { name: "Políticas de conservación" });
    await expect(tabla).toContainText("Vigente");
    await expect(tabla).toContainText("Por vencer");
    await expect(tabla).toContainText("Vencida");
  });

  test("registrar exige la casilla y un segundo registro usa el texto fijo", async ({ page }) => {
    await abrir(page, ["implementador"], { status: 409, code: "CONSERVACION_YA_EJECUTADA" });
    await page.getByRole("button", { name: "Registrar bloqueo de Nómina" }).first().click();
    const dialogo = page.getByRole("dialog", { name: "¿Registrar el bloqueo de los datos de Nómina?" });
    const registrar = dialogo.getByRole("button", { name: "Registrar el bloqueo" });
    await expect(registrar).toBeDisabled();
    await dialogo.getByRole("checkbox", { name: /ya se hizo o se hará/ }).check();
    await expect(registrar).toBeEnabled();
    await registrar.click();
    await expect(page.getByRole("alert").filter({ hasText: "ya tiene la ejecución registrada" })).toHaveText(
      "Esta política ya tiene la ejecución registrada. Actualizamos su estado."
    );
    await expect(page.locator("body")).not.toContainText("texto del servidor");
  });

  test("el DPO ve el listado sin botones y ningún texto promete que la plataforma suprime datos", async ({ page }) => {
    await abrir(page, ["dpo"]);
    await expect(page.getByRole("table", { name: "Políticas de conservación" })).toBeVisible();
    await expect(page.getByRole("button", { name: /Registrar/ })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Nueva política" })).toHaveCount(0);
    await expect(page.getByText("Registran la ejecución la persona administradora o el implementador.")).toBeVisible();
    const texto = await page.getByRole("main", { name: "Conservación de datos" }).innerText();
    expect(texto).not.toMatch(/se suprimen|se eliminan|se bloquean|art\.? ?20/i);
  });

  test("a 375 px no hay desplazamiento horizontal", async ({ page }) => {
    await abrir(page, ["admin_organizacion"]);
    await page.setViewportSize({ width: 375, height: 812 });
    await expect(page.getByRole("main", { name: "Conservación de datos" })).toBeVisible();
    const desborda = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
    expect(desborda).toBe(false);
  });
});
