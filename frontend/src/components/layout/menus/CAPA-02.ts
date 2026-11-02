// ¤navegacion-menus
// ¤controles-periodicos
/** Submenús de CAPA-02: Riesgos y auditoría › Controles periódicos. Solo CAPA-02 edita este archivo. */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    controles_periodicos: true;
  }
}

export const SUBMENUS_CAPA_02: Submenu[] = [
  {
    vista: "controles_periodicos",
    menu: "riesgos_auditoria",
    nombre: "Controles periódicos",
    subtitulo: "Frecuencia, responsable y vencimientos",
    orden: 4,
  },
];
