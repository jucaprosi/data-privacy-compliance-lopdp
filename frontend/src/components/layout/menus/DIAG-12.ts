// ¤navegacion-menus
/**
 * Submenús de DIAG-12. Solo DIAG-12 edita este archivo: Diagnóstico › Estado actual, con los estados
 * que emite el DPO a partir del diagnóstico real.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    diagnostico_estados: true;
  }
}

export const SUBMENUS_DIAG_12: Submenu[] = [
  {
    vista: "diagnostico_estados",
    menu: "diagnostico",
    nombre: "Estado actual",
    subtitulo: "Estados desde el diagnóstico real",
    orden: 5,
  },
];
