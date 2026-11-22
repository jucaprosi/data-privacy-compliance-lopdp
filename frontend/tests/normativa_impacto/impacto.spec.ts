// ¤inteligencia-normativa ¤copiloto-ia ¤dpo-independencia ¤frontend-ide
// ¤¤qa-engineer
/**
 * NORM-03b · pestaña «Impacto» en el panel de una resolución del Centro de Vigilancia Normativa (NORM-02).
 *
 * Corre contra rutas simuladas: el catálogo, el detalle, el original, el análisis de impacto y
 * /organizacion/me/roles. El servidor vuelve a autorizar cada llamada; aquí solo se prueba qué pinta la interfaz.
 *
 * Criterios (especificación NORM-03b §5):
 *  - Cada rol de lectura ve la pestaña «Impacto»; un DPO pide el análisis y lo acepta con nota.
 *  - El operador de la plataforma, que no es miembro de la organización, no la ve y sí ve el documento.
 *  - Con /organizacion/me/roles en 500 no hay pestaña ni aviso de error.
 *  - ArrowRight lleva de «Documento» a «Impacto» y de vuelta, con el foco en la pestaña.
 *  - A 375 px el panel no desborda en horizontal.
 *
 * Mutación m1 (ejecutada y restaurada): en PanelResolucion.tsx se dejó de montar la pestaña
 * («conPestanas» forzado a false). Fallaron los cinco escenarios de los roles de lectura, el del DPO, el del teclado
 * y el de 375 px.
 */
import { expect, test, type Page, type Route } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const NUMERO = "SPDP-N03-2026";
const RESOLUCION = {
  id: "res-n03b",
  numero_resolucion: NUMERO,
  anio_emision: 2026,
  titulo: "Resolución de prueba sobre tratamientos de datos",
  seccion_fuente: "resoluciones",
  estado: "vigente",
  detectada_en: "2026-11-01T10:00:00Z",
};
const DETALLE = {
  ...RESOLUCION,
  organo_emisor: "SPDP",
  materia: "Protección de datos",
  url_fuente: "https://spdp.gob.ec/resoluciones/n03b",
  revisada_por: null,
  revisada_en: null,
  nota_revision: null,
  versiones: [],
};
const ROLES_LECTURA = ["dpo", "admin_organizacion", "coordinador", "implementador", "auditor"] as const;
const ROLES_PEDIDO = ["dpo", "admin_organizacion"];

type Roles = string[] | number;

interface Analisis {
  id: string;
  resolucion_id: string;
  modelo: string;
  propuesta: { tipo: string; referencia_id: string; motivo: string; articulos_citados: string[] }[];
  sin_base_normativa: boolean;
  estado: "propuesta" | "aceptada" | "rechazada";
  creada_en: string;
  decidida_en: string | null;
  nota: string | null;
  hallazgos_generados: number;
}

const json = (route: Route, cuerpo: unknown, status = 200) =>
  route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

/** Simula la API de normativa y de roles. Devuelve las decisiones que recibió el servidor. */
async function simular(page: Page, roles: Roles): Promise<{ decisiones: unknown[] }> {
  const analisis: Analisis[] = [];
  const decisiones: unknown[] = [];

  await page.route((url) => url.pathname.endsWith("/api/v1/organizacion/me/roles"), (route) =>
    typeof roles === "number"
      ? json(route, { detail: "Error interno" }, roles)
      : json(route, { user_id: "persona-n03b", tenant_id: "tenant-corp-demo", roles: roles.map((role) => ({ role })) }));

  await page.route((url) => url.pathname.includes("/api/v1/normativa/"), async (route) => {
    const peticion = route.request();
    const ruta = new URL(peticion.url()).pathname.replace(/^.*\/api\/v1\/normativa/, "");
    const metodo = peticion.method();
    if (metodo === "GET" && ruta === "/resoluciones") {
      return json(route, { total: 1, pagina: 1, por_pagina: 25, items: [RESOLUCION] });
    }
    if (metodo === "GET" && ruta === `/resoluciones/${RESOLUCION.id}`) return json(route, DETALLE);
    if (metodo === "GET" && ruta === `/resoluciones/${RESOLUCION.id}/original`) {
      return route.fulfill({ status: 200, contentType: "application/pdf", body: "%PDF-1.4\n%%EOF\n" });
    }
    if (metodo === "GET" && ruta === "/impacto") return json(route, analisis);
    if (metodo === "POST" && ruta === `/resoluciones/${RESOLUCION.id}/impacto`) {
      const nuevo: Analisis = {
        id: "an-n03b",
        resolucion_id: RESOLUCION.id,
        modelo: "simulado",
        propuesta: [{
          tipo: "tratamiento",
          referencia_id: "RAT-001",
          motivo: "La resolución cambia el plazo de conservación de este tratamiento.",
          articulos_citados: ["Art. 4"],
        }],
        sin_base_normativa: false,
        estado: "propuesta",
        creada_en: "2026-11-21T09:00:00Z",
        decidida_en: null,
        nota: null,
        hallazgos_generados: 0,
      };
      analisis.unshift(nuevo);
      return json(route, nuevo, 201);
    }
    const decision = ruta.match(/^\/impacto\/([^/]+)\/decision$/);
    if (metodo === "POST" && decision) {
      const cuerpo = peticion.postDataJSON() as { decision: "aceptar" | "rechazar"; nota: string };
      decisiones.push(cuerpo);
      const a = analisis.find((x) => x.id === decision[1]);
      if (!a) return json(route, { detail: { codigo: "NORMATIVA_RESOLUCION_NO_ENCONTRADA" } }, 404);
      a.estado = cuerpo.decision === "aceptar" ? "aceptada" : "rechazada";
      a.nota = cuerpo.nota;
      a.decidida_en = "2026-11-21T10:00:00Z";
      return json(route, a);
    }
    return json(route, { detail: { codigo: "NO_SIMULADO" } }, 404);
  });

  return { decisiones };
}

/** Abre el Centro de Vigilancia, espera la lectura de roles y abre la resolución. Devuelve el panel. */
async function abrirPanel(page: Page, roles: Roles, antesDeAbrir?: () => Promise<void>) {
  const simulacion = await simular(page, roles);
  const rolesLeidos = page.waitForResponse((r) => r.url().includes("/api/v1/organizacion/me/roles"));
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad NORM-03b");
  await barraDeMenus(page).getByRole("button", { name: "Conocimiento", exact: true }).click();
  await page.getByRole("group", { name: "Submenús de Conocimiento" })
    .getByRole("button", { name: /^Vigilancia normativa/ }).click();
  const centro = page.getByRole("region", { name: "Vigilancia normativa" });
  await rolesLeidos;
  if (antesDeAbrir) await antesDeAbrir();
  await centro.getByRole("button", { name: NUMERO }).click();
  const panel = page.getByRole("dialog");
  await expect(panel.getByRole("heading", { level: 3 })).toContainText(`${NUMERO}/2026`);
  return { panel, ...simulacion };
}

/** El documento de la norma se ve en el panel. */
async function documentoVisible(page: Page) {
  const panel = page.getByRole("dialog");
  await expect(panel.locator(`iframe[title="Documento: ${NUMERO}/2026"]`)).toBeVisible();
  await expect(panel.getByRole("link", { name: "Abrir el documento en otra pestaña" })).toBeVisible();
}

test.describe("NORM-03b · pestaña «Impacto» en el panel de una resolución", () => {
  for (const rol of ROLES_LECTURA) {
    test(`el rol ${rol} ve la pestaña «Impacto» y abre su análisis`, async ({ page }) => {
      const { panel } = await abrirPanel(page, [rol]);
      const lista = panel.getByRole("tablist", { name: "Secciones de la resolución" });
      await expect(lista.getByRole("tab")).toHaveText(["Documento", "Impacto"]);
      await expect(lista.getByRole("tab", { name: "Documento" })).toHaveAttribute("aria-selected", "true");
      await expect(panel.getByRole("tab", { name: "Impacto" })).toBeVisible();

      await panel.getByRole("tab", { name: "Impacto" }).click();
      const impacto = panel.getByRole("tabpanel", { name: "Impacto" }).last();
      await expect(impacto.getByRole("note")).toContainText("generó una IA");
      await expect(impacto.getByRole("button", { name: "Analizar impacto en mi organización" }))
        .toHaveCount(ROLES_PEDIDO.includes(rol) ? 1 : 0);
    });
  }

  test("un DPO pide el análisis y lo acepta con nota", async ({ page }) => {
    const { panel, decisiones } = await abrirPanel(page, ["dpo"]);
    await panel.getByRole("tab", { name: "Impacto" }).click();
    const impacto = panel.getByRole("tabpanel", { name: "Impacto" }).last();

    await impacto.getByRole("button", { name: "Analizar impacto en mi organización" }).click();
    const analisis = impacto.getByRole("article").first();
    await expect(analisis).toContainText("Pendiente de decisión");
    await expect(analisis).toContainText("Cita: Art. 4");

    await analisis.getByRole("button", { name: "Aceptar" }).click();
    const formulario = impacto.getByRole("form", { name: "Aceptar la propuesta" });
    await formulario.getByRole("button", { name: /^Confirmar/ }).click();
    await expect(formulario.getByRole("alert")).toContainText("nota");
    expect(decisiones).toHaveLength(0);

    await formulario.getByLabel("Nota de la decisión").fill("Revisado por el DPO contra el texto.");
    await formulario.getByRole("button", { name: /^Confirmar/ }).click();
    await expect(analisis).toContainText("Aceptada");
    await expect(analisis).toContainText("Nota del DPO: Revisado por el DPO contra el texto.");
    expect(decisiones).toEqual([{ decision: "aceptar", nota: "Revisado por el DPO contra el texto." }]);
  });

  test("el operador de la plataforma no ve la pestaña y ve el documento", async ({ page }) => {
    // El operador no es miembro de la organización: /organizacion/me/roles no le da ningún rol.
    const { panel } = await abrirPanel(page, []);
    await documentoVisible(page);
    await expect(panel.getByRole("tab", { name: "Impacto" })).toHaveCount(0);
    await expect(panel.getByRole("tablist")).toHaveCount(0);
  });

  test("si falla la lectura de roles no hay pestaña ni aviso de error", async ({ page }) => {
    const { panel } = await abrirPanel(page, 500);
    await documentoVisible(page);
    await expect(panel.getByRole("tab", { name: "Impacto" })).toHaveCount(0);
    await expect(panel.getByRole("alert")).toHaveCount(0);
  });

  test("las flechas recorren las pestañas en ciclo y el foco se queda en la pestaña", async ({ page }) => {
    const { panel } = await abrirPanel(page, ["auditor"]);
    const documento = panel.getByRole("tab", { name: "Documento" });
    const impacto = panel.getByRole("tab", { name: "Impacto" });
    await expect(documento).toHaveAttribute("tabindex", "0");
    await expect(impacto).toHaveAttribute("tabindex", "-1");

    await documento.focus();
    await page.keyboard.press("ArrowRight");
    await expect(impacto).toHaveAttribute("aria-selected", "true");
    await expect(impacto).toBeFocused();
    await expect(impacto).toHaveAttribute("tabindex", "0");
    await expect(documento).toHaveAttribute("tabindex", "-1");
    await expect(panel.getByRole("tabpanel", { name: "Impacto" }).last().getByRole("note")).toBeVisible();

    await page.keyboard.press("ArrowRight");
    await expect(documento).toHaveAttribute("aria-selected", "true");
    await expect(documento).toBeFocused();

    await page.keyboard.press("ArrowLeft");
    await expect(impacto).toHaveAttribute("aria-selected", "true");
    await page.keyboard.press("Home");
    await expect(documento).toHaveAttribute("aria-selected", "true");
    await page.keyboard.press("End");
    await expect(impacto).toHaveAttribute("aria-selected", "true");
    await expect(impacto).toBeFocused();
  });

  test("a 375 px el panel no desborda en horizontal", async ({ page }) => {
    // Se navega con el menú de escritorio y se pasa a 375 px antes de abrir la norma (como en bov01 y con01):
    // al cambiar de ancho el armazón vuelve a montar la vista.
    const { panel } = await abrirPanel(page, ["dpo"], () => page.setViewportSize({ width: 375, height: 812 }));
    const sinDesborde = () => panel.evaluate((el) => el.scrollWidth <= el.clientWidth);
    await documentoVisible(page);
    expect(await sinDesborde()).toBe(true);

    await panel.getByRole("tab", { name: "Impacto" }).click();
    const impacto = panel.getByRole("tabpanel", { name: "Impacto" }).last();
    await impacto.getByRole("button", { name: "Analizar impacto en mi organización" }).click();
    await expect(impacto.getByRole("article").first()).toContainText("Pendiente de decisión");
    expect(await sinDesborde()).toBe(true);
  });
});
