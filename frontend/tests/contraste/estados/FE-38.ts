// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤frontend-ide ¤arbitro
import type { Page } from "@playwright/test";

/**
 * Estados de FE-38 que `rutas.spec.ts` no alcanza solo (abrir un diálogo, abrir una vista NIIF con sus datos de prueba).
 * Clave: «<ruta o vista:id> · <nombre del estado>». El paso se ejecuta con la página cargada y el tema puesto; la prueba mide después.
 * La ficha FE-38 añade aquí sus pasos antes de quitar la ruta o vista de su archivo de pendientes.
 */
export const ESTADOS: Record<string, (page: Page) => Promise<void>> = {};
