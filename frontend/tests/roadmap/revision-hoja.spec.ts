// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
import { expect, test, type Page } from "@playwright/test";

import { medirContraste } from "../contraste";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const ROADMAP_ID = "rm-rev-secret-id-001";
const AUTOR_ID = "usr-autor-secret-999";
const REVISOR_ID = "usr-revisor-secret-888";

interface OpcionesSimulacion {
  rol?: string;
  revisionStatus?: number;
  revisionDelayMs?: number;
  activarDelayMs?: number;
  estadoRevision?: Record<string, unknown> | null;
  activarHandler?: (intento: number) => { status: number; body: Record<string, unknown> };
}

async function prepararEscenario(page: Page, opts: OpcionesSimulacion = {}) {
  const rol = opts.rol ?? "coordinador";
  let estadoActual: Record<string, unknown> | null =
    opts.estadoRevision === undefined
      ? {
          status: "generated",
          generado_por: AUTOR_ID,
          generado_por_nombre: "Ana Implementadora",
          generado_en: "2026-11-19T15:30:00Z",
          revisado_por: null,
          revisado_por_nombre: null,
          revisado_en: null,
          puede_activar: rol === "coordinador" || rol === "dpo",
          es_autor: false,
          etiqueta: null,
        }
      : opts.estadoRevision;

  let intentosActivar = 0;
  let consultasRevision = 0;

  await page.addInitScript((id: string) => {
    window.localStorage.setItem(
      "lopdp-roadmap-store-v1",
      JSON.stringify({
        state: {
          currentRoadmapId: id,
          statusFilter: "todas",
          priorityFilter: "todas",
          areaFilter: "todas",
        },
        version: 0,
      }),
    );
  }, ROADMAP_ID);

  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const p = new URL(req.url()).pathname.replace(/^\/api\/v1/, "");

    if (p === "/organizacion/me/roles") {
      return route.fulfill({ json: [{ role: rol, area_id: null }] });
    }
    if (["/organizacion/usuarios", "/organizacion/areas", "/organizacion/roles"].includes(p)) {
      return route.fulfill({ json: [] });
    }
    if (p === `/roadmaps/${ROADMAP_ID}`) {
      return route.fulfill({
        json: {
          roadmap: {
            id: ROADMAP_ID,
            tenant_id: "tenant-secret-id",
            status: (estadoActual?.status as string) ?? "generated",
            created_at: "2026-11-19T15:00:00Z",
            updated_at: "2026-11-19T15:30:00Z",
            summary: "Plan de cumplimiento organizacional",
            variables_json: {
              plazo_meses: 6,
              presupuesto: 1000,
              moneda: "USD",
              equipo: ["DPO"],
              dpo: "María",
              idioma: "ES",
            },
          },
          waves: [{ id: "w1", name: "Ola 1", sort_order: 1, tasks: [] }],
        },
      });
    }
    if (p === `/roadmaps/${ROADMAP_ID}/kpis`) {
      return route.fulfill({
        json: { total_tareas: 0, completadas: 0, criticas: 0, altas: 0, progreso_porcentaje: 0 },
      });
    }
    if (p === `/roadmaps/${ROADMAP_ID}/revision`) {
      consultasRevision += 1;
      if (opts.revisionDelayMs) {
        await new Promise((r) => setTimeout(r, opts.revisionDelayMs));
      }
      const status = opts.revisionStatus ?? (estadoActual ? 200 : 404);
      if (status !== 200) {
        return route.fulfill({
          status,
          json: { detail: "CRUDO_SERVIDOR_ERROR_CARGA" },
        });
      }
      return route.fulfill({ json: estadoActual });
    }
    if (p === `/roadmaps/${ROADMAP_ID}/activar` && req.method() === "POST") {
      intentosActivar += 1;
      if (opts.activarDelayMs) {
        await new Promise((r) => setTimeout(r, opts.activarDelayMs));
      }
      if (opts.activarHandler) {
        const res = opts.activarHandler(intentosActivar);
        if (res.status === 200) {
          estadoActual = {
            ...(estadoActual ?? {}),
            status: "active",
            revisado_por: REVISOR_ID,
            revisado_por_nombre: "María DPO",
            revisado_en: "2026-11-20T16:00:00Z",
            puede_activar: false,
          };
        }
        return route.fulfill({ status: res.status, json: res.body });
      }
      estadoActual = {
        ...(estadoActual ?? {}),
        status: "active",
        revisado_por: REVISOR_ID,
        revisado_por_nombre: "María DPO",
        revisado_en: "2026-11-20T16:00:00Z",
        puede_activar: false,
      };
      return route.fulfill({
        status: 200,
        json: {
          status: "active",
          revisado_por: REVISOR_ID,
          revisado_por_nombre: "María DPO",
          revisado_en: "2026-11-20T16:00:00Z",
        },
      });
    }
    return route.fulfill({ status: 404, json: { detail: "No simulado" } });
  });

  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad RM-27");
  await irASala(page, /^Hoja de Ruta/);
  await page.getByRole("button", { name: "Olas & Tareas", exact: true }).click();
  await expect(page.getByRole("region", { name: "Hoja de ruta" })).toBeVisible();

  return {
    actualizarEstado: (nuevo: Record<string, unknown>) => {
      estadoActual = nuevo;
    },
    obtenerConsultasRevision: () => consultasRevision,
  };
}

async function verificarTextosLimpios(page: Page) {
  const texto = await page.locator("main").innerText();
  expect(texto).not.toMatch(/\bgenerated\b|(?<!se )\bactive\b|cuatro ojos/i);
  expect(texto).not.toContain(ROADMAP_ID);
  expect(texto).not.toContain(AUTOR_ID);
  expect(texto).not.toContain(REVISOR_ID);
  expect(texto).not.toContain("CRUDO_SERVIDOR");
  expect(texto).not.toMatch(/[\u00a4\u00a6]/);
}

test.describe("Revisión humana de la Hoja de Ruta (RM-27)", () => {
  test("con puede_activar=true muestra franja pendiente en ámbar y botón Revisar y activar", async ({ page }) => {
    await prepararEscenario(page, { rol: "coordinador" });

    const franja = page.getByRole("status").filter({ hasText: /^Pendiente de revisión/ });
    await expect(franja).toBeVisible();
    await expect(franja).toContainText(
      "Esta hoja de ruta aún no vale como plan oficial. Debe revisarla y activarla un coordinador o el DPO que no la haya generado.",
    );
    await expect(franja).toContainText(/Generada por Ana Implementadora el /);
    const boton = page.getByRole("button", { name: "Revisar y activar la hoja de ruta" });
    await expect(boton).toBeVisible();
    await expect(boton).toContainText("Revisar y activar");
    await verificarTextosLimpios(page);
  });

  test("quien generó la hoja no ve el botón sino la nota de personas distintas (y sin nombre solo fecha)", async ({ page }) => {
    await prepararEscenario(page, {
      rol: "coordinador",
      estadoRevision: {
        status: "generated",
        generado_por: AUTOR_ID,
        generado_por_nombre: null,
        generado_en: "2026-11-19T15:30:00Z",
        revisado_por: null,
        revisado_por_nombre: null,
        revisado_en: null,
        puede_activar: false,
        es_autor: true,
        etiqueta: null,
      },
    });
    await expect(page.getByRole("button", { name: "Revisar y activar la hoja de ruta" })).toHaveCount(0);
    await expect(page.getByRole("note")).toHaveText(
      "Generaste esta hoja de ruta, así que debe activarla otra persona: un coordinador o el DPO. Así la revisan dos personas distintas.",
    );
    await expect(page.getByRole("status").filter({ hasText: /^Pendiente de revisión/ })).toContainText(/Generada el /);
    await verificarTextosLimpios(page);
  });

  test("otros roles no ven el botón sino la indicación de quién la activa", async ({ page }) => {
    await prepararEscenario(page, {
      rol: "implementador",
      estadoRevision: {
        status: "generated",
        generado_por: AUTOR_ID,
        generado_por_nombre: "Ana Implementadora",
        generado_en: "2026-11-19T15:30:00Z",
        revisado_por: null,
        revisado_por_nombre: null,
        revisado_en: null,
        puede_activar: false,
        es_autor: false,
        etiqueta: null,
      },
    });
    await expect(page.getByRole("button", { name: "Revisar y activar la hoja de ruta" })).toHaveCount(0);
    await expect(page.getByText("La activa un coordinador o el DPO de la organización.")).toBeVisible();
    await verificarTextosLimpios(page);
  });

  test("el diálogo atrapa el foco, Escape lo cierra y activar muestra Activando, éxito y franja activa", async ({ page }) => {
    await prepararEscenario(page, { rol: "dpo", activarDelayMs: 250 });

    const botonAbrir = page.getByRole("button", { name: "Revisar y activar la hoja de ruta" });
    await botonAbrir.click();

    const dialogo = page.getByRole("dialog", { name: "¿Activar esta hoja de ruta?" });
    await expect(dialogo).toBeVisible();
    await expect(dialogo).toContainText(
      "Al activarla confirmas que la revisaste y pasa a ser el plan oficial de la organización. Queda registrado que la activaste tú, con la fecha.",
    );

    const cancelar = dialogo.getByRole("button", { name: "Cancelar" });
    const confirmar = dialogo.getByRole("button", { name: "Activar la hoja de ruta" });
    await expect(cancelar).toBeFocused();

    await page.keyboard.press("Tab");
    await expect(confirmar).toBeFocused();
    await page.keyboard.press("Tab");
    await expect(cancelar).toBeFocused();
    await page.keyboard.press("Shift+Tab");
    await expect(confirmar).toBeFocused();

    await page.keyboard.press("Escape");
    await expect(dialogo).toHaveCount(0);
    await expect(botonAbrir).toBeFocused();

    await botonAbrir.click();
    await expect(dialogo).toBeVisible();
    await dialogo.getByRole("button", { name: "Activar la hoja de ruta" }).click();

    const activandoBtn = dialogo.getByRole("button", { name: "Activando…" });
    await expect(activandoBtn).toBeVisible();
    await expect(activandoBtn).toHaveAttribute("aria-busy", "true");

    await expect(dialogo).toHaveCount(0);
    await expect(page.getByRole("status").filter({ hasText: "Hoja de ruta activada. Ya puedes descargar el informe." })).toBeVisible();
    await expect(page.getByRole("status").filter({ hasText: /^Activa · revisada por María DPO el / })).toBeVisible();
    await expect(page.getByRole("button", { name: "Descargar informe (PDF)" })).not.toHaveAttribute("aria-disabled", "true");
    await verificarTextosLimpios(page);
  });

  test("409 REVISION_MISMA_PERSONA muestra su texto fijo sin texto del servidor", async ({ page }) => {
    await prepararEscenario(page, {
      rol: "coordinador",
      activarHandler: () => ({
        status: 409,
        body: { detail: "CRUDO_SERVIDOR_MISMA_PERSONA", code: "REVISION_MISMA_PERSONA" },
      }),
    });
    await page.getByRole("button", { name: "Revisar y activar la hoja de ruta" }).click();
    const dialogo = page.getByRole("dialog", { name: "¿Activar esta hoja de ruta?" });
    await dialogo.getByRole("button", { name: "Activar la hoja de ruta" }).click();
    await expect(dialogo.getByRole("alert")).toHaveText(
      "No puedes activar una hoja de ruta que generaste tú. Debe activarla otra persona.",
    );
    await verificarTextosLimpios(page);
  });

  test("409 HOJA_YA_ACTIVA muestra su texto fijo y recarga el estado", async ({ page }) => {
    const ctrl = await prepararEscenario(page, {
      rol: "dpo",
      activarHandler: () => ({
        status: 409,
        body: { detail: "CRUDO_SERVIDOR_YA_ACTIVA", code: "HOJA_YA_ACTIVA" },
      }),
    });
    await page.getByRole("button", { name: "Revisar y activar la hoja de ruta" }).click();
    ctrl.actualizarEstado({
      status: "active",
      generado_por: AUTOR_ID,
      generado_por_nombre: "Ana Implementadora",
      generado_en: "2026-11-19T15:30:00Z",
      revisado_por: REVISOR_ID,
      revisado_por_nombre: "Carlos Coordinador",
      revisado_en: "2026-11-20T16:00:00Z",
      puede_activar: false,
      es_autor: false,
      etiqueta: null,
    });
    const dialogo = page.getByRole("dialog", { name: "¿Activar esta hoja de ruta?" });
    await dialogo.getByRole("button", { name: "Activar la hoja de ruta" }).click();
    await expect(dialogo.getByRole("alert")).toHaveText(
      "Otra persona ya activó esta hoja de ruta. Actualizamos su estado.",
    );
    await dialogo.getByRole("button", { name: "Cancelar" }).click();
    await expect(page.getByRole("status").filter({ hasText: /^Activa · revisada por Carlos Coordinador el / })).toBeVisible();
    await verificarTextosLimpios(page);
  });

  for (const caso of [
    {
      etiqueta: "403",
      status: 403,
      body: { detail: "CRUDO_SERVIDOR_403" },
      esperado: "Solo un coordinador o el DPO pueden activar la hoja de ruta.",
    },
    {
      etiqueta: "404",
      status: 404,
      body: { detail: "CRUDO_SERVIDOR_404" },
      esperado: "No encontramos esta hoja de ruta. Vuelve a cargar la página.",
    },
    {
      etiqueta: "500",
      status: 500,
      body: { detail: "CRUDO_SERVIDOR_500" },
      esperado: "No pudimos activar la hoja de ruta. Inténtalo de nuevo.",
    },
  ]) {
    test(`error ${caso.etiqueta} de activación muestra su texto fijo`, async ({ page }) => {
      await prepararEscenario(page, {
        rol: "coordinador",
        activarHandler: () => ({ status: caso.status, body: caso.body }),
      });
      await page.getByRole("button", { name: "Revisar y activar la hoja de ruta" }).click();
      const dialogo = page.getByRole("dialog", { name: "¿Activar esta hoja de ruta?" });
      await dialogo.getByRole("button", { name: "Activar la hoja de ruta" }).click();
      await expect(dialogo.getByRole("alert")).toHaveText(caso.esperado);
      await verificarTextosLimpios(page);
    });
  }

  test("error de carga inicial muestra alerta y botón Volver a cargar", async ({ page }) => {
    const ctrl = await prepararEscenario(page, { rol: "coordinador", revisionStatus: 500 });
    const region = page.getByRole("region", { name: "Hoja de ruta" });
    await expect(region.getByRole("alert")).toContainText(
      "No pudimos cargar el estado de revisión de la hoja de ruta.",
    );
    await expect(region.getByRole("button", { name: "Volver a cargar" })).toBeVisible();
    expect(ctrl.obtenerConsultasRevision()).toBeGreaterThanOrEqual(1);
    await verificarTextosLimpios(page);
  });

  test("cumple contraste WCAG 2.1 >= 4.5:1 en tema claro y oscuro y no desborda a 375 px", async ({ page }) => {
    await prepararEscenario(page, { rol: "coordinador" });

    for (const tema of ["theme-light", "theme-dark"] as const) {
      await page.evaluate((t) => {
        document.documentElement.classList.remove("theme-light", "theme-dark");
        document.documentElement.classList.add(t);
      }, tema);
      const deficientesFranja = await medirContraste(page, "main", { selectorExcluir: "[data-testid^='tarea-']" });
      expect(deficientesFranja, `${tema} franja: ${JSON.stringify(deficientesFranja)}`).toEqual([]);

      await page.getByRole("button", { name: "Revisar y activar la hoja de ruta" }).click();
      const deficientesDialogo = await medirContraste(page, "[role='dialog']");
      expect(deficientesDialogo, `${tema} diálogo: ${JSON.stringify(deficientesDialogo)}`).toEqual([]);
      await page.keyboard.press("Escape");
    }

    await page.setViewportSize({ width: 375, height: 812 });
    const desborde = await page.evaluate(() => {
      const m = document.querySelector("main");
      return m ? m.scrollWidth > m.clientWidth : document.documentElement.scrollWidth > window.innerWidth;
    });
    expect(desborde).toBe(false);
  });
});
