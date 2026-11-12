/**
 * DIAG-12: Diagnóstico › Estado actual.
 *
 * 1. Con estados emitidos se ve la lista, el actual y su comparación por dimensión con el diagnóstico real;
 *    cambiar a «el estado anterior» pide esa comparación. No hay cifra única de avance.
 * 2. Solo el DPO ve «Emitir un estado»; emitir recarga la lista.
 * 3. Sin estados lo dice.
 *
 * Mutación documentada: mostrar «Emitir un estado» sin comprobar `puedeSellar(roles)` en Estados.tsx
 * hace fallar la prueba 2 (un implementador vería el botón).
 * API simulada en memoria: solo valores generados.
 */
import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const ESTADO = (secuencia: number) => ({
  id: `estado-${secuencia}`,
  secuencia,
  emitido_por: "persona-dpo",
  fecha_corte: `2026-11-0${secuencia}T10:00:00+00:00`,
  resultado_real_id: "real-1",
  escala: "smartcidi_1_5",
  tareas: Array.from({ length: secuencia }, (_, i) => ({ tarea_id: `t-${i}`, control_ref: `P${i + 1}` })),
  indicadores: {},
  huella_anterior: "0".repeat(64),
  huella: "f".repeat(64),
});

const COMPARATIVO = (con: string) => ({
  comparable: true,
  motivo: null,
  con,
  linea_base: { id: "x", tipo: con === "real" ? "real" : "estado", sellado_en: "2026-11-01T10:00:00+00:00" },
  actual: { id: "estado-2", tipo: "estado", sellado_en: "2026-11-02T10:00:00+00:00" },
  por_dimension: [
    { dimension: "D01", nombre: "Gobierno", nivel_base: 1, nivel_actual: con === "real" ? 3 : 2, diferencia_nivel: con === "real" ? 2 : 1, cerradas: 1, nuevas: 0, siguen: 0 },
  ],
  brechas: {
    cerradas: [{ pregunta_id: 1, control: "Control cerrado", dimension: "D01", criticidad: 3 }],
    nuevas: [],
    siguen: [],
  },
});

interface Opciones {
  cadenaIntegra?: boolean;
  falloAlEmitir?: { status: number; code?: string; detail?: string };
}

async function simular(context: BrowserContext, rol: string, estados: ReturnType<typeof ESTADO>[], opciones: Opciones = {}) {
  const servidor = { estados: [...estados], comparaciones: [] as string[], emisiones: 0 };
  await context.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { user_id: "usuario-prueba", tenant_id: "tenant-corp-demo", roles: [{ role: rol }] } })
  );
  await context.route("**/api/v1/diagnostico/estados", async (route) => {
    if (route.request().method() === "POST") {
      if (opciones.falloAlEmitir) {
        const { status, code, detail } = opciones.falloAlEmitir;
        return route.fulfill({ status, json: { detail: detail ?? "detalle interno", code } });
      }
      servidor.emisiones += 1;
      servidor.estados = [ESTADO(servidor.estados.length + 1), ...servidor.estados];
      return route.fulfill({ status: 201, json: servidor.estados[0] });
    }
    return route.fulfill({ json: { estados: servidor.estados, cadena_integra: opciones.cadenaIntegra ?? true, primer_alterado: null } });
  });
  await context.route("**/api/v1/diagnostico/estados/*/comparativo*", (route) => {
    const con = new URL(route.request().url()).searchParams.get("con") ?? "real";
    servidor.comparaciones.push(con);
    return route.fulfill({ json: COMPARATIVO(con) });
  });
  return servidor;
}

async function abrir(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Estado actual/);
}

test("lista los estados y compara el actual con el real y con el anterior", async ({ page, context }) => {
  const servidor = await simular(context, "implementador", [ESTADO(2), ESTADO(1)]);
  await abrir(page);
  const lista = page.getByRole("region", { name: "Estados emitidos" });
  await expect(lista).toContainText("Estado 2");
  await expect(lista).toContainText("Actual");
  const tabla = page.getByRole("table", { name: "Estado por dimensión" });
  await expect(tabla.getByRole("row", { name: /Gobierno/ }).getByRole("cell").nth(1)).toHaveText("3");
  await expect(page.getByRole("region", { name: "Brechas cerradas" })).toContainText("Control cerrado");
  await expect(page.getByText(/avance global/i)).toHaveCount(0);
  await page.getByLabel(/Comparar el estado 2 con/).selectOption("anterior");
  await expect(tabla.getByRole("row", { name: /Gobierno/ }).getByRole("cell").nth(1)).toHaveText("2");
  expect(servidor.comparaciones).toContain("anterior");
});

test("solo el DPO ve «Emitir un estado» y emitir recarga la lista", async ({ page, context }) => {
  await simular(context, "implementador", [ESTADO(1)]);
  await abrir(page);
  await expect(page.getByRole("region", { name: "Estados emitidos" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Emitir un estado" })).toHaveCount(0);
});

test("el DPO emite un estado", async ({ page, context }) => {
  const servidor = await simular(context, "dpo", [ESTADO(1)]);
  await abrir(page);
  await page.getByRole("button", { name: "Emitir un estado" }).click();
  await expect(page.getByText("¿Emitir un estado? Quedará registrado con la fecha de hoy y no se podrá borrar.")).toBeVisible();
  await expect(page.getByRole("button", { name: "Cancelar" })).toBeFocused();
  await page.getByRole("button", { name: "Emitir estado" }).click();
  await expect(page.getByRole("region", { name: "Estados emitidos" })).toContainText("Estado 2");
  await expect(page.getByRole("status").filter({ hasText: "Estado 2 emitido." })).toBeVisible();
  expect(servidor.emisiones).toBe(1);
});

test("sin estados lo dice", async ({ page, context }) => {
  await simular(context, "coordinador", []);
  await abrir(page);
  await expect(page.getByTestId("estados-vacio")).toContainText("Todavía no hay estados emitidos");
});

test("un error al emitir muestra un mensaje fijo, no el de la excepción", async ({ page, context }) => {
  await simular(context, "dpo", [ESTADO(1)], { falloAlEmitir: { status: 500 } });
  await abrir(page);
  await page.getByRole("button", { name: "Emitir un estado" }).click();
  await page.getByRole("button", { name: "Emitir estado" }).click();
  await expect(page.getByText("No se pudo emitir el estado. Inténtalo de nuevo.")).toBeVisible();
  await expect(page.getByText("detalle interno")).toHaveCount(0);
});

test("sin diagnóstico real sellado muestra el texto fijo de ese código", async ({ page, context }) => {
  await simular(context, "dpo", [], { falloAlEmitir: { status: 409, code: "DIAG_ESTADO_SIN_DIAGNOSTICO_REAL" } });
  await abrir(page);
  await page.getByRole("button", { name: "Emitir un estado" }).click();
  await page.getByRole("button", { name: "Emitir estado" }).click();
  await expect(page.getByText("Primero hay que sellar el diagnóstico real.")).toBeVisible();
});

test("con los estados alterados avisa arriba y la página no usa jerga", async ({ page, context }) => {
  await simular(context, "coordinador", [ESTADO(1)], { cadenaIntegra: false });
  await abrir(page);
  await expect(page.getByRole("alert").filter({ hasText: "no coinciden con su registro de integridad" })).toBeVisible();
  const texto = (await page.locator("main").innerText()).toLowerCase();
  for (const jerga of ["cadena", "hash", "huella", "estado-1"]) expect(texto).not.toContain(jerga);
});
