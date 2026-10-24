"use client";

// ¤¤frontend-architect
// ¤frontend-ide
import { AdminPanel } from "@/components/modules/roadmap/admin";
import { EvidenciaPanel } from "@/components/modules/roadmap/evidencia";
import { OlasView } from "@/components/modules/roadmap/olas";
import { PlaneacionForm } from "@/components/modules/roadmap/planeacion";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import type { OrganizacionRole, UserRoleContext } from "@/types/roadmap";

type SubvistaRoadmap = "olas" | "planeacion" | "evidencia" | "admin";

interface RoadmapWorkspaceViewProps {
  subvistaRoadmap: SubvistaRoadmap;
  setSubvistaRoadmap: (vista: SubvistaRoadmap) => void;
  tareaSeleccionadaId: string | null;
  setTareaSeleccionadaId: (id: string | null) => void;
  rolesOrganizacion: UserRoleContext[];
  rolActivo: OrganizacionRole;
  cambiarRolActivo: (rol: OrganizacionRole) => void;
  cargandoRoles: boolean;
  errorRoles: string | null;
  currentRoadmapId: string | null;
}

// ¤frontend-ide
export default function RoadmapWorkspaceView({
  subvistaRoadmap, setSubvistaRoadmap, tareaSeleccionadaId, setTareaSeleccionadaId,
  rolesOrganizacion, rolActivo, cambiarRolActivo, cargandoRoles, errorRoles,
  currentRoadmapId,
}: RoadmapWorkspaceViewProps) {
  return (
    <div className="space-y-6">
      {/* Encabezado del Módulo Hoja de Ruta */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[#26262b] pb-4">
        <div>
          <div className="flex items-center space-x-2">
            <h2 className="text-lg font-semibold text-white">Hoja de Ruta de Implementación</h2>
            <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-[#9a3bf1]/20 text-[#c084fc] border border-[#9a3bf1]/40">
              Módulo 5
            </span>
          </div>
          <p className="text-xs text-zinc-400 mt-1">
            Gestión adaptativa de olas, tareas y custodia de evidencias conforme a la LOPDP.
          </p>
        </div>

        {/* Selector de Rol Activo y Contexto de Organización */}
        <div className="flex items-center space-x-3 text-xs">
          {cargandoRoles ? (
            <span className="text-zinc-500 font-mono text-[11px]">Verificando roles…</span>
          ) : rolesOrganizacion.length > 1 ? (
            <div className="flex items-center space-x-2 bg-[#141417] border border-[#26262b] rounded-lg px-2.5 py-1.5">
              <span className="text-zinc-400 text-[11px]">Rol activo:</span>
              <select
                aria-label="Seleccionar rol activo"
                value={rolActivo}
                onChange={(e) => cambiarRolActivo(e.target.value as OrganizacionRole)}
                className="bg-transparent text-white font-medium focus:outline-none cursor-pointer"
              >
                {rolesOrganizacion.map((r, idx) => (
                  <option key={`${r.role}-${idx}`} value={r.role} className="bg-[#141417] text-white">
                    {r.role} {r.area_nombre ? `(${r.area_nombre})` : ""}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="bg-[#141417] border border-[#26262b] rounded-lg px-3 py-1 text-zinc-300 font-mono text-[11px]">
              Rol: <span className="text-white font-semibold">{rolActivo}</span>
            </div>
          )}
        </div>
      </div>

      {/* Manejo de Error o Sin Roles en Organización */}
      {errorRoles ? (
        <div className="p-4 rounded-lg bg-red-950/40 border border-red-800 text-red-200 text-xs space-y-1">
          <p className="font-semibold">No se pudo verificar tu rol en la organización.</p>
          <p className="text-red-300/80">Causa: {errorRoles}</p>
          <p className="text-zinc-400 text-[11px]">
            Comunícate con el administrador de la organización o verifica la conectividad del servidor para continuar.
          </p>
        </div>
      ) : rolesOrganizacion.length === 0 && !cargandoRoles ? (
        <div className="p-4 rounded-lg bg-amber-950/40 border border-amber-800 text-amber-200 text-xs space-y-1">
          <p className="font-semibold">Sin asignación de roles en la organización.</p>
          <p className="text-amber-300/80">
            Tu usuario no posee ningún rol activo en el tenant actual.
          </p>
          <p className="text-zinc-400 text-[11px]">
            Solicita al administrador de la organización que asigne un rol a tu cuenta para acceder a la planeación, tareas y evidencias.
          </p>
        </div>
      ) : (
        <>
          {/* Selector de Subvistas Acotado por Rol */}
          <div className="flex items-center space-x-2 border-b border-[#26262b]">
            <button
              type="button"
              onClick={() => setSubvistaRoadmap("olas")}
              className={`px-3 py-2 text-xs font-medium border-b-2 transition ${
                subvistaRoadmap === "olas"
                  ? "border-[#9a3bf1] text-white"
                  : "border-transparent text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Olas & Tareas
            </button>

            {/* Planeación solo visible para implementador (PRD §5.2) */}
            {rolActivo === "implementador" && (
              <button
                type="button"
                onClick={() => setSubvistaRoadmap("planeacion")}
                className={`px-3 py-2 text-xs font-medium border-b-2 transition ${
                  subvistaRoadmap === "planeacion"
                    ? "border-[#9a3bf1] text-white"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
              >
                Generar Hoja de Ruta
              </button>
            )}

            {/* Pestaña de Evidencia */}
            <button
              type="button"
              onClick={() => setSubvistaRoadmap("evidencia")}
              className={`px-3 py-2 text-xs font-medium border-b-2 transition ${
                subvistaRoadmap === "evidencia"
                  ? "border-[#9a3bf1] text-white"
                  : "border-transparent text-zinc-400 hover:text-zinc-200"
              }`}
            >
              Custodia de Evidencias
            </button>

            {/* Administración solo visible para admin_organizacion (PRD §5.2) */}
            {rolActivo === "admin_organizacion" && (
              <button
                type="button"
                onClick={() => setSubvistaRoadmap("admin")}
                className={`px-3 py-2 text-xs font-medium border-b-2 transition ${
                  subvistaRoadmap === "admin"
                    ? "border-[#9a3bf1] text-white"
                    : "border-transparent text-zinc-400 hover:text-zinc-200"
                }`}
              >
                Administración
              </button>
            )}
          </div>

          {/* Renderizado de la Subvista Activa */}
          <div className="pt-2">
            {subvistaRoadmap === "olas" && !currentRoadmapId ? (
              <div role="status" data-testid="roadmap-sin-hoja" className="p-4 rounded bg-[#141417] border border-[#26262b] text-zinc-300 text-xs space-y-2">
                <p className="font-semibold text-white">Todavía no hay una hoja de ruta cargada.</p>
                <p className="text-zinc-400">
                  {rolActivo === "implementador"
                    ? "Genérala desde la pestaña «Generar Hoja de Ruta»."
                    : "Pide al implementador que genere la hoja de ruta de la organización."}
                </p>
              </div>
            ) : subvistaRoadmap === "olas" && currentRoadmapId ? (
              <OlasView
                roadmapId={currentRoadmapId}
                onAbrirEvidencia={(taskId) => {
                  setTareaSeleccionadaId(taskId);
                  setSubvistaRoadmap("evidencia");
                }}
              />
            ) : subvistaRoadmap === "planeacion" && rolActivo === "implementador" ? (
              <PlaneacionForm
                onGenerado={(nuevoId) => {
                  void useRoadmapStore.getState().loadRoadmap(nuevoId);
                  setSubvistaRoadmap("olas");
                }}
              />
            ) : subvistaRoadmap === "admin" && rolActivo === "admin_organizacion" ? (
              <AdminPanel />
            ) : subvistaRoadmap === "evidencia" && !tareaSeleccionadaId ? (
              <div role="status" data-testid="roadmap-sin-tarea" className="p-4 rounded bg-[#141417] border border-[#26262b] text-zinc-400 text-xs">
                Elige una tarea en «Olas & Tareas» y usa «Ver evidencia» para ver y gestionar sus archivos.
              </div>
            ) : subvistaRoadmap === "evidencia" && tareaSeleccionadaId ? (
              <EvidenciaPanel
                taskId={tareaSeleccionadaId}
                titulo="Panel de Evidencias de Hoja de Ruta"
              />
            ) : (
              <div className="p-4 rounded bg-[#141417] border border-[#26262b] text-zinc-400 text-xs">
                Acceso no autorizado para tu rol actual en esta subvista.
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}
