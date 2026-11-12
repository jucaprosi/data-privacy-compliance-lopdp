// ¤navegacion-menus
/**
 * Submenú de ORG-15 en el menú INICIO: el tablero de cartera. Solo ORG-15 edita este archivo.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    cartera: true;
  }
}

export const SUBMENUS_ORG_15: Submenu[] = [
  {
    vista: "cartera",
    menu: "inicio",
    nombre: "Tablero de cartera",
    subtitulo: "Tus organizaciones y sus semáforos",
    orden: 2,
  },
];
