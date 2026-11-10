// ¤navegacion-menus
/**
 * Submenús de DIAG-06. Solo DIAG-06 edita este archivo: Diagnóstico › Comparativo, que compara el
 * diagnóstico de prueba con el real de la organización.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    diagnostico_comparativo: true;
  }
}

export const SUBMENUS_DIAG_06: Submenu[] = [
  {
    vista: "diagnostico_comparativo",
    menu: "diagnostico",
    nombre: "Comparativo",
    subtitulo: "Prueba frente a real",
    orden: 4,
  },
];
