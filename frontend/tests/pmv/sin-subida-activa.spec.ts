/**
 * FE-26 · Con la evidencia física encendida (EVYDENTIA) la pantalla queda como antes de FE-26.
 *
 * Usa el ajuste de prueba `window.__LOPDP_EVIDENCIA_PRUEBAS__`, que solo existe fuera de
 * producción (src/lib/config/evidenciaFisica.ts): este archivo corre en el proyecto «desarrollo»
 * (SOLO_DESARROLLO de playwright.config.ts, CI-16). El caso por omisión, sin ganchos, está en
 * `sin-subida.spec.ts`.
 */
import { expect, test, type BrowserContext, type Page } from "@playwright/test";

import { abrirAppLimpia, barraDeMenus, configurarProyecto, irASala, responderControlActual } from "../utiles";
import { abrirCierreDelDiagnostico, simularApiDiagnostico } from "../diagnostico/simulador";

const ROADMAP = "rm-fe26";
const TAREA = "task-fe26";

async function encenderEvidenciaFisica(context: BrowserContext): Promise<void> {
  // En el contexto, no en la página: el cierre del diagnóstico abre otra pestaña.
  await context.addInitScript(() => {
    window.__LOPDP_EVIDENCIA_PRUEBAS__ = true;
  });
}

async function simularHojaDeRuta(page: Page): Promise<void> {
  await page.route("**/api/v1/**", async (route) => {
    const destino = new URL(route.request().url()).pathname.replace(/^\/api\/v1/, "");
    const json = (cuerpo: unknown, status = 200) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });
    if (destino === "/organizacion/me/roles") {
      return json({ user_id: "user-coord-01", tenant_id: "tenant-corp-demo", roles: [{ role: "coordinador", area_id: null }] });
    }
    if (["/organizacion/usuarios", "/organizacion/areas", "/organizacion/roles"].includes(destino)) return json([]);
    if (destino === `/roadmaps/${ROADMAP}`) {
      return json({
        roadmap: { id: ROADMAP, tenant_id: "tenant-corp-demo", status: "active", summary: "Hoja de ruta FE-26" },
        waves: [
          {
            id: "wave-fe26", roadmap_id: ROADMAP, tenant_id: "tenant-corp-demo", name: "Ola 1", sort_order: 1,
            tasks: [
              {
                id: TAREA, wave_id: "wave-fe26", tenant_id: "tenant-corp-demo", control_ref: "P1", dimension: "D01",
                title: "Inventario de tratamientos", description: "Tarea de prueba.", status: "en_progreso",
                priority: "alta", owner: null, area_id: null, evidence: [],
              },
            ],
          },
        ],
      });
    }
    if (destino === `/roadmaps/${ROADMAP}/kpis`) {
      return json({ total: 1, completadas: 0, criticas: 0, altas: 1, porcentaje_avance: 0 });
    }
    if (destino === `/roadmaps/tasks/${TAREA}/evidence`) return json([]);
    return json({ detail: "No simulado", code: "NOT_MOCKED", action_required: null }, 404);
  });
  await page.addInitScript((id: string) => {
    try {
      window.localStorage.setItem(
        "lopdp-roadmap-store-v1",
        JSON.stringify({ state: { currentRoadmapId: id, statusFilter: "todas", priorityFilter: "todas", areaFilter: "todas" }, version: 0 }),
      );
    } catch {
      // Sin almacenamiento la prueba falla al no ver la tarea.
    }
  }, ROADMAP);
}

test.describe("Evidencia física encendida (FE-26, EVYDENTIA)", () => {
  test.beforeEach(async ({ context }) => {
    await encenderEvidenciaFisica(context);
  });

  test("el diagnóstico monta la carga de evidencias y conserva los avisos de respaldo", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["dpo"] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
    await expect(page.getByText("Registro de Evidencias con Huella SHA-256")).toBeVisible();
    await responderControlActual(page, 3);
    await expect.poll(() => servidor.filas.length).toBe(1);

    const cierre = await abrirCierreDelDiagnostico(context, page);
    await expect(cierre.getByTestId("aviso-evidencia-declarada")).toHaveCount(0);
    await cierre.getByRole("button", { name: "Guardar resultado definitivo" }).click();
    await expect(cierre.getByText(/Resultado sellado n\.º 1/)).toBeVisible();
    await expect(cierre.getByText(/un documento que el servidor pudo comprobar/)).toBeVisible();
  });

  test("la hoja de ruta ofrece la custodia y «Ver evidencia» en las tareas", async ({ page }) => {
    await simularHojaDeRuta(page);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);
    await expect(page.getByRole("heading", { name: "Hoja de Ruta de Implementación" })).toBeVisible();

    await expect(page.getByTestId(`tarea-${TAREA}`)).toBeVisible();
    await expect(page.getByRole("button", { name: "Custodia de Evidencias", exact: true })).toBeVisible();
    await page.getByRole("button", { name: "Ver evidencia" }).click();
    await expect(page.getByRole("region", { name: "Evidencia de la tarea" })).toBeVisible();
  });

  test("el menú Biblioteca lista Evidencias", async ({ page }) => {
    await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
    await abrirAppLimpia(page);
    await configurarProyecto(page);

    await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
    const grupo = page.getByRole("group", { name: "Submenús de Biblioteca" });
    await expect(grupo.getByRole("button", { name: /^Evidencias/ })).toBeVisible();
  });
});
