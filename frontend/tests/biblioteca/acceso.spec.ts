// ¤adpa ¤rbac-tenant
// ¤¤qa-engineer
/**
 * BIB-101 · Contexto y acceso: menú BIBLIOTECA, pestañas, botón fijo de la barra superior y panel
 * lateral (`docs/biblioteca-pmv.md` §0). API simulada: no acredita permisos ni persistencia; la
 * denegación real por membresía la prueba `tests/test_bib_101_acceso.py`.
 */
import { expect, test, type Page, type Request } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib101";
const RUTA_PENDIENTES = "**/api/v1/biblioteca/documentos/pendientes";
const PENDIENTES = { borrador: 1, en_revision: 1, por_vencer: 1, vencidos: 0, total: 3 };

async function prepararSesion(page: Page) {
  // Organización de la sesión fijada por la prueba (modo headers de desarrollo).
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, ORGANIZACION);
  // Las vistas consultan la API al montarse; aquí solo importa Biblioteca.
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
}

async function pendientesResponden(page: Page, status: number, json: unknown): Promise<Request[]> {
  const pedidas: Request[] = [];
  await page.route(RUTA_PENDIENTES, (route) => {
    pedidas.push(route.request());
    return route.fulfill({ status, json });
  });
  return pedidas;
}

const botonBiblioteca = (page: Page) => page.getByTestId("boton-biblioteca");
const panel = (page: Page) => page.getByRole("dialog", { name: "Panel de Biblioteca" });

test.describe("Biblioteca: contexto y acceso (BIB-101, API simulada)", () => {
  test.beforeEach(async ({ page }) => {
    await prepararSesion(page);
  });

  test("el menú BIBLIOTECA abre las dos pestañas, con Documentos como vista principal", async ({ page }) => {
    await pendientesResponden(page, 200, PENDIENTES);
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad BIB-101");

    await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
    const dock = page.getByRole("group", { name: "Submenús de Biblioteca" });
    const nombres = (await dock.getByRole("button").allInnerTexts()).map((t) => t.split("\n")[0].trim());
    // === FIRMA-02 ===
    // FIRMA-02 añade «Firmas» al menú BIBLIOTECA (orden 2).
    // FE-26: en el PMV no hay sala Evidencias (NEXT_PUBLIC_EVIDENCIA_FISICA apagado).
    expect(nombres).toEqual(["Documentos y plantillas", "Firmas"]);
    // === fin FIRMA-02 ===

    await dock.getByRole("button", { name: /^Documentos y plantillas/ }).click();
    await expect(page.getByTestId("pestana-vista").getByText("Documentos y plantillas", { exact: true })).toBeVisible();
    const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
    const pestanas = vista.getByRole("tab");
    await expect(pestanas).toHaveText(["Documentos de la organización", "Plantillas"]);
    await expect(vista.getByRole("tab", { name: "Documentos de la organización" })).toHaveAttribute("aria-selected", "true");
    await expect(vista.getByRole("tabpanel")).toContainText("Todavía no hay documentos de la organización");

    await vista.getByRole("tab", { name: "Plantillas" }).click();
    await expect(vista.getByRole("tab", { name: "Plantillas" })).toHaveAttribute("aria-selected", "true");
    await expect(vista.getByRole("tabpanel")).toContainText("catálogo de plantillas");
    await page.keyboard.press("ArrowLeft");
    await expect(vista.getByRole("tab", { name: "Documentos de la organización" })).toBeFocused();
    await expect(vista.getByRole("tab", { name: "Documentos de la organización" })).toHaveAttribute("aria-selected", "true");
  });

  test("botón fijo con contador en todas las pantallas; pide con la organización de la sesión", async ({ page }) => {
    const pedidas = await pendientesResponden(page, 200, PENDIENTES);
    await abrirAppLimpia(page);
    // Ya en el alta, antes de configurar el proyecto.
    await expect(botonBiblioteca(page)).toBeVisible();
    await configurarProyecto(page, "Entidad BIB-101");

    for (const menu of ["Inicio", "Inventario", "Operación"]) {
      await barraDeMenus(page).getByRole("button", { name: menu, exact: true }).click();
      await page.getByRole("group", { name: `Submenús de ${menu}` }).getByRole("button").first().click();
      await expect(botonBiblioteca(page), menu).toBeVisible();
      await expect(page.getByTestId("contador-biblioteca"), menu).toHaveText("3");
    }

    expect(pedidas.length).toBeGreaterThan(0);
    for (const pedida of pedidas) {
      expect(pedida.headers()["x-tenant-id"]).toBe(ORGANIZACION);
      expect(pedida.url()).not.toContain(ORGANIZACION);
      expect(pedida.method()).toBe("GET");
    }
  });

  test("el panel lateral tiene las mismas pestañas y abre la vista a pantalla completa", async ({ page }) => {
    await pendientesResponden(page, 200, PENDIENTES);
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad BIB-101");

    await botonBiblioteca(page).click();
    await expect(botonBiblioteca(page)).toHaveAttribute("aria-expanded", "true");
    await expect(panel(page).getByRole("tab")).toHaveText(["Documentos de la organización", "Plantillas"]);
    await panel(page).getByRole("tab", { name: "Plantillas" }).click();

    await panel(page).getByRole("button", { name: "Abrir en pantalla completa" }).click();
    await expect(panel(page)).toHaveCount(0);
    await expect(page.getByTestId("pestana-vista").getByText("Documentos y plantillas", { exact: true })).toBeVisible();
    await expect(barraDeMenus(page).locator('[aria-current="page"]')).toHaveText("Biblioteca");
    // La pestaña elegida en el panel se conserva en la vista.
    const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
    await expect(vista.getByRole("tab", { name: "Plantillas" })).toHaveAttribute("aria-selected", "true");
  });

  test("Escape cierra el panel y devuelve el foco al botón", async ({ page }) => {
    await pendientesResponden(page, 200, PENDIENTES);
    await abrirAppLimpia(page);
    await botonBiblioteca(page).click();
    await expect(panel(page)).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(panel(page)).toHaveCount(0);
    await expect(botonBiblioteca(page)).toBeFocused();
    await expect(botonBiblioteca(page)).toHaveAttribute("aria-expanded", "false");
  });

  test("sin la ruta de pendientes en el servidor el botón funciona sin contador", async ({ page }) => {
    await pendientesResponden(page, 404, { detail: "Not Found" });
    await abrirAppLimpia(page);
    await expect(botonBiblioteca(page)).toBeVisible();
    await expect(page.getByTestId("contador-biblioteca")).toHaveCount(0);
    await botonBiblioteca(page).click();
    await expect(panel(page).getByRole("tab", { name: "Documentos de la organización" })).toBeVisible();
    await expect(panel(page).getByRole("alert")).toHaveCount(0);
  });

  test("si el servidor deniega la organización, el panel lo dice y no hay contador", async ({ page }) => {
    await pendientesResponden(page, 403, { detail: "Sin membresía activa" });
    await abrirAppLimpia(page);
    await botonBiblioteca(page).click();
    await expect(panel(page).getByRole("alert")).toContainText("Sin membresía activa");
    await expect(page.getByTestId("contador-biblioteca")).toHaveCount(0);
  });

  // === BIB-116 ===
  // El botón avisa cuando no pudo cargar el contador (denegado o error); sin la ruta, no avisa.
  // Mutación documentada: mostrar el aviso solo con `error` en BotonBiblioteca.tsx hace fallar el caso 403.
  test("BIB-116: con 403 el botón muestra el aviso y lo dice en su etiqueta", async ({ page }) => {
    await pendientesResponden(page, 403, { detail: "Sin membresía activa" });
    await abrirAppLimpia(page);
    await expect(page.getByTestId("aviso-biblioteca")).toBeVisible();
    await expect(botonBiblioteca(page)).toHaveAttribute("aria-label", "Biblioteca, no se pudo cargar el contador");
    await expect(botonBiblioteca(page)).toHaveAttribute("title", "Sin membresía activa");
    await expect(page.getByTestId("contador-biblioteca")).toHaveCount(0);
  });

  test("BIB-116: con 500 el botón muestra el aviso", async ({ page }) => {
    await pendientesResponden(page, 500, { detail: "Error interno" });
    await abrirAppLimpia(page);
    await expect(page.getByTestId("aviso-biblioteca")).toBeVisible();
    await expect(botonBiblioteca(page)).toHaveAttribute("aria-label", "Biblioteca, no se pudo cargar el contador");
    await expect(page.getByTestId("contador-biblioteca")).toHaveCount(0);
  });

  test("BIB-116: con 404 no hay aviso ni contador", async ({ page }) => {
    const pedidas = await pendientesResponden(page, 404, { detail: "Not Found" });
    await abrirAppLimpia(page);
    await expect.poll(() => pedidas.length).toBeGreaterThan(0);
    await expect(botonBiblioteca(page)).toHaveAttribute("aria-label", "Biblioteca");
    await expect(page.getByTestId("aviso-biblioteca")).toHaveCount(0);
    await expect(page.getByTestId("contador-biblioteca")).toHaveCount(0);
  });

  test("BIB-116: con 200 y total 3 hay contador y no hay aviso", async ({ page }) => {
    await pendientesResponden(page, 200, PENDIENTES);
    await abrirAppLimpia(page);
    await expect(page.getByTestId("contador-biblioteca")).toHaveText("3");
    await expect(botonBiblioteca(page)).toHaveAttribute("aria-label", "Biblioteca, 3 pendientes");
    await expect(page.getByTestId("aviso-biblioteca")).toHaveCount(0);
  });
  // === fin BIB-116 ===
});
