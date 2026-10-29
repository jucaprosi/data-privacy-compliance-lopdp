// ¤¤frontend-architect
// ¤frontend-ide
// ¤navegacion-menus
import {
  Clock, LayoutDashboard, FileCheck, Activity, Bot,
  UploadCloud, ListTree, PieChart, Download, BookOpen,
} from "lucide-react";
import { esNormativaFinanciera, resolverNormativa } from "@/lib/normativas";
import type { NormativaAuditoria } from "@/store/useAuditStore";
import { SUBMENUS } from "./menus";

/**
 * Vistas que puede montar el panel. Es una interfaz, no una unión cerrada, para que una tarea que
 * añade una pantalla la declare en su propio archivo (`menus/<ID>.ts`) sin editar este:
 *
 *   declare module "../dashboardNavigation" {
 *     interface VistasRegistradas { mi_vista: true }
 *   }
 */
export interface VistasRegistradas {
  dashboard: true;
  configuracion: true;
  diagnostico: true;
  rat: true;
  riesgos: true;
  dpo: true;
  auditoria: true;
  evidencias: true;
  incidentes: true;
  arco: true;
  mtge_relacional: true;
  terceros: true;
  mitigacion_ia: true;
  reportes: true;
  roadmap: true;
  niif_ingesta: true;
  niif_reclasificacion: true;
  niif_subtotales: true;
  niif_mpm: true;
  niif_diagnostico: true;
  niif_exportacion: true;
  niif_doctrina: true;
}

export type VistaActiva = keyof VistasRegistradas;

/**
 * Navegación LOPDP: nueve menús con sus submenús (FE-22, `¤navegacion-menus`). Los menús y las
 * vistas actuales están en `menus/base.ts`; cada tarea que añade submenús lo hace en su propio
 * `menus/<ID>.ts`, y `menus/index.ts` los reúne.
 */
export { MENUS, SUBMENUS, type Menu, type MenuId, type Submenu } from "./menus";

/**
 * Qué navegación corresponde al estado del proyecto. Sin ficha guardada solo se abre el perfil;
 * sin normativa con banco, solo el assessment (donde se elige); NIIF 18 conserva su navegación
 * plana (R5) y LOPDP usa los nueve menús.
 */
export type ModoNavegacion = "alta" | "sin_normativa" | "niif" | "lopdp";

export function modoNavegacion(
  isConfigured: boolean,
  normativa: NormativaAuditoria | null | undefined
): ModoNavegacion {
  if (!isConfigured) return "alta";
  if (!normativa || !resolverNormativa(normativa).bancoDisponible) return "sin_normativa";
  return esNormativaFinanciera(normativa) ? "niif" : "lopdp";
}

/**
 * Vistas que se pueden abrir en cada modo. Con LOPDP son las de los submenús que tienen pantalla
 * registrada (R4). Tras el alta el perfil sigue cerrado, como antes de FE-22: todavía no existe un
 * acceso al perfil después de guardar la ficha.
 */
export function vistasPermitidas(
  modo: ModoNavegacion,
  tienePantalla: (vista: VistaActiva) => boolean
): readonly VistaActiva[] {
  switch (modo) {
    case "alta":
      return ["configuracion"];
    case "sin_normativa":
      return ["diagnostico"];
    case "niif":
      return modulosNavegacionNIIF.map((m) => m.id);
    case "lopdp":
      return SUBMENUS.map((s) => s.vista).filter((v) => v !== "configuracion" && tienePantalla(v));
  }
}

/**
 * NIIF 18 no entra en los nueve menús: es un paquete normativo propio, elegido en «Normativa»,
 * con esta navegación plana.
 */
export const modulosNavegacionNIIF = [
  {
    id: "diagnostico" as VistaActiva,
    nombre: "Normativa",
    subtitulo: "Selección y evaluación",
    icon: Clock,
    badge: "Norma",
  },
  {
    id: "dashboard" as VistaActiva,
    nombre: "Dashboard Central",
    subtitulo: "Panorama NIIF",
    icon: LayoutDashboard,
    badge: "Inicio",
  },
  {
    id: "niif_ingesta" as VistaActiva,
    nombre: "Ingesta de Balance",
    subtitulo: "Subida y Análisis NIIF 18",
    icon: UploadCloud,
    badge: "Paso 1",
  },
  {
    id: "niif_reclasificacion" as VistaActiva,
    nombre: "Matriz Reclasificación",
    subtitulo: "Categorías 0 a 5",
    icon: ListTree,
    badge: "Paso 2",
  },
  {
    id: "niif_subtotales" as VistaActiva,
    nombre: "Árbol de EEFF",
    subtitulo: "Subtotales Mandatorios",
    icon: Activity,
    badge: "Paso 3",
  },
  {
    id: "niif_mpm" as VistaActiva,
    nombre: "Conciliación MPM",
    subtitulo: "Medidas de Rendimiento",
    icon: PieChart,
    badge: "Paso 4",
  },
  {
    id: "niif_diagnostico" as VistaActiva,
    nombre: "Diagnóstico y Plan",
    subtitulo: "Hallazgos y Recomendaciones",
    icon: FileCheck,
    badge: "Paso 5",
  },
  {
    id: "niif_exportacion" as VistaActiva,
    nombre: "Centro de Exportación",
    subtitulo: "Excel e Informe",
    icon: Download,
    badge: "Paso 6",
  },
  {
    id: "niif_doctrina" as VistaActiva,
    nombre: "Visor Doctrinal",
    subtitulo: "Bases NIIF 18",
    icon: BookOpen,
    badge: "Paso 7",
  },
  {
    id: "mitigacion_ia" as VistaActiva,
    nombre: "Copiloto IA",
    subtitulo: "Asistente Financiero",
    icon: Bot,
    badge: "AI",
  }
];
