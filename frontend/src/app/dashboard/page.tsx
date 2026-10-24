"use client";

// ¤¤frontend-architect
// ¤frontend-ide
import React from "react";
import DashboardHeader from "@/components/layout/DashboardHeader";
import RoadmapWorkspaceView from "@/components/layout/RoadmapWorkspaceView";
import { modulosNavegacionLOPDP, modulosNavegacionNIIF, type VistaActiva } from "@/components/layout/dashboardNavigation";
import { useRouter } from "next/navigation";
import {
  Group as PanelGroup,
  Panel,
  Separator as PanelResizeHandle,
} from "react-resizable-panels";
import { Layers, SlidersHorizontal, FileCode } from "lucide-react";
import { useAuditStore } from "@/store/useAuditStore";
import { esNormativaFinanciera, resolverNormativa } from "@/lib/normativas";
import { cerrarSesion, olvidarCuentaDeGoogle, RUTA_LOGIN, tenantConfigurado, useSesion } from "@/lib/auth";
import ProjectConfig from "@/components/ProjectConfig";
import CentralDashboard from "@/components/CentralDashboard";
import NormativaWorkspace from "@/components/NormativaWorkspace";
import AuditHistory from "@/components/AuditHistory";
import CopilotWorkspace from "@/components/copilot/CopilotWorkspace";
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
import { organizacionApi, setIdentitySession } from "@/lib/roadmap/cliente";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import type { OrganizacionRole, UserRoleContext } from "@/types/roadmap";

type SubvistaRoadmap = "olas" | "planeacion" | "evidencia" | "admin";


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
  const router = useRouter();
  const { listo: sesionLeida, requiereSesion, sesion } = useSesion();
  // Con inicio de sesión exigido, no se monta nada del panel hasta tener una sesión vigente.
  const sinSesion = requiereSesion && !sesion;

  React.useEffect(() => {
    setMounted(true);
  }, []);

  React.useEffect(() => {
    if (sesionLeida && sinSesion) router.replace(RUTA_LOGIN);
  }, [sesionLeida, sinSesion, router]);

  const cerrarLaSesion = React.useCallback(() => {
    olvidarCuentaDeGoogle();
    cerrarSesion();
    router.replace(RUTA_LOGIN);
  }, [router]);

  // Estado del módulo Hoja de Ruta (Módulo 5)
  const roadmapSession = useRoadmapStore((s) => s.session);
  const currentRoadmapId = useRoadmapStore((s) => s.currentRoadmapId);
  const [subvistaRoadmap, setSubvistaRoadmap] = React.useState<SubvistaRoadmap>("olas");
  const [tareaSeleccionadaId, setTareaSeleccionadaId] = React.useState<string | null>(null);
  const [rolesOrganizacion, setRolesOrganizacion] = React.useState<UserRoleContext[]>([]);
  const [rolActivo, setRolActivo] = React.useState<OrganizacionRole>(roadmapSession.role);
  const [cargandoRoles, setCargandoRoles] = React.useState(false);
  const [errorRoles, setErrorRoles] = React.useState<string | null>(null);

  // Carga de roles desde /organizacion/me/roles: solo al abrir la pestaña de la Hoja de Ruta y con
  // sesión. Antes se pedía al abrir cualquier vista del panel, aunque no se usara ese módulo.
  const enRoadmap = (activeView as string) === "roadmap";
  const rolesPedidos = React.useRef(false);
  React.useEffect(() => {
    if (!enRoadmap || !sesionLeida || sinSesion || rolesPedidos.current) return;
    rolesPedidos.current = true;
    let cancelado = false;
    async function cargarRoles() {
      setCargandoRoles(true);
      setErrorRoles(null);
      try {
        const roles = await organizacionApi.getMyRoles();
        if (cancelado) return;
        setRolesOrganizacion(roles);
        if (roles.length > 0) {
          const rolInicial = roles[0].role;
          setRolActivo(rolInicial);
          useRoadmapStore.getState().setSession({ role: rolInicial });
          setIdentitySession({ role: rolInicial });
        }
      } catch (err: unknown) {
        if (cancelado) return;
        const msg = err instanceof Error ? err.message : "Error al conectar con el servicio de organización.";
        setErrorRoles(msg);
        rolesPedidos.current = false; // permite reintentar al volver a abrir la pestaña
      } finally {
        if (!cancelado) setCargandoRoles(false);
      }
    }
    cargarRoles();
    return () => {
      cancelado = true;
    };
  }, [enRoadmap, sesionLeida, sinSesion]);

  const cambiarRolActivo = React.useCallback((nuevoRol: OrganizacionRole) => {
    setRolActivo(nuevoRol);
    useRoadmapStore.getState().setSession({ role: nuevoRol });
    setIdentitySession({ role: nuevoRol });
    if (nuevoRol !== "admin_organizacion" && subvistaRoadmap === "admin") {
      setSubvistaRoadmap("olas");
    }
  }, [subvistaRoadmap]);

  React.useEffect(() => {
    // Cuando cambie la normativa, si la vista activa no está en el menú, resetear a dashboard
    const menusValidosLOPDP = ["dashboard", "diagnostico", "rat", "riesgos", "dpo", "auditoria", "evidencias", "incidentes", "arco", "mtge_relacional", "terceros", "mitigacion_ia", "reportes", "roadmap"];
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

  if (!mounted || !sesionLeida || sinSesion) {
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

  const setVistaActiva = (v: VistaActiva) => setActiveView(v as unknown as import("@/store/useAuditStore").ActiveView);


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
      <DashboardHeader
        theme={theme}
        isConfigured={isConfigured}
        workspaceTitle={vistaActiva === "configuracion"
          ? "PERFIL ORGANIZACIONAL"
          : modulosNavegacion.find((m) => m.id === vistaActiva)?.nombre}
        normativaLabel={resolverNormativa(normativaSeleccionada).etiquetaCorta}
        sessionEmail={requiereSesion ? sesion?.email : undefined}
        onLogout={cerrarLaSesion}
        onToggleTheme={toggleTheme}
        onCommandPalette={toggleCommandPalette}
      />

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
                      title={tenantConfigurado()}
                    >
                      {tenantConfigurado()}
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
                ) : vistaActiva === "roadmap" ? (
                  <RoadmapWorkspaceView
                    subvistaRoadmap={subvistaRoadmap}
                    setSubvistaRoadmap={setSubvistaRoadmap}
                    tareaSeleccionadaId={tareaSeleccionadaId}
                    setTareaSeleccionadaId={setTareaSeleccionadaId}
                    rolesOrganizacion={rolesOrganizacion}
                    rolActivo={rolActivo}
                    cambiarRolActivo={cambiarRolActivo}
                    cargandoRoles={cargandoRoles}
                    errorRoles={errorRoles}
                    currentRoadmapId={currentRoadmapId}
                  />
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
