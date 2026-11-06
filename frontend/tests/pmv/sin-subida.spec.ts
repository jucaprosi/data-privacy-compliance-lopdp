/**
 * FE-26 · PMV sin subida de archivos: el caso por omisión, sin la variable `NEXT_PUBLIC_EVIDENCIA_FISICA`.
 *
 * Corre en el proyecto «produccion» del CI contra el build real, que es lo que se publica: no usa
 * ningún gancho que solo exista en desarrollo. El caso con el interruptor encendido vive en
 * `sin-subida-activa.spec.ts` (proyecto «desarrollo»).
 *
 * - El diagnóstico no monta la carga de evidencias y muestra un único aviso de evidencia declarada.
 * - La hoja de ruta no ofrece la pestaña «Custodia de Evidencias» ni «Ver evidencia» en las tareas.
 * - El menú Biblioteca no lista «Evidencias».
 * - El ajuste de prueba `window.__LOPDP_EVIDENCIA_PRUEBAS__` desaparece con NODE_ENV=production.
 *
 * Prueba de mutación documentada (FE-26): en src/lib/config/evidenciaFisica.ts se invirtió el valor
 * por omisión de `porConfiguracion` (`!== "false"` en lugar de `=== "true"`). Fallaron las cinco pruebas
 * de este archivo (las dos del interruptor y las tres de pantalla); se restauró y pasan.
 */
import { expect, test, type Page } from "@playwright/test";

import { AVISO_EVIDENCIA_DECLARADA, evidenciaFisicaActiva } from "../../src/lib/config/evidenciaFisica";
import { abrirAppLimpia, barraDeMenus, configurarProyecto, irASala, responderControlActual } from "../utiles";
import { abrirCierreDelDiagnostico, simularApiDiagnostico } from "../diagnostico/simulador";

const ROADMAP = "rm-fe26";
const TAREA = "task-fe26";

/** Roles del usuario y una hoja de ruta con una tarea, para abrir el panel real. */
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

async function submenusDe(page: Page, menu: string): Promise<string[]> {
  await barraDeMenus(page).getByRole("button", { name: menu, exact: true }).click();
  const grupo = page.getByRole("group", { name: `Submenús de ${menu}` });
  await expect(grupo).toBeVisible();
  return (await grupo.getByRole("button").allInnerTexts()).map((t) => t.trim());
}

test.describe("Interruptor de evidencia física (FE-26)", () => {
  const env = process.env as Record<string, string | undefined>;
  const global = globalThis as unknown as { window?: { __LOPDP_EVIDENCIA_PRUEBAS__?: boolean } };
  const guardado = { nodeEnv: env.NODE_ENV, variable: env.NEXT_PUBLIC_EVIDENCIA_FISICA };

  test.afterEach(() => {
    if (guardado.nodeEnv === undefined) delete env.NODE_ENV;
    else env.NODE_ENV = guardado.nodeEnv;
    if (guardado.variable === undefined) delete env.NEXT_PUBLIC_EVIDENCIA_FISICA;
    else env.NEXT_PUBLIC_EVIDENCIA_FISICA = guardado.variable;
    delete global.window;
  });

  test("por omisión el interruptor está apagado; solo «true» lo enciende", () => {
    delete env.NEXT_PUBLIC_EVIDENCIA_FISICA;
    expect(evidenciaFisicaActiva()).toBe(false);
    for (const valor of ["", "false", "1", "si", "verdadero"]) {
      env.NEXT_PUBLIC_EVIDENCIA_FISICA = valor;
      expect(evidenciaFisicaActiva(), valor).toBe(false);
    }
    env.NEXT_PUBLIC_EVIDENCIA_FISICA = "true";
    expect(evidenciaFisicaActiva()).toBe(true);
  });

  test("el ajuste de prueba del navegador desaparece con NODE_ENV=production", () => {
    delete env.NEXT_PUBLIC_EVIDENCIA_FISICA;
    global.window = { __LOPDP_EVIDENCIA_PRUEBAS__: true };
    env.NODE_ENV = "production";
    expect(evidenciaFisicaActiva()).toBe(false);
    env.NODE_ENV = "development";
    expect(evidenciaFisicaActiva()).toBe(true);
  });
});

test.describe("PMV sin subida de archivos (FE-26)", () => {
  test("el diagnóstico no ofrece cargar evidencias y avisa que la evidencia es declarada", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["dpo"] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await expect(page.getByRole("heading", { name: "Normativa", exact: true })).toBeVisible();
    // Primera pregunta: es donde se montaba la carga de evidencias.
    await expect(page.getByText("Registro de Evidencias con Huella SHA-256")).toHaveCount(0);
    await responderControlActual(page, 3);
    await expect.poll(() => servidor.filas.length).toBe(1);

    const cierre = await abrirCierreDelDiagnostico(context, page);
    const aviso = cierre.getByTestId("aviso-evidencia-declarada");
    await expect(aviso).toHaveText(`${AVISO_EVIDENCIA_DECLARADA}.`);
    await expect(cierre.getByText(/evidencia 0/)).toHaveCount(0);

    await cierre.getByRole("button", { name: "Guardar resultado definitivo" }).click();
    await expect(cierre.getByText(/Resultado sellado n\.º 1/)).toBeVisible();
    await expect(aviso).toHaveCount(1);
    await expect(cierre.getByText(/pudo comprobar|evidencia 0/)).toHaveCount(0);
  });

  test("la hoja de ruta no ofrece la custodia de evidencias", async ({ page }) => {
    await simularHojaDeRuta(page);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Hoja de Ruta/);
    await expect(page.getByRole("heading", { name: "Hoja de Ruta de Implementación" })).toBeVisible();

    await expect(page.getByTestId(`tarea-${TAREA}`)).toBeVisible();
    await expect(page.getByRole("button", { name: "Olas & Tareas", exact: true })).toBeVisible();
    await expect(page.getByRole("button", { name: "Custodia de Evidencias", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Ver evidencia" })).toHaveCount(0);
  });

  test("el menú Biblioteca no lista Evidencias", async ({ page }) => {
    await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
    await abrirAppLimpia(page);
    await configurarProyecto(page);

    const submenus = await submenusDe(page, "Biblioteca");
    expect(submenus.length).toBeGreaterThan(0);
    expect(submenus.some((s) => /^Evidencias/.test(s))).toBe(false);
  });
});
