// ¤adpa ¤arbitro
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const CORTE = "2026-11-04T12:00:00Z";
const indicador = (clave: string, titulo: string, foco: string, conteos: Record<string, number>, avance: number | null) => ({
  clave, titulo, fecha_corte: CORTE, categoria_foco: foco, valor_foco: conteos[foco],
  denominador: Object.entries(conteos).filter(([c]) => c !== "sin_mapear").reduce((a, [, n]) => a + n, 0),
  conteos, sin_mapear: conteos.sin_mapear, avance_implementacion: avance,
  etiqueta_avance: "Avance de implementación. No es una certificación ni garantía de cumplimiento.",
  exclusiones: [{ motivo: "Registros con estado sin mapear: se muestran aparte.", cantidad: conteos.sin_mapear }],
  origen: "biblioteca_" + clave,
});

async function abrir(page: Page) {
  await page.addInitScript(() => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "org-bib305" }; });
  await page.route(/\/api\/v1\/biblioteca\/indicadores(?:\?.*)?$/, (route) => route.fulfill({ json: {
    fecha_corte: CORTE, etiqueta: "Avance de implementación. No es una certificación ni garantía de cumplimiento.",
    indicadores: [
      indicador("acciones", "Acciones verificadas", "verificada", { verificada: 1, no_conforme: 0, pendiente: 2, sin_mapear: 1 }, 33.3),
      indicador("documentos", "Documentos pendientes de revisión", "pendiente_revision", { pendiente_revision: 2, borrador: 1, aprobado: 1, vencido: 0, sin_mapear: 0 }, 25),
      indicador("decisiones", "Decisiones sin información", "sin_informacion", { sin_informacion: 1, decidida: 0, sin_mapear: 0 }, 0),
    ] } }));
  await page.route("**/api/v1/biblioteca/indicadores/acciones/registros?categoria=pendiente", (route) => route.fulfill({ json: {
    clave: "acciones", categoria: "pendiente", fecha_corte: CORTE, registros: [
      { id: "acc-1", categoria: "pendiente", estado_origen: null, descripcion: "Documento enlazado aprobado; falta verificación", origen: "biblioteca_verificaciones" },
      { id: "acc-2", categoria: "pendiente", estado_origen: null, descripcion: "Acción con requisito documental", origen: "biblioteca_verificaciones" },
    ] } }));
  await page.route("**/api/v1/biblioteca/impactos", (route) => route.fulfill({ json: [] }));
  await page.route("**/api/v1/biblioteca/documentos**", (route) => route.fulfill({ json: [] }));
  await abrirAppLimpia(page); await configurarProyecto(page, "Entidad BIB-305");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" }).getByRole("button", { name: /^Documentos y plantillas/ }).click();
}

test("muestra tres indicadores separados con corte, denominador, exclusiones y sin mapear", async ({ page }) => {
  await abrir(page);
  const acciones = page.getByTestId("indicador-acciones");
  await expect(acciones).toContainText("1 de 3 (denominador)");
  await expect(acciones).toContainText("Estados sin mapear: 1");
  await expect(acciones).toContainText("Exclusión:");
  await expect(acciones).toContainText("Avance de implementación: 33.3 %");
  await expect(acciones).toContainText("No es una certificación");
  await expect(page.getByTestId("indicador-documentos")).toContainText("2 de 4 (denominador)");
  await expect(page.getByTestId("indicador-decisiones")).toContainText("Decisiones sin información");
  await expect(page.getByText(/cumplimiento global|certificado/i)).toHaveCount(0);
});

test("abre los registros de origen de una categoría", async ({ page }) => {
  await abrir(page);
  await page.getByTestId("indicador-acciones").getByRole("button", { name: "Pendientes de verificación: 2" }).click();
  await expect(page.getByTestId("registro-origen")).toHaveCount(2);
  await expect(page.getByTestId("registro-origen").first()).toContainText("falta verificación");
});

test("si la carga falla no muestra el panel ni una alerta propia", async ({ page }) => {
  await page.route(/\/api\/v1\/biblioteca\/indicadores(?:\?.*)?$/, (route) => route.fulfill({ status: 500, json: {} }));
  await page.addInitScript(() => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "org-bib305" }; });
  await page.route("**/api/v1/biblioteca/impactos", (route) => route.fulfill({ json: [] }));
  await page.route("**/api/v1/biblioteca/documentos**", (route) => route.fulfill({ json: [] }));
  await abrirAppLimpia(page); await configurarProyecto(page, "Entidad BIB-305");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" }).getByRole("button", { name: /^Documentos y plantillas/ }).click();
  await expect(page.getByTestId("indicador-acciones")).toHaveCount(0);
  await expect(page.getByRole("region", { name: "Indicadores verificables" })).toHaveCount(0);
});
