// ¤adpa ¤frontend-ide
// ¤¤qa-engineer
/**
 * BIB-104 · Descarga controlada de plantillas Word/Excel. API simulada:
 * `POST /api/v1/biblioteca/plantillas/{id}/descargar`.
 *
 * La ranura `plantilla:acciones` se monta mediante el anfitrión de pruebas con
 * `window.__LOPDP_DESCARGA_PRUEBAS__`.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib104";
const PLANTILLA_DOCX = "plantilla-docx-1";

const RESPUESTA_DESCARGA = {
  plantilla_id: PLANTILLA_DOCX,
  codigo: "BIB-001",
  version: "1.0.0",
  formato: "DOCX",
  nombre_archivo: "BIB-001_v1.0.0_politica.docx",
  url_descarga: `/api/v1/biblioteca/descargas/${PLANTILLA_DOCX}/archivo?token=token-prueba`,
  expira_en_segundos: 300,
  aviso_legal: "La descarga de esta plantilla no atribuye cumplimiento legal automático de la LOPDP.",
};

async function prepararSesion(page: Page, plantillaId = PLANTILLA_DOCX) {
  await page.addInitScript(
    ({ tenant, id }) => {
      window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
      window.__LOPDP_DESCARGA_PRUEBAS__ = { plantillaId: id };
    },
    { tenant: ORGANIZACION, id: plantillaId },
  );
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
}

async function abrirDescargas(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-104");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page
    .getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ })
    .click();
  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("tab", { name: "Plantillas" }).click();
  return vista.getByTestId("anfitrion-descargas");
}

test.describe("Biblioteca: descarga controlada de plantillas (BIB-104, API simulada)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "Los ganchos de prueba no existen en producción.");
  });

  test("muestra el botón de descarga en plantilla:acciones y solicita enlace temporal firmado", async ({ page }) => {
    await prepararSesion(page);
    let peticionHecha = false;
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA_DOCX}/descargar`, async (route) => {
      peticionHecha = true;
      await route.fulfill({
        status: 200,
        json: RESPUESTA_DESCARGA,
      });
    });

    const contenedor = await abrirDescargas(page);
    const boton = contenedor.getByTestId("boton-descargar-plantilla");
    await expect(boton).toBeVisible();
    await expect(boton).toContainText("Descargar archivo maestro");

    await boton.click();
    expect(peticionHecha).toBe(true);

    const estado = contenedor.getByTestId("estado-descarga-exitosa");
    await expect(estado).toBeVisible();
    await expect(estado).toContainText("Descarga iniciada: BIB-001_v1.0.0_politica.docx");
    await expect(estado).toContainText("La descarga de esta plantilla no atribuye cumplimiento legal automático");
  });

  test("si la versión está retirada o no publicada, el servidor deniega y muestra error", async ({ page }) => {
    await prepararSesion(page);
    await page.route(`**/api/v1/biblioteca/plantillas/${PLANTILLA_DOCX}/descargar`, async (route) => {
      await route.fulfill({
        status: 403,
        json: {
          code: "BIB_DESCARGA_DENEGADA",
          detail: "Solo se pueden descargar versiones publicadas.",
        },
      });
    });

    const contenedor = await abrirDescargas(page);
    const boton = contenedor.getByTestId("boton-descargar-plantilla");
    await boton.click();

    const alerta = contenedor.getByRole("alert");
    await expect(alerta).toBeVisible();
    await expect(alerta).toContainText("Solo se pueden descargar versiones publicadas.");
  });
});
