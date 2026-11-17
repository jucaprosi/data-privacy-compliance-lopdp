// ¤navegacion-menus
// ¤formacion
/** Submenús de FOR-01: Operación › Formación y Mi formación. */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    formacion: true;
    mi_formacion: true;
  }
}

export const SUBMENUS_FOR_01: Submenu[] = [
  {
    vista: "formacion",
    menu: "operacion",
    nombre: "Formación",
    subtitulo: "Contenidos, capacitaciones y avance",
    orden: 3,
  },
  {
    vista: "mi_formacion",
    menu: "operacion",
    nombre: "Mi formación",
    subtitulo: "Tus capacitaciones y tu examen",
    orden: 4,
  },
];
