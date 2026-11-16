// ¤navegacion-menus
// ¤auditoria-capa ¤hallazgos
/** Submenús de CAPA-04: Riesgos y auditoría › Auditorías (grilla y actas por área). */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    capa04_auditorias: true;
  }
}

export const SUBMENUS_CAPA_04: Submenu[] = [
  {
    vista: "capa04_auditorias",
    menu: "riesgos_auditoria",
    nombre: "Auditorías",
    subtitulo: "Verifica los controles y levanta las actas",
    orden: 5,
  },
];
