// ¤adpa ¤rbac-tenant ¤arbitro
// ¤¤qa-engineer
/**
 * BIB-203 · Tablas de captura en el detalle del documento (ranura `documento:editor`).
 * API simulada: la regla real (IDs, catálogos, tenant, atomicidad) la prueba `tests/test_bib_203_tablas.py`.
 *  - Pegar filas valida primero por fila; con errores no se puede confirmar.
 *  - Una confirmación rechazada se anuncia como «No se guardó ninguna fila», nunca como guardada.
 *  - PLA es de solo lectura y muestra el estado calculado («Sin fecha válida» nunca es «En plazo»).
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const documento = {
  id: "doc-203", codigo: "BIB-006", nombre: "Registro de actividades", origen: "plantilla",
  plantilla_version: "1.0", estado: "borrador", editado: false, proxima_revision: "2027-11-03",
  revision: 1, creado_por: "u", creado_en: "2026-11-03T10:00:00Z", actualizado_en: "2026-11-03T10:00:00Z",
};
const completo = { ...documento, plantilla_id: "p", contenido_markdown: "# RAT", variables_faltantes: [],
  aprobado_por: null, aprobado_en: null, sha256: "a".repeat(64), fecha_emision: "2026-11-03" };
const esquemas = {
  INV: [{ clave: "nombre", etiqueta: "Activo o base de datos", tipo: "texto", obligatoria: true, catalogo: [] },
    { clave: "categoria", etiqueta: "Categoría de datos", tipo: "catalogo", obligatoria: true, catalogo: ["CONTACTO"] }],
  RAT: [], LEG: [],
};
const existente = { id: "f-1", borrador_id: "doc-203", tabla: "INV", codigo: "INV-1",
  datos: { nombre: "Clientes", categoria: "CONTACTO" }, tratamiento_id: null, revision: 1,
  actualizado_en: "2026-11-03T10:00:00Z" };

async function abrir(page: Page, confirmar: { status: number; json: unknown }) {
  await page.addInitScript(() => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "tenant-a" };
    (window as unknown as Record<string, unknown>).__LOPDP_TABLAS_PRUEBAS__ = { roadmapId: "rm-1" };
  });
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/documentos", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (r) =>
    r.fulfill({ json: { borrador: 1, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1 } }));
  await page.route("**/api/v1/biblioteca/documentos/doc-203", (r) => r.fulfill({ json: completo }));
  await page.route("**/api/v1/biblioteca/filas/esquemas", (r) => r.fulfill({ json: esquemas }));
  await page.route("**/api/v1/biblioteca/filas/doc-203/INV", (r) => r.fulfill({ json: [existente] }));
  await page.route("**/api/v1/biblioteca/filas/doc-203/validar", (r) => {
    const { filas } = r.request().postDataJSON() as { filas: { codigo: string; datos: Record<string, string> }[] };
    r.fulfill({ json: { tabla: "INV", valida: filas.every((f) => f.datos.categoria === "CONTACTO"),
      filas: filas.map((f, indice) => ({ indice, codigo: f.codigo,
        errores: f.datos.categoria === "CONTACTO" ? [] : ["categoria: no está en el catálogo permitido."] })) } });
  });
  await page.route("**/api/v1/biblioteca/filas/doc-203", (r) => r.fulfill(confirmar));
  await page.route("**/api/v1/biblioteca/filas/plan/rm-1", (r) => r.fulfill({ json: [
    { id: "t-1", titulo: "Política de privacidad", control_ref: "P1", fecha_inicio: "2026-11-01",
      fecha_fin: null, estado: "Sin fecha válida", editable: false }] }));
  await abrirAppLimpia(page); await configurarProyecto(page, "Entidad BIB-203");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ }).click();
  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("button", { name: "Elegir Registro de actividades" }).click();
  return vista.getByRole("region", { name: "Tablas de captura" });
}

test("pegar valida por fila y con errores no se puede confirmar", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const tablas = await abrir(page, { status: 201, json: [] });
  await expect(tablas.getByRole("table", { name: "Filas INV" })).toContainText("INV-1");
  await tablas.getByLabel("Filas pegadas").fill("INV-2\tProveedores\tCONTACTO\nINV-3\tSalud\tINVENTADA");
  await tablas.getByRole("button", { name: "Validar filas" }).click();
  const previa = tablas.getByRole("list", { name: "Validación previa" });
  await expect(previa).toContainText("Fila 1 (INV-2): correcta");
  await expect(previa).toContainText("Fila 2 (INV-3): categoria: no está en el catálogo permitido.");
  await expect(tablas.getByRole("button", { name: /^Confirmar/ })).toBeDisabled();
});

test("una confirmación rechazada no se anuncia como guardada", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const tablas = await abrir(page, { status: 422, json: { detail: "Hay filas con errores; no se guardó ninguna." } });
  await tablas.getByLabel("Filas pegadas").fill("INV-2\tProveedores\tCONTACTO");
  await tablas.getByRole("button", { name: "Validar filas" }).click();
  await tablas.getByRole("button", { name: "Confirmar 1 filas" }).click();
  await expect(tablas.getByRole("status").last()).toContainText("No se guardó ninguna fila");
  await expect(tablas).not.toContainText("filas guardadas");
  await expect(tablas.getByRole("alert")).toHaveCount(0);
});

test("PLA es de solo lectura y una fecha inválida no aparece En plazo", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const tablas = await abrir(page, { status: 201, json: [] });
  await tablas.getByRole("tab", { name: "Plan (solo lectura)" }).click();
  const plan = tablas.getByRole("table", { name: "Plan (solo lectura)" });
  await expect(plan).toContainText("Política de privacidad");
  await expect(plan).toContainText("Sin fecha válida");
  await expect(plan).not.toContainText("En plazo");
  await expect(plan.getByRole("textbox")).toHaveCount(0);
});
