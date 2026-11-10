/**
 * FE-27 · Armazón responsive del tablero (governance/tareas/FE-27.md).
 *
 * Mutaciones: M1, quitar el breakpoint md del copiloto (que a 900 px siga en el layout) hace fallar
 * la prueba 3; M2, quitar la devolución del foco al cerrar el cajón (CajonLateral) también.
 */
import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";
import { simularApiDiagnostico } from "../diagnostico/simulador";

const MENU = { name: "Menú", exact: true } as const;
const COPILOTO = { name: "Copiloto", exact: true } as const;

async function prepararApp(page: Page, context: BrowserContext, ancho: number): Promise<void> {
  await simularApiDiagnostico(context, { roles: ["dpo"] });
  await page.setViewportSize({ width: 1280, height: 800 });
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad de Prueba S.A.");
  await page.setViewportSize({ width: ancho, height: 800 });
  // Al cambiar de armazón el lienzo se vuelve a montar y la alerta de la primera pregunta reaparece.
  const alerta = page.getByRole("button", { name: "Cerrar alerta" });
  if (ancho !== 1280) {
    await alerta.waitFor({ state: "visible", timeout: 5000 }).catch(() => undefined);
    if (await alerta.isVisible()) await alerta.click();
  }
}

const armazon = (page: Page) => page.getByTestId("armazon-responsive");

test.describe("Armazón responsive (FE-27)", () => {
  test("1. a 1280 px hay tres paneles y ningún botón Menú ni Copiloto", async ({ page, context }) => {
    await prepararApp(page, context, 1280);
    for (const id of ["panel-dock-izquierdo", "panel-lienzo-central", "panel-copiloto-derecho"]) {
      await expect(page.locator(`[id="${id}"]`)).toBeVisible();
    }
    await expect(page.getByRole("button", MENU)).toHaveCount(0);
    await expect(page.getByRole("button", COPILOTO)).toHaveCount(0);
  });

  test("2. a 1280 px el grupo de paneles sigue y guarda sus tamaños", async ({ page, context }) => {
    await prepararApp(page, context, 1280);
    await expect(page.locator('[id="dashboard-paneles-v1"]')).toBeVisible();
    const separadores = page.getByRole("separator");
    await expect(separadores).toHaveCount(2);
    const caja = (await separadores.first().boundingBox())!;
    await page.mouse.move(caja.x + caja.width / 2, caja.y + caja.height / 2);
    await page.mouse.down();
    await page.mouse.move(caja.x + 60, caja.y + caja.height / 2, { steps: 5 });
    await page.mouse.up();
    const guardado = await page.evaluate(() =>
      Object.keys(window.localStorage).filter((k) => k.includes("dashboard-paneles-v1")),
    );
    expect(guardado.length).toBeGreaterThan(0);
  });

  test("3. a 900 px el copiloto va en un cajón que atrapa el foco y lo devuelve", async ({ page, context }) => {
    await prepararApp(page, context, 900);
    await expect(page.locator('[id="panel-copiloto-derecho"]')).toHaveCount(0);
    await expect(page.locator('[id="panel-dock-izquierdo"]')).toHaveCount(0);
    await expect(page.getByTestId("panel-menu-md")).toBeVisible();
    await expect(page.getByRole("separator")).toHaveCount(0);
    await expect(page.getByRole("button", MENU)).toHaveCount(0);

    const boton = page.getByRole("button", COPILOTO);
    await boton.focus();
    await boton.click();
    const cajon = page.getByRole("dialog", { name: "Copiloto" });
    await expect(cajon).toBeVisible();
    expect((await cajon.boundingBox())!.width).toBeLessThanOrEqual(400);
    await expect(page.getByRole("button", { name: "Cerrar copiloto" })).toBeVisible();

    for (let i = 0; i < 25; i += 1) {
      await page.keyboard.press("Tab");
      expect(await cajon.evaluate((el) => el.contains(document.activeElement))).toBe(true);
    }

    await page.keyboard.press("Escape");
    await expect(cajon).toHaveCount(0);
    await expect(boton).toBeFocused();
  });

  test("4. a 375 px el centro ocupa el ancho y solo la barra de menús se desplaza", async ({ page, context }) => {
    await prepararApp(page, context, 375);
    const medidas = await armazon(page).evaluate((el) => ({ s: el.scrollWidth, c: el.clientWidth }));
    expect(medidas.s).toBeLessThanOrEqual(medidas.c);
    const centro = (await page.getByRole("main").boundingBox())!;
    expect(centro.width).toBeGreaterThan(375 - 24);
    const barra = await barraDeMenus(page).evaluate((el) => ({ s: el.scrollWidth, c: el.clientWidth }));
    expect(barra.s).toBeGreaterThan(barra.c);
    await expect(page.getByRole("separator")).toHaveCount(0);
  });

  test("5. a 375 px Menú abre el cajón; elegir un submenú cambia la vista y lo cierra", async ({ page, context }) => {
    await prepararApp(page, context, 375);
    await page.getByRole("button", MENU).click();
    const cajon = page.getByRole("dialog", { name: "Menú de navegación" });
    await expect(cajon).toBeVisible();
    await expect(cajon.getByText("Organización:", { exact: true })).toBeVisible();
    await cajon.getByRole("button", { name: /^Reporte/ }).click();
    await expect(cajon).toHaveCount(0);
    await expect(page.getByRole("main").getByText("Reporte", { exact: true })).toBeVisible();
  });

  test("6. a 375 px, en el diagnóstico, los cinco niveles se ven sin solaparse", async ({ page, context }) => {
    await prepararApp(page, context, 375);
    const niveles = page.getByRole("radiogroup", { name: /Nivel de madurez/ });
    const radios = niveles.getByRole("radio");
    await expect(radios).toHaveCount(5);
    const cajas = [];
    for (let i = 0; i < 5; i += 1) {
      await expect(radios.nth(i)).toBeVisible();
      cajas.push((await radios.nth(i).boundingBox())!);
    }
    for (let i = 0; i < cajas.length; i += 1) {
      for (let j = i + 1; j < cajas.length; j += 1) {
        const a = cajas[i];
        const b = cajas[j];
        const solapa = a.x < b.x + b.width && b.x < a.x + a.width && a.y < b.y + b.height && b.y < a.y + a.height;
        expect(solapa, `niveles ${i + 1} y ${j + 1}`).toBe(false);
      }
    }
  });

  test("8. a 1280 px la pestaña muestra el submenú activo y el pie no enseña el tenant", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await page.setViewportSize({ width: 1280, height: 800 });
    await abrirAppLimpia(page);
    const centro = page.getByRole("main");
    // Sin ficha guardada la vista es la de configuración.
    await expect(centro.getByText("Perfil de la organización", { exact: true })).toBeVisible();
    await expect(centro).not.toContainText(/adpa\.view|\.view|Zustand|useAuditStore/);

    await configurarProyecto(page, "Entidad de Prueba S.A.");
    await expect(centro).not.toContainText(/adpa\.view|\.view|Zustand|useAuditStore/);
    await expect(page.getByText("Organización:", { exact: true })).toHaveCount(1);
    await expect(page.getByText("Entidad de Prueba S.A.").first()).toBeVisible();
    await expect(page.getByText("Tenant ID:", { exact: false })).toHaveCount(0);
    expect(await page.locator("aside").first().innerText()).not.toMatch(/tenant-/i);
  });
});
