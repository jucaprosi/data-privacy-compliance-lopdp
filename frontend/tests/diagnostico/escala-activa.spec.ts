// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * DIAG-09 con la evidencia física encendida (EVYDENTIA, FE-26): la propuesta de la IA sobre un archivo
 * subido a la carga de evidencias marca el rango del estado y deja el nivel sin elegir.
 *
 * Usa el ajuste de prueba `window.__LOPDP_EVIDENCIA_PRUEBAS__`, que solo existe fuera de producción,
 * y corre en el proyecto «desarrollo» (convención `*-activa.spec.ts`). El resto de la escala está en
 * `escala.spec.ts`.
 *
 * DIAG-07 R6: tres sesiones con un solo rol cada una (ORG-13). El DPO sube y vincula la evidencia, el
 * administrador pide la propuesta de la IA y elige el nivel y el escalón, y el DPO sella. Mutaciones del §5:
 * sin evidencia vinculada, el panel del administrador no ofrece «Analizar con IA» y muestra el aviso
 * (segunda prueba); en la sesión del administrador no aparecen la carga ni la vinculación (paso 2); en la
 * del DPO no aparecen el selector de nivel ni el escalón (paso 1).
 */
import { expect, test, type Browser, type BrowserContext, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, responderControlActual, simularSubidaFirmada } from "../utiles";
import { simularRespuestasDiagnostico08 } from "./respuestas08";
import { abrirCierreDelDiagnostico, simularApiDiagnostico } from "./simulador";

async function simularIA(page: Page): Promise<string[]> {
  const pedidas: string[] = [];
  await page.route("**/api/v1/preanalisis/**", async (route) => {
    const ruta = new URL(route.request().url()).pathname;
    if (ruta.endsWith("/preanalisis/estado")) {
      await route.fulfill({ json: { disponible: true, proveedor: "simulado", modelo: "qa-09", motivo: null, ubicacion: "Estados Unidos", region: "us" } });
    } else if (ruta.endsWith("/preanalisis/preparar")) {
      await route.fulfill({
        json: {
          formato: "pdf",
          caracteres_totales: 49,
          fragmentos: [{ texto: "politica de privacidad y tratamiento", origen: "p. 1", relevancia: 1 }],
          pii_enmascarada: 0,
          advertencias: [],
        },
      });
    } else if (ruta.endsWith("/preanalisis/analizar")) {
      const cuerpo = route.request().postDataJSON() as { dimension: string };
      pedidas.push(`${route.request().headers()["x-role"] ?? ""}:${cuerpo.dimension}`);
      await route.fulfill({
        json: {
          estado: "Parcial",
          nivel_evidencia_maximo: 1,
          citas: [{ fragmento: "politica de privacidad y tratamiento", motivo: "Sustento simulado" }],
          citas_descartadas: 0,
          razonamiento: "La evidencia simulada sustenta el control en parte.",
          limitaciones: [],
          modelo: "qa-09",
        },
      });
    } else {
      await route.fallback();
    }
  });
  return pedidas;
}

const DOCUMENTO = {
  name: "politica-privacidad.pdf",
  mimeType: "application/pdf",
  buffer: Buffer.from("%PDF-1.4 politica de privacidad y tratamiento"),
};

async function abrir(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
}

async function contextoConEvidencia(browser: Browser): Promise<BrowserContext> {
  const contexto = await browser.newContext();
  await contexto.addInitScript(() => {
    window.__LOPDP_EVIDENCIA_PRUEBAS__ = true;
  });
  return contexto;
}

test.describe("Escala de madurez de 1 a 5 con evidencia física (DIAG-09, EVYDENTIA)", () => {
  test("el DPO vincula, el administrador pide la propuesta y elige el nivel, y el DPO sella", async ({ browser }) => {
    test.slow(); // Tres sesiones de navegador en una prueba.
    // 1. El DPO sube y vincula la evidencia sin elegir escalón; no ve el selector de nivel, el escalón ni la IA.
    const contextoDpo = await contextoConEvidencia(browser);
    await simularApiDiagnostico(contextoDpo, { roles: ["dpo"], usuario: "usuario-dpo" });
    await simularRespuestasDiagnostico08(contextoDpo);
    const almacen = await simularSubidaFirmada(contextoDpo);
    const dpo = await contextoDpo.newPage();
    await simularIA(dpo);
    await abrir(dpo);
    await expect(dpo.locator("[data-nivel]")).toHaveCount(0);
    await expect(dpo.locator("[data-evidencia]")).toHaveCount(0);
    await dpo.getByTestId("carga-evidencia-dpo").locator('input[type="file"]').first().setInputFiles(DOCUMENTO);
    await expect.poll(() => almacen.documentos[0]?.controles_vinculados.length ?? 0).toBeGreaterThan(0);
    await expect(dpo.getByRole("button", { name: "Analizar con IA" })).toHaveCount(0);

    // 2. El administrador ve la evidencia que vinculó el DPO, pide la propuesta y elige el nivel y el escalón.
    const contextoAdmin = await contextoConEvidencia(browser);
    await simularApiDiagnostico(contextoAdmin, { roles: ["admin_organizacion"], usuario: "usuario-admin" });
    // Las respuestas de DIAG-08 se registran después y atienden el guardado del administrador.
    const servidorAdmin = await simularRespuestasDiagnostico08(contextoAdmin);
    await simularSubidaFirmada(contextoAdmin);
    await contextoAdmin.route("**/api/v1/evidencias/documentos", (route) =>
      route.request().method() === "GET"
        ? route.fulfill({ json: { total: almacen.documentos.length, documentos: almacen.documentos } })
        : route.fallback()
    );
    const inicial = await contextoAdmin.newPage();
    await abrir(inicial);
    // Configurar el proyecto cambia la normativa y limpia el registro local: en una pestaña nueva del mismo
    // contexto (la ficha persiste y abrirAppLimpia no vuelve a borrarla), el administrador lee del servidor
    // la evidencia que vinculó el DPO.
    await inicial.close();
    const admin = await contextoAdmin.newPage();
    const pedidas = await simularIA(admin);
    await admin.goto("/");
    // La vista persistida vuelve a Normativa; la alerta modal de D01 se descarta si se vuelve a abrir.
    const alerta = admin.getByRole("button", { name: "Cerrar alerta" });
    // La alerta se monta tras hidratar: se espera un momento antes de decidir que no está.
    await alerta.waitFor({ state: "visible", timeout: 5000 }).catch(() => undefined);
    if (await alerta.isVisible()) await alerta.click();
    await expect(admin.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
    await expect(admin.getByTestId("carga-evidencia-dpo")).toHaveCount(0);
    await expect(admin.getByLabel("Vincular evidencia registrada")).toHaveCount(0);
    await admin.getByRole("button", { name: "Analizar con IA" }).first().click();
    await admin.getByLabel("Volver a presentar el archivo").setInputFiles(DOCUMENTO);
    await admin
      .getByRole("dialog", { name: "Confirmar envío al modelo de IA" })
      .getByRole("button", { name: "Enviar y analizar" })
      .click();
    await expect(admin.getByText("Propuesta de la IA", { exact: true })).toBeVisible();
    await admin.getByRole("button", { name: "Aceptar propuesta" }).click();
    expect(pedidas).toEqual(["admin_organizacion:D01"]);

    const niveles = admin.getByRole("radiogroup", { name: /Nivel de madurez/ });
    // Parcial = niveles 2 y 3: ninguno elegido, los dos marcados y los demás sin marca.
    await expect(niveles.getByRole("radio", { checked: true })).toHaveCount(0);
    await expect(niveles.locator("[data-sugerido]")).toHaveCount(2);
    await expect(niveles.locator('[data-nivel="2"]')).toHaveAttribute("data-sugerido", "true");
    await expect(niveles.locator('[data-nivel="3"]')).toHaveAttribute("data-sugerido", "true");
    await expect(admin.getByTestId("rango-sugerido")).toContainText("entre 2 y 3");
    await expect(admin.getByTestId("estado-derivado")).toHaveText("Pendiente");
    await responderControlActual(admin, 3);
    await expect(niveles.locator('[data-nivel="3"]')).toHaveAttribute("aria-checked", "true");
    const escalon = admin.locator('[data-evidencia="2"]');
    await escalon.click();
    await expect(escalon).toHaveAttribute("aria-checked", "true");
    await expect.poll(() => servidorAdmin.filas.find((f) => f.nivel_evidencia === 2)?.nivel_asignado ?? null).toBe(3);

    // 3. El DPO sella lo que respondió el administrador.
    const contextoSello = await contextoConEvidencia(browser);
    const servidorSello = await simularApiDiagnostico(contextoSello, {
      roles: ["dpo"],
      usuario: "usuario-dpo",
      filas: servidorAdmin.filas.map((f) => ({ ...f, estado: f.estado ?? "Pendiente" })),
    });
    const sello = await contextoSello.newPage();
    await abrir(sello);
    const cierre = await abrirCierreDelDiagnostico(contextoSello, sello);
    await cierre.getByRole("button", { name: /^Sellar diagnóstico/ }).click();
    await expect.poll(() => servidorSello.cuerposSellado.length).toBe(1);

    await Promise.all([contextoDpo.close(), contextoAdmin.close(), contextoSello.close()]);
  });

  test("sin evidencia vinculada, el panel del administrador muestra el aviso y no ofrece «Analizar con IA»", async ({ browser }) => {
    const contexto = await contextoConEvidencia(browser);
    await simularApiDiagnostico(contexto, { roles: ["admin_organizacion"] });
    await simularRespuestasDiagnostico08(contexto);
    await simularSubidaFirmada(contexto);
    const page = await contexto.newPage();
    const pedidas = await simularIA(page);
    await abrir(page);
    await expect(page.getByTestId("propuesta-sin-evidencia")).toHaveText(
      "Esta pregunta aún no tiene evidencia vinculada. El DPO debe vincularla para que puedas pedir la propuesta de la IA."
    );
    await expect(page.getByRole("button", { name: "Analizar con IA" })).toHaveCount(0);
    expect(pedidas).toEqual([]);
    await contexto.close();
  });
});
