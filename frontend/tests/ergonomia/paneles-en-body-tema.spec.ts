// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤frontend-ide ¤arbitro
/**
 * FE-30 · Los tokens base siguen al tema y los paneles montados en `body` heredan el texto del tema.
 * Caso real (2026-11-23): con el tema claro, el panel de la Biblioteca pintaba `rgb(244,244,245)` sobre blanco.
 * Contrato: `governance/especificaciones/FE-30.md`.
 */
import { expect, test, type Page } from "@playwright/test";

import { medirContraste } from "../contraste";

type Tema = "light" | "dark";
const CORTE = "2026-11-04T12:00:00Z";
const BLANCO = "rgb(255, 255, 255)";
const FONDO_OSCURO = "rgb(10, 10, 12)";
const TEXTO_OSCURO = "rgb(244, 244, 245)";
const TEXTO_CLARO = "rgb(9, 9, 11)";
const PANEL = '[aria-label="Panel de Biblioteca"]';

const INDICADOR = {
  clave: "acciones",
  titulo: "Acciones verificadas",
  fecha_corte: CORTE,
  categoria_foco: "verificada",
  valor_foco: 1,
  denominador: 3,
  conteos: { verificada: 1, no_conforme: 0, pendiente: 2, sin_mapear: 0 },
  sin_mapear: 0,
  avance_implementacion: 33.3,
  etiqueta_avance: "Avance de implementación. No es una certificación ni garantía de cumplimiento.",
  exclusiones: [{ motivo: "Registros con estado sin mapear: se muestran aparte.", cantidad: 0 }],
  origen: "biblioteca_acciones",
};

async function guardarTema(page: Page, tema: Tema | "invalido") {
  await page.addInitScript((t) => {
    try {
      window.localStorage.setItem(
        "jubys-audit-storage",
        t === "invalido" ? "{no es json" : JSON.stringify({ state: { theme: t }, version: 6 }),
      );
    } catch {
      // Almacenamiento bloqueado: la prueba mide entonces el tema por defecto.
    }
  }, tema);
}

async function simularApi(page: Page) {
  await page.addInitScript(() => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant: "org-fe30" };
  });
  await page.route(/\/api\/v1\/(?!biblioteca)/, (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
  await page.route("**/api/v1/biblioteca/documentos**", (route) => route.fulfill({ json: [] }));
  await page.route("**/api/v1/biblioteca/impactos", (route) => route.fulfill({ json: [] }));
  await page.route("**/api/v1/biblioteca/documentos/pendientes", (route) =>
    route.fulfill({ json: { borrador: 0, en_revision: 0, por_vencer: 0, vencidos: 0, total: 0 } }),
  );
  await page.route(/\/api\/v1\/biblioteca\/indicadores(?:\?.*)?$/, (route) =>
    route.fulfill({
      json: {
        fecha_corte: CORTE,
        etiqueta: "Avance de implementación. No es una certificación ni garantía de cumplimiento.",
        indicadores: [INDICADOR],
      },
    }),
  );
}

async function abrirPanel(page: Page, tema: Tema) {
  await guardarTema(page, tema);
  await simularApi(page);
  await page.goto("/");
  await page.getByTestId("boton-biblioteca").click();
  await expect(page.getByRole("dialog", { name: "Panel de Biblioteca" })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Indicadores verificables" })).toBeVisible();
}

const estilo = (page: Page, selector: string) =>
  page.evaluate((s) => {
    const e = getComputedStyle(document.querySelector(s) as HTMLElement);
    return { color: e.color, fondo: e.backgroundColor, esquema: e.colorScheme };
  }, selector);

for (const tema of ["light", "dark"] as const) {
  test(`con el tema ${tema} todo texto de un hijo de body fuera de la raíz de la aplicación es legible`, async ({ page }) => {
    await abrirPanel(page, tema);
    await expect(page.locator("html")).toHaveClass(new RegExp(`theme-${tema}`));
    expect(await medirContraste(page, PANEL), `panel ilegible con el tema ${tema}`).toEqual([]);

    // Cualquier otro hijo de body que no sea la raíz de la aplicación se mide igual.
    const otros = await page.evaluate(() => {
      const raiz = document.querySelector("main, header, aside")?.closest("body > *");
      return Array.from(document.body.children)
        .filter((n) => n !== raiz && n.tagName === "DIV" && !n.matches('[aria-label="Panel de Biblioteca"]'))
        .map((n, i) => {
          n.setAttribute("data-fe30-hijo", String(i));
          return `[data-fe30-hijo="${i}"]`;
        });
    });
    for (const selector of otros) {
      expect(await medirContraste(page, selector), `hijo de body ${selector} con el tema ${tema}`).toEqual([]);
    }
  });
}

test("con el tema claro «Indicadores verificables» contrasta con el fondo del panel", async ({ page }) => {
  await abrirPanel(page, "light");
  const titulo = await page.getByRole("heading", { name: "Indicadores verificables" }).evaluate((el) => getComputedStyle(el).color);
  expect(titulo).not.toBe(TEXTO_OSCURO);
  const panel = await estilo(page, PANEL);
  expect(panel.fondo).toBe(BLANCO);
  expect(titulo).toBe(TEXTO_CLARO);
  expect(await medirContraste(page, PANEL)).toEqual([]);
  // El token mismo sigue al tema: el color no puede venir solo de la herencia del navegador.
  const tokens = await page.evaluate(() => {
    const e = getComputedStyle(document.documentElement);
    // El minificador de CSS puede acortar #ffffff a #fff: se compara el valor expandido.
    const largo = (v: string) => (/^#[0-9a-f]{3}$/i.test(v) ? "#" + [...v.slice(1)].map((c) => c + c).join("") : v);
    return [largo(e.getPropertyValue("--background").trim()), largo(e.getPropertyValue("--foreground").trim())];
  });
  expect(tokens).toEqual(["#ffffff", "#09090b"]);
});

test("con el tema oscuro body mantiene su color y su fondo de siempre", async ({ page }) => {
  await abrirPanel(page, "dark");
  const b = await estilo(page, "body");
  expect(b.color).toBe(TEXTO_OSCURO);
  expect(b.fondo).toBe(FONDO_OSCURO);
});

test("con el tema oscuro «Indicadores verificables» es claro sobre el fondo oscuro del panel", async ({ page }) => {
  await abrirPanel(page, "dark");
  const titulo = await page.getByRole("heading", { name: "Indicadores verificables" }).evaluate((el) => getComputedStyle(el).color);
  expect(titulo).toBe(TEXTO_OSCURO);
  expect(await medirContraste(page, PANEL)).toEqual([]);
  // m6: si el tema no estuviera en <html>, el panel (hijo de body) perdería el texto del tema.
  await page.evaluate(() => document.documentElement.classList.remove("theme-dark", "dark"));
  const sinClase = await page.getByRole("heading", { name: "Indicadores verificables" }).evaluate((el) => getComputedStyle(el).color);
  expect(sinClase).not.toBe(TEXTO_OSCURO);
});

test("el tema oscuro guardado pinta body en oscuro ya en DOMContentLoaded, sin destello", async ({ page }) => {
  await guardarTema(page, "dark");
  await simularApi(page);
  await page.addInitScript(() => {
    // La clase de <html> en el instante en que el analizador crea <body>: un script diferido llega tarde.
    let claseAlCrearBody = "";
    new MutationObserver((_, obs) => {
      if (document.body) {
        claseAlCrearBody = document.documentElement.className;
        obs.disconnect();
      }
    }).observe(document, { childList: true, subtree: true });
    document.addEventListener("DOMContentLoaded", () => {
      (window as unknown as { __fe30: unknown }).__fe30 = {
        fondo: getComputedStyle(document.body).backgroundColor,
        clase: claseAlCrearBody,
      };
    });
  });
  await page.goto("/dashboard", { waitUntil: "commit" });
  await page.waitForFunction(() => Boolean((window as unknown as { __fe30?: unknown }).__fe30));
  const medida = await page.evaluate(() => (window as unknown as { __fe30: { fondo: string; clase: string } }).__fe30);
  expect(medida.clase).toContain("theme-dark");
  expect(medida.fondo).toBe(FONDO_OSCURO);
});

for (const ruta of ["/", "/login"]) {
  test(`con el tema claro html y body son blancos en ${ruta} y color-scheme es light`, async ({ page }) => {
    await guardarTema(page, "light");
    await simularApi(page);
    await page.goto(ruta);
    for (const selector of ["html", "body"]) {
      const c = await estilo(page, selector);
      expect(c.fondo, selector).toBe(BLANCO);
      expect(c.fondo, selector).not.toBe(FONDO_OSCURO);
    }
    expect((await estilo(page, "html")).esquema).toBe("light");
  });
}

test("con el tema oscuro color-scheme es dark", async ({ page }) => {
  await guardarTema(page, "dark");
  await simularApi(page);
  await page.goto("/login");
  expect((await estilo(page, "html")).esquema).toBe("dark");
});

test("con un localStorage inválido html queda en theme-light y no hay errores de consola", async ({ page }) => {
  const errores: string[] = [];
  page.on("pageerror", (e) => errores.push(e.message));
  await guardarTema(page, "invalido");
  await simularApi(page);
  await page.goto("/login");
  await expect(page.locator("html")).toHaveClass(/theme-light/);
  await expect(page.locator("html")).not.toHaveClass(/theme-dark/);
  expect(errores).toEqual([]);
});
