// ¤adpa ¤rbac-tenant ¤arbitro
// ¤¤qa-engineer
/**
 * BIB-206 · Vista previa antes de emitir (ranura `documento:acciones`).
 * API simulada: la misma instantánea, la fidelidad con el DOCX, la RLS y la invalidez tras editar contra
 * la base los prueba `tests/test_bib_206_preview.py`.
 *  - La vista previa muestra estado, revisión, archivo y contenido (acentos, texto largo, tabla de varias filas).
 *  - Si el documento cambió, emitir se rechaza, la vista previa se descarta y se pide volver a previsualizar.
 *  - Ningún fallo se anuncia con `role="alert"`.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const DOC = "doc-206";
const LARGO = "Tratamiento de niñas, niños y adolescentes — Ñandú, acción. ".repeat(30).trim();
const documento = {
  id: DOC, codigo: "BIB-001", nombre: "Política de datos", origen: "plantilla", plantilla_version: "0.2.0",
  estado: "borrador", editado: false, proxima_revision: "2027-11-04", revision: 1, creado_por: "u",
  creado_en: "2026-11-04T10:00:00Z", actualizado_en: "2026-11-04T10:00:00Z",
};
const completo = { ...documento, plantilla_id: "p", contenido_markdown: "# Política", variables_faltantes: [],
  aprobado_por: null, aprobado_en: null, sha256: "a".repeat(64), fecha_emision: "2026-11-04" };

function vista(revision: number, finalidad: string) {
  return {
    borrador_id: DOC, revision, modo: "revision", formato: "docx", estado: "para_revision",
    plantilla_sha256: "b".repeat(64), instantanea_sha256: String(revision).repeat(64), archivo_sha256: "d".repeat(64),
    nombre_archivo: "BIB-001-v0.2.0-para_revision.docx", faltantes: [],
    bloques: [
      { tipo: "titulo", texto: "Política de Cámara Ñandú", nivel: 1, filas: [] },
      { tipo: "parrafo", texto: `Zonas: ${finalidad}`, nivel: 0, filas: [] },
      { tipo: "tabla", texto: "", nivel: 0, filas: [["Dato", "Fecha"], ["1790012345001", "2026-11-04"], ["", "2026-11-05"]] },
    ],
  };
}

async function abrir(page: Page, emitidos: unknown[]) {
  let revision = 1;
  await page.addInitScript(() => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "tenant-a" }; });
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/documentos", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos?**", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (r) =>
    r.fulfill({ json: { borrador: 1, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1 } }));
  await page.route(`**/api/v1/biblioteca/documentos/${DOC}`, (r) => r.fulfill({ json: completo }));
  await page.route(`**/api/v1/biblioteca/generaciones/borradores/${DOC}`, (r) => r.fulfill({ json: [] }));
  await page.route(`**/api/v1/biblioteca/preview/borradores/${DOC}`, (r) =>
    r.fulfill({ json: vista(revision, revision === 1 ? LARGO : "Bodega") }));
  await page.route(`**/api/v1/biblioteca/preview/borradores/${DOC}/emitir`, (r) => {
    const cuerpo = r.request().postDataJSON() as { revision: number };
    emitidos.push(cuerpo);
    if (cuerpo.revision !== revision) {
      return r.fulfill({ status: 409, json: { code: "BIB_PREVIEW_OBSOLETA",
        detail: "La vista previa quedó obsoleta: el documento cambió. Vuelva a previsualizar." } });
    }
    return r.fulfill({ status: 201, json: { id: "g", borrador_id: DOC, modo: "revision", formato: "docx",
      estado: "para_revision", plantilla_sha256: "b".repeat(64), instantanea_sha256: "2".repeat(64),
      archivo_sha256: "d".repeat(64), nombre_archivo: "BIB-001-v0.2.0-para_revision.docx", bytes: 9,
      faltantes: [], creado_en: "2026-11-04T10:05:00Z" } });
  });
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-206");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ }).click();
  await page.getByRole("button", { name: "Elegir Política de datos" }).click();
  return { panel: page.getByRole("region", { name: "Vista previa" }), editar: () => { revision = 2; } };
}

test("muestra estado y revisión; tras editar, la vista previa anterior no se emite", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const emitidos: { revision: number }[] = [];
  const { panel, editar } = await abrir(page, emitidos);
  await panel.getByRole("button", { name: "Previsualizar" }).click();

  const datos = panel.getByRole("definition");
  await expect(panel.getByLabel("Datos de la vista previa")).toContainText("Estado: Para revisión");
  await expect(panel.getByLabel("Datos de la vista previa")).toContainText("Revisión: 1");
  await expect(datos.filter({ hasText: "BIB-001-v0.2.0-para_revision.docx" })).toHaveCount(1);
  const contenido = panel.getByRole("article", { name: "Contenido de la vista previa" });
  await expect(contenido).toContainText("Política de Cámara Ñandú");
  await expect(contenido).toContainText(LARGO);
  await expect(contenido.getByRole("row")).toHaveCount(3);
  await expect(contenido).not.toContainText("{{");

  editar();
  await panel.getByRole("button", { name: "Emitir este archivo" }).click();
  await expect(panel.getByRole("status")).toContainText("La vista previa quedó obsoleta");
  await expect(contenido).toHaveCount(0);

  await panel.getByRole("button", { name: "Previsualizar" }).click();
  await expect(panel.getByLabel("Datos de la vista previa")).toContainText("Revisión: 2");
  await expect(contenido).toContainText("Zonas: Bodega");
  await panel.getByRole("button", { name: "Emitir este archivo" }).click();
  await expect(panel.getByRole("status")).toContainText("Archivo emitido: BIB-001-v0.2.0-para_revision.docx");
  expect(emitidos.map((e) => e.revision)).toEqual([1, 2]);
  await expect(panel.getByRole("alert")).toHaveCount(0);
});
