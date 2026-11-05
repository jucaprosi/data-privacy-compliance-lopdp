import { test, expect } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const DOC = "doc-bib306";
const documento = {
  id: DOC, codigo: "PRO-01", nombre: "Política", origen: "plantilla", plantilla_version: "1.0",
  estado: "borrador", editado: true, proxima_revision: "2027-11-03", revision: 2,
  creado_por: "actor", creado_en: "2026-11-03T12:00:00Z", actualizado_en: "2026-11-03T12:00:00Z",
  plantilla_id: "plantilla", contenido_markdown: "Contenido", variables_faltantes: [], aprobado_por: null,
  aprobado_en: null, sha256: "a".repeat(64), fecha_emision: "2026-11-03", tarea_hoja_ruta_id: null,
};

test("muestra la cronología completa, el bloqueo legal y restaura como revisión nueva", async ({ page }, testInfo) => {
  test.skip(testInfo.project.name === "produccion", "El gancho de identidad de pruebas solo existe en desarrollo.");
  await page.addInitScript(() => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "org-bib306" };
  });
  await page.route("**/api/v1/biblioteca/documentos?**", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos", (r) => r.fulfill({ json: [documento] }));
  await page.route(`**/api/v1/biblioteca/documentos/${DOC}`, (r) => r.fulfill({ json: documento }));
  await page.route(`**/api/v1/biblioteca/documentos/${DOC}/conservacion`, (r) => r.fulfill({ json: {
    documento_id: DOC, retenido_hasta: null, bloqueo_legal: true, motivo: "Litigio", politica_id: null,
    politica_aprobada: false, actualizado_por: "actor", actualizado_en: "2026-11-03T12:00:00Z",
  }}));
  const tipos = ["cambio", "descarga", "generacion", "aprobacion", "notificacion", "reapertura"];
  await page.route(`**/api/v1/biblioteca/documentos/${DOC}/cronologia`, (r) => r.fulfill({ json: tipos.map((tipo, i) => ({
    id: String(i), tipo, revision: i === 0 ? 1 : 2, actor_id: "actor", detalle: {},
    creado_en: `2026-11-03T12:0${i}:00Z`,
  })) }));
  let restaurada = false;
  await page.route(`**/api/v1/biblioteca/documentos/${DOC}/restauraciones`, async (r) => {
    expect((await r.request().postDataJSON()).revision_origen).toBe(1); restaurada = true;
    await r.fulfill({ json: { ...documento, revision: 3 } });
  });
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (r) => r.fulfill({ json: {
    borrador: 1, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1,
  }}));
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-306");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ }).click();
  await page.getByRole("button", { name: "Elegir Política" }).click();
  const historial = page.getByTestId("historial-documento");
  await expect(historial).toBeVisible();
  for (const tipo of tipos) await expect(historial.getByTestId(`evento-${tipo}`)).toBeVisible();
  await expect(historial.getByTestId("bloqueo-legal")).toContainText("no se permite eliminar");
  await expect(historial.getByTestId("politica-pendiente")).toContainText("no se ejecutará borrado");
  await historial.getByRole("button", { name: "Restaurar como nueva revisión" }).click();
  await expect.poll(() => restaurada).toBe(true);
});
