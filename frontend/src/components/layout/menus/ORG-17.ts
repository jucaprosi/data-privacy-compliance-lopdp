// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤navegacion-menus
/**
 * Submenú de ORG-17 en el menú INVENTARIO: activos y sistemas, soportes y personas. Solo ORG-17 edita
 * este archivo.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    inventario_activos: true;
  }
}

export const SUBMENUS_ORG_17: Submenu[] = [
  {
    vista: "inventario_activos",
    menu: "inventario",
    nombre: "Activos y personas",
    subtitulo: "Sistemas, soportes y personas",
    orden: 3,
  },
];
