// ¤navegacion-menus
// ¤vigilancia-spdp
/** Submenú de NORM-02: Conocimiento › Vigilancia normativa. Solo NORM-02 edita este archivo. */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    vigilancia_normativa: true;
  }
}

export const SUBMENUS_NORM_02: Submenu[] = [
  {
    vista: "vigilancia_normativa",
    menu: "conocimiento",
    nombre: "Vigilancia normativa",
    subtitulo: "Resoluciones de la SPDP",
    orden: 5,
  },
];
