/**
 * Arnés de interfaz de la paleta de comandos.
 *
 * La aplicación es una sola vista con salas conmutables, no un enrutado por
 * URL: la paleta es la vía de navegación rápida y tiene que abrir y cerrar sin
 * dejar la sala anterior a medias.
 */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto } from "./utiles";

test.describe("Paleta de comandos", () => {
  test.beforeEach(async ({ page }) => {
    await abrirAppLimpia(page);
    await configurarProyecto(page);
  });

  /** Buscador de la paleta; su presencia equivale a que la paleta esté abierta. */
  const buscador = (page: import("@playwright/test").Page) =>
    page.getByPlaceholder(/Escribe un comando/i);

  test("se abre con el atajo y se cierra con Escape", async ({ page }) => {
    // Una segunda instancia montada en la página conmutaba el estado dos veces
    // por pulsación y dejaba la paleta cerrada: el atajo tiene que abrirla.
    await page.keyboard.press("Control+K");
    await expect(buscador(page)).toBeVisible();

    await page.keyboard.press("Escape");
    await expect(buscador(page)).toBeHidden();
  });

  test("filtra por texto y navega a la sala elegida", async ({ page }) => {
    await page.keyboard.press("Control+K");
    await buscador(page).fill("Diagnóstico");

    await page.getByRole("option", { name: /Diagnóstico/ }).first().click();

    await expect(buscador(page)).toBeHidden();
    await expect(
      page.getByRole("group", { name: "Evaluación de conformidad del control" })
    ).toBeVisible();
  });
});
