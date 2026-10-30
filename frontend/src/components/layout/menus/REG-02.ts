// ¤navegacion-menus
/**
 * Submenús de REG-02: menú 8 «Conocimiento» (Normativa Ecuador, Resúmenes y guías, Ayuda). El Copiloto
 * (orden 1) sigue en `base.ts`; Cursos y Material comercial no son de esta tarea.
 */
import type { Submenu } from "./base";

declare module "../dashboardNavigation" {
  interface VistasRegistradas {
    normativa_ecuador: true;
    resumenes_guias: true;
    ayuda_conocimiento: true;
  }
}

export const SUBMENUS_REG_02: Submenu[] = [
  { vista: "normativa_ecuador", menu: "conocimiento", nombre: "Normativa Ecuador", subtitulo: "LOPDP y Reglamento por artículo", orden: 2 },
  { vista: "resumenes_guias", menu: "conocimiento", nombre: "Resúmenes y guías", subtitulo: "Resúmenes con su cita", orden: 3 },
  { vista: "ayuda_conocimiento", menu: "conocimiento", nombre: "Ayuda", subtitulo: "Base legal de cada control", orden: 4 },
];
