// ¤¤frontend-architect
// ¤frontend-ide
// ¤navegacion-menus
/**
 * Nueve menús de la estructura funcional y la reubicación de las vistas actuales
 * (governance/especificaciones/FE-22.md, reglas R1 y R2). Es una capa de presentación:
 * las salas, sus compuertas y sus rutas de API no cambian.
 */
import type { VistaActiva } from "../dashboardNavigation";

export type MenuId =
  | "inicio" | "diagnostico" | "inventario" | "biblioteca" | "operacion"
  | "riesgos_auditoria" | "dpo" | "conocimiento" | "configuracion";

export interface Menu { id: MenuId; nombre: string; orden: number }

export interface Submenu {
  vista: VistaActiva;          // la vista que monta dashboard/page.tsx
  menu: MenuId;
  nombre: string;
  subtitulo: string;
  orden: number;               // orden dentro de su menú
}

/** R1 · Menús fijos, en este orden. */
export const MENUS: readonly Menu[] = [
  { id: "inicio", nombre: "Inicio", orden: 1 },
  { id: "diagnostico", nombre: "Diagnóstico", orden: 2 },
  { id: "inventario", nombre: "Inventario", orden: 3 },
  { id: "biblioteca", nombre: "Biblioteca", orden: 4 },
  { id: "operacion", nombre: "Operación", orden: 5 },
  { id: "riesgos_auditoria", nombre: "Riesgos y auditoría", orden: 6 },
  { id: "dpo", nombre: "DPO", orden: 7 },
  { id: "conocimiento", nombre: "Conocimiento", orden: 8 },
  { id: "configuracion", nombre: "Configuración", orden: 9 },
];

/** R2 · Cada vista LOPDP actual, en exactamente un menú. */
export const SUBMENUS_BASE: readonly Submenu[] = [
  { vista: "dashboard", menu: "inicio", nombre: "Tablero de la organización", subtitulo: "Cuatro dimensiones y brechas", orden: 1 },
  { vista: "diagnostico", menu: "diagnostico", nombre: "Assessment", subtitulo: "Selección de normativa y evaluación", orden: 1 },
  { vista: "reportes", menu: "diagnostico", nombre: "Reporte", subtitulo: "Informes descargables", orden: 2 },
  { vista: "roadmap", menu: "diagnostico", nombre: "Hoja de ruta", subtitulo: "Olas, tareas y evidencias", orden: 3 },
  { vista: "rat", menu: "inventario", nombre: "Tratamientos (RAT)", subtitulo: "Registro de actividades de tratamiento", orden: 1 },
  { vista: "terceros", menu: "inventario", nombre: "Encargados y terceros", subtitulo: "Transferencias y flujos de datos", orden: 2 },
  { vista: "evidencias", menu: "biblioteca", nombre: "Evidencias", subtitulo: "Custodia con huella SHA-256", orden: 1 },
  { vista: "arco", menu: "operacion", nombre: "Solicitudes de titulares", subtitulo: "Derechos de los titulares", orden: 1 },
  { vista: "incidentes", menu: "operacion", nombre: "Vulneraciones", subtitulo: "Bitácora y notificación", orden: 2 },
  { vista: "riesgos", menu: "riesgos_auditoria", nombre: "Matriz de riesgos", subtitulo: "Impacto y criticidad", orden: 1 },
  { vista: "mtge_relacional", menu: "riesgos_auditoria", nombre: "Evaluaciones de impacto", subtitulo: "Gran escala y EIPD", orden: 2 },
  { vista: "auditoria", menu: "riesgos_auditoria", nombre: "Auditorías", subtitulo: "Historial y acciones correctivas", orden: 3 },
  { vista: "dpo", menu: "dpo", nombre: "Panel del DPO", subtitulo: "Supervisión del delegado", orden: 1 },
  { vista: "mitigacion_ia", menu: "conocimiento", nombre: "Copiloto", subtitulo: "Seguimiento de mitigaciones con IA", orden: 1 },
  { vista: "configuracion", menu: "configuracion", nombre: "Perfil de la organización", subtitulo: "Datos de la entidad", orden: 1 },
];
