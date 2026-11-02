// ¤navegacion-menus
/**
 * Submenú de ORG-16 en el menú CONFIGURACIÓN: el alta de la organización en siete pasos. Solo ORG-16
 * edita este archivo.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    alta_organizacion: true;
  }
}

export const SUBMENUS_ORG_16: Submenu[] = [
  {
    vista: "alta_organizacion",
    menu: "configuracion",
    nombre: "Alta de la organización",
    subtitulo: "Asistente de siete pasos",
    orden: 2,
  },
];
