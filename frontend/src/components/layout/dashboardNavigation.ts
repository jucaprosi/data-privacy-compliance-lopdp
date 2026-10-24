// ¤¤frontend-architect
// ¤frontend-ide
import {
  Clock, LayoutDashboard, Map, FileSpreadsheet, Scale, FileCheck, GitCommit,
  FolderLock, AlertOctagon, Shield, Activity, Network, Bot, FileText,
  UploadCloud, ListTree, PieChart, Download, BookOpen,
} from "lucide-react";

export type VistaActiva =
  | "dashboard"
  | "configuracion"
  | "diagnostico"
  | "rat"
  | "riesgos"
  | "dpo"
  | "auditoria"
  | "evidencias"
  | "incidentes"
  | "arco"
  | "mtge_relacional"
  | "terceros"
  | "mitigacion_ia"
  | "reportes"
  | "roadmap"
  | "niif_ingesta"
  | "niif_reclasificacion"
  | "niif_subtotales"
  | "niif_mpm"
  | "niif_diagnostico"
  | "niif_exportacion"
  | "niif_doctrina";

export const modulosNavegacionLOPDP = [
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
    subtitulo: "Scoring Multidimensional",
    icon: LayoutDashboard,
    badge: "Módulo 1",
  },
  {
    id: "roadmap" as VistaActiva,
    nombre: "Hoja de Ruta",
    subtitulo: "Olas, Tareas y Evidencias",
    icon: Map,
    badge: "Módulo 5",
  },
  {
    id: "rat" as VistaActiva,
    nombre: "RAT Maestro",
    subtitulo: "Registro de Tratamiento",
    icon: FileSpreadsheet,
    badge: "Art. 35",
  },
  {
    id: "riesgos" as VistaActiva,
    nombre: "Riesgos & MTGE",
    subtitulo: "Impacto y Criticidad",
    icon: Scale,
    badge: "ISO 27005",
  },
  {
    id: "dpo" as VistaActiva,
    nombre: "Cockpit DPD / DPO",
    subtitulo: "Panel del Oficial",
    icon: FileCheck,
    badge: "Art. 48",
  },
  {
    id: "auditoria" as VistaActiva,
    nombre: "Historial de Auditoría",
    subtitulo: "Snapshots & Doctrina 10",
    icon: GitCommit,
    badge: "Módulo 3",
  },
  {
    id: "evidencias" as VistaActiva,
    nombre: "Bóveda Evidencias",
    subtitulo: "Custodia Notarial",
    icon: FolderLock,
    badge: "Sha-256",
  },
  {
    id: "incidentes" as VistaActiva,
    nombre: "Playbook Incidentes",
    subtitulo: "SLA Legal 72h · Ley 2026",
    icon: AlertOctagon,
    badge: "SLA 72h",
  },
  {
    id: "arco" as VistaActiva,
    nombre: "Derechos ARCO+",
    subtitulo: "Arts. 21-24 LOPDP · SLA 15d",
    icon: Shield,
    badge: "Art. 37",
  },
  {
    id: "mtge_relacional" as VistaActiva,
    nombre: "MTGE Relacional",
    subtitulo: "Gran Escala · EIPD Forzosa",
    icon: Activity,
    badge: "EIPD",
  },
  {
    id: "terceros" as VistaActiva,
    nombre: "Transferencias",
    subtitulo: "Terceros y Flujos de Datos",
    icon: Network,
    badge: "Art. 60",
  },
  {
    id: "mitigacion_ia" as VistaActiva,
    nombre: "Copiloto Mitigación",
    subtitulo: "Mitigation Tracker & IA",
    icon: Bot,
    badge: "AI",
  },
  {
    id: "reportes" as VistaActiva,
    nombre: "Reportes",
    subtitulo: "Informes descargables",
    icon: FileText,
    badge: "PDF",
  }
];

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
