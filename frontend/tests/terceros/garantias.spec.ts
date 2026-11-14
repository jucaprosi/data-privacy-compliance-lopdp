/**
 * TER-01 · Módulo Terceros: contrato, garantía y distintivo de hallazgo (especificación TER-01 §4-§5).
 *
 * API simulada. Comprueba: columnas, distintivo con texto completo y enlace accesible, «Evaluar terceros»
 * solo con permiso y su mensaje de estado, modal accesible (foco inicial en Cancelar, Escape y retorno del
 * foco), estados fijos de error y tarjetas sin desplazamiento horizontal a 375 px.
 * Mutación documentada: si el módulo deja de pintar el distintivo, falla la primera prueba.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const SIN_CONTRATO = {
  id: "t-1", nombre: "Nube Andina S.A.", rol: "ENCARGADO", pais: "EC",
  contrato_sha256: null, contrato_vigente_hasta: null, garantia_tipo: null, garantia_sha256: null,
  criticidad: "alta", proxima_revision: "2027-01-15",
  hallazgos: [{ id: "h-1", origen_ref: "t-1:contrato", estado: "abierto", regla: "contrato" }],
};
const CON_CONTRATO = {
  id: "t-2", nombre: "Datos Globales LLC", rol: "DESTINATARIO", pais: "US",
  contrato_sha256: "a".repeat(64), contrato_vigente_hasta: "2099-12-31", garantia_tipo: null, garantia_sha256: null,
  criticidad: null, proxima_revision: null,
  hallazgos: [{ id: "h-2", origen_ref: "t-2:garantia", estado: "abierto", regla: "garantia" }],
};

async function instalarApi(page: Page, opciones: { roles?: string[]; fallaCarga?: boolean } = {}) {
  const roles = opciones.roles ?? ["implementador"];
  const evaluar = roles.includes("implementador");
  await page.route("**/api/v1/**", async (route) => {
    const url = new URL(route.request().url());
    const ruta = url.pathname.replace(/^\/api\/v1/, "");
    const metodo = route.request().method();
    const responder = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });
    if (ruta === "/organizacion/me/roles") {
      return responder(200, {
        user_id: "u-ter01", tenant_id: "tenant-ter01",
        roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })),
      });
    }
    if (ruta === "/terceros/garantias" && metodo === "GET") {
      if (opciones.fallaCarga) return responder(500, { detail: "Traceback interno" });
      return responder(200, { terceros: [SIN_CONTRATO, CON_CONTRATO], permisos: { gestionar: true, evaluar } });
    }
    if (ruta === "/terceros/evaluar" && metodo === "POST") return responder(200, { hallazgos_creados: 1, cerrados: 2 });
    if (ruta === "/evidencias/documentos") return responder(200, { documentos: [] });
    return responder(200, {});
  });
}

async function abrirTerceros(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Corporación TER-01");
  await irASala(page, /Encargados y terceros/);
}

test.describe("Terceros · contrato y garantía (TER-01)", () => {
  test("el tercero sin contrato muestra el distintivo con texto completo y el enlace al hallazgo", async ({ page }) => {
    await instalarApi(page);
    await abrirTerceros(page);
    const fila = page.getByTestId("tercero-t-1");
    await expect(fila.getByTestId("distintivo-contrato")).toHaveText("Hallazgo alto: encargado sin contrato");
    await expect(fila.getByRole("link", { name: "Ver el hallazgo de Nube Andina S.A." })).toBeVisible();
    await expect(fila).toContainText("Sin contrato");
    await expect(fila).toContainText("15/01/2027");
    const otra = page.getByTestId("tercero-t-2");
    await expect(otra.getByTestId("distintivo-garantia")).toHaveText(
      "Hallazgo crítico: transferencia sin garantía registrada",
    );
    await expect(otra).toContainText("Vigente hasta 31/12/2099");
    await expect(otra).toContainText("Sin garantía registrada");
    await expect(page.getByText(/garantías adecuadas|conforme/i)).toHaveCount(0);
  });

  test("evaluar terceros anuncia el resultado con singular y plural", async ({ page }) => {
    await instalarApi(page);
    await abrirTerceros(page);
    await page.getByRole("button", { name: "Evaluar terceros" }).click();
    await expect(page.getByTestId("estado-evaluacion")).toHaveAttribute("role", "status");
    await expect(page.getByTestId("estado-evaluacion")).toHaveText("Evaluación terminada: 1 hallazgo creado y 2 cerrados.");
  });

  test("sin rol implementador no aparece «Evaluar terceros»", async ({ page }) => {
    await instalarApi(page, { roles: ["coordinador"] });
    await abrirTerceros(page);
    await expect(page.getByTestId("tercero-t-1")).toBeVisible();
    await expect(page.getByRole("button", { name: "Evaluar terceros" })).toHaveCount(0);
  });

  test("el modal es accesible: foco en Cancelar, Escape cierra y devuelve el foco", async ({ page }) => {
    await instalarApi(page);
    await abrirTerceros(page);
    const abrir = page.getByTestId("tercero-t-1").getByRole("button", { name: "Registrar garantías" });
    await abrir.click();
    const dialogo = page.getByRole("dialog", { name: "Registrar garantías de Nube Andina S.A." });
    await expect(dialogo).toBeVisible();
    await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
    await expect(dialogo.getByLabel("País", { exact: true })).toContainText("Ecuador");
    await page.keyboard.press("Escape");
    await expect(dialogo).toHaveCount(0);
    await expect(abrir).toBeFocused();
  });

  test("el error de carga usa el texto fijo y no el del servidor", async ({ page }) => {
    await instalarApi(page, { fallaCarga: true });
    await abrirTerceros(page);
    await expect(page.getByTestId("error-carga")).toHaveAttribute("role", "alert");
    await expect(page.getByTestId("error-carga")).toContainText("No pudimos cargar los terceros. Inténtalo de nuevo.");
    await expect(page.getByTestId("error-carga").getByRole("button", { name: "Volver a cargar", exact: true })).toBeVisible();
    await expect(page.getByText("Traceback interno")).toHaveCount(0);
  });

  test("a 375 px las tarjetas no desplazan en horizontal", async ({ page }) => {
    await instalarApi(page);
    await abrirTerceros(page);
    await page.setViewportSize({ width: 375, height: 812 });
    await expect(page.getByTestId("tercero-t-1")).toBeVisible();
    const desborda = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(desborda).toBe(false);
  });
});
