// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤frontend-ide ¤arbitro
import type { Page } from "@playwright/test";

/**
 * Estados de FE-39 que `rutas.spec.ts` no alcanza solo (abrir un diálogo, abrir una vista NIIF con sus datos de prueba).
 * Clave: «<ruta o vista:id> · <nombre del estado>». El paso se ejecuta con la página cargada y el tema puesto; la prueba mide después.
 * La ficha FE-39 añade aquí sus pasos antes de quitar la ruta o vista de su archivo de pendientes.
 */
/** La Administración editorial solo aparece con una capacidad editorial: se simula la del operador. */
export const PREPARACIONES: Record<string, (page: Page) => Promise<void>> = {
  "vista:biblioteca_editorial": async (page) => {
    await page.route("**/api/v1/biblioteca/capacidades/mias", (r) => r.fulfill({ json: { capacidades: ["editor"] } }));
  },
};

export const ESTADOS: Record<string, (page: Page) => Promise<void>> = {};
