import { expect, test, type Page } from "@playwright/test";

import {
  BANCO_PREGUNTAS,
  PERFIL_VACIO,
  normalizarTamano,
  podarBancoPorTamano,
  type PerfilOperacion,
} from "../../src/lib/bancoPreguntas";

const CLAVES = ["jubys-audit-storage", "jubys-proyectos-v1"];

async function simularApi(page: Page): Promise<void> {
  await page.route("**/api/**", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ success: true }),
    });
  });
}

async function abrirSinEstado(page: Page): Promise<void> {
  await simularApi(page);
  await page.goto("/");
  await page.evaluate((claves) => claves.forEach((clave) => localStorage.removeItem(clave)), CLAVES);
  await page.reload();
  await expect(page.getByRole("textbox", { name: /Razón Social/ })).toHaveValue(/.+/);
}

async function responderPerfil(page: Page, respuesta: "Sí" | "No"): Promise<void> {
  const grupos = page.getByRole("radiogroup");
  expect(await grupos.count()).toBe(Object.keys(PERFIL_VACIO).length);
  for (let indice = 0; indice < (await grupos.count()); indice += 1) {
    await grupos.nth(indice).getByRole("radio", { name: respuesta, exact: true }).check();
  }
}

test.describe("Ergonomía del dashboard y antecedencia de la ficha", () => {
  test("arrastrar el separador cambia materialmente el ancho del panel", async ({ page }) => {
    await abrirSinEstado(page);

    const panel = page.locator("#panel-dock-izquierdo");
    const separador = page.getByTitle("Arrastra para redimensionar el panel").first();
    const antes = await panel.boundingBox();
    const asa = await separador.boundingBox();
    expect(antes).not.toBeNull();
    expect(asa).not.toBeNull();

    await page.mouse.move(asa!.x + asa!.width / 2, asa!.y + asa!.height / 2);
    await page.mouse.down();
    await page.mouse.move(asa!.x + 120, asa!.y + asa!.height / 2, { steps: 8 });
    await page.mouse.up();

    await expect
      .poll(async () => (await panel.boundingBox())?.width ?? 0)
      .toBeGreaterThan(antes!.width + 50);
  });

  test("la ficha precede al diagnóstico, poda sus preguntas y se rehidrata", async ({ page }) => {
    await abrirSinEstado(page);

    await expect(page.getByText(/Progreso: Pregunta/)).toHaveCount(0);
    await expect(page.getByRole("button", { name: /Normativa/ })).toHaveCount(0);

    const razonSocial = "Ergonomía QA-07 S.A.";
    const campoRazonSocial = page.getByRole("textbox", { name: /Razón Social/ });
    await campoRazonSocial.fill(razonSocial);
    await responderPerfil(page, "No");
    await page.getByRole("button", { name: /Guardar Ficha y Continuar/ }).click();
    await expect(page.getByText(/Ficha organizacional guardada/)).toBeVisible();

    await page.locator("#selector-normativa").selectOption("LOPDP");
    await page.getByRole("button", { name: "Cerrar alerta" }).click();

    const perfilNo = Object.fromEntries(
      Object.keys(PERFIL_VACIO).map((clave) => [clave, "no"])
    ) as PerfilOperacion;
    const totalEsperado = podarBancoPorTamano(
      BANCO_PREGUNTAS,
      normalizarTamano("Organización mediana (50-199)"),
      perfilNo
    ).length;
    await expect(page.getByText(new RegExp(`Progreso: Pregunta\\s+1\\s+de\\s+${totalEsperado}`))).toBeVisible();

    await page.reload();
    await expect(page.getByText(new RegExp(`Progreso: Pregunta\\s+1\\s+de\\s+${totalEsperado}`))).toBeVisible();
    await expect(page.getByText(razonSocial, { exact: true }).first()).toBeVisible();
  });
});
