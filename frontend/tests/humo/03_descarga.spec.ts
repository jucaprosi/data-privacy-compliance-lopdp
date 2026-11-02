/**
 * Humo 5, lo más lento: la exportación del RAT (RAT-06) descarga el archivo real. La huella que muestra la
 * pantalla debe ser la de los bytes descargados, no solo una cabecera con buen aspecto.
 */
import { createHash, randomBytes } from "crypto";
import * as fs from "fs";

import { expect, test } from "@playwright/test";

import { configurarProyecto, irASala } from "../utiles";
import { bearer, firmarToken, iniciarSesion, leerEscenario, ROL_HUMO } from "./escenario";

test("Exportar XLSX descarga el archivo y su huella coincide con la mostrada", async ({ page, request }) => {
  const { a } = leerEscenario();
  const creada = await request.post("/api/v1/rat/actividades", {
    headers: { ...bearer(firmarToken(a)), "X-Tenant-ID": a.tenantId, "X-Role": ROL_HUMO },
    data: {
      codigo: `HUMO-${randomBytes(3).toString("hex")}`,
      nombre: "Tratamiento exportable",
      finalidad: "Comprobar la descarga",
      area_responsable: "Calidad",
    },
  });
  expect(creada.ok()).toBe(true);

  await iniciarSesion(page, a);
  await expect(page.getByRole("textbox", { name: /Razón Social/ })).toBeVisible();
  await configurarProyecto(page, a.nombre);
  await irASala(page, /RAT Maestro/);

  const descarga = page.waitForEvent("download");
  await page.getByRole("button", { name: "Exportar XLSX" }).click();
  const archivo = await descarga;
  expect(archivo.suggestedFilename()).toMatch(new RegExp(`^rat-${a.tenantId}-.+\\.xlsx$`));

  const bytes = fs.readFileSync(await archivo.path());
  expect(bytes.subarray(0, 2).toString()).toBe("PK"); // un .xlsx es un zip
  const huella = createHash("sha256").update(bytes).digest("hex");
  await expect(page.getByRole("status").filter({ hasText: "Huella SHA-256" })).toContainText(huella);
});
