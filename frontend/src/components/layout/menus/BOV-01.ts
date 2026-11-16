// ¤navegacion-menus
/**
 * Submenú de BOV-01 en el menú CONFIGURACIÓN: el plan de almacenamiento de la organización. Solo BOV-01 edita
 * este archivo. Lo ven administración, DPO y coordinación en solo lectura; la pantalla comprueba el rol con
 * /organizacion/me/roles y el servidor vuelve a autorizar.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    bov01_suscripcion: true;
  }
}

export const SUBMENUS_BOV_01: Submenu[] = [
  {
    vista: "bov01_suscripcion",
    menu: "configuracion",
    nombre: "Almacenamiento",
    subtitulo: "Espacio y descargas de tu plan",
    orden: 8,
  },
];
