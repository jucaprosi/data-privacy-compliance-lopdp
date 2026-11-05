// ¤adpa ¤arbitro
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const DOC = "doc-bib202";
const documento = {
  id: DOC, codigo: "PRO-01", nombre: "Política", origen: "plantilla", plantilla_version: "1.0",
  estado: "aprobado", editado: false, proxima_revision: "2027-11-03", revision: 1,
  creado_por: "actor", creado_en: "2026-11-03T12:00:00Z", actualizado_en: "2026-11-03T12:00:00Z",
  plantilla_id: "plantilla", contenido_markdown: "RUC 1790012345001", variables_faltantes: [], aprobado_por: "actor",
  aprobado_en: "2026-11-03T12:00:00Z", sha256: "a".repeat(64), fecha_emision: "2026-11-03", tarea_hoja_ruta_id: null,
};
const campo = (valor: string) => ({
  clave: "organizacion.ruc", valor, fuente: "organizacion", fuente_id: "org-bib202", revision: null,
  fecha: "2026-11-03T12:00:00+00:00", validador: null, estado: "sin_validar",
  limitacion: "La fuente no guarda historial ni versión.", huella: "b".repeat(64),
});
const rat = {
  clave: "rat.A-01.finalidad", valor: "Nómina", fuente: "rat", fuente_id: "act-1", revision: "3",
  fecha: "2026-11-03T12:00:00+00:00", validador: "dpd-1", estado: "validado", limitacion: null, huella: "c".repeat(64),
};

async function abrir(page: Page, cambios: (r: import("@playwright/test").Route) => Promise<void>) {
  await page.addInitScript(() => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "org-bib202" }; });
  await page.route("**/api/v1/biblioteca/documentos?**", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos", (r) => r.fulfill({ json: [documento] }));
  await page.route(`**/api/v1/biblioteca/documentos/${DOC}`, (r) => r.fulfill({ json: documento }));
  await page.route(`**/api/v1/biblioteca/documentos/${DOC}/**`, (r) => r.fulfill({ status: 404, json: {} }));
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (r) => r.fulfill({ json: {
    borrador: 0, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1,
  }}));
  await page.route(`**/api/v1/biblioteca/fuentes/documentos/${DOC}/cambios`, cambios);
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-202");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ }).click();
  await page.getByRole("button", { name: "Elegir Política" }).click();
  return page.getByTestId("procedencia-documento");
}

test("muestra el origen de cada dato y avisa el cambio de fuente conservando lo emitido", async ({ page }) => {
  let propuesta: unknown = null;
  await page.route(`**/api/v1/biblioteca/fuentes/documentos/${DOC}/propuestas`, async (r) => {
    propuesta = r.request().postDataJSON();
    await r.fulfill({ status: 201, json: { documento_id: DOC, estado: "propuesto", valor_canonico: "0999999999001",
      fuente: "organizacion", fuente_id: "org-bib202", ...(propuesta as object) } });
  });
  const panel = await abrir(page, (r) => r.fulfill({ json: {
    documento_id: DOC, cambiado: true,
    cambios: [{ clave: "organizacion.ruc", emitido: "1790012345001", actual: "0999999999001" }],
    emitida: { documento_id: DOC, revision_documento: 1, campos: [campo("1790012345001"), rat], sha256: "d".repeat(64), tomada_en: null },
    actual: { documento_id: DOC, revision_documento: null, campos: [campo("0999999999001"), rat], sha256: "e".repeat(64), tomada_en: null },
  }}));
  await expect(panel.getByTestId("aviso-cambio-fuente")).toContainText("«1790012345001» → «0999999999001»");
  const filas = panel.getByTestId("campo-procedencia");
  await expect(filas).toHaveCount(2);
  await expect(filas.nth(0)).toContainText("1790012345001");
  await expect(filas.nth(0)).toContainText("sin versión");
  await expect(filas.nth(0)).toContainText("Sin validar");
  await expect(filas.nth(1)).toContainText("Validado por dpd-1");
  await panel.getByLabel("Dato").selectOption("organizacion.ruc");
  await panel.getByLabel("Valor propuesto").fill("1790012345002");
  await panel.getByLabel("Motivo").fill("Dígito mal copiado");
  await panel.getByRole("button", { name: "Proponer corrección" }).click();
  await expect(panel.getByRole("status").first()).toContainText("El dato de origen no cambió");
  expect(propuesta).toEqual({ clave: "organizacion.ruc", valor_propuesto: "1790012345002", motivo: "Dígito mal copiado" });
});

test("sin instantánea ofrece guardarla y una carga fallida no muestra alerta", async ({ page }) => {
  let emitida = false;
  await page.route(`**/api/v1/biblioteca/fuentes/documentos/${DOC}/instantanea`, async (r) => {
    emitida = true; await r.fulfill({ status: 201, json: {} });
  });
  const panel = await abrir(page, (r) => r.fulfill({ status: 404, json: {
    code: "BIB_PROCEDENCIA_SIN_INSTANTANEA", detail: "Sin instantánea" } }));
  await expect(panel).toContainText("aún no guarda de dónde salen sus datos");
  await expect(panel.getByRole("alert")).toHaveCount(0);
  await panel.getByRole("button", { name: "Guardar procedencia" }).click();
  await expect.poll(() => emitida).toBe(true);
});
