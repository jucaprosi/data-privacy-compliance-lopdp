// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤cita-verificada ¤arbitro
// ¤¤qa-engineer
/**
 * BIB-408 · Pantalla editorial de versiones Markdown (governance/especificaciones/BIB-408.md). API simulada: comprueba lo que
 * muestra y pide la pantalla; la autorización y la persistencia las prueban los árbitros del servidor.
 *
 * Mutaciones (cada una hace fallar la prueba indicada):
 *   - m1: mostrar `en_revision` en la lista            -> «la lista muestra los cuatro estados con su texto y la autoría de la IA»;
 *   - m2: habilitar «Aprobar y publicar» con una cita sin verificar -> «con una cita sin verificar …»;
 *   - m3: volver al texto fijo de la l. 114            -> «no existe «Registrar revisión jurídica» …»;
 *   - m4: quitar la leyenda del catálogo               -> «el catálogo muestra la leyenda …»;
 *   - m5: dejar «Proponer cambio» habilitado con una propuesta en revisión -> «con una propuesta en revisión …».
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ruta = "/harness-biblioteca/editorial";
const CONFLICTO = "Ya hay una propuesta de la IA en revisión para esta plantilla. Apruébala, devuélvela o descártala antes de pedir otra.";
const LEYENDA = "Redactada con IA y aprobada por Ana Pérez el 25 de noviembre de 2026.";
const FICHA = { nombre: "Política de protección de datos", objetivo: "Prueba", fuentes: "LOPDP", fecha_revision: "2026-11-01",
  instrucciones: "Prueba", dependencias: "Ninguna", restricciones: "Solo prueba" };
const base = { ficha: FICHA, responsable_id: "u-ana", autores: ["u-luis"], generacion: 1, sha256: "a".repeat(64),
  nombre_archivo: null, sustituye_id: null, creada_en: "2026-11-25T12:00:00Z", redactada_por: "persona", solicitante_nombre: "Luis Mora" };
const ia = { ...base, formato: "MD", autores: ["ia"], redactada_por: "ia", modelo_ia: "modelo-de-prueba", origen_ia: "peticion",
  motivo_ia: "Revisar el plazo de respuesta", solicitante_nombre: "Ana Pérez", cambios_ia: [] };

const publicada = { ...base, id: "v-pub", codigo: "BIB-001", version: "1.0", formato: "MD", estado: "publicada",
  leyenda: { redaccion: "ia", aprobada_por: "Ana Pérez", aprobada_en: "25 de noviembre de 2026", texto: LEYENDA } };
const propuesta = { ...ia, id: "v-prop", codigo: "BIB-001", version: "1.1", estado: "en_revision", leyenda: null };
const devuelta = { ...ia, ficha: { ...FICHA, nombre: "Aviso de privacidad" }, id: "v-dev", codigo: "BIB-002", version: "1.1", estado: "en_revision", leyenda: null };
const descartada = { ...ia, ficha: { ...FICHA, nombre: "Política de cookies" }, id: "v-desc", codigo: "BIB-003", version: "1.1", estado: "retirada", nota_descarte: "No aplica", leyenda: null };
const manual = { ...base, id: "v-man", codigo: "BIB-004", version: "2.0", formato: "DOCX", estado: "en_revision", sha256: null,
  ficha: null, leyenda: null, nombre_archivo: null };
const revisiones = [{ version_id: "v-dev", generacion: 1, tipo: "tecnica", aprobado: false, revisor_id: "u-ana",
  comentario: "Falta el artículo", creada_en: "2026-11-25T15:00:00Z" }];

const cita = (verificada: boolean) => ({ clave: "c1", norma: "LOPDP", articulo: "Art. 12", verificada,
  url: verificada ? "https://www.finanzaspopulares.gob.ec/lopdp" : null, fecha_vigencia: verificada ? "2026-05-26" : null });
const comparacion = (verificada: boolean) => ({ primera_version: false, secciones: [
  { titulo: "Plazo", cambiada: true, cambios: [{ antes: "treinta días", despues: "quince días", cita: cita(verificada) }] },
  { titulo: "Alcance", cambiada: false, cambios: [] }, { titulo: "Definiciones", cambiada: false, cambios: [] }] });

async function abrir(page: Page, capacidades: string[], versiones: unknown[], opciones: { verificada?: boolean; actor?: string } = {}) {
  await page.route("**/api/v1/biblioteca/editorial", route => route.fulfill({ json: {
    actor_id: opciones.actor ?? "u-ana", capacidades, versiones, revisiones } }));
  await page.route("**/api/v1/biblioteca/editorial/versiones/*/comparacion", route => route.fulfill({ json: comparacion(opciones.verificada ?? true) }));
  await page.goto(ruta);
}
const todas = ["editor", "revisor_tecnico", "publicador"];
const principal = (page: Page) => page.getByRole("main", { name: "Administración editorial" });

test.describe("Pantalla editorial de versiones Markdown (BIB-408, API simulada)", () => {
  test("la lista muestra los cuatro estados con su texto y la autoría de la IA", async ({ page }) => {
    await abrir(page, todas, [publicada, propuesta, devuelta, descartada]);
    const tabla = page.getByRole("table", { name: "Versiones de Política de protección de datos" });
    await expect(tabla.getByRole("columnheader")).toHaveText(["Versión", "Formato", "Estado", "Autoría", "Origen", "Fecha"]);
    await expect(tabla.getByRole("row", { name: /1\.0/ })).toContainText("Publicada");
    await expect(tabla.getByRole("row", { name: /1\.1/ })).toContainText("En revisión");
    await expect(tabla.getByRole("row", { name: /1\.1/ })).toContainText("Redactada por la IA");
    await expect(page.getByRole("table", { name: "Versiones de Aviso de privacidad" }).getByRole("row", { name: /1\.1/ })).toContainText("Devuelta con observaciones");
    await expect(page.getByRole("table", { name: "Versiones de Política de cookies" }).getByRole("row", { name: /1\.1/ })).toContainText("Descartada");
    await expect(tabla.getByRole("row", { name: /1\.0/ })).toContainText("Markdown");
    await expect(principal(page)).not.toContainText(/en_revision|retirada|sustituida|\bia\b|peticion|resolucion/);
  });

  test("con una cita sin verificar «Aprobar y publicar» lleva aria-disabled y la comparación muestra el texto y su cita", async ({ page }) => {
    await abrir(page, todas, [publicada, propuesta], { verificada: false });
    await page.getByRole("button", { name: "BIB-001 · 1.1" }).click();
    await expect(page.getByRole("heading", { name: "Versión 1.1 · En revisión" })).toBeVisible();
    await expect(page.getByRole("note").filter({ hasText: "La redactó la IA. Revisa cada cambio y su cita antes de aprobarla." })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Origen de esta versión" })).toBeVisible();
    await expect(page.getByText("Modelo: modelo-de-prueba")).toBeVisible();
    await expect(page.getByText("A partir de: petición de Ana Pérez, «Revisar el plazo de respuesta»")).toBeVisible();
    await expect(page.getByRole("heading", { name: "Plazo" })).toBeVisible();
    await expect(page.getByText("Texto actual")).toBeVisible();
    await expect(page.getByText("Texto propuesto")).toBeVisible();
    await expect(page.locator("del")).toHaveText("treinta días");
    await expect(page.locator("ins")).toHaveText("quince días");
    await expect(page.getByText("Cita sin verificar", { exact: true })).toBeVisible();
    await expect(page.getByText("2 secciones sin cambios")).toBeVisible();
    const aprobar = page.getByRole("button", { name: "Aprobar y publicar" });
    await expect(aprobar).toHaveAttribute("aria-disabled", "true");
    await expect(aprobar).toHaveAccessibleDescription("Hay citas sin verificar.");
    await expect(page.getByText("Publicación pendiente: falta que las citas estén verificadas.")).toBeVisible();
    await aprobar.click({ force: true });
    await expect(page.getByRole("dialog")).toHaveCount(0);
  });

  test("con la cita verificada muestra su motivo con enlace y «Aprobar y publicar» está disponible", async ({ page }) => {
    await abrir(page, todas, [publicada, propuesta]);
    await page.getByRole("button", { name: "BIB-001 · 1.1" }).click();
    await expect(page.getByText("Motivo: LOPDP, Art. 12 · entra en vigencia el 26 de mayo de 2026")).toBeVisible();
    await expect(page.getByRole("link", { name: "LOPDP, Art. 12" })).toHaveAttribute("href", /^https:/);
    await expect(page.getByRole("button", { name: "Aprobar y publicar" })).not.toHaveAttribute("aria-disabled", "true");
    await expect(page.getByText(/Publicación pendiente/)).toHaveCount(0);
  });

  test("no existe «Registrar revisión jurídica» y el aviso de pendiente enumera solo lo que falta", async ({ page }) => {
    await abrir(page, todas, [manual], { actor: "u-otra" });
    await page.getByRole("button", { name: "BIB-004 · 2.0" }).click();
    await expect(page.getByRole("button", { name: "Registrar revisión jurídica" })).toHaveCount(0);
    await expect(page.getByText("Publicación pendiente: falta el archivo, la ficha y una revisión técnica aprobada.")).toBeVisible();
    await expect(page.getByText(/completa archivo, ficha/)).toHaveCount(0);
  });

  test("el aviso omite lo que ya está y nombra las revisiones sin texto de otra época", async ({ page }) => {
    await abrir(page, todas, [{ ...manual, sha256: "b".repeat(64), nombre_archivo: "a.docx", ficha: FICHA }], { actor: "u-otra" });
    await page.getByRole("button", { name: "BIB-004 · 2.0" }).click();
    await expect(page.getByText("Publicación pendiente: falta una revisión técnica aprobada.")).toBeVisible();
    await expect(page.getByText(/jurídica/i)).toHaveCount(0);
  });

  test("lo cargado a mano muestra la separación de funciones como botones con aria-disabled y su motivo", async ({ page }) => {
    await abrir(page, todas, [{ ...manual, autores: ["u-otra"] }], { actor: "u-otra" });
    await page.getByRole("button", { name: "BIB-004 · 2.0" }).click();
    const revisar = page.getByRole("button", { name: "Registrar revisión técnica" });
    await expect(revisar).toHaveAttribute("aria-disabled", "true");
    await expect(revisar).toHaveAccessibleDescription("No puedes revisar una versión de la que tienes la autoría.");
    const publicar = page.getByRole("button", { name: "Publicar versión" });
    await expect(publicar).toHaveAccessibleDescription("No puedes publicar una versión de la que tienes la autoría.");
  });

  test("sin permisos, los botones nombran el permiso que falta", async ({ page }) => {
    await abrir(page, ["editor"], [{ ...manual, ficha: FICHA, sha256: "b".repeat(64) }], { actor: "u-otra" });
    await page.getByRole("button", { name: "BIB-004 · 2.0" }).click();
    await expect(page.getByRole("button", { name: "Registrar revisión técnica" })).toHaveAccessibleDescription("Necesitas el permiso de revisión técnica.");
    await expect(page.getByRole("button", { name: "Publicar versión" })).toHaveAccessibleDescription("Necesitas el permiso de publicación.");
  });

  test("con una propuesta en revisión «Proponer cambio» lleva aria-disabled con el texto del conflicto y el enlace al detalle", async ({ page }) => {
    await abrir(page, todas, [publicada, propuesta, { ...publicada, id: "v-otra", codigo: "BIB-005", ficha: { ...FICHA, nombre: "Otra" }, leyenda: null }]);
    const proponer = page.getByRole("listitem").filter({ hasText: "Versiones de Política de protección de datos" }).getByRole("button", { name: "Proponer cambio" });
    await expect(proponer).toHaveAttribute("aria-disabled", "true");
    await expect(proponer).toHaveAccessibleDescription(CONFLICTO);
    await expect(page.getByText(CONFLICTO)).toBeVisible();
    await proponer.click({ force: true });
    await expect(page.getByRole("dialog")).toHaveCount(0);
    await page.getByRole("link", { name: "Ver la propuesta en revisión" }).click();
    await expect(page.getByRole("heading", { name: "Versión 1.1 · En revisión" })).toBeVisible();
  });

  test("«Proponer cambio» abre su diálogo con foco en Cancelar, cierra con Escape y no muestra ningún límite de uso", async ({ page }) => {
    await abrir(page, todas, [publicada]);
    await page.getByRole("button", { name: "Proponer cambio" }).click();
    const dialogo = page.getByRole("dialog");
    await expect(dialogo.getByRole("heading", { name: "Pedir una propuesta a la IA" })).toBeVisible();
    await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
    await expect(dialogo).toContainText("La IA redactará una versión nueva, con la cita de cada cambio, y quedará en revisión. Tu nombre quedará en su origen.");
    await expect(dialogo.getByLabel("Qué quieres que revise")).not.toHaveAttribute("required", "");
    await expect(dialogo).not.toContainText(/límite|tope|cuota|consumo|solicitudes restantes/i);
    await page.keyboard.press("Escape");
    await expect(dialogo).toHaveCount(0);
  });

  for (const [resultado, cuerpo, texto, rol] of [
    ["creada", { resultado: "creada", versiones: [], omitidas: [] }, "Propuesta lista para revisar.", "status"],
    ["sin cambios", { resultado: "sin_cambios", versiones: [], omitidas: [] }, "La IA no encontró cambios necesarios en esta plantilla.", "status"],
    ["conflicto", { resultado: "propuesta_en_revision", versiones: [], omitidas: [] }, CONFLICTO, "alert"],
  ] as const) {
    test(`proponer un cambio: ${resultado}`, async ({ page }) => {
      await abrir(page, todas, [publicada]);
      let enviada: Record<string, unknown> = {};
      await page.route("**/api/v1/biblioteca/editorial/propuestas", async route => {
        enviada = route.request().postDataJSON(); await route.fulfill({ status: 202, json: cuerpo });
      });
      await page.getByRole("button", { name: "Proponer cambio" }).click();
      await page.getByLabel("Qué quieres que revise").fill("Revisar el plazo");
      await page.getByRole("button", { name: "Pedir propuesta" }).click();
      await expect(page.getByRole("dialog").getByRole(rol).filter({ hasText: texto })).toBeVisible();
      expect(enviada).toEqual({ codigo: "BIB-001", motivo: "Revisar el plazo" });
    });
  }

  test("proponer un cambio: el servidor falla", async ({ page }) => {
    await abrir(page, todas, [publicada]);
    await page.route("**/api/v1/biblioteca/editorial/propuestas", route => route.fulfill({ status: 500, json: { detail: "interno" } }));
    await page.getByRole("button", { name: "Proponer cambio" }).click();
    await page.getByRole("button", { name: "Pedir propuesta" }).click();
    await expect(page.getByRole("dialog").getByRole("alert")).toHaveText("No pudimos preparar la propuesta. Inténtalo de nuevo más tarde.");
  });

  test("«Aprobar y publicar» registra la revisión técnica y la publicación en un paso", async ({ page }) => {
    await abrir(page, todas, [publicada, propuesta]);
    const llamadas: string[] = [];
    await page.route("**/api/v1/biblioteca/editorial/versiones/v-prop/revisiones", async route => {
      llamadas.push("revisiones"); await route.fulfill({ status: 201, json: propuesta });
    });
    await page.route("**/api/v1/biblioteca/editorial/versiones/v-prop/publicar", async route => {
      llamadas.push("publicar"); await route.fulfill({ json: { ...propuesta, estado: "publicada" } });
    });
    await page.getByRole("button", { name: "BIB-001 · 1.1" }).click();
    await page.getByRole("button", { name: "Aprobar y publicar" }).click();
    const dialogo = page.getByRole("dialog");
    await expect(dialogo.getByRole("heading", { name: "Aprobar y publicar esta versión" })).toBeVisible();
    await expect(dialogo).toContainText("Se publicará en el catálogo y sustituirá a la versión 1.0 publicada. Quedará registrado que la aprobaste.");
    await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
    await dialogo.getByRole("button", { name: "Aprobar y publicar" }).click();
    await expect(dialogo.getByRole("status")).toHaveText("Versión publicada.");
    expect(llamadas).toEqual(["revisiones", "publicar"]);
  });

  test("«Devolver con observaciones» exige las observaciones y «Descartar» exige el motivo", async ({ page }) => {
    await abrir(page, todas, [publicada, propuesta]);
    let devuelta: Record<string, unknown> = {};
    let descartada: Record<string, unknown> = {};
    await page.route("**/api/v1/biblioteca/editorial/versiones/v-prop/revisiones", async route => {
      devuelta = route.request().postDataJSON(); await route.fulfill({ status: 201, json: propuesta });
    });
    await page.route("**/api/v1/biblioteca/editorial/versiones/v-prop/descartar", async route => {
      descartada = route.request().postDataJSON(); await route.fulfill({ json: { ...propuesta, estado: "retirada" } });
    });
    await page.getByRole("button", { name: "BIB-001 · 1.1" }).click();
    await page.getByRole("button", { name: "Devolver con observaciones" }).click();
    const dialogo = page.getByRole("dialog");
    await expect(dialogo).toContainText("La versión vuelve con tus observaciones. Para corregirla, pide una propuesta nueva con «Proponer cambio».");
    await expect(dialogo.getByRole("button", { name: "Devolver con observaciones" })).toBeDisabled();
    await dialogo.getByLabel("Observaciones").fill("Falta la cita del artículo 12");
    await dialogo.getByRole("button", { name: "Devolver con observaciones" }).click();
    await expect(dialogo.getByRole("status")).toHaveText("Versión devuelta.");
    expect(devuelta).toMatchObject({ tipo: "tecnica", aprobado: false, comentario: "Falta la cita del artículo 12" });
    await page.keyboard.press("Escape");
    await page.getByRole("button", { name: "Descartar" }).click();
    await expect(page.getByRole("dialog")).toContainText("Descartar es definitivo; la propuesta quedará en el historial.");
    await page.getByLabel("Motivo del descarte").fill("Ya no aplica");
    await page.getByRole("dialog").getByRole("button", { name: "Descartar" }).click();
    await expect(page.getByRole("dialog").getByRole("status")).toHaveText("Propuesta descartada.");
    expect(descartada).toMatchObject({ nota: "Ya no aplica", generacion: 1 });
  });

  test("el detalle de una versión publicada muestra su leyenda con la fecha en <time>; sin aprobación no se muestra", async ({ page }) => {
    await abrir(page, todas, [publicada, { ...publicada, id: "v-sin", codigo: "BIB-006", version: "3.0", leyenda: null }]);
    await page.getByRole("button", { name: "BIB-001 · 1.0" }).click();
    const leyenda = page.getByTestId("leyenda-version");
    await expect(leyenda).toHaveText(LEYENDA);
    await expect(leyenda.locator("time")).toHaveAttribute("datetime", "2026-11-25");
    await expect(leyenda).not.toContainText(/validada|certificada|conforme|legal/i);
    await page.getByRole("button", { name: "BIB-006 · 3.0" }).click();
    await expect(page.getByTestId("leyenda-version")).toHaveCount(0);
    await expect(page.getByText(/aprobada por —/)).toHaveCount(0);
  });

  test("a 375 px no hay desplazamiento horizontal", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 812 });
    await abrir(page, todas, [publicada, propuesta]);
    await page.getByRole("button", { name: "BIB-001 · 1.1" }).click();
    await expect(page.getByRole("heading", { name: "Versión 1.1 · En revisión" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
});

// --- Leyenda en el catálogo y en la ficha de la plantilla ------------------------------------------

const ORGANIZACION = "org-prueba-bib408";
const plantilla = (codigo: string, extra: Record<string, unknown> = {}) => ({
  id: `id-${codigo}`, codigo, nombre: `Plantilla ${codigo}`, tipo: "politica", fuente: "catalogo", version: "1.0",
  formato: "MD", validacion_legal: "validada", ola: 1, estado: "publicada", descargable: false, ...extra });

async function abrirCatalogo(page: Page, lista: unknown[]) {
  await page.addInitScript((tenant) => { window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant }; }, ORGANIZACION);
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/plantillas**", (r) => r.fulfill({ json: lista }));
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-408");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" }).getByRole("button", { name: /^Documentos y plantillas/ }).click();
  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("tab", { name: "Plantillas" }).click();
  return vista.getByTestId("catalogo-plantillas");
}

test.describe("Leyenda de la plantilla en el catálogo (BIB-408 + BIB-410, API simulada)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("el catálogo muestra la leyenda de cada plantilla aprobada y ninguna si no hay aprobación", async ({ page }) => {
    const catalogo = await abrirCatalogo(page, [
      plantilla("BIB-001", { leyenda: { redaccion: "ia", aprobada_por: "Ana Pérez", aprobada_en: "25 de noviembre de 2026", texto: LEYENDA } }),
      plantilla("BIB-002", { leyenda: { redaccion: "persona", aprobada_por: "Ana Pérez", aprobada_en: "1 de marzo de 2026",
        texto: "Redactada por Luis Mora y aprobada por Ana Pérez el 1 de marzo de 2026." } }),
      plantilla("BIB-003", { leyenda: null }), plantilla("BIB-004"),
    ]);
    await expect(catalogo.getByTestId("plantilla-BIB-001").getByTestId("leyenda-version")).toHaveText(LEYENDA);
    await expect(catalogo.getByTestId("plantilla-BIB-002").getByTestId("leyenda-version"))
      .toHaveText("Redactada por Luis Mora y aprobada por Ana Pérez el 1 de marzo de 2026.");
    await expect(catalogo.getByTestId("plantilla-BIB-003").getByTestId("leyenda-version")).toHaveCount(0);
    await expect(catalogo.getByTestId("plantilla-BIB-004").getByTestId("leyenda-version")).toHaveCount(0);
    await expect(catalogo).not.toContainText(/aprobada por —/);
  });

  test("a 375 px el catálogo con leyenda no se desplaza en horizontal", async ({ page }) => {
    await abrirCatalogo(page, [plantilla("BIB-001", { leyenda: { redaccion: "ia", aprobada_por: "Ana Pérez",
      aprobada_en: "25 de noviembre de 2026", texto: LEYENDA } })]);
    await expect(page.getByTestId("leyenda-version")).toBeVisible();
    await page.setViewportSize({ width: 375, height: 812 });
    await expect(page.getByTestId("leyenda-version")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
});
