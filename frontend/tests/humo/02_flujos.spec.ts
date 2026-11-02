/**
 * Humo 1, 2 y 4 con navegador: entrar, escribir una ficha del RAT que sobreviva a recargar y leer un módulo
 * con datos del servidor. El aislamiento de lo escrito se comprueba con la otra organización.
 */
import { randomBytes } from "crypto";

import { expect, test, type Page } from "@playwright/test";

import { configurarProyecto, irASala } from "../utiles";
import { bearer, firmarToken, iniciarSesion, leerEscenario, ROL_HUMO } from "./escenario";

async function entrar(page: Page) {
  const { a } = leerEscenario();
  await iniciarSesion(page, a);
  await expect(page.getByRole("textbox", { name: /Razón Social/ })).toBeVisible();
  await configurarProyecto(page, a.nombre);
}

test.describe.configure({ mode: "serial" });

test.describe("Flujos críticos en el navegador", () => {
  test("una ficha del RAT creada en el formulario sigue ahí al recargar y no cruza de organización", async ({
    page,
    request,
  }) => {
    const { a, b } = leerEscenario();
    const codigo = `HUMO-${randomBytes(3).toString("hex")}`;
    await entrar(page);
    await irASala(page, /RAT Maestro/);

    await page.getByRole("button", { name: /Nueva Actividad/ }).click();
    const formulario = page.locator("form").filter({ hasText: "Guardar en RAT" });
    const campos = formulario.getByRole("textbox");
    await campos.nth(0).fill(codigo);
    await campos.nth(1).fill("Tratamiento de humo");
    await campos.nth(2).fill("Calidad");
    await campos.nth(3).fill("Comprobar el recorrido completo");
    await formulario.getByRole("button", { name: "Guardar en RAT" }).click();
    await expect(page.getByRole("cell", { name: codigo })).toBeVisible();

    await page.reload();
    await irASala(page, /RAT Maestro/);
    await expect(page.getByRole("cell", { name: codigo })).toBeVisible();

    const deA = await request.get("/api/v1/rat/actividades", {
      headers: { ...bearer(firmarToken(a)), "X-Tenant-ID": a.tenantId, "X-Role": ROL_HUMO },
    });
    expect((await deA.json()).actividades.map((x: { codigo: string }) => x.codigo)).toContain(codigo);

    const deB = await request.get("/api/v1/rat/actividades", {
      headers: { ...bearer(firmarToken(b)), "X-Tenant-ID": b.tenantId, "X-Role": ROL_HUMO },
    });
    expect(deB.status()).toBe(200);
    expect((await deB.json()).actividades).toEqual([]);
  });

  test("la Hoja de Ruta muestra el rol real que devuelve el servidor", async ({ page }) => {
    await entrar(page);
    await irASala(page, /^Hoja de Ruta/i);
    await expect(page.getByText(/Rol:/i)).toContainText(ROL_HUMO);
  });
});
