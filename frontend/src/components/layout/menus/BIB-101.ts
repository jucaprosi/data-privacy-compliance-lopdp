// ¤navegacion-menus ¤adpa
/**
 * Submenú de BIB-101 en el menú BIBLIOTECA: la vista con las pestañas «Documentos de la organización»
 * y «Plantillas» (`docs/biblioteca-pmv.md` §0). Solo BIB-101 edita este archivo.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    biblioteca: true;
  }
}

export const SUBMENUS_BIB_101: Submenu[] = [
  {
    vista: "biblioteca",
    menu: "biblioteca",
    nombre: "Documentos y plantillas",
    subtitulo: "Documentos de la organización y plantillas",
    orden: 0,
  },
];
