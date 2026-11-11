// ¤navegacion-menus
/**
 * Submenús de ORG-18 en el menú INVENTARIO: sedes y clientes por encargo. Solo ORG-18 edita este archivo.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    sedes_organizacion: true;
    clientes_encargo: true;
  }
}

export const SUBMENUS_ORG_18: Submenu[] = [
  {
    vista: "sedes_organizacion",
    menu: "inventario",
    nombre: "Sedes y áreas",
    subtitulo: "Dónde opera la organización",
    orden: 4,
  },
  {
    vista: "clientes_encargo",
    menu: "inventario",
    nombre: "Clientes",
    subtitulo: "Organizaciones para las que tratas datos",
    orden: 5,
  },
];
