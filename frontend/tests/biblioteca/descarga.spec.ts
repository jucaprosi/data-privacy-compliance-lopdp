// ¤adpa ¤frontend-ide
// ¤¤qa-engineer
/**
 * BIB-104 · Descarga controlada de plantillas Word/Excel. API simulada:
 * `POST /api/v1/biblioteca/plantillas/{id}/descargar`.
 *
 * La ranura `plantilla:acciones` se monta mediante el anfitrión de pruebas con
 * `window.__LOPDP_DESCARGA_PRUEBAS__`.
 *
 * SEC-19: el archivo se pide con la sesión (`Authorization`) y se guarda con `nombre_archivo`. Criterios
 * de UX/UI (a) 401, (b) 403 de token inválido, (c) 403 de otra sesión, (d) doble clic.
 * MUTACIÓN M4: volver al `<a href>` directo en `lib/biblioteca/descargas.ts` hace fallar «la petición
 * al archivo lleva la sesión», porque la navegación no envía `Authorization`.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";
import { CLAVE_SESION, credencialSimulada, fijarAjustes, sembrarSesion } from "../auth/utilesAuth";

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

    await page.route("**/api/v1/biblioteca/descargas/**", (route) =>
      route.fulfill({ status: 200, contentType: "application/octet-stream", body: "contenido" }));
    await boton.click();
    expect(peticionHecha).toBe(true);

    const estado = contenedor.getByTestId("estado-descarga-exitosa");
    await expect(estado).toBeVisible();
    await expect(estado).toContainText("Archivo descargado: BIB-001_v1.0.0_politica.docx");
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

    // La alerta de la descarga, no cualquier `role="alert"`: el anfitrión también monta el botón
    // «Usar plantilla», que avisa por su cuenta si la ficha no se pudo cargar (CI-16).
    const alerta = contenedor.getByTestId("error-descarga");
    await expect(alerta).toHaveAttribute("role", "alert");
    await expect(alerta).toBeVisible();
    await expect(alerta).toContainText("Solo se pueden descargar versiones publicadas.");
  });
});

// --------------------------------------------------------------------------- SEC-19, con sesión OIDC

const ARCHIVO = `**/api/v1/biblioteca/descargas/${PLANTILLA_DOCX}/archivo*`;
const POST_DESCARGA = `**/api/v1/biblioteca/plantillas/${PLANTILLA_DOCX}/descargar`;

/** Sesión OIDC simulada y API simulada; devuelve la credencial y el contador de peticiones POST. */
async function prepararOidc(page: Page) {
  const credencial = credencialSimulada({ email: "ana@correo.invalid" });
  await fijarAjustes(page, { modo: "oidc", tenant: ORGANIZACION });
  await sembrarSesion(page, credencial);
  await page.addInitScript(({ id, tenant }) => {
    window.__LOPDP_DESCARGA_PRUEBAS__ = { plantillaId: id };
    sessionStorage.setItem("lopdp-organizacion-activa-v1",
      JSON.stringify({ tenant_id: tenant, nombre_comercial: "Entidad SEC-19", roles: ["implementador"] }));
  }, { id: PLANTILLA_DOCX, tenant: ORGANIZACION });
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { roles: [{ role: "implementador", area_id: null, area_nombre: null, valid_to: null }] } }));
  const cuenta = { post: 0 };
  await page.route(POST_DESCARGA, (route) => { cuenta.post++; return route.fulfill({ json: RESPUESTA_DESCARGA }); });
  return { credencial, cuenta };
}

const error403 = (code: string) => ({ status: 403, json: { code, detail: "texto del servidor que no se muestra" } });
const archivoOk = { status: 200, contentType: "application/octet-stream", body: "PK contenido" };

test.describe("Biblioteca: descarga con sesión (SEC-19, API simulada)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "Los ganchos de prueba no existen en producción.");
  });

  test("la petición al archivo lleva la sesión y se guarda con nombre_archivo", async ({ page }) => {
    const { credencial } = await prepararOidc(page);
    let autorizacion: string | undefined;
    await page.route(ARCHIVO, (route) => {
      autorizacion = route.request().headers()["authorization"];
      return route.fulfill(archivoOk);
    });
    const contenedor = await abrirDescargas(page);
    const descarga = page.waitForEvent("download");
    await contenedor.getByTestId("boton-descargar-plantilla").click();
    expect((await descarga).suggestedFilename()).toBe(RESPUESTA_DESCARGA.nombre_archivo);
    expect(autorizacion).toBe(`Bearer ${credencial.token}`);
    await expect(contenedor.getByTestId("estado-descarga-exitosa")).toContainText("Archivo descargado");
  });

  test("(a) un 401 activa el manejo global de sesión caducada y no muestra el aviso de éxito ni error-descarga", async ({ page }) => {
    await prepararOidc(page);
    await page.route(ARCHIVO, (route) => route.fulfill({ status: 401, json: { detail: "Sesión caducada" } }));
    const contenedor = await abrirDescargas(page);
    await contenedor.getByTestId("boton-descargar-plantilla").click();
    await expect(page).toHaveURL(/\/login\?motivo=expirada/);
    await expect(page.getByTestId("estado-descarga-exitosa")).toHaveCount(0);
    await expect(page.getByTestId("error-descarga")).toHaveCount(0);
  });

  test("(b) un token inválido se reintenta una vez en silencio y luego muestra el mensaje con «Reintentar descarga»", async ({ page }) => {
    const { cuenta } = await prepararOidc(page);
    await page.route(ARCHIVO, (route) => route.fulfill(error403("BIB_TOKEN_DESCARGA_INVALIDO")));
    const contenedor = await abrirDescargas(page);
    await contenedor.getByTestId("boton-descargar-plantilla").click();
    const alerta = contenedor.getByTestId("error-descarga");
    await expect(alerta).toHaveAttribute("data-codigo", "BIB_TOKEN_DESCARGA_INVALIDO");
    await expect(alerta).toContainText("No pudimos preparar la descarga. Inténtalo de nuevo.");
    await expect(alerta).not.toContainText("texto del servidor");
    expect(cuenta.post).toBe(2);
    await expect(alerta.getByRole("button", { name: "Reintentar descarga" })).toBeFocused();
    await expect(contenedor.getByTestId("estado-descarga-exitosa")).toHaveCount(0);
  });

  test("(b) si el reintento silencioso funciona, no se muestra ningún error", async ({ page }) => {
    await prepararOidc(page);
    let llamadas = 0;
    await page.route(ARCHIVO, (route) =>
      route.fulfill(++llamadas === 1 ? error403("BIB_TOKEN_DESCARGA_INVALIDO") : archivoOk));
    const contenedor = await abrirDescargas(page);
    await contenedor.getByTestId("boton-descargar-plantilla").click();
    await expect(contenedor.getByTestId("estado-descarga-exitosa")).toBeVisible();
    await expect(contenedor.getByTestId("error-descarga")).toHaveCount(0);
  });

  test("(c) un token de otra sesión muestra el mensaje sin cerrar la sesión", async ({ page }) => {
    const { cuenta } = await prepararOidc(page);
    await page.route(ARCHIVO, (route) => route.fulfill(error403("BIB_TOKEN_DE_OTRA_PERSONA")));
    const contenedor = await abrirDescargas(page);
    await contenedor.getByTestId("boton-descargar-plantilla").click();
    const alerta = contenedor.getByTestId("error-descarga");
    await expect(alerta).toHaveAttribute("data-codigo", "BIB_TOKEN_DE_OTRA_PERSONA");
    await expect(alerta).toContainText("La descarga se pidió con otra sesión. Vuelve a pedirla desde aquí.");
    expect(cuenta.post).toBe(1);
    await expect(alerta.getByRole("button", { name: "Reintentar descarga" })).toBeFocused();
    expect(page.url()).not.toContain("/login");
    expect(await page.evaluate((c) => sessionStorage.getItem(c), CLAVE_SESION)).not.toBeNull();
  });

  test("(d) un doble clic pide una sola descarga y el botón queda ocupado mientras tanto", async ({ page }) => {
    const { cuenta } = await prepararOidc(page);
    let soltar: () => void = () => {};
    const espera = new Promise<void>((r) => { soltar = r; });
    await page.route(ARCHIVO, async (route) => {
      await espera;
      await route.fulfill(archivoOk);
    });
    const contenedor = await abrirDescargas(page);
    const boton = contenedor.getByTestId("boton-descargar-plantilla");
    await boton.dblclick();
    await expect(boton).toHaveAttribute("aria-busy", "true");
    soltar();
    await expect(contenedor.getByTestId("estado-descarga-exitosa")).toBeVisible();
    await expect(boton).toHaveAttribute("aria-busy", "false");
    expect(cuenta.post).toBe(1);
  });

  test("otros errores del archivo muestran el mensaje genérico", async ({ page }) => {
    await prepararOidc(page);
    await page.route(ARCHIVO, (route) => route.fulfill({ status: 500, json: { detail: "texto interno" } }));
    const contenedor = await abrirDescargas(page);
    await contenedor.getByTestId("boton-descargar-plantilla").click();
    const alerta = contenedor.getByTestId("error-descarga");
    await expect(alerta).toContainText("No se pudo descargar la plantilla. Inténtalo de nuevo.");
    await expect(alerta).not.toContainText("texto interno");
    await expect(alerta.getByRole("button", { name: "Reintentar descarga" })).toHaveCount(0);
  });
});
