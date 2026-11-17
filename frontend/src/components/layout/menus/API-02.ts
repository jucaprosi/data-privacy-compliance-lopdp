// ¤navegacion-menus ¤api-integraciones
/**
 * Submenú de API-02 en el menú CONFIGURACIÓN: claves de integración y techos de paquete.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    integraciones: true;
  }
}

export const SUBMENUS_API_02: Submenu[] = [
  {
    vista: "integraciones",
    menu: "configuracion",
    nombre: "Claves de integración",
    subtitulo: "Claves de acceso y techos de paquete",
    orden: 9,
  },
];
