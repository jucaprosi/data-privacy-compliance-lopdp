// ¤¤frontend-architect
// ¤frontend-ide
// ¤navegacion-menus
/**
 * Pantallas que monta el lienzo central del panel, por vista (FE-22). Es la misma tabla que antes
 * vivía como cadena de condicionales en dashboard/page.tsx; el contenido de cada vista no cambia.
 */
import React from "react";
import type { VistaActiva } from "../dashboardNavigation";
import RoadmapWorkspaceView from "@/components/layout/RoadmapWorkspaceView";
import ProjectConfig from "@/components/ProjectConfig";
import CentralDashboard from "@/components/CentralDashboard";
import NormativaWorkspace from "@/components/NormativaWorkspace";
import CapaModule from "@/components/modules/CapaModule";
import AuditHistory from "@/components/AuditHistory";
import RatModule from "@/components/modules/RatModule";
import MtgeModule from "@/components/modules/MtgeModule";
import DpoCockpitModule from "@/components/modules/DpoCockpitModule";
import EvidenciasModule from "@/components/modules/EvidenciasModule";
import IncidentPlaybook from "@/components/IncidentPlaybook";
import ArcoModule from "@/components/modules/ArcoModule";
import MtgeRelacionalModule from "@/components/modules/MtgeRelacionalModule";
import TercerosModule from "@/components/modules/TercerosModule";
import NiifIngestaView from "@/components/modules/NiifIngestaView";
import NiifReclasificacionView from "@/components/modules/NiifReclasificacionView";
import NiifSubtotalesView from "@/components/modules/NiifSubtotalesView";
import NiifMpmView from "@/components/modules/NiifMpmView";
import NiifExportView from "@/components/modules/NiifExportView";
import NiifDiagnosticoView from "@/components/modules/NiifDiagnosticoView";
import NiifDoctrinaView from "@/components/modules/NiifDoctrinaView";
import MitigationTracker from "@/components/MitigationTracker";
import ReportesModule from "@/components/modules/ReportesModule";

/** Estado del panel que alguna pantalla necesita; hoy solo la Hoja de Ruta. */
export interface ContextoPantalla {
  roadmap: React.ComponentProps<typeof RoadmapWorkspaceView>;
}

export type Pantalla = (contexto: ContextoPantalla) => React.ReactNode;

export type RegistroPantallas = Partial<Record<VistaActiva, Pantalla>>;

export const PANTALLAS_BASE: RegistroPantallas = {
  dashboard: () => <CentralDashboard />,
  configuracion: () => <ProjectConfig />,
  diagnostico: () => <NormativaWorkspace />,
  roadmap: ({ roadmap }) => <RoadmapWorkspaceView {...roadmap} />,
  rat: () => <RatModule />,
  riesgos: () => <MtgeModule />,
  dpo: () => <DpoCockpitModule />,
  auditoria: () => (
    <div className="space-y-8">
      <AuditHistory />
      <CapaModule />
    </div>
  ),
  evidencias: () => <EvidenciasModule />,
  incidentes: () => <IncidentPlaybook />,
  arco: () => <ArcoModule />,
  mtge_relacional: () => <MtgeRelacionalModule />,
  terceros: () => <TercerosModule />,
  niif_ingesta: () => <NiifIngestaView />,
  niif_reclasificacion: () => <NiifReclasificacionView />,
  niif_subtotales: () => <NiifSubtotalesView />,
  niif_mpm: () => <NiifMpmView />,
  niif_diagnostico: () => <NiifDiagnosticoView />,
  niif_exportacion: () => <NiifExportView />,
  niif_doctrina: () => <NiifDoctrinaView />,
  mitigacion_ia: () => <MitigationTracker />,
  reportes: () => <ReportesModule />,
};
