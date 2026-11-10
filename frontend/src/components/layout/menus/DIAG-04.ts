// ¤navegacion-menus
// ¤diagnostico-asignacion
/** Submenús de DIAG-04: Diagnóstico › Asignación. Solo DIAG-04 edita este archivo. */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    asignacion_dominios: true;
  }
}

export const SUBMENUS_DIAG_04: Submenu[] = [
  {
    vista: "asignacion_dominios",
    menu: "diagnostico",
    nombre: "Asignación",
    subtitulo: "Encargado de cada dominio",
    orden: 4,
  },
];
