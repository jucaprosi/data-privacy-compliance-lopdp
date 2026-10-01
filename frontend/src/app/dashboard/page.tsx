"use client";

import React from "react";
import {
  Group as PanelGroup,
  Panel,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";
import {
  Search,
  SlidersHorizontal,
  Layers,
  Clock,
  FileSpreadsheet,
  Scale,
  FileCheck,
  ChevronRight,
  FileCode,
  FolderLock,
  GitCommit,
  Sun,
  Moon,
  LayoutDashboard,
  AlertOctagon,
  Shield,
  Activity,
  Network,
  Bot,
  ListTree,
  PieChart,
  Download,
  BookOpen,
  UploadCloud,
  FileText,
} from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { esNormativaFinanciera, resolverNormativa } from "@/lib/normativas";
import { TENANT_ID } from "@/lib/api";
import ProjectConfig from "@/components/ProjectConfig";
import CentralDashboard from "@/components/CentralDashboard";
import NormativaWorkspace from "@/components/NormativaWorkspace";
import AuditHistory from "@/components/AuditHistory";
import CopilotWorkspace from "@/components/copilot/CopilotWorkspace";
import FileMenu from "@/components/layout/FileMenu";
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

type VistaActiva =
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
  | "niif_ingesta"
  | "niif_reclasificacion"
  | "niif_subtotales"
  | "niif_mpm"
  | "niif_diagnostico"
  | "niif_exportacion"
  | "niif_doctrina";

export default function DashboardPage() {
  // Escucha reactiva del store de Zustand
  const {
    isConfigured,
    companyData,
    normativaSeleccionada,
    activeView,
    setActiveView,
    toggleCommandPalette,
    theme,
    toggleTheme,
  } = useAuditStore();

  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  React.useEffect(() => {
    // Cuando cambie la normativa, si la vista activa no está en el menú, resetear a dashboard
    const menusValidosLOPDP = ["dashboard", "diagnostico", "rat", "riesgos", "dpo", "auditoria", "evidencias", "incidentes", "arco", "mtge_relacional", "terceros", "mitigacion_ia", "reportes"];
    const menusValidosNIIF = ["dashboard", "diagnostico", "niif_ingesta", "niif_reclasificacion", "niif_subtotales", "niif_mpm", "niif_diagnostico", "niif_exportacion", "niif_doctrina", "mitigacion_ia"];
    const validos = !isConfigured
      ? ["configuracion"]
      : !normativaSeleccionada || !resolverNormativa(normativaSeleccionada).bancoDisponible
        ? ["diagnostico"]
        : esNormativaFinanciera(normativaSeleccionada)
          ? menusValidosNIIF
          : menusValidosLOPDP;

    if (!validos.includes(activeView)) {
      setActiveView(!isConfigured ? "configuracion" : !normativaSeleccionada || validos.length === 1 ? "diagnostico" : "dashboard");
    }
  }, [isConfigured, normativaSeleccionada, activeView, setActiveView]);

  if (!mounted) {
    return (
      <div className="flex h-screen w-screen items-center justify-center bg-white text-[#9a3bf1] font-mono text-sm select-none">
        <div className="flex flex-col items-center space-y-4 animate-pulse">
          <Layers className="w-8 h-8" />
          <span>Iniciando Entorno Cero Regresiones...</span>
        </div>
      </div>
    );
  }

  const vistaActiva: VistaActiva =
    activeView === "ia_chat"
      ? "configuracion"
      : (activeView as VistaActiva) || "dashboard";

  const setVistaActiva = (v: VistaActiva) => setActiveView(v);

  const modulosNavegacionLOPDP = [
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

  const modulosNavegacionNIIF = [
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

  const moduloNormativa = modulosNavegacionLOPDP[0];

  // El Perfil Organizacional vive exclusivamente en el pie durante el alta inicial.
  // Guardada la ficha, el pie muestra la identidad y la navegación inicia en Normativa.
  const modulosNavegacion = !isConfigured
    ? []
    : !normativaSeleccionada || !resolverNormativa(normativaSeleccionada).bancoDisponible
      ? [moduloNormativa]
      : [
          ...(esNormativaFinanciera(normativaSeleccionada)
            ? modulosNavegacionNIIF
            : modulosNavegacionLOPDP),
        ];

  return (
    <div
      className={`app-frame-canvas flex flex-col h-screen w-screen overflow-hidden gap-0.5 p-1 font-sans transition-colors duration-200 ${
        theme === "light"
          ? "theme-light bg-[#f2ecfa] text-zinc-900"
          : "theme-dark bg-[#202024] text-zinc-100"
      }`}
    >
      {/* Barra de Encabezado Superior (Alta Densidad Estilo Render) */}
      <header className="h-10 bg-[#141417] border border-[#e8dcf5] dark:border-[#3f3f46] rounded-lg px-3.5 flex items-center justify-between shrink-0 text-xs z-20 shadow-sm">
        <div className="flex items-center space-x-2.5">
          {/* Logo Plataforma */}
          <div className="flex items-center space-x-2">
            <div className="w-5 h-5 rounded bg-gradient-to-br from-[#9a3bf1] to-[#3892f3] flex items-center justify-center text-white shadow-sm">
              <Layers className="w-3.5 h-3.5" />
            </div>
            <span className="font-bold text-white tracking-tight text-xs">
              JUBYS{" "}
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#9a3bf1] to-[#3892f3]">
                LOPDP 360
              </span>
            </span>
          </div>

          <FileMenu />

          <span className="text-zinc-600">/</span>
          <span className="text-zinc-400 font-mono text-[11px]">Workspace</span>
          <ChevronRight className="w-3.5 h-3.5 text-zinc-600" />
          <span className="text-white font-medium text-[11px] bg-[#1e1e24] px-2 py-0.5 rounded border border-[#26262b]">
            {vistaActiva === "configuracion"
              ? "PERFIL ORGANIZACIONAL"
              : modulosNavegacion.find((m) => m.id === vistaActiva)?.nombre}
          </span>
        </div>

        {/* Indicadores de Entorno & Calibración + Botón Command Palette + Conmutador de Tema */}
        <div className="flex items-center space-x-3 text-[11px]">
          {/* Conmutador Minimalista de Tema Dual Acromático (Módulo 8) */}
          <button
            type="button"
            onClick={toggleTheme}
            className="h-7 w-7 rounded-md bg-[#0a0a0c] hover:bg-[#1e1e24] border border-[#26262b] text-zinc-400 hover:text-white flex items-center justify-center transition cursor-pointer"
            title={`Cambiar a tema ${theme === "dark" ? "claro" : "oscuro"}`}
          >
            {theme === "dark" ? (
              <Sun className="w-3.5 h-3.5 text-amber-400" />
            ) : (
              <Moon className="w-3.5 h-3.5 text-zinc-300" />
            )}
          </button>

          {/* Botón de Acceso Rápido Command Palette */}
          <button
            type="button"
            onClick={toggleCommandPalette}
            className="flex items-center space-x-2 px-2.5 py-1 rounded bg-[#0a0a0c] hover:bg-[#1e1e24] border border-[#26262b] hover:border-[#9a3bf1]/60 text-zinc-400 hover:text-white transition cursor-pointer shadow-xs"
            title="Abrir Command Palette (Ctrl + K)"
          >
            <Search className="w-3.5 h-3.5 text-[#9a3bf1]" />
            <span className="hidden md:inline">Buscar comando o artículo...</span>
            <kbd className="bg-[#141417] px-1.5 py-0.5 rounded border border-[#26262b] font-mono text-[10px] text-zinc-300">
              Ctrl + K
            </kbd>
          </button>

          <div className="flex items-center space-x-1.5 bg-[#0a0a0c] px-2.5 py-1 rounded border border-[#26262b]">
            <span
              className={`w-2 h-2 rounded-full ${
                isConfigured
                  ? "bg-[#00c853] shadow-[0_0_8px_rgba(0,200,83,0.8)]"
                  : "bg-amber-500 animate-pulse"
              }`}
            />
            <span className="font-mono text-zinc-300">
              {isConfigured ? "Calibrado" : "Ficha Pendiente"}
            </span>
          </div>

          <div className="hidden sm:flex items-center space-x-1.5 text-zinc-400 font-mono">
            <span className="text-zinc-500">Norma:</span>
            <span className="text-zinc-200 font-semibold">
              {resolverNormativa(normativaSeleccionada).etiquetaCorta}
            </span>
          </div>
        </div>
      </header>

      {/* Contenedor Principal con Layout de Split Panes (react-resizable-panels) */}
      <div className={`flex-1 min-h-0 flex overflow-hidden ${theme === "light" ? "bg-[#f2ecfa]" : "bg-[#202024]"}`}>
        <PanelGroup orientation="horizontal" className="flex-1 flex overflow-hidden gap-0.5">
          {/* ========================================================================= */}
          {/* PANEL IZQUIERDO: Dock / Sidebar Plegable (15% a 20%)                      */}
          {/* ========================================================================= */}
          <Panel
            id="panel-dock-izquierdo"
            defaultSize="18%"
            minSize="14%"
            maxSize="25%"
            collapsible={true}
            collapsedSize="4%"
            className="h-full"
          >
            <aside className="h-full bg-white dark:bg-[#141417] border border-[#e8dcf5] dark:border-[#3f3f46] rounded-lg flex flex-col justify-between overflow-hidden shadow-sm">
              {/* Lista de Salas ADPA / Módulos LOPDP */}
              <div className="flex-1 overflow-y-auto p-2.5 space-y-1">
                <div className="px-1 py-1 text-[10px] uppercase font-bold tracking-wider text-zinc-500 font-mono">
                  Salas Operativas ADPA
                </div>

                {modulosNavegacion.map((item) => {
                  const Icon = item.icon;
                  const isSelected = vistaActiva === item.id;
                  return (
                    <button
                      key={item.id}
                      type="button"
                      onClick={() => setVistaActiva(item.id)}
                      className={`w-full text-left px-2.5 py-2 rounded-lg text-xs flex items-center justify-between transition group cursor-pointer ${
                        isSelected
                          ? "bg-[#1e1e24] text-white border border-[#26262b] font-medium"
                          : "text-zinc-400 hover:text-zinc-200 hover:bg-[#18181d] border border-transparent"
                      }`}
                    >
                      <div className="flex items-center space-x-2.5 min-w-0">
                        <Icon
                          className={`w-4 h-4 shrink-0 transition ${
                            isSelected
                              ? "text-[#9a3bf1]"
                              : "text-zinc-500 group-hover:text-zinc-300"
                          }`}
                        />
                        <span className="truncate text-[11px] font-medium">
                          {item.nombre}
                        </span>
                      </div>

                      <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-[#0a0a0c] border border-[#26262b] text-zinc-500 shrink-0">
                        {item.badge}
                      </span>
                    </button>
                  );
                })}
              </div>

              {/* Pie contextual: alta inicial o identidad inmutable de la organización activa */}
              {!isConfigured ? (
                <button
                  type="button"
                  onClick={() => setVistaActiva("configuracion")}
                  className="w-full p-3 border-t border-[#7c16df] bg-[#9a3bf1]/15 shrink-0 text-left text-[#b66cff] hover:bg-[#9a3bf1]/25 transition cursor-pointer"
                  title="Completar el perfil organizacional"
                >
                  <div className="flex items-center gap-2 font-bold text-xs tracking-wide">
                    <SlidersHorizontal className="h-4 w-4 text-[#b66cff]" />
                    <span>PERFIL ORGANIZACIONAL</span>
                  </div>
                  <p className="mt-1 text-[10px] text-zinc-400">Ficha Organizacional</p>
                </button>
              ) : (
                <div className="w-full p-3 border-t border-[#26262b] bg-[#0a0a0c]/60 shrink-0 space-y-1.5 text-left">
                  <div className="flex min-w-0 items-center gap-2 text-[10px] text-zinc-400">
                    <span className="w-14 shrink-0 font-mono uppercase text-zinc-500">Organización:</span>
                    <span
                      className="min-w-0 flex-1 truncate font-semibold text-zinc-200"
                      title={companyData.razonSocial.trim()}
                    >
                      {companyData.razonSocial.trim()}
                    </span>
                  </div>
                  <div className="flex min-w-0 items-center gap-2 text-[10px] text-zinc-400">
                    <span className="w-14 shrink-0 font-mono uppercase text-zinc-500">Sector:</span>
                    <span
                      className="min-w-0 flex-1 truncate text-zinc-300"
                      title={companyData.sector}
                    >
                      {companyData.sector}
                    </span>
                  </div>
                  <div className="flex min-w-0 items-center gap-2 text-[10px] text-zinc-400">
                    <span className="w-14 shrink-0 font-mono uppercase text-zinc-500">Tenant ID:</span>
                    <span
                      className="min-w-0 flex-1 truncate font-mono text-zinc-300"
                      title={TENANT_ID}
                    >
                      {TENANT_ID}
                    </span>
                  </div>
                </div>
              )}
            </aside>
          </Panel>

          {/* ========================================================================= */}
          {/* SEPARADOR 1: Resize Handle con Hover & Active Púrpura de Render (#9a3bf1) */}
          {/* ========================================================================= */}
          <PanelResizeHandle
            className="w-0.5 bg-transparent cursor-col-resize select-none shrink-0"
            title="Arrastra para redimensionar el panel"
          />

          {/* ========================================================================= */}
          {/* PANEL CENTRAL: Lienzo de Trabajo (50% a 55%)                              */}
          {/* ========================================================================= */}
          <Panel
            id="panel-lienzo-central"
            defaultSize="54%"
            minSize="40%"
            className="h-full"
          >
            <main className="h-full flex flex-col overflow-hidden rounded-lg border border-[#e8dcf5] dark:border-[#3f3f46] bg-white dark:bg-[#0a0a0c] shadow-sm">
              {/* Barra de Pestañas del Workspace (Alta Densidad Estilo Render) */}
              <div className="h-9 bg-[#141417] border-b border-[#26262b] px-3 flex items-center justify-between shrink-0 text-xs">
                <div className="flex items-center space-x-2">
                  <div className="flex items-center space-x-2 px-3 py-1 bg-[#0a0a0c] border-t-2 border-[#9a3bf1] border-x border-[#26262b] text-white font-medium rounded-t shadow-xs">
                    <FileCode className="w-3.5 h-3.5 text-[#9a3bf1]" />
                    <span>
                      {vistaActiva === "configuracion"
                        ? "PerfilOrganizacional.view"
                        : `${vistaActiva}.adpa.view`}
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-2 text-[10px] text-zinc-500 font-mono">
                  <span>Store: Zustand (useAuditStore)</span>
                </div>
              </div>

              {/* Área del Lienzo de Trabajo con Scroll Independiente */}
              <div className="flex-1 overflow-y-auto p-6 bg-[#0a0a0c]">
                {vistaActiva === "dashboard" ? (
                  <CentralDashboard />
                ) : vistaActiva === "configuracion" ? (
                  <ProjectConfig />
                ) : vistaActiva === "diagnostico" ? (
                  <NormativaWorkspace />
                ) : vistaActiva === "rat" ? (
                  <RatModule />
                ) : vistaActiva === "riesgos" ? (
                  <MtgeModule />
                ) : vistaActiva === "dpo" ? (
                  <DpoCockpitModule />
                ) : vistaActiva === "auditoria" ? (
                  <AuditHistory />
                ) : vistaActiva === "evidencias" ? (
                  <EvidenciasModule />
                ) : vistaActiva === "incidentes" ? (
                  <IncidentPlaybook />
                ) : vistaActiva === "arco" ? (
                  <ArcoModule />
                ) : vistaActiva === "mtge_relacional" ? (
                  <MtgeRelacionalModule />
                ) : vistaActiva === "terceros" ? (
                  <TercerosModule />
                ) : vistaActiva === "niif_ingesta" ? (
                  <NiifIngestaView />
                ) : vistaActiva === "niif_reclasificacion" ? (
                  <NiifReclasificacionView />
                ) : vistaActiva === "niif_subtotales" ? (
                  <NiifSubtotalesView />
                ) : vistaActiva === "niif_mpm" ? (
                  <NiifMpmView />
                ) : vistaActiva === "niif_diagnostico" ? (
                  <NiifDiagnosticoView />
                ) : vistaActiva === "niif_exportacion" ? (
                  <NiifExportView />
                ) : vistaActiva === "niif_doctrina" ? (
                  <NiifDoctrinaView />
                ) : vistaActiva === "mitigacion_ia" ? (
                  <MitigationTracker />
                ) : vistaActiva === "reportes" ? (
                  <ReportesModule />
                ) : null}
              </div>
            </main>
          </Panel>

          {/* ========================================================================= */}
          {/* SEPARADOR 2: Resize Handle con Hover & Active Púrpura de Render (#9a3bf1) */}
          {/* ========================================================================= */}
          <PanelResizeHandle
            className="w-0.5 bg-transparent cursor-col-resize select-none shrink-0"
            title="Arrastra para redimensionar el panel"
          />

          {/* ========================================================================= */}
          {/* PANEL DERECHO: Copiloto IA Legal (25% a 30%)                              */}
          {/* ========================================================================= */}
          <Panel
            id="panel-copiloto-derecho"
            defaultSize="28%"
            minSize="20%"
            maxSize="45%"
            className="h-full"
          >
            <aside className="h-full bg-white dark:bg-[#141417] border border-[#e8dcf5] dark:border-[#3f3f46] rounded-lg flex flex-col overflow-hidden shadow-sm">
              <CopilotWorkspace />
            </aside>
          </Panel>
        </PanelGroup>
      </div>

      {/*
        La paleta de comandos se monta una sola vez, en el layout raíz. Cada
        instancia registra su propio listener global de Ctrl+K, de modo que una
        segunda montada aquí conmutaba el estado dos veces por pulsación y la
        paleta no llegaba a abrirse nunca desde el teclado.
      */}
    </div>
  );
}






