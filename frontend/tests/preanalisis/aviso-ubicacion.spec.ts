// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * IA-09 / IA-15 · Aviso de consentimiento del preanálisis con el país y la región donde se procesa.
 *
 * Verifica en navegador real (Diagnóstico › Preanálisis):
 *  - Con `ubicacion` (país) y `region` del estado, el aviso dice «Se procesan en {pais} (región {region}), fuera de
 *    Ecuador.» y la etiqueta corta es «{destinatario} · {pais}, {region}» con `title` hacia el texto completo.
 *  - Con el país Ecuador no dice «fuera de Ecuador».
 *  - Sin `region` o sin `ubicacion`, no se ofrece el consentimiento y aparece un `role="status"` (falla cerrado).
 *  - Sin configuración (`disponible: false`), se mantiene el texto de IA-09 y no se pinta el botón de envío.
 *  - Ni el país ni la región están escritos a mano en `frontend/src/` (m3); nada recorta «servidores en …» (m1).
 *  - Ningún texto del panel o del aviso contiene las palabras prohibidas de la especificación IA-15 §4.
 */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import path from "node:path";

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
  region: string | null;
}

const PROHIBIDOS_VISIBLES = /adecuad|conforme|provisional|por confirmar/i;
const PROHIBIDOS_AVISO = /adecuad|conforme|provisional|por confirmar|pendiente|seguro|garantiza|cumple|puede estar/i;
const MENSAJE_FALLA_CERRADO = "El preanálisis no está disponible: falta configurar dónde se procesan los datos.";
const ESTADO_US: EstadoSimulado = {
  disponible: true,
  proveedor: "Google Vertex AI",
  modelo: "gemini-3.8-flash",
  motivo: null,
  ubicacion: "Estados Unidos",
  region: "us",
};
const RAIZ_SRC = path.resolve(__dirname, "../../src");

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

test.describe("IA-15 · aviso de país y región en preanálisis", () => {
  test("nombra el país y la región del estado en la etiqueta, su title y el consentimiento", async ({ browser }) => {
    const context = await prepararContextoConEvidencia(browser);
    try {
      const page = await context.newPage();
      await simularPreanalisis(page, () => ESTADO_US);
      await abrirDiagnostico(page);

      const fraseEsperada =
        "Estos fragmentos se envían a Google Vertex AI para procesarlos con el modelo gemini-3.8-flash. Se procesan en Estados Unidos (región us), fuera de Ecuador.";
      const etiqueta = page.getByText("Google Vertex AI · Estados Unidos, us", { exact: true });
      await expect(etiqueta).toBeVisible();
      await expect(etiqueta).toHaveAttribute("title", fraseEsperada);

      const dialogo = await abrirDialogoConsentimiento(page);
      await expect(dialogo.getByTestId("consentimiento-destino")).toHaveText(fraseEsperada);
      await expect(dialogo.getByRole("button", { name: "Enviar y analizar" })).toBeVisible();
      await verificarTextosSinEncuadre(page, await dialogo.innerText());
    } finally {
      await context.close();
    }
  });

  test("con Ecuador como país no dice «fuera de Ecuador»", async ({ browser }) => {
    const context = await prepararContextoConEvidencia(browser);
    try {
      const page = await context.newPage();
      await simularPreanalisis(page, () => ({ ...ESTADO_US, ubicacion: "Ecuador", region: "quito" }));
      await abrirDiagnostico(page);
      const dialogo = await abrirDialogoConsentimiento(page);
      await expect(dialogo.getByTestId("consentimiento-destino")).toHaveText(
        "Estos fragmentos se envían a Google Vertex AI para procesarlos con el modelo gemini-3.8-flash. Se procesan en Ecuador (región quito)."
      );
    } finally {
      await context.close();
    }
  });

  for (const [nombre, falta] of [
    ["sin region", { region: null }],
    ["sin ubicacion", { ubicacion: null }],
    ["con region vacía", { region: "  " }],
  ] as const) {
    test(`falla cerrado ${nombre}: sin consentimiento y con aviso de estado`, async ({ browser }) => {
      const context = await prepararContextoConEvidencia(browser);
      try {
        const page = await context.newPage();
        await simularPreanalisis(page, () => ({ ...ESTADO_US, ...falta }));
        await abrirDiagnostico(page);
        await expect(page.getByRole("status").filter({ hasText: MENSAJE_FALLA_CERRADO })).toBeVisible();
        await expect(page.getByRole("button", { name: "Analizar con IA" })).toHaveCount(0);
        await expect(page.getByRole("dialog")).toHaveCount(0);
        await expect(page.locator("body")).not.toContainText("undefined");
        await expect(page.locator("body")).not.toContainText("null");
        await verificarTextosSinEncuadre(page);
      } finally {
        await context.close();
      }
    });
  }

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
        region: null,
      }));
      await abrirDiagnostico(paginaApagada);
      await expect(paginaApagada.getByRole("button", { name: "Analizar con IA" })).toHaveCount(0);
      await expect(paginaApagada.getByText(/El análisis con IA no está disponible/)).toBeVisible();
      await expect(paginaApagada.locator("body")).not.toContainText("null");
      await verificarTextosSinEncuadre(paginaApagada);
      await paginaApagada.close();

      // 2. Si deja de estar disponible al abrir el consentimiento: aviso fijo y sin botón de envío.
      const page = await context.newPage();
      let estado: EstadoSimulado = ESTADO_US;
      await simularPreanalisis(page, () => estado);
      await abrirDiagnostico(page);

      estado = { disponible: false, proveedor: null, modelo: null, motivo: "No disponible.", ubicacion: null, region: null };
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

  test("el código de los componentes no escribe el país, la región ni recorta «servidores en»", () => {
    const archivos = [
      "components/preanalisis/ConsentimientoEnvio.tsx",
      "components/preanalisis/PanelPreanalisis.tsx",
      "lib/preanalisis/cliente.ts",
      "lib/preanalisis/tipos.ts",
    ];
    for (const rel of archivos) {
      const texto = readFileSync(path.join(RAIZ_SRC, rel), "utf-8");
      expect(texto, `${rel}: país escrito a mano`).not.toMatch(/Estados Unidos/);
      expect(texto, `${rel}: región escrita a mano`).not.toMatch(/(["'`])us\1/);
      expect(texto, `${rel}: recorta o nombra «servidores»`).not.toMatch(/servidores/i);
    }
  });
});
