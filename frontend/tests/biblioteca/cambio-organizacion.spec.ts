// ¤adpa ¤rbac-tenant ¤arbitro
// ¤¤qa-engineer
/**
 * BIB-110 · Biblioteca al cambiar de organización (criterios 1 y 3 del kit de BIB-101).
 *
 * Se ejerce el almacén por los ganchos de prueba de `useBibliotecaStore` (solo fuera de producción);
 * el aviso de «guardar o descartar» es el de FE-21 y lo prueba `tests/auth/organizaciones.spec.ts`.
 * Mutaciones documentadas:
 *  - no invalidar al cambiar de organización (dejar `vigilarCambioDeOrganizacion` sin efecto): fallan los dos primeros;
 *  - no mantener `cambiosSinGuardar` mientras haya una fuente (quitar el oyente de `useAuditStore`): falla el cuarto;
 *  - persistir el true ajeno (quitar el `haySinGuardarExterno()` de `partialize`): falla el quinto.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, configurarProyecto } from "../utiles";

const ORG_A = "org-prueba-bib110-a";
const ORG_B = "org-prueba-bib110-b";
const PENDIENTES_A = { borrador: 2, en_revision: 1, por_vencer: 0, vencidos: 0, total: 3 };

async function abrir(page: Page) {
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, ORG_A);
  // Playwright da prioridad a la ruta registrada última: la general va primero.
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (r) => r.fulfill({ status: 200, json: PENDIENTES_A }));
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-110");
  await page.waitForFunction(() => Boolean(window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__));
  // Configurar el proyecto deja cambios propios del diagnóstico: aquí solo importan los de Biblioteca.
  await page.evaluate(() => window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__!.fijarCambiosPropios(false));
}

/** Trabaja en A: carga contadores, elige un documento y deja un editor con cambios sin guardar. */
async function trabajarEnA(page: Page) {
  await page.evaluate(async () => {
    const g = window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__!;
    await g.almacen.getState().cargarPendientes();
    g.almacen.getState().elegirPestana("plantillas");
    g.seleccion.getState().elegirDocumento("documento-de-a");
    g.seleccion.getState().elegirPlantilla("plantilla-de-a");
    g.marcarCambios("editor", true);
  });
}

async function cambiarAB(page: Page) {
  await page.evaluate((b) => {
    window.__LOPDP_AUTH_PRUEBAS__!.tenant = b;
    return window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__!.almacen.getState().sincronizarOrganizacion();
  }, ORG_B);
}

const leer = (page: Page) =>
  page.evaluate(async () => {
    const g = window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__!;
    const a = g.almacen.getState();
    const s = g.seleccion.getState();
    return {
      organizacion: a.organizacion, pestana: a.pestana, pendientes: a.pendientes, estado: a.estadoPendientes,
      documento: s.documentoId, plantilla: s.plantillaId, sinGuardar: await g.cambiosSinGuardar(),
    };
  });

test.describe("Biblioteca al cambiar de organización (BIB-110)", () => {
  test("al cambiar de A a B se descarta lo cargado de A: contador, pestaña y selección", async ({ page }) => {
    await abrir(page);
    await trabajarEnA(page);
    const enA = await leer(page);
    expect(enA).toMatchObject({ organizacion: ORG_A, pestana: "plantillas", documento: "documento-de-a", estado: "listo" });
    expect(enA.pendientes?.total).toBe(3);

    await cambiarAB(page);
    expect(await leer(page)).toMatchObject({
      organizacion: ORG_B, pestana: "documentos", pendientes: null, estado: "inicial", documento: null, plantilla: null,
    });
  });

  test("lo cambiado sin guardar en A no queda marcado en B", async ({ page }) => {
    await abrir(page);
    await trabajarEnA(page);
    expect((await leer(page)).sinGuardar).toBe(true);
    await cambiarAB(page);
    expect((await leer(page)).sinGuardar).toBe(false);
  });

  test("la primera carga no invalida lo que una vista ya marcó", async ({ page }) => {
    await abrir(page);
    await page.evaluate(() => {
      const g = window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__!;
      g.marcarCambios("editor", true);
      g.almacen.getState().sincronizarOrganizacion();
    });
    expect((await leer(page)).sinGuardar).toBe(true);
  });

  test("con cambios pendientes en Biblioteca, el aviso de FE-21 los ve; al resolverlos se apaga", async ({ page }) => {
    await abrir(page);
    expect((await leer(page)).sinGuardar).toBe(false);
    await page.evaluate(() => window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__!.marcarCambios("editor", true));
    expect((await leer(page)).sinGuardar).toBe(true);
    await page.evaluate(() => window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__!.marcarCambios("editor", false));
    expect((await leer(page)).sinGuardar).toBe(false);
  });

  test("ese «sin guardar» ajeno no se persiste: otra organización no lo hereda al recargar", async ({ page }) => {
    await abrir(page);
    await page.evaluate(() => window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__!.marcarCambios("editor", true));
    // fuerza una escritura del almacén persistido
    await page.evaluate(() => window.__LOPDP_BIBLIOTECA_CAMBIO_PRUEBAS__!.escribirAuditoria());
    const guardado = await page.evaluate(() => JSON.parse(window.localStorage.getItem("jubys-audit-storage") ?? "{}"));
    expect(guardado.state?.cambiosSinGuardar ?? false).toBe(false);
  });
});
