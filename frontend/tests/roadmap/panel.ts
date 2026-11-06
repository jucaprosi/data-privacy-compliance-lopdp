/**
 * Panel de la Hoja de Ruta simulado (FE-06): API sobre /api/v1/**, ficha completa y entrada en la sala.
 *
 * Lo comparten `integracion.spec.ts` (PMV, evidencia declarada) e `integracion-activa.spec.ts`
 * (custodia física de EVYDENTIA, FE-26). Este archivo no declara pruebas.
 */
import { expect, type Page, type Request } from "@playwright/test";

import { abrirAppLimpia, barraDeMenus, irASala } from "../utiles";

export type Rol = "responsable_area" | "coordinador" | "dpo" | "implementador" | "admin_organizacion";

export interface Escenario {
  /** Respuesta de /organizacion/me/roles. Un número es un estado HTTP de error. */
  roles: Rol[] | number;
  /** Hoja de ruta con la que arranca el almacén persistido, si la hay. */
  roadmapId?: string;
}

export const ruta = (url: string) => new URL(url).pathname.replace(/^\/api\/v1/, "");

export async function prepararApi(page: Page, escenario: Escenario): Promise<Request[]> {
  const llamadas: Request[] = [];
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    llamadas.push(peticion);
    const destino = ruta(peticion.url());

    if (destino === "/organizacion/me/roles") {
      if (typeof escenario.roles === "number") {
        return route.fulfill({
          status: escenario.roles,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Servicio no disponible", code: "ORG_UNAVAILABLE", action_required: null }),
        });
      }
      const cuerpo = escenario.roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null }));
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(cuerpo) });
    }
    if (["/organizacion/usuarios", "/organizacion/areas", "/organizacion/roles"].includes(destino)) {
      return route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
    }
    // Cualquier otra llamada al backend en estas pruebas es inesperada: se responde 404 y queda registrada.
    return route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: "No simulado", code: "NOT_MOCKED", action_required: null }),
    });
  });

  if (escenario.roadmapId) {
    await page.addInitScript((id: string) => {
      try {
        window.localStorage.setItem(
          "lopdp-roadmap-store-v1",
          JSON.stringify({ state: { currentRoadmapId: id, statusFilter: "todas", priorityFilter: "todas", areaFilter: "todas" }, version: 0 }),
        );
      } catch {
        // Sin almacenamiento, la prueba lo detectará al no ver la hoja de ruta.
      }
    }, escenario.roadmapId);
  }
  return llamadas;
}

/**
 * Completa la ficha del proyecto como lo exige la interfaz actual.
 *
 * No se usa configurarProyecto de ../utiles porque rellena solo la razón social, y desde que el
 * perfil de operación es obligatorio (commit c92490e) el botón «Guardar Ficha» sigue desactivado
 * hasta responder todas sus preguntas Sí/No. Ese helper compartido no es de esta tarea; el resto del
 * flujo (guardar, elegir normativa, cerrar la alerta de la primera pregunta) es el mismo.
 */
export async function completarFicha(page: Page): Promise<void> {
  await page.getByRole("textbox", { name: /Razón Social/ }).fill("Entidad de Prueba S.A.");

  const grupos = page.getByRole("radiogroup");
  const total = await grupos.count();
  expect(total, "la ficha debe traer preguntas de perfil").toBeGreaterThan(0);
  for (let i = 0; i < total; i += 1) {
    await grupos.nth(i).getByRole("radio", { name: "No", exact: true }).check();
  }

  await page.getByRole("button", { name: /Guardar Ficha y Continuar/ }).click();
  await expect(page.getByText(/Ficha organizacional guardada/)).toBeVisible();
  await page.locator("#selector-normativa").selectOption("LOPDP");
  await page.getByRole("button", { name: "Cerrar alerta" }).click();
  await expect(barraDeMenus(page).getByRole("button", { name: "Inicio", exact: true })).toBeVisible();
}

export async function entrarEnHojaDeRuta(page: Page): Promise<void> {
  await abrirAppLimpia(page);
  await completarFicha(page);
  await irASala(page, /^Hoja de Ruta/);
  await expect(page.getByRole("heading", { name: "Hoja de Ruta de Implementación" })).toBeVisible();
}

export const subvista = (page: Page, nombre: string) => page.getByRole("button", { name: nombre, exact: true });
