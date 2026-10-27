import { expect, test } from "@playwright/test";
import fs from "node:fs";
import path from "node:path";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const DATOS_INVENTADOS = /RAT-RRHH-001|DPO-DICT-01|Respuesta asistida:/;

test.describe("fallos de API visibles y sin datos inventados", () => {
  test("RAT muestra HTTP 500 y conserva el inventario vacío", async ({ page }) => {
    await page.route("**/api/v1/rat/actividades", (route) =>
      route.fulfill({ status: 500, body: "fallo RAT" })
    );
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /RAT Maestro/);

    await expect(page.getByRole("alert").filter({ hasText: /No se pudo cargar el RAT: HTTP 500/ })).toBeVisible();
    await expect(page.getByText("No hay actividades registradas en el RAT.")).toBeVisible();
    await expect(page.getByText(DATOS_INVENTADOS)).toHaveCount(0);
  });

  test("bitácora DPO muestra HTTP 500 y conserva el historial vacío", async ({ page }) => {
    await page.route("**/api/v1/dpo/bitacora", (route) =>
      route.fulfill({ status: 500, body: "fallo DPO" })
    );
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Cockpit DPD \/ DPO/i);

    await expect(page.getByRole("alert").filter({ hasText: /No se pudo cargar la bitácora: HTTP 500/ })).toBeVisible();
    await expect(page.getByText("No hay dictámenes asentados en la bitácora.")).toBeVisible();
    await expect(page.getByText(DATOS_INVENTADOS)).toHaveCount(0);
  });

  test("el módulo CAPA pendiente de montaje mantiene el contrato de error vacío", async () => {
    const raiz = path.resolve(process.cwd(), "src/components/modules");
    const contratos = [
      ["CapaModule.tsx", "setTickets([])", "role=\"alert\""],
    ] as const;

    for (const [archivo, estadoVacio, alerta] of contratos) {
      const fuente = fs.readFileSync(path.join(raiz, archivo), "utf8");
      expect(fuente, `${archivo} debe vaciar sus datos o avisar del fallo`).toContain(estadoVacio);
      expect(fuente, `${archivo} debe exponer el fallo a tecnología asistiva`).toContain(alerta);
      expect(fuente, `${archivo} no debe conservar respuestas de ejemplo`).not.toMatch(DATOS_INVENTADOS);
    }
  });
});
