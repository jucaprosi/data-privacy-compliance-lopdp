// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
import { expect, test, type Page } from "@playwright/test";

import { medirContraste } from "../contraste";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const ROADMAP_ID = "rm-inf-secret-002";
const AUTOR_ID = "usr-autor-inf-999";
const REVISOR_ID = "usr-revisor-inf-888";

interface OpcionesInforme {
  rol?: string;
  revisionStatus?: number;
  estadoRevision?: Record<string, unknown> | null;
  informeStatus?: number;
  informeBody?: Record<string, unknown>;
}

async function prepararInforme(page: Page, opts: OpcionesInforme = {}) {
  const descargas: string[] = [];
  const rol = opts.rol ?? "implementador";

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
    const p = new URL(route.request().url()).pathname.replace(/^\/api\/v1/, "");

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
            tenant_id: "tenant-inf-secret",
            status: (opts.estadoRevision?.status as string) ?? "active",
            created_at: "2026-11-18T10:00:00Z",
            updated_at: "2026-11-19T10:00:00Z",
            summary: "Plan estratégico de cumplimiento",
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
      if (opts.revisionStatus && opts.revisionStatus !== 200) {
        return route.fulfill({ status: opts.revisionStatus, json: { detail: "CRUDO_SERVIDOR_REV" } });
      }
      if (opts.estadoRevision === null) {
        return route.fulfill({ status: 404, json: { detail: "No simulado" } });
      }
      return route.fulfill({ json: opts.estadoRevision });
    }
    if (p === `/roadmaps/${ROADMAP_ID}/informe.pdf`) {
      descargas.push(p);
      if (opts.informeStatus && opts.informeStatus !== 200) {
        return route.fulfill({
          status: opts.informeStatus,
          json: opts.informeBody ?? { detail: "CRUDO_SERVIDOR_PDF" },
        });
      }
      return route.fulfill({
        status: 200,
        contentType: "application/pdf",
        headers:
          opts.estadoRevision && opts.estadoRevision.generado_por === null
            ? { "X-Roadmap-Revision": "sin revisión registrada" }
            : {},
        body: Buffer.from("%PDF-1.4 simulado"),
      });
    }
    return route.fulfill({ status: 404, json: { detail: "No simulado" } });
  });

  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad Informe RM-27");
  await irASala(page, /^Hoja de Ruta/);
  await page.getByRole("button", { name: "Olas & Tareas", exact: true }).click();
  await expect(page.getByRole("region", { name: "Hoja de ruta" })).toBeVisible();

  return descargas;
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

test.describe("Informe PDF y estado de revisión (RM-27)", () => {
  test("hoja nueva sin activar deshabilita la descarga con aria-disabled y explicación", async ({ page }) => {
    const descargas = await prepararInforme(page, {
      estadoRevision: {
        status: "generated",
        generado_por: AUTOR_ID,
        generado_por_nombre: "Ana Implementadora",
        generado_en: "2026-11-19T12:00:00Z",
        revisado_por: null,
        revisado_por_nombre: null,
        revisado_en: null,
        puede_activar: false,
        es_autor: true,
        etiqueta: null,
      },
    });

    const boton = page.getByRole("button", { name: "Descargar informe (PDF)" });
    await expect(boton).toBeVisible();
    await expect(boton).toHaveAttribute("aria-disabled", "true");
    const descId = await boton.getAttribute("aria-describedby");
    expect(descId).toBeTruthy();
    await expect(page.locator(`#${descId}`)).toHaveText(
      "El informe se puede descargar cuando la hoja de ruta esté activa.",
    );

    await boton.click({ force: true });
    expect(descargas).toEqual([]);
    await verificarTextosLimpios(page);

    for (const tema of ["theme-light", "theme-dark"] as const) {
      await page.evaluate((t) => {
        document.documentElement.classList.remove("theme-light", "theme-dark");
        document.documentElement.classList.add(t);
      }, tema);
      const deficientes = await medirContraste(page, "main", { selectorExcluir: "[data-testid^='tarea-']" });
      expect(deficientes, `${tema}: ${JSON.stringify(deficientes)}`).toEqual([]);
    }
  });

  test("hoja anterior muestra «Sin revisión registrada», permite descargar con nombre sin id y pasa contraste", async ({ page }) => {
    const descargas = await prepararInforme(page, {
      estadoRevision: {
        status: "active",
        generado_por: null,
        generado_por_nombre: null,
        generado_en: null,
        revisado_por: null,
        revisado_por_nombre: null,
        revisado_en: null,
        puede_activar: false,
        es_autor: false,
        etiqueta: "sin revisión registrada",
      },
    });

    await expect(page.getByText("Sin revisión registrada")).toBeVisible();
    await expect(
      page.getByText("Esta hoja de ruta es anterior a la revisión por dos personas. El informe lo indica."),
    ).toBeVisible();

    const boton = page.getByRole("button", { name: "Descargar informe (PDF)" });
    await expect(boton).not.toHaveAttribute("aria-disabled", "true");

    const promesaDescarga = page.waitForEvent("download");
    await boton.click();
    const descarga = await promesaDescarga;
    expect(descargas).toEqual([`/roadmaps/${ROADMAP_ID}/informe.pdf`]);
    expect(descarga.suggestedFilename()).toMatch(/^informe-hoja-de-ruta-\d{4}-\d{2}-\d{2}\.pdf$/);
    expect(descarga.suggestedFilename()).not.toContain(ROADMAP_ID);
    await verificarTextosLimpios(page);

    for (const tema of ["theme-light", "theme-dark"] as const) {
      await page.evaluate((t) => {
        document.documentElement.classList.remove("theme-light", "theme-dark");
        document.documentElement.classList.add(t);
      }, tema);
      const deficientes = await medirContraste(page, "main", { selectorExcluir: "[data-testid^='tarea-']" });
      expect(deficientes, `${tema}: ${JSON.stringify(deficientes)}`).toEqual([]);
    }

    await page.setViewportSize({ width: 375, height: 812 });
    const desborde = await page.evaluate(() => {
      const m = document.querySelector("main");
      return m ? m.scrollWidth > m.clientWidth : document.documentElement.scrollWidth > window.innerWidth;
    });
    expect(desborde).toBe(false);
  });

  test("hoja activa no muestra etiqueta anterior y 409 HOJA_PENDIENTE_DE_REVISION muestra texto fijo", async ({ page }) => {
    await prepararInforme(page, {
      estadoRevision: {
        status: "active",
        generado_por: AUTOR_ID,
        generado_por_nombre: "Ana Implementadora",
        generado_en: "2026-11-19T12:00:00Z",
        revisado_por: REVISOR_ID,
        revisado_por_nombre: "María DPO",
        revisado_en: "2026-11-20T12:00:00Z",
        puede_activar: false,
        es_autor: false,
        etiqueta: null,
      },
      informeStatus: 409,
      informeBody: { detail: "CRUDO_SERVIDOR_PENDIENTE", code: "HOJA_PENDIENTE_DE_REVISION" },
    });

    await expect(page.getByText("Sin revisión registrada")).toHaveCount(0);
    await page.getByRole("button", { name: "Descargar informe (PDF)" }).click();
    await expect(page.getByRole("region", { name: "Hoja de ruta" }).getByRole("alert")).toHaveText(
      "Esta hoja de ruta está pendiente de revisión. El informe se podrá descargar cuando se active.",
    );
    await verificarTextosLimpios(page);
  });

  test("error 500 de descarga muestra el mensaje fijo genérico y nunca texto del servidor", async ({ page }) => {
    await prepararInforme(page, {
      estadoRevision: {
        status: "active",
        generado_por: AUTOR_ID,
        generado_por_nombre: "Ana Implementadora",
        generado_en: "2026-11-19T12:00:00Z",
        revisado_por: REVISOR_ID,
        revisado_por_nombre: "María DPO",
        revisado_en: "2026-11-20T12:00:00Z",
        puede_activar: false,
        es_autor: false,
        etiqueta: null,
      },
      informeStatus: 500,
      informeBody: { detail: "CRUDO_SERVIDOR_500_INF" },
    });
    await page.getByRole("button", { name: "Descargar informe (PDF)" }).click();
    await expect(page.getByRole("region", { name: "Hoja de ruta" }).getByRole("alert")).toHaveText(
      "No pudimos descargar el informe. Inténtalo de nuevo.",
    );
    await verificarTextosLimpios(page);
  });
});
