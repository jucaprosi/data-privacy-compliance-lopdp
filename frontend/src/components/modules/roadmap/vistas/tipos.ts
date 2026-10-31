/**
 * Tipos de lo que RM-21 añade a la hoja de ruta y que las vistas de RM-22 leen.
 * Forma de `GET /roadmaps/hallazgos` (governance/contratos/hoja_de_ruta.openapi.json): el contrato
 * declara la ruta, pero no el cuerpo de la respuesta.
 */
import type { RoadmapTask } from "../../../../types/roadmap";

export type OrigenHallazgo = "diagnostico" | "auditoria" | "eipd" | "incidente" | "tercero" | "control_periodico";

export interface HallazgoItem {
  id: string;
  origen: OrigenHallazgo;
  origen_ref: string;
  control_ref: string | null;
  dimension: string | null;
  severidad: "critica" | "alta" | "media";
  titulo: string;
  descripcion: string | null;
  estado: "abierto" | "en_tratamiento" | "cerrado";
  tarea_id: string | null;
  creado_en: string;
}

/** Tarea del plan de acción; `hallazgo_id` es el hallazgo de origen cuando la creó RM-21. */
export type TareaConOrigen = RoadmapTask & { hallazgo_id?: string | null };
