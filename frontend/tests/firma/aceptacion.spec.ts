/**
 * Playwright: página pública /aceptar/<token> (FIRMA-02).
 *
 * Casos:
 * - Al pulsar «Acepto» el servidor registra la aceptación, la página muestra el acuse
 *   y el enlace deja de funcionar (410).
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const BASE = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3000";

/* Token ficticio para pruebas de interfaz sin base de datos real.
   El servidor de desarrollo devuelve respuestas mockeadas si FIRMA02_MOCK=true. */
const TOKEN_VIGENTE = process.env.FIRMA02_TOKEN_VIGENTE ?? "test-token-vigente-placeholder";
const TOKEN_CADUCADO = process.env.FIRMA02_TOKEN_CADUCADO ?? "test-token-caducado-placeholder";

test.describe("Página /aceptar/<token>", () => {
  test("muestra información del documento para un enlace vigente", async ({ page }) => {
    await page.route(`**/api/v1/aceptar/${TOKEN_VIGENTE}`, (route) =>
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          nombre_documento: "Política de Privacidad v2.0",
          organizacion: "Empresa Demo SA",
          sha256: "a".repeat(64),
        }),
      }),
    );

    await page.goto(`${BASE}/aceptar/${TOKEN_VIGENTE}`);

    await expect(page.getByText("Política de Privacidad v2.0")).toBeVisible();
    await expect(page.getByText("Empresa Demo SA")).toBeVisible();
    await expect(page.getByTestId("btn-acepto")).toBeVisible();
  });

  test("al pulsar Acepto muestra el acuse y el enlace deja de funcionar", async ({ page }) => {
    let llamadas = 0;

    // Primera GET: enlace vigente.
    await page.route(`**/api/v1/aceptar/${TOKEN_VIGENTE}`, async (route) => {
      llamadas++;
      if (llamadas === 1) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            nombre_documento: "Política de Privacidad v2.0",
            organizacion: "Empresa Demo SA",
            sha256: "a".repeat(64),
          }),
        });
      } else {
        // Segunda llamada GET después de aceptar → 410.
        await route.fulfill({
          status: 410,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Enlace ya utilizado", code: "ACEPTACION_CADUCADA" }),
        });
      }
    });

    // POST: registrar aceptación.
    await page.route(`**/api/v1/aceptar/${TOKEN_VIGENTE}`, async (route) => {
      if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ acuse_sha256: "f".repeat(64) }),
        });
      } else {
        await route.fallback();
      }
    });

    await page.goto(`${BASE}/aceptar/${TOKEN_VIGENTE}`);
    await expect(page.getByTestId("btn-acepto")).toBeVisible();

    await page.getByTestId("btn-acepto").click();

    // El acuse aparece.
    await expect(page.getByTestId("acuse-ok")).toBeVisible();
    await expect(page.getByTestId("acuse-sha256")).toContainText("f".repeat(64));

    // El botón ya no está.
    await expect(page.getByTestId("btn-acepto")).not.toBeVisible();
  });

  test("un enlace caducado muestra el mensaje de enlace no disponible", async ({ page }) => {
    await page.route(`**/api/v1/aceptar/${TOKEN_CADUCADO}`, (route) =>
      route.fulfill({
        status: 410,
        contentType: "application/json",
        body: JSON.stringify({ detail: "El enlace de aceptación ha caducado.", code: "ACEPTACION_CADUCADA" }),
      }),
    );

    await page.goto(`${BASE}/aceptar/${TOKEN_CADUCADO}`);

    await expect(page.getByTestId("enlace-caducado")).toBeVisible();
    await expect(page.getByTestId("btn-acepto")).not.toBeVisible();
  });
});

/** Hoy en ISO, desplazado en días: caducidades y aceptaciones de ejemplo. */
const enDias = (dias: number) => new Date(Date.now() + dias * 86_400_000).toISOString();

const ENVIOS = [
  { id: "1", documento_id: "doc-politica", documento_sha256: "a".repeat(64), persona_id: "p1", nombre: "Ana Pérez",
    email: "ana@demo.test", caduca_en: enDias(5), aceptado_en: null, ip: null, acuse_sha256: null, creado_en: enDias(-2) },
  { id: "2", documento_id: "doc-politica", documento_sha256: "a".repeat(64), persona_id: "p2", nombre: "Luis Mora",
    email: "luis@demo.test", caduca_en: enDias(5), aceptado_en: enDias(-1), ip: "10.0.0.2", acuse_sha256: "b".repeat(64), creado_en: enDias(-2) },
  { id: "3", documento_id: "doc-politica", documento_sha256: "a".repeat(64), persona_id: "p3", nombre: "Eva Ruiz",
    email: "eva@demo.test", caduca_en: enDias(-3), aceptado_en: null, ip: null, acuse_sha256: null, creado_en: enDias(-9) },
];

async function abrirDesdeMenu(page: Page, menu: string, submenu: string) {
  await barraDeMenus(page).getByRole("button", { name: menu, exact: true }).click();
  await page.getByRole("group", { name: `Submenús de ${menu}` }).getByRole("button", { name: new RegExp(`^${submenu}`) }).click();
}

async function prepararPanel(page: Page, rol: string) {
  const posts: unknown[] = [];
  // El alta de la ficha se hace con la API caída, como en menus.spec; las respuestas reales
  // se registran después (la última ruta registrada es la que atiende).
  await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad FIRMA-02");
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    const ruta = new URL(peticion.url()).pathname.replace("/api/v1", "");
    const json = (status: number, body: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });
    if (ruta === "/organizacion/me/roles") {
      return json(200, { roles: [{ role: rol, area_id: null, area_nombre: null, valid_to: null }] });
    }
    if (ruta === "/firma/aceptaciones" && peticion.method() === "GET") return json(200, { aceptaciones: ENVIOS });
    if (ruta === "/firma/aceptaciones" && peticion.method() === "POST") {
      posts.push({ cabeceras: peticion.headers(), cuerpo: peticion.postDataJSON() });
      return json(201, { enlaces: [{ persona_id: "p9", url: "/aceptar/tok-p9" }] });
    }
    if (ruta === "/firma/verificar") return json(200, { coincide: false, tipo: null });
    return json(503, { detail: "API simulada" });
  });
  return posts;
}

test.describe("Firmas y Verificar documento en el panel (FIRMA-02)", () => {
  test("Biblioteca › Firmas lista los envíos con su estado y permite enviar", async ({ page }) => {
    const posts = await prepararPanel(page, "coordinador");
    await abrirDesdeMenu(page, "Biblioteca", "Firmas");

    const tabla = page.getByTestId("tabla-envios").locator("tbody");
    await expect(tabla.getByText("Pendiente")).toHaveCount(1);
    await expect(tabla.getByText("Aceptado")).toHaveCount(1);
    await expect(tabla.getByText("Caducado")).toHaveCount(1);

    await page.getByTestId("btn-enviar-aceptacion").click();
    await page.getByLabel("Documento", { exact: true }).fill("doc-politica");
    await page.getByLabel(/^Personas/).fill("p9");
    await page.getByRole("button", { name: "Generar enlaces" }).click();

    await expect(page.getByTestId("enlaces-generados")).toContainText("/aceptar/tok-p9");
    expect(posts).toHaveLength(1);
    const { cabeceras, cuerpo } = posts[0] as { cabeceras: Record<string, string>; cuerpo: unknown };
    expect(cuerpo).toEqual({ documento_id: "doc-politica", persona_ids: ["p9"], dias_vigencia: 7 });
    // Las rutas autenticadas exigen el rol con el que se actúa.
    expect(cabeceras["x-role"]).toBe("coordinador");
  });

  test("sin rol de envío no aparece el botón «Enviar a aceptación»", async ({ page }) => {
    await prepararPanel(page, "dpo");
    await abrirDesdeMenu(page, "Biblioteca", "Firmas");
    await expect(page.getByTestId("tabla-envios")).toBeVisible();
    await expect(page.getByTestId("btn-enviar-aceptacion")).toHaveCount(0);
  });

  test("Configuración › Verificar documento muestra «No coincide» para un archivo ajeno", async ({ page }) => {
    await prepararPanel(page, "coordinador");
    await abrirDesdeMenu(page, "Configuración", "Verificar documento");

    await page.locator('input[type="file"]').setInputFiles({
      name: "ajeno.pdf", mimeType: "application/pdf", buffer: Buffer.from("no es un documento aprobado"),
    });
    await expect(page.getByTestId("resultado-verificacion")).toContainText("No coincide");
  });
});
