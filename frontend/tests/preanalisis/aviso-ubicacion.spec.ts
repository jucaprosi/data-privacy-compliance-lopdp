// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * IA-09 · Aviso de consentimiento del preanálisis con la ubicación real donde se procesa.
 *
 * Verifica en navegador real (Diagnóstico › Preanálisis):
 *  - Con una ubicación distinta (p. ej. "servidores en Irlanda"), muestra exactamente esa ubicación en
 *    `consentimiento-destino`, la etiqueta corta con `title` en `PanelPreanalisis` y el párrafo del panel.
 *  - Con `ubicacion: null`, muestra proveedor y modelo sin país ni marcadores provisionales.
 *  - Sin configuración (`disponible: false`), muestra "No podemos mostrar a quién se enviarían los datos. Por eso no los enviamos."
 *    y no renderiza el botón de envío.
 *  - Ningún texto visible contiene "adecuad", "conforme" ni "provisional".
 */
import { createHash } from "node:crypto";

import { expect, test, type Browser, type BrowserContext, type Page } from "@playwright/test";

import { simularApiDiagnostico } from "../diagnostico/simulador";
import { abrirAppLimpia, configurarProyecto, simularSubidaFirmada } from "../utiles";

const DOCUMENTO = {
  name: "politica-privacidad.pdf",
  mimeType: "application/pdf",
  buffer: Buffer.from("%PDF-1.4 politica de privacidad y tratamiento"),
};
const SHA256_DOCUMENTO = createHash("sha256").update(DOCUMENTO.buffer).digest("hex");

interface EstadoSimulado {
  disponible: boolean;
  proveedor: string | null;
  modelo: string | null;
  motivo: string | null;
  ubicacion: string | null;
}

const PROHIBIDOS_VISIBLES = /adecuad|conforme|provisional|por confirmar|Estados Unidos/i;
const PROHIBIDOS_AVISO = /adecuad|conforme|provisional|por confirmar|pendiente|Estados Unidos/i;

async function prepararContextoConEvidencia(browser: Browser): Promise<BrowserContext> {
  const context = await browser.newContext();
  await simularApiDiagnostico(context, { roles: ["admin_organizacion"], usuario: "usuario-admin-ia09" });
  const almacen = await simularSubidaFirmada(context);
  almacen.documentos.push({
    id: "doc-ia09",
    codigo: "EVD-2026-0001",
    nombre_archivo: DOCUMENTO.name,
    tipo_mime: DOCUMENTO.mimeType,
    tamano_bytes: DOCUMENTO.buffer.length,
    sha256_hash: SHA256_DOCUMENTO,
    normativa: "LOPDP",
    subido_por: "usuario-dpo-ia09",
    subido_en: "2026-11-19T12:00:00Z",
    retencion_dias: 1825,
    controles_vinculados: [1],
  });

  const inicial = await context.newPage();
  await abrirAppLimpia(inicial);
  await configurarProyecto(inicial, "Entidad IA-09");
  await expect(inicial.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
  await inicial.close();
  return context;
}

async function simularPreanalisis(page: Page, estadoActual: () => EstadoSimulado): Promise<void> {
  await page.route("**/api/v1/preanalisis/**", async (route) => {
    const ruta = new URL(route.request().url()).pathname;
    if (ruta.endsWith("/preanalisis/estado")) {
      await route.fulfill({ json: estadoActual() });
      return;
    }
    if (ruta.endsWith("/preanalisis/preparar")) {
      await route.fulfill({
        json: {
          formato: "pdf",
          caracteres_totales: 49,
          fragmentos: [{ texto: "politica de privacidad y tratamiento", origen: "p. 1", relevancia: 1 }],
          pii_enmascarada: 0,
          advertencias: [],
        },
      });
      return;
    }
    await route.fallback();
  });
}

async function abrirDiagnostico(page: Page): Promise<void> {
  await page.goto("/");
  const alerta = page.getByRole("button", { name: "Cerrar alerta" });
  await alerta.waitFor({ state: "visible", timeout: 5000 }).catch(() => undefined);
  if (await alerta.isVisible()) await alerta.click();
  await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
  await expect(page.getByText("EVD-2026-0001", { exact: true })).toBeVisible();
}

async function abrirDialogoConsentimiento(page: Page) {
  await page.getByRole("button", { name: "Analizar con IA" }).first().click();
  await page.getByLabel("Volver a presentar el archivo").setInputFiles(DOCUMENTO);
  const dialogo = page.getByRole("dialog", { name: "Confirmar envío al modelo de IA" });
  await expect(dialogo).toBeVisible();
  return dialogo;
}

async function verificarTextosSinEncuadre(page: Page, textoDialogo?: string): Promise<void> {
  const textoVisible = await page.locator("body").innerText();
  expect(textoVisible).not.toMatch(PROHIBIDOS_VISIBLES);
  expect(textoVisible).not.toContain("PENDIENTE");
  const panelPreanalisis = page.getByRole("heading", { name: "Pre-llenado asistido" }).locator("xpath=../..");
  expect(await panelPreanalisis.innerText()).not.toMatch(PROHIBIDOS_AVISO);
  if (textoDialogo !== undefined) {
    expect(textoDialogo).not.toMatch(PROHIBIDOS_AVISO);
    expect(textoDialogo).not.toContain("PENDIENTE");
  }
}

test.describe("IA-09 · aviso de ubicación en preanálisis", () => {
  test("muestra la ubicación simulada en el panel, su title y consentimiento-destino", async ({ browser }) => {
    const context = await prepararContextoConEvidencia(browser);
    try {
      const page = await context.newPage();
      const estado: EstadoSimulado = {
        disponible: true,
        proveedor: "Servicio Simulado",
        modelo: "modelo-ia09",
        motivo: null,
        ubicacion: "servidores en Irlanda",
      };
      await simularPreanalisis(page, () => estado);
      await abrirDiagnostico(page);

      const fraseEsperada =
        "Estos fragmentos se envían a Servicio Simulado (modelo modelo-ia09), que los procesa en servidores en Irlanda.";
      const etiqueta = page.getByText("Servicio Simulado · Irlanda", { exact: true });
      await expect(etiqueta).toBeVisible();
      await expect(etiqueta).toHaveAttribute("title", fraseEsperada);
      await expect(
        page.getByText(
          "La IA solo propone; nada se aplica sin tu decisión. Solo saldrán fragmentos enmascarados a Servicio Simulado; verás el texto exacto antes de autorizar el envío."
        )
      ).toBeVisible();

      const dialogo = await abrirDialogoConsentimiento(page);
      await expect(dialogo.getByTestId("consentimiento-destino")).toHaveText(fraseEsperada);
      await expect(dialogo.getByRole("button", { name: "Enviar y analizar" })).toBeVisible();
      await verificarTextosSinEncuadre(page, await dialogo.innerText());
    } finally {
      await context.close();
    }
  });

  test("con ubicacion null muestra proveedor y modelo sin país ni marcadores provisionales", async ({ browser }) => {
    const context = await prepararContextoConEvidencia(browser);
    try {
      const page = await context.newPage();
      const estado: EstadoSimulado = {
        disponible: true,
        proveedor: "Servicio Simulado",
        modelo: "modelo-ia09",
        motivo: null,
        ubicacion: null,
      };
      await simularPreanalisis(page, () => estado);
      await abrirDiagnostico(page);

      const fraseEsperada = "Estos fragmentos se envían a Servicio Simulado (modelo modelo-ia09).";
      const etiqueta = page.getByText("Servicio Simulado", { exact: true });
      await expect(etiqueta).toBeVisible();
      await expect(etiqueta).toHaveAttribute("title", fraseEsperada);
      await expect(
        page.getByText(
          "La IA solo propone; nada se aplica sin tu decisión. Solo saldrán fragmentos enmascarados a Servicio Simulado; verás el texto exacto antes de autorizar el envío."
        )
      ).toBeVisible();

      const dialogo = await abrirDialogoConsentimiento(page);
      const destino = dialogo.getByTestId("consentimiento-destino");
      await expect(destino).toHaveText(fraseEsperada);
      await expect(destino).not.toContainText("servidores en");
      await verificarTextosSinEncuadre(page, await dialogo.innerText());
    } finally {
      await context.close();
    }
  });

  test("sin configuración bloquea el envío y no muestra el botón de autorizar", async ({ browser }) => {
    const context = await prepararContextoConEvidencia(browser);
    try {
      // 1. Desde el inicio sin configuración: no ofrece Analizar con IA.
      const paginaApagada = await context.newPage();
      await simularPreanalisis(paginaApagada, () => ({
        disponible: false,
        proveedor: null,
        modelo: null,
        motivo: "Servicio sin configurar.",
        ubicacion: null,
      }));
      await abrirDiagnostico(paginaApagada);
      await expect(paginaApagada.getByRole("button", { name: "Analizar con IA" })).toHaveCount(0);
      await expect(paginaApagada.getByText(/El análisis con IA no está disponible/)).toBeVisible();
      await expect(paginaApagada.locator("body")).not.toContainText("null");
      await verificarTextosSinEncuadre(paginaApagada);
      await paginaApagada.close();

      // 2. Si deja de estar disponible al abrir el consentimiento: aviso fijo y sin botón de envío.
      const page = await context.newPage();
      let estado: EstadoSimulado = {
        disponible: true,
        proveedor: "Servicio Simulado",
        modelo: "modelo-ia09",
        motivo: null,
        ubicacion: "servidores en Irlanda",
      };
      await simularPreanalisis(page, () => estado);
      await abrirDiagnostico(page);

      estado = {
        disponible: false,
        proveedor: null,
        modelo: null,
        motivo: "No disponible.",
        ubicacion: null,
      };
      const dialogo = await abrirDialogoConsentimiento(page);
      await expect(dialogo.getByTestId("consentimiento-destino")).toHaveText(
        "No podemos mostrar a quién se enviarían los datos. Por eso no los enviamos."
      );
      await expect(dialogo.getByRole("button", { name: "Enviar y analizar" })).toHaveCount(0);
      await verificarTextosSinEncuadre(page, await dialogo.innerText());
    } finally {
      await context.close();
    }
  });
});
