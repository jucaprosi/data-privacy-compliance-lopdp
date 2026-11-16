// ¤navegacion-menus
/**
 * Submenús de ORG-20 en el menú CONFIGURACIÓN: la papelera y la exportación de los datos. Solo ORG-20
 * edita este archivo. La papelera la ven administración e implementación; la exportación, solo administración
 * (la pantalla comprueba el rol con /organizacion/me/roles y explica si no corresponde).
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    papelera: true;
    exportar_datos: true;
  }
}

export const SUBMENUS_ORG_20: Submenu[] = [
  { vista: "papelera", menu: "configuracion", nombre: "Papelera", subtitulo: "Elementos retirados que puedes restaurar", orden: 6 },
  { vista: "exportar_datos", menu: "configuracion", nombre: "Exportar datos", subtitulo: "Una copia de los datos de tu organización", orden: 7 },
];
