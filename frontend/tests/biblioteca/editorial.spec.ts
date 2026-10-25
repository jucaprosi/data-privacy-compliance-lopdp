// ¤adpa
// ¤¤developer-architect
import { expect, test, type Page } from "@playwright/test";

const ruta = "/harness-biblioteca/editorial";
const version = { id: "sintetica", codigo: "TEST-01", version: "1.0", formato: "DOCX", ficha: null,
  responsable_id: "editor", autores: ["editor"], estado: "en_revision", generacion: 1,
  sha256: null, nombre_archivo: null, sustituye_id: null, creada_en: "2026-10-25T12:00:00Z" };

async function listado(page: Page, capacidades: string[], actor = "editor", completa = false) {
  const v = completa ? { ...version, sha256: "a".repeat(64), nombre_archivo: "prueba.docx",
    ficha: { nombre: "Maestro prueba", objetivo: "Prueba", fuentes: "Prueba", fecha_revision: "2026-10-25",
      instrucciones: "Prueba", dependencias: "Ninguna", restricciones: "Solo prueba" } } : version;
  await page.route("**/api/v1/biblioteca/editorial", route => route.fulfill({ json: {
    actor_id: actor, capacidades, versiones: [v], revisiones: [],
  } }));
}

test.describe("Interfaz editorial con API simulada (no acredita persistencia/RLS)", () => {
  test.skip(!!process.env.BIB105_REAL_API, "La aceptación real se ejecuta por separado");

  test("sin capacidad muestra denegación y no ofrece publicación", async ({ page }) => {
    await page.route("**/api/v1/biblioteca/editorial", route => route.fulfill({ status: 403,
      json: { code: "BIB_SIN_CAPACIDAD", detail: "No tienes capacidad editorial asignada." } }));
    await page.goto(ruta);
    await expect(page.getByRole("alert")).toContainText("No tienes capacidad editorial");
    await expect(page.getByRole("button", { name: "Publicar versión" })).toHaveCount(0);
  });

  test("editor crea siempre en revisión y no revisa su propia versión", async ({ page }) => {
    await listado(page, ["editor", "revisor_tecnico", "publicador"]);
    let enviada: Record<string, unknown> = {};
    await page.route("**/api/v1/biblioteca/editorial/versiones", async route => {
      enviada = route.request().postDataJSON();
      await route.fulfill({ status: 201, json: version });
    });
    await page.goto(ruta);
    await page.getByLabel("Código", { exact: true }).fill("TEST-01");
    await page.getByLabel("Versión nueva").fill("1.0");
    await page.getByRole("button", { name: "Crear versión en revisión" }).click();
    await expect(page.getByRole("status")).toContainText("no está publicada");
    expect(enviada).toEqual({ codigo: "TEST-01", version: "1.0", formato: "DOCX", sustituye_id: null });
    await expect(page.getByRole("button", { name: "Publicar versión" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Registrar revisión técnica" })).toHaveCount(0);
  });

  test("publicador ve faltantes y publicación deshabilitada sin revisiones", async ({ page }) => {
    await listado(page, ["publicador"], "publicador", true);
    await page.goto(ruta);
    await page.getByRole("button", { name: /TEST-01 · 1.0/ }).click();
    await page.getByLabel("Motivo de la decisión").fill("Prueba");
    await expect(page.getByRole("button", { name: "Publicar versión" })).toBeDisabled();
    await expect(page.getByText(/Publicación pendiente:/)).toBeVisible();
  });

  test("dictamen usa API y presenta el error real sin simular éxito", async ({ page }) => {
    await listado(page, ["revisor_tecnico"], "tecnico");
    await page.route("**/api/v1/biblioteca/editorial/versiones/sintetica/revisiones", route => route.fulfill({
      status: 409, json: { code: "BIB_CONFLICTO_VERSION", detail: "La versión cambió; actualiza el listado." },
    }));
    await page.goto(ruta);
    await page.getByRole("button", { name: /TEST-01 · 1.0/ }).click();
    await page.getByLabel("Dictamen", { exact: true }).fill("Revisado");
    await page.getByRole("button", { name: "Registrar revisión técnica" }).click();
    await expect(page.getByRole("alert")).toContainText("La versión cambió");
    await expect(page.getByText("Dictamen registrado.", { exact: true })).toHaveCount(0);
  });

  test("archivo y ficha guardan datos reales por el cliente HTTP", async ({ page }) => {
    await listado(page, ["editor"]);
    let subida = false;
    await page.route("**/api/v1/biblioteca/editorial/versiones/sintetica/archivo", async route => {
      const cuerpo = route.request().postDataJSON();
      subida = cuerpo.generacion === 1 && cuerpo.nombre === "prueba.docx" && !!cuerpo.contenido_base64;
      await route.fulfill({ json: { ...version, generacion: 2 } });
    });
    await page.goto(ruta);
    await page.getByRole("button", { name: /TEST-01 · 1.0/ }).click();
    await page.getByLabel("Archivo maestro (máximo 10 MB)").setInputFiles({
      name: "prueba.docx", mimeType: "application/octet-stream", buffer: Buffer.from("fixture de cliente HTTP"),
    });
    await page.getByRole("button", { name: "Guardar archivo maestro" }).click();
    await expect(page.getByRole("status")).toContainText("Archivo guardado");
    expect(subida).toBe(true);
  });
});

test.describe("Aceptación contra backend real", () => {
  test.skip(!process.env.BIB105_REAL_API, "Pendiente de backend y rama Neon propia; sin simulación de API");
  test("sin asignación editorial deniega acceso", async ({ page }) => {
  // Sin page.route: atraviesa proxy, autenticación, servicio y base real.
  await page.goto(ruta);
  await expect(page.getByRole("alert")).toContainText(/capacidad editorial|identifica|autentic/i);
  await expect(page.getByRole("button", { name: "Crear versión en revisión" })).toHaveCount(0);
});
});
