/**
 * Arnés de interfaz del tablero de madurez SGPDP.
 *
 * Fija en el navegador las reglas que `tests/test_assessment_matriz.py` fija en
 * el motor: que el tope de nivel llegue hasta la pantalla y se explique. Un
 * cálculo correcto que la interfaz presenta como un nivel alcanzado sin matices
 * engaña igual que un cálculo equivocado.
 */
import { expect, test } from "@playwright/test";

import {
  abrirAppLimpia,
  configurarProyecto,
  irASala,
  panelAssessment,
  responderControlActual,
} from "./utiles";

test.describe("Tablero de resultados del assessment", () => {
  test.beforeEach(async ({ page }) => {
    await abrirAppLimpia(page);
    await configurarProyecto(page);
  });

  test("sin respuestas no inventa un resultado", async ({ page }) => {
    await irASala(page, /Dashboard Central/);

    await expect(page.getByText("Sin Evaluación Registrada")).toBeVisible();
    // Declara el alcance aunque no haya nada evaluado: el usuario tiene que
    // saber contra cuántos controles se le va a medir.
    await expect(page.getByText(/\d+ controles aplicables en el alcance podado/)).toBeVisible();
  });

  test("con cobertura insuficiente no emite nivel y dice por qué", async ({ page }) => {
    // Un solo control respondido deja la cobertura muy por debajo del 60 %.
    await irASala(page, /Normativa/);
    await responderControlActual(page, "Conforme");
    await irASala(page, /Dashboard Central/);

    const panel = panelAssessment(page);
    await expect(panel.getByText("Nivel 0").first()).toBeVisible();
    await expect(panel.getByText("Sin evaluación suficiente").first()).toBeVisible();

    // La causa se declara, no se deja deducir del número.
    await expect(panel.getByText("Condiciones que limitan el nivel.")).toBeVisible();
    await expect(
      panel.getByText(/por debajo del mínimo exigido para emitir un nivel/)
    ).toBeVisible();
  });

  test("un control declarado sin sustento documental no acredita madurez", async ({ page }) => {
    await irASala(page, /Normativa/);
    // "Parcial" arranca en E1 (mínimo de su rango): un control de alta
    // criticidad sostenido solo en un borrador no basta como evidencia
    // suficiente, así que el diagnóstico topa el nivel y lo explica. Con
    // "Conforme" no se puede reproducir este caso: su rango exige E2 o E3,
    // que ya satisfacen el mínimo de evidencia exigido.
    await responderControlActual(page, "Parcial");
    await irASala(page, /Dashboard Central/);

    const panel = panelAssessment(page);
    await expect(
      panel.getByText(/sin evidencia suficiente, sostenidos solo en la declaración/)
    ).toBeVisible();
  });

  test("la cobertura mostrada concuerda con los controles del alcance", async ({ page }) => {
    await irASala(page, /Normativa/);
    await responderControlActual(page, "Conforme");
    await irASala(page, /Dashboard Central/);

    // El mosaico dice "1 de N controles aplicables"; el porcentaje que lo
    // encabeza tiene que ser exactamente 1/N, no una cifra sobre otra base.
    const mosaico = panelAssessment(page).getByRole("group", { name: "Cobertura" });
    await expect(mosaico).toBeVisible();

    const detalle = mosaico.getByText(/^\d+ de \d+ controles aplicables$/);
    const [evaluados, aplicables] = (await detalle.innerText()).match(/\d+/g)!.map(Number);
    expect(aplicables).toBeGreaterThan(evaluados);

    const porcentaje = await mosaico.getByText(/^\d+(\.\d+)?%$/).innerText();
    const esperado = Math.round((evaluados / aplicables) * 1000) / 10;
    expect(Number.parseFloat(porcentaje)).toBeCloseTo(esperado, 1);
  });

  test("la portada invita a explorar sin llamar demostrada a una lectura sin documentos", async ({ page }) => {
    await irASala(page, /Normativa/);
    await responderControlActual(page, "Conforme");
    await irASala(page, /Dashboard Central/);

    const portada = panelAssessment(page);
    await expect(portada.getByRole("heading", { name: /Necesitamos consolidar su respaldo documental/ })).toBeVisible();
    await expect(portada.getByText(/no representa madurez demostrada/)).toBeVisible();
    await portada.getByRole("link", { name: /Consultar prioridades/ }).click();
    await expect(page.locator("#assessment-bases")).toBeInViewport();
  });
});
