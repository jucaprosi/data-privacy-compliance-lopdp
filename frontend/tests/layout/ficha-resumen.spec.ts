/**
 * FE-25 · Ficha resumen de la organización bajo el encabezado (governance/especificaciones/FE-25.md).
 *
 * Lee la fila de la organización activa de `GET /organizacion/cartera` (simulada, valores ficticios).
 * Mutación documentada: añadir un promedio o un porcentaje global a la ficha hace fallar
 * «sin cifra única» (por ejemplo, un `<span>Promedio: 62 %</span>` en FichaResumen.tsx).
 */
import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { simularApiDiagnostico } from "../diagnostico/simulador";
import { abrirAppLimpia, configurarProyecto } from "../utiles";

const TENANT = "tenant-corp-demo";

const DIAGNOSTICO = {
  escala: "smartcidi_1_5",
  niveles_por_dimension: [
    { dimension: "D01", nivel: 4 },
    { dimension: "D02", nivel: 2 },
  ],
  cumplimiento: false,
  respaldo_documental: 55,
  brechas_criticas: 3,
  brechas_altas: 5,
  sellado_en: "2026-11-09T12:00:00+00:00",
};

const FILA = {
  tenant_id: TENANT,
  nombre: "Cooperativa Andina",
  roles: ["dpo"],
  diagnostico: DIAGNOSTICO,
  hallazgos_abiertos: 4,
  tareas_vencidas: 2,
  cadena_integra: true,
};

async function abrir(page: Page, context: BrowserContext, responder: () => { status: number; json: unknown }) {
  await simularApiDiagnostico(context, { roles: ["dpo"] });
  await context.route("**/api/v1/organizacion/cartera", (ruta) => {
    return ruta.fulfill(responder());
  });
  await page.setViewportSize({ width: 1280, height: 800 });
  await abrirAppLimpia(page);
  await configurarProyecto(page);
}

const texto0 = (t: string) => t;
const ficha = (page: Page) => page.getByTestId("ficha-resumen");

test.describe("Ficha resumen de la organización (FE-25)", () => {
  test("sin cifra única: nombre, alertas y cuatro semáforos", async ({ page, context }) => {
    await abrir(page, context, () => ({ status: 200, json: { organizaciones: [FILA] } }));
    await expect(ficha(page).getByTestId("ficha-nombre")).toHaveText("Cooperativa Andina");
    await expect(ficha(page).getByTestId("ficha-tareas-vencidas")).toContainText("2");
    await expect(ficha(page).getByTestId("ficha-hallazgos")).toContainText("4");
    for (const id of ["madurez", "conformidad", "evidencia", "riesgo"]) {
      await expect(ficha(page).getByTestId(`ficha-dimension-${id}`)).toBeVisible();
    }
    // Con un DPO asignado en el servidor, la ficha no puede afirmar que no hay nadie.
    await expect(ficha(page)).not.toContainText("Sin designar");
    await expect(ficha(page)).toContainText("Tamaño: Microempresa");
    await expect(ficha(page).getByTestId("ficha-dimension-conformidad")).toContainText("Cumplimiento");
    await expect(ficha(page).getByTestId("ficha-dimension-evidencia")).toContainText("Respaldo con documentos");
    expect(texto0(await ficha(page).innerText())).not.toMatch(/Conformidad|Organización micro/);
    const texto = await ficha(page).innerText();
    expect(texto, "ningún porcentaje, promedio ni puntaje global").not.toMatch(/%|puntaje|promedio/i);
    expect(texto).not.toMatch(/tenant-|undefined|null|NaN/);
  });

  test("sin diagnóstico sellado no inventa semáforos ni ceros", async ({ page, context }) => {
    await abrir(page, context, () => ({
      status: 200,
      json: { organizaciones: [{ ...FILA, diagnostico: null, hallazgos_abiertos: null, tareas_vencidas: null }] },
    }));
    for (const id of ["madurez", "conformidad", "evidencia", "riesgo"]) {
      await expect(ficha(page).getByTestId(`ficha-dimension-${id}`)).toContainText("Sin diagnóstico sellado");
    }
    expect(await ficha(page).innerText()).not.toMatch(/%/);
    await expect(ficha(page).getByTestId("ficha-hallazgos")).toContainText("Sin datos");
    await expect(ficha(page).getByTestId("ficha-tareas-vencidas")).toContainText("Sin datos");
  });

  test("mientras carga hay esqueleto y no ceros; si falla se puede reintentar", async ({ page, context }) => {
    // En desarrollo React monta dos veces el efecto: se falla hasta que la prueba lo decida.
    let fallar = true;
    await abrir(page, context, () =>
      fallar ? { status: 500, json: { detail: "simulado" } } : { status: 200, json: { organizaciones: [FILA] } },
    );
    await expect(ficha(page)).toContainText("No pudimos cargar la ficha de la organización");
    fallar = false;
    await ficha(page).getByRole("button", { name: /Volver a cargar/ }).click();
    await expect(ficha(page).getByTestId("ficha-nombre")).toHaveText("Cooperativa Andina");
  });

  test("el cero se ve como 0 y la falta de dato como «Sin datos»", async ({ page, context }) => {
    await abrir(page, context, () => ({
      status: 200,
      json: { organizaciones: [{ ...FILA, tareas_vencidas: 0, hallazgos_abiertos: null }] },
    }));
    await expect(ficha(page).getByTestId("ficha-tareas-vencidas")).toHaveText("Tareas vencidas: 0");
    await expect(ficha(page).getByTestId("ficha-hallazgos")).toHaveText("Hallazgos abiertos: Sin datos");
  });

  test("la ficha se pliega y se muestra", async ({ page, context }) => {
    await abrir(page, context, () => ({ status: 200, json: { organizaciones: [FILA] } }));
    const ocultar = ficha(page).getByRole("button", { name: "Ocultar ficha" });
    await expect(ocultar).toHaveAttribute("aria-expanded", "true");
    await ocultar.click();
    await expect(ficha(page).getByTestId("ficha-tareas-vencidas")).toHaveCount(0);
    const mostrar = ficha(page).getByRole("button", { name: /^Mostrar ficha/ });
    await expect(mostrar).toHaveAttribute("aria-expanded", "false");
    // La elección queda guardada para la próxima vez.
    expect(await page.evaluate(() => window.localStorage.getItem("ficha-resumen-plegada"))).toBe("1");
    await mostrar.click();
    await expect(ficha(page).getByTestId("ficha-tareas-vencidas")).toBeVisible();
  });

  test("en móvil es una línea con el nombre y las alertas", async ({ page, context }) => {
    await abrir(page, context, () => ({ status: 200, json: { organizaciones: [FILA] } }));
    await page.setViewportSize({ width: 375, height: 800 });
    const linea = ficha(page).getByTestId("ficha-linea-compacta");
    await expect(linea).toContainText("Cooperativa Andina");
    await expect(linea).toContainText("2 tareas vencidas");
    await expect(linea).toContainText("4 hallazgos abiertos");
    await expect(linea).toHaveAttribute("title", "Cooperativa Andina");
    expect((await ficha(page).boundingBox())!.height).toBeLessThanOrEqual(64);
  });

  test("el indicador del encabezado dice si el perfil está completo", async ({ page, context }) => {
    await abrir(page, context, () => ({ status: 200, json: { organizaciones: [FILA] } }));
    await expect(page.getByText("Organización configurada", { exact: true })).toBeVisible();
    await expect(page.getByText(/Calibrado|Ficha Pendiente/)).toHaveCount(0);
  });
});
