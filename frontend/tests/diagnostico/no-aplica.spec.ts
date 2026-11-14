/**
 * DIAG-05: «no aplica» exige una justificación en el assessment. ¤diagnostico-no-aplica
 *
 * Con la API simulada en memoria: marcar «no aplica» pide la justificación; sin una de al menos 10
 * caracteres no se envía nada; con ella se envía junto a la respuesta (sin autor, lo fija el
 * servidor), y una pestaña nueva la muestra al revisar.
 */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala, responderControlActual } from "../utiles";
import { simularApiDiagnostico } from "./simulador";
import type { RespuestaServidor } from "../../src/lib/diagnostico/clienteRespuestas";

const JUSTIFICACION = "La organización no trata datos de menores de edad";

test.describe("«No aplica» con justificación (DIAG-05)", () => {
  test("sin justificación no se envía; con ella se envía y se conserva", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["admin_organizacion"] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);
    await responderControlActual(page, 1);
    await expect.poll(() => servidor.envios.length).toBeGreaterThan(0);
    const enviosPrevios = servidor.envios.length;

    await page.getByTestId("no-aplica").check();
    const campo = page.getByLabel("Justificación (obligatoria)");
    await expect(campo).toBeVisible();
    await expect(campo).toHaveAttribute("aria-invalid", "true");
    await campo.fill("corta");
    await expect(page.locator("#ayuda-no-aplica")).toContainText("al menos 10 caracteres");
    await page.waitForTimeout(300);
    expect(servidor.envios.length).toBe(enviosPrevios);

    await campo.fill(JUSTIFICACION);
    await expect(campo).toHaveAttribute("aria-invalid", "false");
    await expect.poll(() => servidor.envios.length).toBeGreaterThan(enviosPrevios);
    // La fila enviada sigue el contrato del cliente, que declara los campos de «no aplica».
    const enviado = servidor.envios.at(-1)![0] as RespuestaServidor;
    expect(enviado.no_aplica).toBe(true);
    expect(enviado.justificacion_no_aplica).toBe(JUSTIFICACION);
    expect(enviado).not.toHaveProperty("justificado_por");
  });

  test("al revisar, otra persona ve la justificación y su autor", async ({ page, context, browser }) => {
    // El DPO responde la pregunta en pantalla; se toma su fila tal como la guardaría el servidor.
    const servidorDpo = await simularApiDiagnostico(context, { roles: ["admin_organizacion"] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);
    await responderControlActual(page, 1);
    await page.getByTestId("no-aplica").check();
    await page.getByLabel("Justificación (obligatoria)").fill(JUSTIFICACION);
    await expect.poll(() => servidorDpo.filas.some((f) => (f as RespuestaServidor).no_aplica)).toBe(true);
    const fila = { ...servidorDpo.filas.find((f) => (f as RespuestaServidor).no_aplica)!, justificado_por: "dpo-prueba" };

    // Otra persona, con un rol que solo consulta, abre el diagnóstico en su propio navegador.
    const otro = await browser.newContext();
    await simularApiDiagnostico(otro, { roles: ["implementador"], filas: [fila] });
    const preparacion = await otro.newPage();
    await abrirAppLimpia(preparacion);
    await configurarProyecto(preparacion);
    await irASala(preparacion, /Normativa/);
    // Pestaña nueva: conserva la ficha y, al hidratarse, lee las respuestas del servidor.
    const revisor = await otro.newPage();
    await revisor.goto("/");
    await revisor.getByRole("button", { name: "Cerrar alerta" }).click();
    await irASala(revisor, /Normativa/);
    const revision = revisor.getByTestId("no-aplica-revision");
    await expect(revision).toContainText(JUSTIFICACION);
    await expect(revision).toContainText("dpo-prueba");
    await expect(revisor.getByTestId("no-aplica")).toHaveCount(0);
    await otro.close();
  });
});
