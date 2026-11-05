// ¤navegacion-menus ¤firma-electronica
/**
 * Submenús de FIRMA-02: «Firmas» en BIBLIOTECA (envíos a aceptación) y «Verificar documento» en
 * CONFIGURACIÓN. Solo FIRMA-02 edita este archivo.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    firmas: true;
    verificar_documento: true;
  }
}

export const SUBMENUS_FIRMA_02: Submenu[] = [
  {
    vista: "firmas",
    menu: "biblioteca",
    nombre: "Firmas",
    subtitulo: "Envíos a aceptación y su estado",
    orden: 2,
  },
  {
    vista: "verificar_documento",
    menu: "configuracion",
    nombre: "Verificar documento",
    subtitulo: "Comprobar un archivo por su huella",
    orden: 3,
  },
];
