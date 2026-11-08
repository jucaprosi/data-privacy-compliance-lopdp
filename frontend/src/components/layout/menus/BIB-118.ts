// ¤navegacion-menus ¤adpa
/**
 * Submenú de BIB-118 en el menú BIBLIOTECA: «Administración editorial», visible solo con al menos una
 * capacidad editorial. Es comodidad: la autorización sigue en el servidor. Solo BIB-118 edita este archivo.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    biblioteca_editorial: true;
  }
}

export const SUBMENUS_BIB_118: Submenu[] = [
  {
    vista: "biblioteca_editorial",
    menu: "biblioteca",
    nombre: "Administración editorial",
    subtitulo: "Versiones maestras, revisiones y publicación",
    orden: 2,
    visible: (ctx) => (ctx.capacidadesEditoriales?.length ?? 0) > 0,
  },
];
