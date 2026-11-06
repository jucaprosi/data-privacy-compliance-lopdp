// ¤adpa ¤rbac-tenant ¤frontend-ide
// ¤¤qa-engineer
/**
 * BIB-115 · Biblioteca envía la identidad completa. Las rutas de Biblioteca exigen `X-Role` (y
 * `X-User-ID` en modo headers, el de desarrollo y el de este arnés): toda petición a
 * `/api/v1/biblioteca/` debe llevarlas, y un rechazo de identidad se muestra en lugar de ocultar el
 * contador. API simulada: la exigencia real la prueba `tests/test_bib115_identidad_biblioteca.py`.
 *
 * Mutación documentada: quitar `"X-Role": rol` de `cabecerasDeMiembro` hace fallar la primera prueba.
 */
import { expect, test, type Page, type Request } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const PENDIENTES = { borrador: 2, en_revision: 1, por_vencer: 1, vencidos: 0, total: 4 };
const ORGANIZACION_ACTIVA = "lopdp-organizacion-activa-v1";

/** Simula la API: pendientes con `pendientes`; el resto, de Biblioteca o no, «no disponible» (503). */
async function simularApi(page: Page, pendientes: { status: number; json: unknown }): Promise<Request[]> {
  const deBiblioteca: Request[] = [];
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/**", (route) => {
    const pedida = route.request();
    deBiblioteca.push(pedida);
    if (new URL(pedida.url()).pathname.endsWith("/biblioteca/documentos/pendientes")) {
      return route.fulfill(pendientes);
    }
    return route.fulfill({ status: 503, json: { detail: "API simulada" } });
  });
  return deBiblioteca;
}

const botonBiblioteca = (page: Page) => page.getByTestId("boton-biblioteca");

test.describe("Biblioteca: identidad completa en cada petición (BIB-115, API simulada)", () => {
  test("toda llamada a Biblioteca lleva X-Role y X-User-ID, y el contador se muestra", async ({ page }) => {
    const pedidas = await simularApi(page, { status: 200, json: PENDIENTES });
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad BIB-115");
    await expect(page.getByTestId("contador-biblioteca")).toHaveText("4");

    // Más rutas de Biblioteca: la vista a pantalla completa con sus dos pestañas.
    await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
    await page.getByRole("group", { name: "Submenús de Biblioteca" })
      .getByRole("button", { name: /^Documentos y plantillas/ }).click();
    const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
    await vista.getByRole("tab", { name: "Plantillas" }).click();

    await expect.poll(() => new Set(pedidas.map((p) => new URL(p.url()).pathname)).size).toBeGreaterThan(1);
    for (const pedida of pedidas) {
      const cabeceras = pedida.headers();
      const ruta = new URL(pedida.url()).pathname;
      expect(cabeceras["x-role"], ruta).toBeTruthy();
      expect(cabeceras["x-user-id"], ruta).toBeTruthy();
      expect(cabeceras["x-tenant-id"], ruta).toBeTruthy();
    }
  });

  test("el rol sale de la organización activa", async ({ page }) => {
    await page.addInitScript((clave) => {
      window.sessionStorage.setItem(clave, JSON.stringify({
        tenant_id: "org-bib115", nombre_comercial: "Org BIB-115", roles: ["dpo"],
      }));
    }, ORGANIZACION_ACTIVA);
    const pedidas = await simularApi(page, { status: 200, json: PENDIENTES });
    await abrirAppLimpia(page);
    await expect(page.getByTestId("contador-biblioteca")).toHaveText("4");
    const pendientes = pedidas.filter((p) => p.url().includes("/biblioteca/documentos/pendientes"));
    expect(pendientes.length).toBeGreaterThan(0);
    for (const pedida of pendientes) expect(pedida.headers()["x-role"]).toBe("dpo");
  });

  test("un 422 por cabecera se muestra con su mensaje en lugar de ocultarse", async ({ page }) => {
    await simularApi(page, {
      status: 422,
      json: { detail: [{ type: "missing", loc: ["header", "X-Role"], msg: "Field required", input: null }] },
    });
    await abrirAppLimpia(page);
    await botonBiblioteca(page).click();
    const panel = page.getByRole("dialog", { name: "Panel de Biblioteca" });
    await expect(panel.getByRole("alert")).toHaveText("Falta la cabecera X-Role");
    await expect(page.getByTestId("contador-biblioteca")).toHaveCount(0);
  });

  test("un 403 se muestra con el mensaje del servidor", async ({ page }) => {
    await simularApi(page, { status: 403, json: { detail: "Sin membresía activa" } });
    await abrirAppLimpia(page);
    await botonBiblioteca(page).click();
    const panel = page.getByRole("dialog", { name: "Panel de Biblioteca" });
    await expect(panel.getByRole("alert")).toHaveText("Sin membresía activa");
  });
});
