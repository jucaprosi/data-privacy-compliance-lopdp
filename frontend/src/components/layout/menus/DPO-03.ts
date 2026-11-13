// ¤navegacion-menus
// ¤dpo-cockpit
/** Submenús de DPO-03: Operación › Consultas al DPO y DPO › Consultas atendidas. Solo DPO-03 edita este archivo. */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    consultas_dpo_mias: true;
    consultas_dpo_atendidas: true;
  }
}

export const SUBMENUS_DPO_03: Submenu[] = [
  {
    vista: "consultas_dpo_mias",
    menu: "operacion",
    nombre: "Consultas al DPO",
    subtitulo: "Pregunta al DPO y consulta sus respuestas",
    orden: 3,
  },
  {
    vista: "consultas_dpo_atendidas",
    menu: "dpo",
    nombre: "Consultas atendidas",
    subtitulo: "Consultas de la organización y sus respuestas",
    orden: 2,
  },
];
