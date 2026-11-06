// ¤adpa ¤arbitro
/**
 * BIB-208 · Cobertura de las ocho fichas iniciales (pestaña «Plantillas»). API simulada: comprueba que
 * se ven las ocho con su modo de captura y que una carga fallida no rompe la pestaña ni muestra alertas.
 * Permisos y persistencia se acreditan en tests/test_bib_208_fichas.py, no aquí.
 */
import { expect, test, type Page, type Route } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const RUTA = /\/api\/v1\/biblioteca\/fichas-iniciales(?:\?.*)?$/;
const campo = (clave: string, requisito: "O" | "C" | "D", extra: Record<string, unknown> = {}) => ({
  clave, etiqueta: clave.replace(/_/g, " "), tipo: "string", requisito, valores: [], editable: requisito !== "D",
  columna: null, seccion: null, ...extra,
});
const tabla = (codigo: string, interfaz: string) => ({
  codigo, modo: "tabla", version_esquema: "1.0-proposed", plantilla: `${codigo}.xlsx`, interfaz, secciones: [],
  colecciones: [], estado_generacion: "schema_and_template_migration_required",
  campos: [campo("registro_id", "D", { columna: "A" }), campo("finalidad", "O", { columna: "B" })],
});
const secciones = (codigo: string, interfaz: string, colecciones: string[]) => ({
  codigo, modo: "secciones", version_esquema: "1.0-proposed", plantilla: `${codigo}.docx`, interfaz,
  secciones: ["Identificación", "Control"], colecciones, estado_generacion: "schema_and_template_migration_required",
  campos: [campo("identificacion_responsable", "O", { seccion: "Identificación" }),
    campo("nombre_dpd", "C", { seccion: "Identificación" }), campo("elabora", "D", { seccion: "Control" })],
});
const OCHO = [
  tabla("INV-01", "Tabla de categorías de datos por actividad"), tabla("INV-02", "Tabla de activos"),
  tabla("RAT-01", "Tabla por actividad de tratamiento"), tabla("LEG-01", "Tabla de evaluación por finalidad"),
  tabla("PLA-01", "Vista y exportación del plan de acción existente"),
  secciones("EIPD-00", "Asistente de EIPD", ["criteria"]), secciones("AVI-01", "Asistente de aviso", ["purposes"]),
  secciones("PRO-01", "Asistente de procedimiento", ["operational_roles", "right_policies"]),
];

async function abrirPlantillas(page: Page, responder: (ruta: Route) => Promise<void> | void) {
  await page.addInitScript(() => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "org-bib208" }; });
  await page.route("**/api/v1/**", (ruta) => ruta.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route(RUTA, responder);
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-208");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ }).click();
  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("tab", { name: "Plantillas" }).click();
  return vista;
}

test.describe("Biblioteca: cobertura de ocho fichas (BIB-208, API simulada)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("muestra las ocho fichas con su modo de captura y sus campos", async ({ page }) => {
    const vista = await abrirPlantillas(page, (ruta) => ruta.fulfill({ json: OCHO }));
    const cobertura = vista.getByRole("region", { name: "Cobertura de fichas iniciales" });
    await expect(cobertura.getByRole("article")).toHaveCount(8);
    for (const codigo of ["INV-01", "INV-02", "RAT-01", "LEG-01"]) {
      await expect(cobertura.getByTestId(`ficha-inicial-${codigo}`)).toContainText("Captura en tabla");
    }
    await expect(cobertura.getByTestId("ficha-inicial-PLA-01")).toContainText("Instantánea del plan existente");
    for (const codigo of ["EIPD-00", "AVI-01", "PRO-01"]) {
      await expect(cobertura.getByTestId(`ficha-inicial-${codigo}`)).toContainText("Asistente por secciones");
    }
    const avi = cobertura.getByTestId("ficha-inicial-AVI-01");
    await expect(avi).toContainText("necesita migración");
    await avi.getByRole("button", { name: "Ver campos" }).click();
    const campos = avi.getByTestId("campos-AVI-01");
    await expect(campos.getByRole("region", { name: "AVI-01: Identificación" })).toContainText("nombre dpd · Condicional");
    await expect(campos.getByRole("region", { name: "AVI-01: Control" })).toContainText("elabora · Lo asigna el servidor");
    await expect(campos).toContainText("Colecciones repetibles: purposes");
  });

  test("si la carga falla la pestaña sigue usable y no muestra alertas", async ({ page }) => {
    const vista = await abrirPlantillas(page, (ruta) => ruta.fulfill({ status: 500, json: { detail: "fallo" } }));
    await expect(vista.getByRole("tab", { name: "Plantillas" })).toBeVisible();
    await expect(vista.getByRole("region", { name: "Cobertura de fichas iniciales" })).toHaveCount(0);
    // Otras vistas de la pestaña avisan de su propio 503 simulado; ninguna alerta es de esta vista.
    await expect(vista.getByRole("alert").filter({ hasText: /fichas iniciales|cobertura/i })).toHaveCount(0);
    await expect(vista.getByTestId(/^ficha-inicial-/)).toHaveCount(0);
  });
});
