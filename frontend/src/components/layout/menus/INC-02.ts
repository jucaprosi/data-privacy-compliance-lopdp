// ¤navegacion-menus
// ¤incidentes
/** Submenú de INC-02: Operación › Asistente de vulneración. Solo INC-02 edita este archivo. */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    asistente_vulneraciones: true;
  }
}

export const SUBMENUS_INC_02: Submenu[] = [
  {
    vista: "asistente_vulneraciones",
    menu: "operacion",
    nombre: "Asistente de vulneración",
    subtitulo: "Decisión de notificar e informes",
    orden: 4,
  },
];
