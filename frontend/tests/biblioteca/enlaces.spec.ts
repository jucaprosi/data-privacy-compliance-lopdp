// ¤adpa ¤rbac-tenant ¤arbitro
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const documento = {
  id: "doc-302", codigo: "BIB-302", nombre: "Política enlazada", origen: "plantilla",
  plantilla_version: "1.0", estado: "borrador", editado: false, proxima_revision: "2027-11-03",
  revision: 3, creado_por: "u", creado_en: "2026-11-03T10:00:00Z", actualizado_en: "2026-11-03T10:00:00Z",
};
const completo = { ...documento, plantilla_id: "p", contenido_markdown: "# Política", variables_faltantes: [],
  aprobado_por: null, aprobado_en: null, sha256: "a".repeat(64), fecha_emision: "2026-11-03" };
const enlace = { id: "e-1", documento_id: documento.id, documento_revision: 3, accion_id: "a-1",
  accion_titulo: "Corregir consentimiento", accion_estado: "pendiente", requisito: "P7", hallazgo_id: "h-1",
  hallazgo_titulo: "Consentimiento incompleto", hallazgo_origen: "diagnostico", hallazgo_origen_ref: "r-1:P7",
  pregunta: "P7", assessment_version: 4, creado_por: "u", creado_en: "2026-11-03T10:00:00Z" };

async function abrir(page: Page) {
  await page.addInitScript(() => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "tenant-a" }; });
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/documentos", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (r) => r.fulfill({ json: { borrador: 1, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1 } }));
  await page.route("**/api/v1/biblioteca/documentos/doc-302", (r) => r.fulfill({ json: completo }));
  await page.route("**/api/v1/biblioteca/documentos/doc-302/enlaces", (r) =>
    r.request().method() === "POST" ? r.fulfill({ status: 201, json: enlace }) : r.fulfill({ json: [enlace] }));
  await abrirAppLimpia(page); await configurarProyecto(page, "Entidad BIB-302");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" }).getByRole("button", { name: /^Documentos y plantillas/ }).click();
  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("button", { name: "Elegir Política enlazada" }).click();
  return vista;
}

test("muestra acción, revisión, requisito, hallazgo, pregunta y versión reales", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const vista = await abrir(page);
  const panel = vista.getByRole("region", { name: "Acciones vinculadas" });
  await expect(panel).toContainText("Corregir consentimiento · pendiente");
  await expect(panel).toContainText("Revisión 3 · requisito P7");
  await expect(panel).toContainText("Hallazgo: Consentimiento incompleto (h-1)");
  await expect(panel).toContainText("Pregunta P7 · assessment versión 4");
  await expect(panel).toContainText("no cambia el estado de la acción");
});
