// ¤adpa ¤rbac-tenant ¤arbitro
// ¤¤qa-engineer
/**
 * BIB-106 · Documentos externos del cliente (API simulada; la persistencia, la RLS y la cuarentena reales
 * las acredita `tests/test_bib_106_externos.py` contra PostgreSQL local).
 *
 * Contrato: POST /biblioteca/cargas → PUT /{id}/archivo (binario) → POST /{id}/finalizar (solo limpio)
 * y GET /biblioteca/cargas?documento_id= para las revisiones.
 *
 * MUTACIÓN DECISIVA (frontend): en `src/lib/biblioteca/cargas.ts` quitar
 * `if (carga.estado_analisis !== "limpio") return carga;` hace que se pida finalizar un archivo pendiente
 * y falla «un archivo pendiente queda retenido y no se finaliza».
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib106";
const DOC = {
  id: "doc-ext-1", codigo: "POL-EXT", nombre: "Política propia", origen: "subido", plantilla_version: null,
  estado: "borrador", editado: false, proxima_revision: "2027-11-07", revision: 1, creado_por: "usr-1",
  creado_en: "2026-11-07T10:00:00Z", actualizado_en: "2026-11-07T10:00:00Z",
};
const carga = (extra: Record<string, unknown> = {}) => ({
  id: "carga-1", titulo: "Política propia", codigo: "POL-EXT", version_propia: "2026.1", version_maestra: null,
  formato: "DOCX", nombre_archivo: "politica.docx", tamano_bytes: 12, sha256: "a".repeat(64),
  estado_analisis: "limpio", descargable: true, documento_id: null, revision_externa: null, finalizada: false,
  creado_en: "2026-11-07T10:00:00Z", expira_en: "2026-11-07T10:15:00Z", ...extra,
});

async function abrir(page: Page, estadoAnalisis: string) {
  const llamadas: string[] = [];
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, ORGANIZACION);
  await page.route("**/api/v1/**", (ruta) => ruta.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/documentos**", (ruta) => {
    const url = ruta.request().url();
    if (url.includes("/pendientes")) {
      return ruta.fulfill({ json: { borrador: 1, en_revision: 0, por_vencer: 0, vencidos: 0, total: 1 } });
    }
    // Recursos de otras fichas bajo el documento (enlaces, historial…): vacíos.
    if (/documentos\/[^/?]+\//.test(url)) return ruta.fulfill({ status: 404, json: { detail: "Sin datos" } });
    return ruta.fulfill({ json: /documentos\/[^/?]+/.test(url) ? { ...DOC, contenido_markdown: "# x" } : [DOC] });
  });
  await page.route("**/api/v1/biblioteca/cargas**", (ruta) => {
    const peticion = ruta.request();
    const url = new URL(peticion.url());
    llamadas.push(`${peticion.method()} ${url.pathname.replace("/api/v1", "")}${url.search}`);
    if (peticion.method() === "POST" && url.pathname.endsWith("/cargas")) {
      return ruta.fulfill({ status: 201, json: carga({ estado_analisis: "sin_archivo", descargable: false }) });
    }
    if (peticion.method() === "PUT") {
      return ruta.fulfill({ json: carga({ estado_analisis: estadoAnalisis, descargable: estadoAnalisis === "limpio" }) });
    }
    if (url.pathname.endsWith("/finalizar")) return ruta.fulfill({ json: { ...DOC, contenido_markdown: "# x" } });
    if (url.searchParams.get("documento_id")) {
      return ruta.fulfill({ json: [carga({ documento_id: DOC.id, revision_externa: 1, finalizada: true })] });
    }
    return ruta.fulfill({ json: carga({ documento_id: DOC.id, revision_externa: 1, finalizada: true }) });
  });
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-106");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ }).click();
  return { vista: page.getByRole("region", { name: "Biblioteca", exact: true }), llamadas };
}

async function adjuntar(page: Page, vista: ReturnType<Page["getByRole"]>) {
  await vista.getByTestId("carga-abrir").click();
  const formulario = vista.getByTestId("carga-formulario");
  await formulario.getByLabel("Título").fill("Política propia");
  await formulario.getByLabel("Código").fill("POL-EXT");
  await formulario.getByLabel("Versión propia").fill("2026.1");
  await formulario.getByLabel(/^Archivo/).setInputFiles({
    name: "politica.docx", mimeType: "application/octet-stream", buffer: Buffer.from("PK-sintetico"),
  });
  await formulario.getByRole("button", { name: "Subir" }).click();
  return formulario;
}

test.describe("Biblioteca: documentos externos (BIB-106, API simulada)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("adjunta un DOCX limpio como borrador y muestra origen no vinculado en sus revisiones", async ({ page }) => {
    const { vista, llamadas } = await abrir(page, "limpio");
    const formulario = await adjuntar(page, vista);
    await expect(formulario.getByTestId("carga-mensaje")).toHaveText("Documento externo guardado como borrador.");
    expect(llamadas.slice(0, 3)).toEqual(["POST /biblioteca/cargas", "PUT /biblioteca/cargas/carga-1/archivo",
      "POST /biblioteca/cargas/carga-1/finalizar"]);

    await vista.getByTestId("documento-POL-EXT").getByRole("button", { name: /^Elegir/ }).click();
    const revision = vista.getByTestId("revision-externa-1");
    await expect(revision.getByTestId("origen-maestra")).toHaveText("Origen no vinculado");
    await expect(revision.getByRole("button", { name: "Descargar" })).toBeVisible();
  });

  test("un archivo pendiente queda retenido y no se finaliza", async ({ page }) => {
    const { vista, llamadas } = await abrir(page, "pendiente");
    const formulario = await adjuntar(page, vista);
    await expect(formulario.getByTestId("carga-mensaje")).toContainText("Análisis pendiente");
    expect(llamadas.some((l) => l.endsWith("/finalizar"))).toBe(false);
  });

  test("rechaza en el navegador un archivo que no es DOCX ni XLSX", async ({ page }) => {
    const { vista, llamadas } = await abrir(page, "limpio");
    await vista.getByTestId("carga-abrir").click();
    const formulario = vista.getByTestId("carga-formulario");
    await formulario.getByLabel("Título").fill("T");
    await formulario.getByLabel("Código").fill("X");
    await formulario.getByLabel("Versión propia").fill("1");
    await formulario.getByLabel(/^Archivo/).setInputFiles({ name: "a.pdf", mimeType: "application/pdf", buffer: Buffer.from("x") });
    await formulario.getByRole("button", { name: "Subir" }).click();
    await expect(formulario.getByTestId("carga-mensaje")).toHaveText("Solo se admiten archivos DOCX o XLSX.");
    expect(llamadas.filter((l) => l.startsWith("POST"))).toEqual([]);
  });
});
