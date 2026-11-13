// ¤navegacion-menus
// ¤riesgos-eipd
/** Submenús de MTGE-03: Riesgos y auditoría › Evaluación de impacto guiada. Solo MTGE-03 edita este archivo. */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    eipd_guiada: true;
  }
}

export const SUBMENUS_MTGE_03: Submenu[] = [
  {
    vista: "eipd_guiada",
    menu: "riesgos_auditoria",
    nombre: "Evaluación de impacto guiada",
    subtitulo: "Asistente de ocho pasos",
    orden: 2,
  },
];
