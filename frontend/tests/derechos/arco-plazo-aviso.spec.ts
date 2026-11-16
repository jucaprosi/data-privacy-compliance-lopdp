/**
 * DER-07 · Plazo legal estimado y aviso provisional en la pantalla de derechos de los titulares.
 *
 * La pantalla solo muestra lo que llega en `plazo_dias`, `plazo_unidad` y `plazo_estimado` (DER-05).
 * Valores simulados. Mutación: reponer «SLA», «laborables», «Art. 37» o «72h» en un texto visible
 * hace fallar la última prueba.
 */
import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { simularApiDiagnostico } from "../diagnostico/simulador";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const DIA = 86_400_000;

function solicitud(id: string, tipo: string, dias: number, plazo: number, unidad: string, estimado: boolean) {
  const vence = Date.now() + dias * DIA;
  return {
    id,
    tipo_solicitud: tipo,
    estado: "RECIBIDA",
    nombre_solicitante: "Titular Simulado",
    cedula_solicitante: "0000000000",
    fecha_recepcion: new Date(vence - plazo * DIA).toISOString(),
    fecha_vencimiento: new Date(vence).toISOString(),
    plazo_dias: plazo,
    plazo_unidad: unidad,
    plazo_estimado: estimado,
  };
}

async function abrirDerechos(page: Page, context: BrowserContext, filas: unknown[]): Promise<void> {
  await simularApiDiagnostico(context, { roles: ["dpo"] });
  await context.route("**/api/v1/arco/solicitudes", (ruta) => ruta.fulfill({ status: 200, json: filas }));
  await page.setViewportSize({ width: 1280, height: 800 });
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Derechos ARCO/);
  await expect(page.getByRole("heading", { name: /Derechos ARCO\+ y Titulares/ })).toBeVisible();
}

const aviso = (page: Page) => page.getByTestId("aviso-plazo-provisional");

test.describe("Derechos de los titulares: plazo legal estimado (DER-07)", () => {
  test("con unidad estimada se ve el plazo con su unidad y el aviso provisional", async ({ page, context }) => {
    await abrirDerechos(page, context, [solicitud("a1", "ACCESO", 10, 15, "corridos", true)]);
    await expect(page.getByText("Plazo legal estimado", { exact: true })).toBeVisible();
    await expect(page.getByText(/15 días corridos · vence el \d{2}\/\d{2}\/\d{4}/)).toBeVisible();
    await expect(aviso(page)).toBeVisible();
    await expect(aviso(page)).toHaveAttribute("role", "note");
    await expect(aviso(page)).toContainText("Criterio provisional");
    await expect(page.getByText(/arts\. 13 a 16: las solicitudes de acceso/)).toBeVisible();
  });

  test("con unidad confirmada el aviso desaparece", async ({ page, context }) => {
    await abrirDerechos(page, context, [solicitud("a2", "PORTABILIDAD", 5, 10, "habiles", false)]);
    await expect(page.getByText(/10 días hábiles · vence el/)).toBeVisible();
    await expect(aviso(page)).toHaveCount(0);
  });

  test("hábiles con estimado verdadero conserva el aviso", async ({ page, context }) => {
    await abrirDerechos(page, context, [solicitud("a6", "ACCESO", 5, 15, "habiles", true)]);
    await expect(aviso(page)).toBeVisible();
  });

  test("por confirmar se muestra sin unidad y con aviso", async ({ page, context }) => {
    await abrirDerechos(page, context, [solicitud("a3", "ACCESO", 5, 15, "por confirmar", false)]);
    await expect(page.getByText(/^15 días · vence el/)).toBeVisible();
    await expect(aviso(page)).toBeVisible();
  });

  test("la solicitud vencida lleva texto «Vencido por N días»", async ({ page, context }) => {
    await abrirDerechos(page, context, [solicitud("a4", "ACCESO", -3, 15, "corridos", true)]);
    await expect(page.getByText(/Vencido por \d+ días/)).toBeVisible();
  });

  test("ningún texto visible del módulo nombra Art. 37, laborables, SLA ni 72 h", async ({ page, context }) => {
    await abrirDerechos(page, context, [solicitud("a5", "ACCESO", 10, 15, "corridos", true)]);
    const texto = await page.getByRole("main").innerText();
    expect(texto).not.toMatch(/Art\.? ?37|laborables?|\bSLA\b|72 ?h/i);
  });
});
