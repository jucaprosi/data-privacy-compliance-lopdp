/**
 * FE-24: tablero de la organización con las cuatro dimensiones y las brechas críticas, sin cifra
 * única (Doctrina 4, INV_LOPDP_MULTIDIMENSIONAL_METRICS). API simulada.
 */
import { expect, test, type BrowserContext, type Locator, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";
import { simularApiDiagnostico } from "../diagnostico/simulador";

const HOY = new Date();
const enDias = (n: number) => new Date(HOY.getTime() + n * 86_400_000).toISOString().slice(0, 10);

async function simularHojaDeRuta(context: BrowserContext) {
  await context.route("**/api/v1/roadmaps/hoja-1", (route) =>
    route.fulfill({
      json: {
        roadmap: { id: "hoja-1" },
        waves: [
          {
            id: "o1",
            name: "Ola 1",
            sort_order: 1,
            tasks: [
              { id: "t1", control_ref: "C1", dimension: "D01", title: "a", priority: "alta", status: "pendiente", end_date: enDias(-3) },
              { id: "t2", control_ref: "C2", dimension: "D01", title: "b", priority: "alta", status: "en_progreso", end_date: enDias(3) },
              { id: "t3", control_ref: "C3", dimension: "D01", title: "c", priority: "media", status: "pendiente", end_date: enDias(30) },
              { id: "t4", control_ref: "C4", dimension: "D01", title: "d", priority: "media", status: "completada", end_date: enDias(-9) },
              { id: "t5", control_ref: "C5", dimension: "D01", title: "e", priority: "media", status: "pendiente", end_date: null },
            ],
          },
        ],
      },
    })
  );
}

function tablero(page: Page): Locator {
  return page.getByRole("region", { name: "Tablero de la organización" });
}

async function abrirTablero(page: Page, context: BrowserContext, conResultado: boolean, conHoja = false) {
  const servidor = await simularApiDiagnostico(context, { roles: ["dpo"] });
  if (conHoja) await simularHojaDeRuta(context);
  if (conHoja) {
    await page.addInitScript(() => {
      window.localStorage.setItem(
        "lopdp-roadmap-store-v1",
        JSON.stringify({ state: { currentRoadmapId: "hoja-1" }, version: 0 })
      );
    });
  }
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  if (conResultado) {
    // Sella un resultado en el servidor simulado (el DPO), como lo haría el cierre del diagnóstico.
    await page.evaluate(async () => {
      await fetch("/api/v1/diagnostico/resultados", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-User-Role": "dpo" },
        body: JSON.stringify({ perfil: {} }),
      });
    });
  }
  await irASala(page, /Dashboard Central/);
  return servidor;
}

test.describe("Tablero de la organización sin cifra única (FE-24)", () => {
  test("muestra las cuatro dimensiones y las brechas críticas, cada una por separado", async ({ page, context }) => {
    await abrirTablero(page, context, true);
    const t = tablero(page);

    for (const id of ["madurez", "conformidad", "evidencia", "riesgo"]) {
      await expect(t.getByTestId(`dimension-${id}`)).toBeVisible();
    }
    await expect(t.getByTestId("dimension-madurez")).toContainText("Sin evaluación suficiente");
    await expect(t.getByTestId("dimension-conformidad")).toContainText("No conforme");
    await expect(t.getByTestId("dimension-riesgo")).toContainText("65 críticas y 2 altas");
    await expect(t.getByTestId("brechas-criticas")).toContainText("65");
  });

  test("no aparece ningún porcentaje ni puntaje global de la organización", async ({ page, context }) => {
    await abrirTablero(page, context, true);
    const t = tablero(page);
    await expect(t.getByTestId("dimension-riesgo")).toBeVisible();

    const texto = (await t.innerText()).replace(/\s+/g, " ");
    expect(texto, "ningún porcentaje en el tablero").not.toMatch(/\d\s*%/);
    expect(texto, "ningún puntaje global").not.toMatch(/\b(puntaje|score|promedio|nivel de cumplimiento|cumplimiento global)\b/i);
    // Solo hay cuatro tarjetas de dimensión y ninguna otra cifra de resumen fuera de las brechas.
    await expect(t.locator('[data-testid^="dimension-"]')).toHaveCount(4);
    // Las únicas cifras sueltas son: nivel, conteos de controles/respuestas, brechas y n.º de sellado.
    expect(texto).not.toMatch(/\b\d+(\.\d+)?\s*\/\s*100\b/);
  });

  test("sin resultados del diagnóstico lo dice, lleva al assessment y no muestra ceros", async ({ page, context }) => {
    await abrirTablero(page, context, false);
    const t = tablero(page);

    await expect(t.getByText("Aún no hay resultados del diagnóstico")).toBeVisible();
    await expect(t.locator('[data-testid^="dimension-"]')).toHaveCount(0);
    await expect(t.getByTestId("brechas-criticas")).toHaveCount(0);
    await expect(t).not.toContainText(/\b0\b/);

    await t.getByRole("button", { name: "Ir al assessment" }).click();
    await expect(page.getByRole("button", { name: /Siguiente/ }).first()).toBeVisible();
  });

  test("los semáforos de plazos cuentan solo tareas con fecha del servidor", async ({ page, context }) => {
    await abrirTablero(page, context, true, true);
    const t = tablero(page);

    await expect(t.getByTestId("plazo-vencidas")).toContainText("1");
    await expect(t.getByTestId("plazo-proximas")).toContainText("1");
    await expect(t.getByTestId("plazo-en-plazo")).toContainText("1");
  });

  test("sin hoja de ruta no inventa plazos", async ({ page, context }) => {
    await abrirTablero(page, context, true);
    await expect(tablero(page).getByText(/Sin tareas con fecha/)).toBeVisible();
    await expect(tablero(page).getByTestId("plazo-vencidas")).toHaveCount(0);
  });
});
