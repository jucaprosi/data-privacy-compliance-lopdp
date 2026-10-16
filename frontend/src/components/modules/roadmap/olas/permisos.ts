/**
 * Qué puede hacer cada rol sobre una tarea de la hoja de ruta.
 *
 * Fuente: matriz de permisos del PRD (Módulo 5, §5.2), que verifica en el backend
 * tests/test_matriz_permisos.py. La interfaz no concede nada: solo evita ofrecer una acción
 * que el servidor va a rechazar con 403.
 */
import type { OrganizacionRole, RoadmapTask, UserRoleContext } from "../../../../types/roadmap";

export interface AccionesTarea {
  /** Marcar la tarea como pendiente, en progreso, completada o bloqueada. */
  cambiarEstado: boolean;
  /** Editar título, fechas, prioridad, KPI y entregable. */
  editar: boolean;
  /** Distribuir la tarea a un responsable. */
  asignar: boolean;
  /** Consultar el registro de auditoría. */
  verAuditoria: boolean;
  /** Abrir la evidencia de la tarea (todos los roles la ven; la subida y la validación son de FE-04). */
  verEvidencia: boolean;
}

export function accionesPermitidas(rol: OrganizacionRole): AccionesTarea {
  return {
    cambiarEstado: rol === "implementador",
    editar: rol === "implementador",
    asignar: rol === "encargado",
    verAuditoria: rol === "encargado" || rol === "dpo" || rol === "implementador" || rol === "admin_organizacion",
    verEvidencia: true,
  };
}

/**
 * Áreas que puede ver un responsable de área, según sus asignaciones activas.
 * `null` significa sin restricción: tiene una asignación sin área (transversal al tenant).
 */
export function areasVisibles(roles: UserRoleContext[]): string[] | null {
  const propias = roles.filter((r) => r.role === "responsable_area");
  if (propias.some((r) => !r.area_id)) return null;
  return propias.map((r) => r.area_id as string);
}

/** Aplica el alcance de áreas y los filtros elegidos por la persona. */
export function filtrarTareas(
  tareas: RoadmapTask[],
  filtros: { estado: string; prioridad: string; area: string },
  areasPermitidas: string[] | null,
): RoadmapTask[] {
  return tareas.filter((t) => {
    if (areasPermitidas !== null && (!t.area_id || !areasPermitidas.includes(t.area_id))) return false;
    if (filtros.estado !== "todas" && t.status !== filtros.estado) return false;
    if (filtros.prioridad !== "todas" && t.priority !== filtros.prioridad) return false;
    if (filtros.area !== "todas" && t.area_id !== filtros.area) return false;
    return true;
  });
}
