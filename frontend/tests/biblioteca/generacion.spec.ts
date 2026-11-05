// ¤adpa ¤rbac-tenant ¤arbitro
// ¤¤qa-engineer
/**
 * BIB-205 · Generar Word y Excel desde el documento elegido (ranura `documento:acciones`).
 * API simulada: el contenido, la instantánea, el checksum, la RLS y la inmutabilidad los prueba
 * `tests/test_bib_205_generacion.py` contra la base propia.
 *  - «Generar para revisión» con datos pendientes se informa como no generado y no añade archivo.
 *  - «Generar borrador» lista el archivo con su marca Borrador y los datos que faltan.
 *  - Ningún fallo se anuncia con `role="alert"`.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const DOC = "doc-205";
const documento = {
  id: DOC, codigo: "BIB-001", nombre: "Política de datos", origen: "plantilla", plantilla_version: "0.2.0",
  estado: "borrador", editado: false, proxima_revision: "2027-11-04", revision: 1, creado_por: "u",
  creado_en: "2026-11-04T10:00:00Z", actualizado_en: "2026-11-04T10:00:00Z",
};
const completo = { ...documento, plantilla_id: "p", contenido_markdown: "# Política", variables_faltantes: ["contexto.finalidad"],
  aprobado_por: null, aprobado_en: null, sha256: "a".repeat(64), fecha_emision: "2026-11-04" };
const generada = {
  id: "gen-1", borrador_id: DOC, modo: "borrador", formato: "xlsx", estado: "borrador",
  plantilla_sha256: "b".repeat(64), instantanea_sha256: "c".repeat(64), archivo_sha256: "d".repeat(64),
  nombre_archivo: "BIB-001-v0.2.0-borrador.xlsx", bytes: 4096, faltantes: ["contexto.finalidad"],
  creado_en: "2026-11-04T10:05:00Z",
};

async function abrir(page: Page, pedidos: unknown[]) {
  await page.addInitScript(() => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "tenant-a" }; });
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/documentos", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos?**", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (r) =>
    r.fulfill({ json: { borrador: 1, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1 } }));
  await page.route(`**/api/v1/biblioteca/documentos/${DOC}`, (r) => r.fulfill({ json: completo }));
  await page.route(`**/api/v1/biblioteca/generaciones/borradores/${DOC}`, async (r) => {
    if (r.request().method() === "GET") return r.fulfill({ json: [] });
    const cuerpo = r.request().postDataJSON() as { modo: string; formato: string };
    pedidos.push(cuerpo);
    if (cuerpo.modo === "revision") {
      return r.fulfill({ status: 422, json: { detail: "Faltan: contexto.finalidad", code: "BIB_GEN_INCOMPLETA" } });
    }
    return r.fulfill({ status: 201, json: { ...generada, formato: cuerpo.formato } });
  });
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-205");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ }).click();
  await page.getByRole("button", { name: "Elegir Política de datos" }).click();
  return page.getByRole("region", { name: "Generar Word y Excel" });
}

test("para revisión con faltantes no genera; el borrador sí, marcado y con su listado", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const pedidos: unknown[] = [];
  const panel = await abrir(page, pedidos);
  await expect(panel).toContainText("Generarlo no aprueba el documento");
  await panel.getByLabel("Formato").selectOption("xlsx");

  await panel.getByRole("button", { name: "Generar para revisión" }).click();
  await expect(panel.getByRole("status")).toContainText("No se generó el archivo: Faltan: contexto.finalidad");
  await expect(panel.getByRole("list", { name: "Archivos generados" })).toHaveCount(0);

  await panel.getByRole("button", { name: "Generar borrador" }).click();
  await expect(panel.getByRole("status")).toContainText("Borrador generado con 1 datos por completar");
  const archivo = panel.getByRole("list", { name: "Archivos generados" }).getByRole("listitem");
  await expect(archivo).toContainText("BIB-001-v0.2.0-borrador.xlsx");
  await expect(archivo).toContainText("Borrador");
  await expect(archivo).toContainText("Faltan: contexto.finalidad");
  expect(pedidos).toEqual([{ modo: "revision", formato: "xlsx" }, { modo: "borrador", formato: "xlsx" }]);
  await expect(panel.getByRole("alert")).toHaveCount(0);
});
