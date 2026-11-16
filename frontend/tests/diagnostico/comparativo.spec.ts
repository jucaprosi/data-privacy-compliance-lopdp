/**
 * DIAG-06: Diagnóstico › Comparativo.
 *
 * 1. Con prueba y real sellados, la tabla muestra cada dimensión con su nivel de partida, el de
 *    llegada y su cambio, y las brechas cerradas, nuevas y que siguen; no hay cifra única.
 * 2. Con un solo sello, la pantalla lo dice y no compara.
 *
 * Mutación documentada (INV_LOPDP_MULTIDIMENSIONAL_METRICS): intercambiar `nivel_base` y
 * `nivel_actual` en Comparativo.tsx hace fallar la prueba 1 (el nivel de partida sale 3 y no 1).
 * API simulada en memoria: solo valores generados.
 */
import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const CON_DOS_SELLOS = {
  comparable: true,
  motivo: null,
  linea_base: { id: "r1", tipo: "prueba", sellado_en: "2026-11-01T10:00:00+00:00" },
  actual: { id: "r2", tipo: "real", sellado_en: "2026-11-08T10:00:00+00:00" },
  por_dimension: [
    { dimension: "D01", nombre: "Gobierno", nivel_base: 1, nivel_actual: 3, diferencia_nivel: 2, cerradas: 1, nuevas: 0, siguen: 0 },
    { dimension: "D02", nombre: "Derechos", nivel_base: 3, nivel_actual: 2, diferencia_nivel: -1, cerradas: 0, nuevas: 1, siguen: 1 },
  ],
  brechas: {
    cerradas: [{ pregunta_id: 1, control: "Control cerrado", dimension: "D01", criticidad: 3 }],
    nuevas: [{ pregunta_id: 2, control: "Control nuevo", dimension: "D02", criticidad: 3 }],
    siguen: [{ pregunta_id: 3, control: "Control que sigue", dimension: "D02", criticidad: 3 }],
  },
};

const CON_UN_SELLO = {
  comparable: false,
  motivo: "Falta el diagnóstico real: cuando el DPO lo selle podrás compararlo con el de prueba.",
  codigo_motivo: "sin_real",
  linea_base: { id: "r1", tipo: "prueba", sellado_en: "2026-11-01T10:00:00+00:00" },
  actual: null,
  por_dimension: [],
  brechas: { cerradas: [], nuevas: [], siguen: [] },
};

async function simular(context: BrowserContext, cuerpo: unknown) {
  await context.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { user_id: "usuario-prueba", tenant_id: "tenant-corp-demo", roles: [{ role: "implementador" }] } })
  );
  await context.route("**/api/v1/diagnostico/comparativo", (route) => route.fulfill({ json: cuerpo }));
}

async function abrir(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Comparativo/);
}

test("compara la prueba con el real por dimensión, sin cifra única", async ({ page, context }) => {
  await simular(context, CON_DOS_SELLOS);
  await abrir(page);
  const tabla = page.getByRole("table", { name: "Comparativo por dimensión" });
  const gobierno = tabla.getByRole("row", { name: /Gobierno/ });
  await expect(gobierno.getByRole("cell").nth(0)).toHaveText("1");
  await expect(gobierno.getByRole("cell").nth(1)).toHaveText("3");
  await expect(gobierno.getByText("Mejora")).toBeVisible();
  await expect(tabla.getByRole("row", { name: /Derechos/ }).getByText("Empeora")).toBeVisible();
  await expect(page.getByRole("region", { name: "Brechas cerradas" })).toContainText("Control cerrado");
  await expect(page.getByRole("region", { name: "Brechas nuevas" })).toContainText("Control nuevo");
  await expect(page.getByRole("region", { name: "Brechas que siguen" })).toContainText("Control que sigue");
  await expect(page.getByText(/avance global/i)).toHaveCount(0);
  await expect(tabla.getByRole("columnheader", { name: "Nivel en la prueba" })).toBeVisible();
  await expect(tabla.getByRole("columnheader", { name: "Siguen abiertas" })).toBeVisible();
});

test("con un solo sello lo dice y no compara", async ({ page, context }) => {
  await simular(context, CON_UN_SELLO);
  await abrir(page);
  await expect(page.getByTestId("comparativo-sin-comparar")).toContainText("Falta el diagnóstico real");
  await expect(page.getByRole("table", { name: "Comparativo por dimensión" })).toHaveCount(0);
});

test("sin diagnósticos sellados muestra el texto por código y no compara", async ({ page, context }) => {
  await simular(context, { ...CON_UN_SELLO, motivo: "texto de respaldo", codigo_motivo: "sin_sellos", linea_base: null });
  await abrir(page);
  await expect(page.getByTestId("comparativo-sin-comparar")).toContainText("Todavía no hay diagnósticos sellados");
  await expect(page.getByRole("table", { name: "Comparativo por dimensión" })).toHaveCount(0);
});

test("ante un error muestra un aviso fijo y permite reintentar", async ({ page, context }) => {
  await context.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { user_id: "usuario-prueba", tenant_id: "tenant-corp-demo", roles: [{ role: "implementador" }] } })
  );
  // Falla hasta que se pulsa «Reintentar» (en desarrollo React lanza la carga dos veces).
  let falla = true;
  await context.route("**/api/v1/diagnostico/comparativo", (route) => {
    return falla ? route.fulfill({ status: 500, json: { detail: "detalle interno" } }) : route.fulfill({ json: CON_DOS_SELLOS });
  });
  await abrir(page);
  await expect(page.getByText("No se pudo cargar el comparativo. Inténtalo de nuevo.")).toBeVisible();
  await expect(page.getByText("detalle interno")).toHaveCount(0);
  falla = false;
  await page.getByRole("button", { name: "Reintentar" }).click();
  await expect(page.getByRole("table", { name: "Comparativo por dimensión" })).toBeVisible();
});
