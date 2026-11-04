// ¤adpa ¤rbac-tenant
// ¤¤qa-engineer
/**
 * BIB-102 · Catálogo de plantillas (pestaña «Plantillas»). API simulada: comprueba qué pide la
 * pantalla y cómo distingue vacío, desconexión, falta de permiso y fallo del servidor; la autorización
 * real y los filtros de datos los prueba `tests/test_bib_102_catalogo.py` contra la base.
 *
 * Pendiente del coordinador: añadir esta prueba a `SOLO_DESARROLLO` de `playwright.config.ts` (fuera
 * de la `propiedad` de BIB-102). Usa `window.__LOPDP_AUTH_PRUEBAS__`, que no existe en producción;
 * hasta entonces, en CI cae en el proyecto «produccion» y se omite.
 */
import { expect, test, type Page, type Route } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib102";
const RUTA = "**/api/v1/biblioteca/plantillas**";

const plantilla = (codigo: string, extra: Record<string, unknown> = {}) => ({
  id: `id-${codigo}`, codigo, nombre: `Plantilla ${codigo}`, tipo: "politica", fuente: "smartcidi",
  version: "0.1.0", formato: "MD", validacion_legal: "pendiente", ola: 1, estado: "publicada",
  descargable: false, ...extra,
});

async function abrirPlantillas(page: Page, responder: (ruta: Route) => Promise<void> | void) {
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, ORGANIZACION);
  await page.route("**/api/v1/**", (ruta) => ruta.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route(RUTA, responder);
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-102");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ }).click();
  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("tab", { name: "Plantillas" }).click();
  return vista.getByTestId("catalogo-plantillas");
}

test.describe("Biblioteca: catálogo de plantillas (BIB-102, API simulada)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("lista las plantillas, pide con los filtros elegidos y no ofrece descarga", async ({ page }) => {
    const pedidas: string[] = [];
    const catalogo = await abrirPlantillas(page, (ruta) => {
      const url = new URL(ruta.request().url());
      pedidas.push(url.search);
      const ola = url.searchParams.get("ola");
      const lista = [plantilla("BIB-001"), plantilla("BIB-002", { ola: 2, tipo: "aviso", estado: "en_revision" })];
      return ruta.fulfill({ json: ola ? lista.filter((p) => String(p.ola) === ola) : lista });
    });

    await expect(catalogo.getByTestId("plantilla-BIB-001")).toContainText("versión 0.1.0");
    await expect(catalogo.getByTestId("plantilla-BIB-001")).toContainText("Validación legal: pendiente");
    await expect(catalogo.getByTestId("plantilla-BIB-002")).toContainText("En revisión");
    // Ninguna entrada ofrece descargar, ni publicada ni en otro estado.
    await expect(catalogo.getByRole("button", { name: /descarg/i })).toHaveCount(0);
    expect(pedidas[0]).toBe("");

    await catalogo.getByLabel("Ola").selectOption("2");
    await expect(catalogo.getByTestId("plantilla-BIB-001")).toHaveCount(0);
    await expect(catalogo.getByTestId("plantilla-BIB-002")).toBeVisible();
    await catalogo.getByLabel("Tipo").selectOption("aviso");
    await catalogo.getByLabel("Fuente").selectOption("smartcidi");
    await expect.poll(() => pedidas.at(-1)).toBe("?fuente=smartcidi&tipo=aviso&ola=2");
  });

  test("elegir una plantilla la marca y volver a elegirla la suelta", async ({ page }) => {
    const catalogo = await abrirPlantillas(page, (ruta) => ruta.fulfill({ json: [plantilla("BIB-001")] }));
    const boton = catalogo.getByRole("button", { name: "Elegir Plantilla BIB-001" });
    await expect(boton).toHaveAttribute("aria-pressed", "false");
    await boton.click();
    await expect(boton).toHaveAttribute("aria-pressed", "true");
    await boton.click();
    await expect(boton).toHaveAttribute("aria-pressed", "false");
  });

  test("vacío con filtros se explica y permite limpiarlos; vacío sin filtros es otro mensaje", async ({ page }) => {
    const catalogo = await abrirPlantillas(page, (ruta) => {
      const hayFiltro = new URL(ruta.request().url()).search !== "";
      return ruta.fulfill({ json: hayFiltro ? [] : [plantilla("BIB-001")] });
    });
    await expect(catalogo.getByTestId("plantilla-BIB-001")).toBeVisible();
    await catalogo.getByLabel("Ola").selectOption("3");
    await expect(catalogo).toContainText("Ninguna plantilla coincide con los filtros");
    await catalogo.getByRole("button", { name: "Limpiar filtros" }).click();
    await expect(catalogo.getByTestId("plantilla-BIB-001")).toBeVisible();
    await expect(catalogo).not.toContainText("Ninguna plantilla coincide");
  });

  test("sin plantillas y sin filtros dice que todavía no hay publicadas", async ({ page }) => {
    const catalogo = await abrirPlantillas(page, (ruta) => ruta.fulfill({ json: [] }));
    await expect(catalogo).toContainText("Todavía no hay plantillas publicadas");
    await expect(catalogo.getByRole("button", { name: "Limpiar filtros" })).toBeDisabled();
  });

  test("falta de permiso, desconexión y fallo del servidor se distinguen y no muestran ejemplos", async ({ page }) => {
    let modo: "denegado" | "desconexion" | "caida" = "denegado";
    const catalogo = await abrirPlantillas(page, (ruta) => {
      if (modo === "desconexion") return ruta.abort("connectionrefused");
      if (modo === "caida") return ruta.fulfill({ status: 500, json: { detail: "Fallo interno" } });
      return ruta.fulfill({ status: 403, json: { code: "BIB_SIN_ACCESO", detail: "No tienes acceso a la Biblioteca de esta organización." } });
    });

    await expect(catalogo.getByTestId("catalogo-denegado")).toContainText("No tienes acceso a la Biblioteca");
    await expect(catalogo.getByRole("button", { name: "Reintentar" })).toHaveCount(0);

    modo = "desconexion";
    await catalogo.getByLabel("Tipo").selectOption("aviso");
    await expect(catalogo.getByTestId("catalogo-desconectado")).toContainText("No hay conexión con el servidor");
    await expect(catalogo.getByTestId("catalogo-denegado")).toHaveCount(0);

    modo = "caida";
    await catalogo.getByRole("button", { name: "Reintentar" }).click();
    await expect(catalogo.getByTestId("catalogo-error")).toContainText("El servidor no pudo entregar el catálogo");
    // Ningún fallo deja plantillas de relleno ni el mensaje de vacío.
    await expect(catalogo.getByRole("list", { name: "Plantillas" })).toHaveCount(0);
    await expect(catalogo).not.toContainText("Todavía no hay plantillas");
    await expect(catalogo).not.toContainText("Ninguna plantilla coincide");
  });
});
