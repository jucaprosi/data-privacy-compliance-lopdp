// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤navegacion-menus
// ¤notificaciones
/** Submenú de NOTIF-02: Inicio › Avisos. Solo NOTIF-02 edita este archivo. */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    avisos: true;
  }
}

export const SUBMENUS_NOTIF_02: Submenu[] = [
  {
    vista: "avisos",
    menu: "inicio",
    nombre: "Avisos",
    subtitulo: "Versiones por revisar",
    orden: 4,
  },
];
