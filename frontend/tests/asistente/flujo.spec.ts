// ¤asistente ¤frontend-ide
// Aceptación del patrón de asistente (FE-23). Contrato: governance/especificaciones/FE-23.md §5.
import { expect, test, type Page } from "@playwright/test";
import { abrirPaginaPrueba } from "./montaje";

const AVISO_ERROR = "No se pudo guardar este paso. Intenta de nuevo.";

const llamadas = (page: Page) => page.evaluate(() => window.__asistente.llamadas);
const pasoActual = (page: Page) => page.locator('[aria-current="step"]');
const boton = (page: Page, nombre: string) => page.getByRole("button", { name: nombre, exact: true });

async function completarDatos(page: Page) {
  await page.getByLabel("Nombre").fill("Cooperativa de prueba");
  await boton(page, "Siguiente").click();
  await expect(page.getByRole("heading", { name: "Sedes" })).toBeVisible();
}

test.beforeEach(async ({ page }) => {
  await abrirPaginaPrueba(page);
});

test("no avanza inválido", async ({ page }) => {
  await boton(page, "Siguiente").click();
  await expect(page.getByRole("alert")).toHaveText("Escribe el nombre de la organización.");
  await expect(page.getByRole("heading", { name: "Datos generales" })).toBeVisible();
  await expect(pasoActual(page)).toHaveAttribute("data-paso", "datos");
  await expect(page.getByTestId("asistente-progreso")).toHaveText("Paso 1 de 3");
  expect(await llamadas(page)).toEqual([]);
});

test("avanza y enfoca", async ({ page }) => {
  await completarDatos(page);
  expect(await llamadas(page)).toEqual(["datos"]);
  await expect(page.getByRole("heading", { name: "Sedes" })).toBeFocused();
  await expect(pasoActual(page)).toHaveAttribute("data-paso", "sedes");
  await expect(page.getByTestId("asistente-progreso")).toHaveText("Paso 2 de 3");
  await expect(page.locator('li[data-paso="datos"]')).toHaveAttribute("data-estado", "completado");
  await expect(page.getByRole("alert")).toHaveCount(0);

  // R3 · Anterior: retrocede sin validar ni guardar, y enfoca el título.
  await boton(page, "Anterior").click();
  await expect(page.getByRole("heading", { name: "Datos generales" })).toBeFocused();
  expect(await llamadas(page)).toEqual(["datos"]);

  // Teclado: Tab hasta «Siguiente» y Enter.
  await boton(page, "Siguiente").focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: "Sedes" })).toBeFocused();

  // Último paso: «Terminar» llama a alTerminar y muestra el resumen.
  await boton(page, "Siguiente").click();
  await expect(boton(page, "Terminar")).toBeVisible();
  await boton(page, "Terminar").click();
  await expect(page.getByTestId("asistente-resumen")).toBeVisible();
  await expect(page.getByRole("heading", { name: "Resumen" })).toBeFocused();
  expect(await page.evaluate(() => window.__asistente.terminado)).toBe(1);
  expect(await llamadas(page)).toEqual(["datos", "datos", "sedes", "confirmacion"]);
});

test("error al guardar", async ({ page }) => {
  await page.evaluate(() => (window.__asistente.modo = "rechazar"));
  await page.getByLabel("Nombre").fill("Cooperativa de prueba");
  await boton(page, "Siguiente").click();
  await expect(page.getByRole("alert")).toHaveText(AVISO_ERROR);
  await expect(page.getByRole("heading", { name: "Datos generales" })).toBeVisible();
  await expect(pasoActual(page)).toHaveAttribute("data-paso", "datos");
  expect(await llamadas(page)).toEqual(["datos"]);
  await expect(boton(page, "Siguiente")).toBeEnabled();

  // Reintento con guardado correcto: avanza y el aviso desaparece.
  await page.evaluate(() => (window.__asistente.modo = "resolver"));
  await boton(page, "Siguiente").click();
  await expect(page.getByRole("heading", { name: "Sedes" })).toBeVisible();
  await expect(page.getByRole("alert")).toHaveCount(0);
});

test("saltar", async ({ page }) => {
  // Paso obligatorio: no hay «Saltar».
  await expect(boton(page, "Saltar")).toHaveCount(0);
  await completarDatos(page);

  // Paso opcional: «Saltar» existe, avanza sin validar ni guardar.
  await boton(page, "Saltar").click();
  await expect(page.getByRole("heading", { name: "Confirmación" })).toBeFocused();
  await expect(page.locator('li[data-paso="sedes"]')).toHaveAttribute("data-estado", "saltado");
  expect(await llamadas(page)).toEqual(["datos"]);

  // Último paso obligatorio: tampoco hay «Saltar».
  await expect(boton(page, "Saltar")).toHaveCount(0);
});

test("ocupado", async ({ page }) => {
  await completarDatos(page);
  await page.evaluate(() => (window.__asistente.modo = "pendiente"));
  await boton(page, "Siguiente").click();
  await expect(boton(page, "Anterior")).toBeDisabled();
  await expect(boton(page, "Saltar")).toBeDisabled();
  await expect(boton(page, "Siguiente")).toBeDisabled();
  expect(await llamadas(page)).toEqual(["datos", "sedes"]);

  await page.evaluate(() => window.__asistente.resolverPendiente?.());
  await expect(page.getByRole("heading", { name: "Confirmación" })).toBeVisible();
  await expect(boton(page, "Terminar")).toBeEnabled();
  await expect(boton(page, "Anterior")).toBeEnabled();
});
