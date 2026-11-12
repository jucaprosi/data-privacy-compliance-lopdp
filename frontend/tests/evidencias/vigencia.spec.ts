/**
 * EVI-02: vigencia, visibilidad y paquete para inspección en la Bóveda de Evidencias.
 *
 * Usa el ajuste de prueba `window.__LOPDP_EVIDENCIA_PRUEBAS__` (solo fuera de producción) y la subida firmada simulada
 * de `../utiles`, que enciende `subida_firmada` y sirve el registro. Las rutas propias de EVI-02 (atributos y paquete)
 * se simulan aquí: ninguna otra función las mockea.
 *
 * Mutación documentada (EVI-02): en `src/components/evidencias/PaqueteInspeccion.tsx`, mostrar siempre «Vigente»
 * (ignorar `d.vigente`) -> «un documento vencido se ve como vencido y sin respaldo» falla.
 */
import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { simularApiDiagnostico } from "../diagnostico/simulador";
import { abrirAppLimpia, barraDeMenus, configurarProyecto, simularSubidaFirmada } from "../utiles";

const PDF = { name: "politica.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4 politica") };

interface AtributosSimulados {
  documento_id: string;
  codigo: string;
  nombre_archivo: string;
  tipo_mime: string;
  tamano_bytes: number;
  sha256_hash: string;
  subido_en: string;
  vence_en: string | null;
  vigente: boolean;
  visible_para: string[];
  controles_vinculados: number[];
}

async function simularVigencia(
  context: BrowserContext,
  opciones: { vencido?: boolean; paquete?: "ok" | "vacio" } = {}
) {
  const estado = { guardados: [] as unknown[], paquetes: 0 };
  const documentos: AtributosSimulados[] = [
    {
      documento_id: "doc-1", codigo: "EVD-2026-0001", nombre_archivo: "politica.pdf", tipo_mime: "application/pdf",
      tamano_bytes: 17, sha256_hash: "a".repeat(64), subido_en: new Date().toISOString(),
      vence_en: opciones.vencido ? "2020-01-01" : null, vigente: !opciones.vencido,
      visible_para: ["coordinador", "dpo", "implementador", "admin_organizacion"], controles_vinculados: [],
    },
  ];
  await context.route("**/api/v1/evidencias/atributos", (ruta) => ruta.fulfill({ json: { total: documentos.length, documentos } }));
  await context.route("**/api/v1/evidencias/documentos/*/atributos", async (ruta) => {
    estado.guardados.push(ruta.request().postDataJSON());
    await ruta.fulfill({ json: { status: "SUCCESS" } });
  });
  await context.route("**/api/v1/evidencias/paquete-inspeccion", async (ruta) => {
    estado.paquetes += 1;
    if (opciones.paquete === "vacio") {
      return ruta.fulfill({ status: 409, json: { detail: "texto tecnico del servidor", code: "EVI_PAQUETE_VACIO" } });
    }
    return ruta.fulfill({ status: 200, contentType: "application/zip", body: Buffer.from("PK\u0003\u0004") });
  });
  return estado;
}

/** Por el menú, no con irASala: la tabla de submenús se evalúa en Node, donde el ajuste del navegador no existe. */
async function irALaBoveda(page: Page) {
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Biblioteca" }).getByRole("button", { name: /^Evidencias/ }).click();
}

async function abrirBoveda(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
  await page.locator('input[type="file"]').first().setInputFiles(PDF);
  await expect(page.getByTestId("evidencia-en-servidor")).toBeVisible();
  await irALaBoveda(page);
  await expect(page.getByTestId("paquete-inspeccion")).toBeVisible();
}

test.describe("Vigencia y paquete para inspección (EVI-02)", () => {
  test.beforeEach(async ({ context }) => {
    await context.addInitScript(() => {
      window.__LOPDP_EVIDENCIA_PRUEBAS__ = true;
    });
  });

  test("un documento vencido se ve como vencido y sin respaldo", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularSubidaFirmada(context);
    await simularVigencia(context, { vencido: true });
    await abrirBoveda(page);
    await expect(page.getByTestId("documento-vencido")).toContainText("no respalda ningún requisito");
    await expect(page.getByText(/Vigente/)).toHaveCount(0);
  });

  test("el DPO cambia la vigencia y la visibilidad de un documento", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularSubidaFirmada(context);
    const estado = await simularVigencia(context);
    await abrirBoveda(page);
    await page.getByRole("button", { name: /Cambiar vigencia y visibilidad de EVD-2026-0001/ }).click();
    await page.getByLabel("Vence el").fill("2030-12-31");
    await page.getByLabel("Implementador").uncheck();
    await page.getByRole("button", { name: "Guardar" }).click();
    await expect.poll(() => estado.guardados.length).toBe(1);
    expect(estado.guardados[0]).toEqual({
      vence_en: "2030-12-31",
      visible_para: ["coordinador", "dpo", "admin_organizacion"],
    });
  });

  test("quien no es DPO no ve cómo cambiar la vigencia, pero sí descarga el paquete", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["coordinador"] });
    const servidor = await simularSubidaFirmada(context);
    // El coordinador no sube antes del real: el documento ya está registrado en el servidor.
    servidor.documentos.push({
      id: "doc-1", codigo: "EVD-2026-0001", nombre_archivo: "politica.pdf", tipo_mime: "application/pdf",
      tamano_bytes: 17, sha256_hash: "a".repeat(64), normativa: "LOPDP", subido_por: "usuario-simulado",
      subido_en: new Date().toISOString(), retencion_dias: 1825, controles_vinculados: [],
    });
    const estado = await simularVigencia(context);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irALaBoveda(page);
    await expect(page.getByTestId("paquete-inspeccion")).toBeVisible();
    const boton = page.getByRole("button", { name: "Descargar paquete para inspección" });
    await expect(boton).toBeVisible();
    await expect(page.getByRole("button", { name: /Cambiar vigencia y visibilidad/ })).toHaveCount(0);
    const descarga = page.waitForEvent("download");
    await boton.click();
    expect((await descarga).suggestedFilename()).toMatch(/^paquete-inspeccion-\d{4}-\d{2}-\d{2}\.zip$/);
    expect(estado.paquetes).toBe(1);
  });

  test("sin documentos vigentes y visibles, el paquete muestra un mensaje fijo", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["dpo"] });
    await simularSubidaFirmada(context);
    await simularVigencia(context, { paquete: "vacio" });
    await abrirBoveda(page);
    await page.getByRole("button", { name: "Descargar paquete para inspección" }).click();
    const alerta = page.getByRole("alert").filter({ hasText: "No hay documentos vigentes y visibles" });
    await expect(alerta).toBeVisible();
    await expect(alerta).not.toContainText(/tecnico|EVI_/);
  });
});
