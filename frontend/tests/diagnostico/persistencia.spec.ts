/**
 * DIAG-01: el diagnóstico se guarda en el servidor y se lee de él.
 *
 * La API se simula a nivel de contexto (compartida por todas las pestañas) con un «servidor» en
 * memoria: así se comprueba qué envía la interfaz y que una pestaña nueva muestra lo que hay
 * guardado, aunque no lo haya respondido ella. Desde DIAG-03 responde el DPO.
 */
import { expect, test } from "@playwright/test";

import { etiquetaEstadoCumplimiento } from "../../src/lib/estadosCumplimiento";
import { abrirAppLimpia, configurarProyecto, irASala, responderControlActual } from "../utiles";
import { simularApiDiagnostico } from "./simulador";

test.describe("Diagnóstico guardado en el servidor (DIAG-01)", () => {
  test("responder un control envía solo esa respuesta, con su pregunta, control y dimensión", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["dpo"] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);
    const enviosPrevios = servidor.envios.length;

    await responderControlActual(page, "Parcial");

    await expect.poll(() => servidor.envios.length).toBe(enviosPrevios + 1);
    const enviado = servidor.envios.at(-1)!;
    expect(enviado).toHaveLength(1);
    expect(enviado[0].estado).toBe("Parcial");
    expect(enviado[0].pregunta_id).toBeGreaterThan(0);
    expect(enviado[0].control.trim().length).toBeGreaterThan(0);
    expect(enviado[0].dimension).toMatch(/^D(0[1-9]|10)$/);
  });

  test("otra pestaña muestra la respuesta que hay en el servidor", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["dpo"] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);
    await responderControlActual(page, "Parcial");
    await expect.poll(() => servidor.filas.length).toBe(1);

    // Otra persona cambia la respuesta en el servidor.
    servidor.filas = [{ ...servidor.filas[0], estado: "No Conforme" }];

    // Pestaña nueva del mismo navegador: sin el script que limpia el almacenamiento, conserva la
    // ficha y el control en pantalla, y al hidratarse lee del servidor.
    const otra = await context.newPage();
    await otra.goto("/");
    // El aviso de la dimensión (AlertaDimension, diálogo modal) se abre al volver a la pregunta.
    await otra.getByRole("button", { name: "Cerrar alerta" }).click();
    await irASala(otra, /Normativa/);
    const noConforme = otra.getByRole("button", { name: etiquetaEstadoCumplimiento("No Conforme"), exact: true });
    await expect(noConforme).toHaveAttribute("aria-pressed", "true");
  });
});
