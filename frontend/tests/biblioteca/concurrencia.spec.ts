// ¤adpa ¤rbac-tenant ¤arbitro
// ¤¤qa-engineer
/**
 * BIB-207 · Guardado con control de cambios y trabajos de generación (ranuras `documento:editor` y
 * `documento:acciones`). API simulada: la atomicidad, la idempotencia en base, la RLS y el reintento sin
 * duplicar los prueba `tests/test_bib_207_concurrencia.py` contra la base propia.
 *  - Un guardado en conflicto muestra la comparación y «Recuperar mis cambios» guarda sobre la revisión vigente.
 *  - Una petición repetida tras un fallo de red reutiliza la misma clave de idempotencia.
 *  - Se ve Pendiente, Generando, Fallido y Listo; «Reintentar» recupera el trabajo fallido.
 *  - Ningún fallo se anuncia con `role="alert"`.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const DOC = "doc-207";
const documento = {
  id: DOC, codigo: "BIB-001", nombre: "Política de datos", origen: "plantilla", plantilla_version: "0.2.0",
  estado: "borrador", editado: false, proxima_revision: "2027-11-04", revision: 2, creado_por: "u",
  creado_en: "2026-11-04T10:00:00Z", actualizado_en: "2026-11-04T10:00:00Z",
};
const completo = { ...documento, plantilla_id: "p", contenido_markdown: "# Política", variables_faltantes: [],
  aprobado_por: null, aprobado_en: null, sha256: "a".repeat(64), fecha_emision: "2026-11-04" };
const borrador = {
  id: DOC, codigo: "BIB-001", revision: 2, contexto: { "contexto.finalidad": "Recepción" },
  campos: [{ clave: "contexto.finalidad", etiqueta: "Finalidad", tipo: "texto" }],
};
const trabajo = {
  id: "job-1", borrador_id: DOC, revision_borrador: 2, clave: "", modo: "borrador", formato: "docx",
  estado: "pendiente", intentos: 0, generacion_id: null, error_codigo: null, error_detalle: null, creado_por: "u",
  creado_en: "2026-11-04T10:05:00Z", actualizado_en: "2026-11-04T10:05:00Z", vencido: false,
};

async function abrir(page: Page, rutas: (p: Page) => Promise<void>) {
  await page.addInitScript(() => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "tenant-a" };
    window.__LOPDP_TRABAJOS_PRUEBAS__ = { intervaloMs: 150 };
  });
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/documentos", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos?**", (r) => r.fulfill({ json: [documento] }));
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (r) =>
    r.fulfill({ json: { borrador: 1, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1 } }));
  await page.route(`**/api/v1/biblioteca/documentos/${DOC}`, (r) => r.fulfill({ json: completo }));
  await page.route(`**/api/v1/biblioteca/borradores/${DOC}`, (r) => r.fulfill({ json: borrador }));
  await rutas(page);
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-207");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ }).click();
  await page.getByRole("button", { name: "Elegir Política de datos" }).click();
}

test("un conflicto de edición se compara y se recuperan los cambios sobre la revisión vigente", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const guardados: { revision: number; contexto: Record<string, string> }[] = [];
  await abrir(page, async (p) => {
    await p.route(`**/api/v1/biblioteca/trabajos/borradores/${DOC}`, async (r) => {
      if (r.request().method() === "GET") return r.fulfill({ json: [] });
      const cuerpo = r.request().postDataJSON();
      guardados.push(cuerpo);
      if (cuerpo.revision === 2) {
        return r.fulfill({ status: 409, json: {
          detail: "Otra persona guardó este borrador", code: "BIB_CONFLICTO_EDICION", conflicto: {
            borrador_id: DOC, revision_esperada: 2, revision_vigente: 3, fecha_vigente: "2026-11-04",
            contexto_vigente: { "contexto.finalidad": "Archivo" },
            diferencias: [{ clave: "contexto.finalidad", mio: "Recepción y pasillos", vigente: "Archivo" }] } } });
      }
      return r.fulfill({ json: { borrador_id: DOC, revision: 4 } });
    });
  });
  const panel = page.getByRole("region", { name: "Guardado con control de cambios" });
  await expect(panel).toContainText("Editas la revisión 2");
  await panel.getByLabel("Finalidad").fill("Recepción y pasillos");
  await panel.getByRole("button", { name: "Guardar cambios" }).click();
  await expect(panel.getByRole("status")).toContainText("otra persona cambió el borrador");
  const fila = panel.getByRole("table", { name: "Comparación de cambios" }).getByRole("row").nth(1);
  await expect(fila).toContainText("Finalidad");
  await expect(fila).toContainText("Recepción y pasillos");
  await expect(fila).toContainText("Archivo");

  await panel.getByRole("button", { name: "Recuperar mis cambios" }).click();
  await expect(panel.getByRole("status")).toContainText("Cambios guardados (revisión 4)");
  await expect(panel.getByRole("group", { name: "Conflicto de edición" })).toHaveCount(0);
  expect(guardados.map((g) => g.revision)).toEqual([2, 3]);
  expect(guardados[1].contexto).toEqual({ "contexto.finalidad": "Recepción y pasillos" });
  await expect(panel.getByRole("alert")).toHaveCount(0);
});

test("la petición repetida reutiliza la clave y el trabajo fallido se reintenta hasta Listo", async ({ page }, info) => {
  test.skip(info.project.name === "produccion", "La API simulada solo corre en desarrollo.");
  const claves: string[] = [];
  const estados = ["generando", "fallido"];
  let reintentado = false;
  await abrir(page, async (p) => {
    await p.route(`**/api/v1/biblioteca/trabajos/borradores/${DOC}`, (r) => r.fulfill({ json: [] }));
    await p.route(`**/api/v1/biblioteca/trabajos/borradores/${DOC}/generaciones`, async (r) => {
      const cuerpo = r.request().postDataJSON();
      claves.push(cuerpo.clave);
      if (claves.length === 1) return r.abort("connectionreset");
      return r.fulfill({ status: 202, json: { ...trabajo, clave: cuerpo.clave } });
    });
    await p.route("**/api/v1/biblioteca/trabajos/job-1", (r) => {
      if (reintentado) {
        return r.fulfill({ json: { ...trabajo, estado: "listo", intentos: 2, generacion_id: "gen-1" } });
      }
      const estado = estados.length > 1 ? estados.shift()! : estados[0];
      return r.fulfill({ json: { ...trabajo, estado, intentos: 1,
        ...(estado === "fallido" ? { error_codigo: "BIB_TRABAJO_FALLO_INTERNO",
          error_detalle: "La generación falló por un error interno; puedes reintentarla." } : {}) } });
    });
    await p.route("**/api/v1/biblioteca/trabajos/job-1/reintentar", (r) => {
      reintentado = true;
      return r.fulfill({ status: 202, json: { ...trabajo, estado: "pendiente", intentos: 1 } });
    });
  });
  const panel = page.getByRole("region", { name: "Trabajos de generación" });
  await panel.getByRole("button", { name: "Pedir archivo" }).click();
  await expect(panel.getByRole("status")).toContainText("Si vuelves a pedirlo se usará la misma petición");
  await panel.getByRole("button", { name: "Pedir archivo" }).click();
  await expect.poll(() => claves.length).toBe(2);
  expect(claves[1]).toBe(claves[0]);

  const estado = panel.getByTestId("estado-trabajo");
  await expect(estado).toHaveText("Fallido");
  await expect(panel).toContainText("puedes reintentarla");
  await panel.getByRole("button", { name: "Reintentar" }).click();
  await expect(estado).toHaveText("Listo");
  await expect(panel).toContainText("Intentos: 2");
  await expect(panel.getByRole("button", { name: "Reintentar" })).toHaveCount(0);
  await expect(panel.getByRole("alert")).toHaveCount(0);
});
