// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤notificaciones ¤¤qa-engineer
/**
 * NOTIF-02 · Avisos de versiones por revisar: campana de la cabecera y bandeja Inicio › Avisos.
 * API simulada: no acredita permisos ni persistencia (la RLS la prueba `tests/test_notif02_avisos.py`).
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, configurarProyecto } from "../utiles";

const AVISO = {
  id: "a1", titulo: "Versión por revisar: Política de privacidad",
  texto: "Motivo del cambio: Resolución 1, que entra en vigencia el 5 de diciembre de 2026.",
  enlace: "/biblioteca?version=v1", leido: false, pendiente: true, creado_en: new Date().toISOString(),
};

async function simular(page: Page, avisos: unknown[], sinLeer: number, status = 200) {
  await page.addInitScript(() => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "org-prueba-notif02" };
  });
  await page.route("**/api/v1/avisos/*/leido", (route) => route.fulfill({ status: 204 }));
  await page.route("**/api/v1/avisos?**", (route) =>
    route.fulfill({ status, json: status === 200 ? { avisos, sin_leer: sinLeer } : { detail: "error" } }));
  await page.route(/\/api\/v1\/(?!avisos).*/, (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
}

async function abrirBandeja(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad NOTIF-02");
  await page.getByTestId("campana-avisos").click();
}

test("la campana dice cuántos avisos hay sin leer", async ({ page }) => {
  await simular(page, [AVISO], 1);
  await abrirAppLimpia(page);
  await expect(page.getByRole("button", { name: "Avisos, 1 sin leer" })).toBeVisible();
});

test("sin avisos sin leer la campana se llama solo «Avisos»", async ({ page }) => {
  await simular(page, [], 0);
  await abrirAppLimpia(page);
  await expect(page.getByRole("button", { name: "Avisos", exact: true })).toBeVisible();
});

test("«Marcar como leído» saca el aviso de «Sin leer»", async ({ page }) => {
  await simular(page, [AVISO], 1);
  await abrirBandeja(page);
  await expect(page.getByRole("heading", { level: 2, name: "Avisos" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 3, name: /Versión por revisar/ })).toBeVisible();
  await page.getByRole("button", { name: "Marcar como leído" }).click();
  // La pantalla tiene otros avisos con role=status (entorno): se busca el de la bandeja por su texto.
  await expect(page.getByRole("status").filter({ hasText: "No tienes avisos sin leer." })).toBeVisible();
});

test("con un 500 se ven el error y «Reintentar»", async ({ page }) => {
  await simular(page, [], 0, 500);
  await abrirBandeja(page);
  await expect(page.getByText("No pudimos cargar tus avisos. Inténtalo de nuevo.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Reintentar" })).toBeVisible();
});

test("a 375 px no hay desplazamiento horizontal", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await simular(page, [AVISO], 1);
  await abrirBandeja(page);
  await expect(page.getByRole("heading", { level: 2, name: "Avisos" })).toBeVisible();
  const desborda = await page.evaluate(() => document.documentElement.scrollWidth > document.documentElement.clientWidth);
  expect(desborda).toBe(false);
});

const AVISO_CAPACIDAD = {
  id: "a2", titulo: "Capacidad editorial concedida", texto: "Ana te concedió la capacidad Editor.",
  enlace: "/plataforma/capacidades", leido: false, pendiente: true, creado_en: new Date().toISOString(),
};

test("el enlace de un aviso de capacidades dice «Ver capacidades editoriales» (NOTIF-05, m1)", async ({ page }) => {
  await simular(page, [AVISO_CAPACIDAD], 1);
  await abrirBandeja(page);
  const enlace = page.getByRole("link", { name: "Ver capacidades editoriales" });
  await expect(enlace).toHaveAttribute("href", "/plataforma/capacidades");
  await expect(page.getByRole("link", { name: "Revisar la versión" })).toHaveCount(0);
});

test("el enlace de un aviso de versión por revisar sigue diciendo «Revisar la versión» (NOTIF-05, m2)", async ({ page }) => {
  await simular(page, [AVISO], 1);
  await abrirBandeja(page);
  await expect(page.getByRole("link", { name: "Revisar la versión" })).toHaveAttribute("href", "/biblioteca?version=v1");
  await expect(page.getByRole("link", { name: "Ver capacidades editoriales" })).toHaveCount(0);
});
