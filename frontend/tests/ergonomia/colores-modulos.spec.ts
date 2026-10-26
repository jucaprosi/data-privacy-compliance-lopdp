import { expect, test, type Page } from "@playwright/test";

import { medirContraste } from "../contraste";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const SALAS_LOPDP = [
  /Dashboard Central/,
  /^Hoja de Ruta/,
  /Riesgos & MTGE/,
  /Cockpit DPD \/ DPO/,
  /Historial de Auditoría/,
  /Playbook Incidentes/,
  /Derechos ARCO/,
  /MTGE Relacional/,
  /^Transferencias/,
  /Copiloto Mitigación/,
] as const;

const SALAS_NIIF = [
  /Dashboard Central/,
  /Ingesta de Balance/,
  /Matriz Reclasificación/,
  /Árbol de EEFF/,
  /Conciliación MPM/,
  /Diagnóstico y Plan/,
  /Centro de Exportación/,
  /Visor Doctrinal/,
] as const;

type TemaContraste = "theme-light" | "theme-dark";

async function simularApi(page: Page): Promise<void> {
  await page.route("**/api/v1/**", async (route) => {
    await route.fulfill({ status: 503, json: { detail: "API simulada no disponible para FE-17" } });
  });
}

async function aplicarTema(page: Page, tema: TemaContraste): Promise<void> {
  await page.locator("html").evaluate((html, nombreTema) => {
    html.classList.remove("theme-light", "theme-dark");
    html.classList.add(nombreTema);
  }, tema);
}

async function comprobarContraste(page: Page, sala: RegExp, tema: TemaContraste): Promise<void> {
  await irASala(page, sala);
  await aplicarTema(page, tema);

  const contenido = (await page.locator("main").innerText()).trim();
  expect(contenido.length, `${sala} debe renderizar contenido verificable`).toBeGreaterThan(20);

  const deficientes = await medirContraste(page, "body");
  expect(deficientes, `${sala} en ${tema}: ${JSON.stringify(deficientes, null, 2)}`).toEqual([]);
}

test.describe("contraste AA de los módulos FE-17", () => {
  test.beforeEach(async ({ page }) => {
    await simularApi(page);
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad FE-17");
  });

  test("LOPDP conserva contraste 4.5:1 en ambos temas", async ({ page }) => {
    for (const tema of ["theme-light", "theme-dark"] as const) {
      for (const sala of SALAS_LOPDP) {
        await comprobarContraste(page, sala, tema);
      }
    }
  });

  test("NIIF conserva contraste 4.5:1 en ambos temas", async ({ page }) => {
    await page.locator("#selector-normativa").selectOption("NIIF");
    const confirmacion = page.getByRole("alertdialog");
    if (await confirmacion.count()) {
      await confirmacion.getByRole("button", { name: "Cambiar normativa" }).click();
    }
    await expect(page.locator("#selector-normativa")).toHaveValue("NIIF");

    for (const tema of ["theme-light", "theme-dark"] as const) {
      for (const sala of SALAS_NIIF) {
        await comprobarContraste(page, sala, tema);
      }
    }
  });
});
