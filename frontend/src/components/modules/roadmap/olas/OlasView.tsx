"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { AlertCircle, Loader2 } from "lucide-react";

import { organizacionApi } from "@/lib/roadmap/cliente";
import { useRoadmapStore } from "@/store/useRoadmapStore";
import { ApiError } from "@/types/roadmap";
import type { AreaItem, RoadmapTask, TaskDetailsUpdate, TaskPriority, TaskStatus, UserItem } from "@/types/roadmap";
import { KpiBar } from "./KpiBar";
import { accionesPermitidas, areasVisibles, filtrarTareas } from "./permisos";
import { ESTADOS, PRIORIDADES, TareaCard, type ErrorAccion } from "./TareaCard";

export interface OlasViewProps {
  roadmapId: string;
  /** Se invoca al pedir la evidencia de una tarea; el panel de evidencia lo aporta FE-04. */
  onAbrirEvidencia?: (taskId: string) => void;
}

interface EstadoAccion {
  ocupada: boolean;
  error: ErrorAccion | null;
}

type UsuarioAsignable = UserItem & { roles?: Array<{ role: string; area_id?: string | null }> };

const SELECTOR =
  "rounded-md bg-[#0a0a0c] border border-[#26262b] px-2.5 py-1.5 text-xs text-zinc-100 " +
  "focus:outline-none focus:ring-2 focus:ring-[#3892f3]";

function aErrorAccion(err: unknown): ErrorAccion {
  if (err instanceof ApiError) return { mensaje: err.message, codigo: err.code, accion: err.action_required };
  return { mensaje: "No se pudo completar la acción. Inténtalo de nuevo." };
}

export function OlasView({ roadmapId, onAbrirEvidencia }: OlasViewProps) {
  const rol = useRoadmapStore((s) => s.session.role);
  const roadmap = useRoadmapStore((s) => s.roadmap);
  const olas = useRoadmapStore((s) => s.waves);
  const kpis = useRoadmapStore((s) => s.kpis);
  const auditLog = useRoadmapStore((s) => s.auditLog);
  const cargando = useRoadmapStore((s) => s.isLoading);
  const errorCarga = useRoadmapStore((s) => s.lastError);
  const filtroEstado = useRoadmapStore((s) => s.statusFilter);
  const filtroPrioridad = useRoadmapStore((s) => s.priorityFilter);
  const filtroArea = useRoadmapStore((s) => s.areaFilter);
  const store = useRoadmapStore.getState;

  const [areasPermitidas, setAreasPermitidas] = useState<string[] | null>(null);
  const [alcanceListo, setAlcanceListo] = useState(rol !== "responsable_area");
  const [nombresArea, setNombresArea] = useState<Record<string, string>>({});
  const [areas, setAreas] = useState<AreaItem[]>([]);
  const [areasAsignacion, setAreasAsignacion] = useState<Record<string, string>>({});
  const [usuarios, setUsuarios] = useState<UsuarioAsignable[]>([]);
  const [responsablesAsignacion, setResponsablesAsignacion] = useState<Record<string, string>>({});
  const [acciones, setAcciones] = useState<Record<string, EstadoAccion>>({});
  const [auditoriaAbierta, setAuditoriaAbierta] = useState<string | null>(null);
  const [cargaInicial, setCargaInicial] = useState(true);

  const permisos = useMemo(() => accionesPermitidas(rol), [rol]);

  useEffect(() => {
    let vigente = true;
    setCargaInicial(true);
    store()
      .loadRoadmap(roadmapId)
      .catch(() => undefined)
      .finally(() => {
        if (vigente) setCargaInicial(false);
      });
    return () => {
      vigente = false;
    };
  }, [roadmapId, store]);

  // Un responsable de área solo ve las tareas de sus áreas (PRD §5.2): se sabe por sus roles activos.
  useEffect(() => {
    let vigente = true;
    if (rol !== "responsable_area") {
      setAreasPermitidas(null);
      setAlcanceListo(true);
      return;
    }
    setAlcanceListo(false);
    organizacionApi
      .getMyRoles()
      .then((roles) => {
        if (vigente) setAreasPermitidas(areasVisibles(roles));
      })
      .catch(() => {
        // Sin poder confirmar su alcance, no se muestra nada: es la opción segura.
        if (vigente) setAreasPermitidas([]);
      })
      .finally(() => {
        if (vigente) setAlcanceListo(true);
      });
    return () => {
      vigente = false;
    };
  }, [rol]);

  // Los nombres de las áreas los lista solo el administrador; el resto verá el identificador.
  useEffect(() => {
    let vigente = true;
    organizacionApi
      .listAreas()
      .then((areas) => {
        if (vigente) {
          setAreas(areas);
          setNombresArea(Object.fromEntries(areas.map((a) => [a.id, a.nombre])));
        }
      })
      .catch(() => undefined);
    organizacionApi.listUsers().then((items) => {
      if (vigente) setUsuarios(items as UsuarioAsignable[]);
    }).catch(() => undefined);
    return () => {
      vigente = false;
    };
  }, [rol]);

  const ejecutar = useCallback(async (tareaId: string, accion: () => Promise<void>) => {
    setAcciones((previo) => ({ ...previo, [tareaId]: { ocupada: true, error: null } }));
    try {
      await accion();
      setAcciones((previo) => ({ ...previo, [tareaId]: { ocupada: false, error: null } }));
    } catch (err: unknown) {
      setAcciones((previo) => ({ ...previo, [tareaId]: { ocupada: false, error: aErrorAccion(err) } }));
    }
  }, []);

  const verAuditoria = useCallback(
    (tareaId: string) => {
      setAuditoriaAbierta(tareaId);
      void store().loadAuditLog(roadmapId, 200, 0);
    },
    [roadmapId, store],
  );

  const olasOrdenadas = useMemo(() => [...olas].sort((a, b) => a.sort_order - b.sort_order), [olas]);

  const areasEnTareas = useMemo(() => {
    const ids = new Set<string>();
    for (const ola of olas) for (const t of ola.tasks ?? []) if (t.area_id) ids.add(t.area_id);
    return [...ids].sort();
  }, [olas]);

  const etiquetaArea = (id?: string | null) => (id ? nombresArea[id] ?? `Área ${id}` : undefined);

  if ((cargaInicial || !alcanceListo) && !roadmap) {
    return (
      <div role="status" className="flex items-center gap-2 text-sm text-zinc-300">
        <Loader2 className="w-4 h-4 animate-spin text-[#3892f3]" aria-hidden="true" />
        Cargando la hoja de ruta…
      </div>
    );
  }

  if (!roadmap) {
    return (
      <div role="alert" className="flex items-start gap-2.5 p-3 rounded-lg bg-[#ff1744]/10 border border-[#ff1744]/40 text-xs text-zinc-200">
        <AlertCircle className="w-4 h-4 shrink-0 mt-0.5 text-[#ff1744]" aria-hidden="true" />
        <div className="space-y-0.5">
          <p data-testid="error-carga">{errorCarga?.message ?? "No se pudo cargar la hoja de ruta."}</p>
          {errorCarga?.code && <p className="text-zinc-400">Código: {errorCarga.code}</p>}
          {errorCarga?.action_required && <p className="text-zinc-400">Acción requerida: {errorCarga.action_required}</p>}
        </div>
      </div>
    );
  }

  const filtros = { estado: filtroEstado, prioridad: filtroPrioridad, area: filtroArea };
  const totalVisibles = olasOrdenadas.reduce(
    (suma, ola) => suma + filtrarTareas(ola.tasks ?? [], filtros, areasPermitidas).length,
    0,
  );

  return (
    <section aria-label="Hoja de ruta" className="space-y-5 text-zinc-200">
      <header className="space-y-1">
        <h2 className="text-sm font-bold uppercase tracking-wider text-white">Hoja de ruta</h2>
        {roadmap.summary && <p className="text-xs text-zinc-400">{roadmap.summary}</p>}
      </header>

      <KpiBar kpis={kpis} />

      <div role="group" aria-label="Filtros" className="flex flex-wrap items-end gap-3">
        <div>
          <label htmlFor="filtro-estado" className="block text-[11px] font-semibold text-zinc-300 mb-1">
            Estado
          </label>
          <select
            id="filtro-estado"
            className={SELECTOR}
            value={filtroEstado}
            onChange={(e) => store().setStatusFilter(e.target.value as TaskStatus | "todas")}
          >
            <option value="todas">Todos</option>
            {(Object.keys(ESTADOS) as TaskStatus[]).map((e) => (
              <option key={e} value={e}>
                {ESTADOS[e]}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="filtro-prioridad" className="block text-[11px] font-semibold text-zinc-300 mb-1">
            Prioridad
          </label>
          <select
            id="filtro-prioridad"
            className={SELECTOR}
            value={filtroPrioridad}
            onChange={(e) => store().setPriorityFilter(e.target.value as TaskPriority | "todas")}
          >
            <option value="todas">Todas</option>
            {(Object.keys(PRIORIDADES) as TaskPriority[]).map((p) => (
              <option key={p} value={p}>
                {PRIORIDADES[p]}
              </option>
            ))}
          </select>
        </div>
        {areasEnTareas.length > 0 && (
          <div>
            <label htmlFor="filtro-area" className="block text-[11px] font-semibold text-zinc-300 mb-1">
              Área
            </label>
            <select
              id="filtro-area"
              className={SELECTOR}
              value={filtroArea}
              onChange={(e) => store().setAreaFilter(e.target.value)}
            >
              <option value="todas">Todas</option>
              {areasEnTareas
                .filter((a) => areasPermitidas === null || areasPermitidas.includes(a))
                .map((a) => (
                  <option key={a} value={a}>
                    {etiquetaArea(a)}
                  </option>
                ))}
            </select>
          </div>
        )}
        <p role="status" data-testid="total-visibles" className="text-xs text-zinc-400 pb-1.5">
          {totalVisibles} {totalVisibles === 1 ? "tarea visible" : "tareas visibles"}
          {cargando ? " · actualizando…" : ""}
        </p>
      </div>

      {totalVisibles === 0 && (
        <p role="status" className="text-xs text-zinc-400">
          {rol === "responsable_area" && areasPermitidas !== null && areasPermitidas.length === 0
            ? "No tienes un área asignada, por eso no hay tareas que mostrar."
            : "Ninguna tarea coincide con los filtros elegidos."}
        </p>
      )}

      <div className="space-y-6">
        {olasOrdenadas.map((ola) => {
          const tareas: RoadmapTask[] = filtrarTareas(ola.tasks ?? [], filtros, areasPermitidas);
          if (tareas.length === 0) return null;
          return (
            <section key={ola.id} aria-label={`Ola: ${ola.name}`} data-testid={`ola-${ola.id}`} className="space-y-3">
              <header>
                <h3 className="text-xs font-bold uppercase tracking-wider text-white">{ola.name}</h3>
                {ola.objective && <p className="text-[11px] text-zinc-400 mt-0.5">{ola.objective}</p>}
              </header>
              <div className="space-y-3">
                {tareas.map((tarea) => {
                  const estado = acciones[tarea.id] ?? { ocupada: false, error: null };
                  return (
                    <div key={tarea.id} className="space-y-2">
                      {permisos.asignar && (
                        <div className="flex max-w-2xl flex-wrap items-end gap-2">
                          <label htmlFor={`area-asignacion-${tarea.id}`} className="block text-[11px] font-semibold text-zinc-300 mb-1">
                            Área para {tarea.title}
                          </label>
                          <select
                            id={`area-asignacion-${tarea.id}`}
                            className={SELECTOR}
                            value={areasAsignacion[tarea.id] ?? tarea.area_id ?? ""}
                            onChange={(e) => setAreasAsignacion((actual) => ({ ...actual, [tarea.id]: e.target.value }))}
                          >
                            <option value="">Selecciona un área</option>
                            {areas.map((area) => <option key={area.id} value={area.id}>{area.nombre}</option>)}
                          </select>
                          <div>
                            <label htmlFor={`responsable-asignacion-${tarea.id}`} className="block text-[11px] font-semibold text-zinc-300 mb-1">
                              Responsable del área
                            </label>
                            <select
                              id={`responsable-asignacion-${tarea.id}`}
                              className={SELECTOR}
                              value={responsablesAsignacion[tarea.id] ?? ""}
                              onChange={(e) => setResponsablesAsignacion((actual) => ({ ...actual, [tarea.id]: e.target.value }))}
                            >
                              <option value="">Selecciona un responsable</option>
                              {usuarios.filter((usuario) => {
                                const areaId = areasAsignacion[tarea.id] ?? tarea.area_id;
                                const area = areas.find((item) => item.id === areaId);
                                return areaId && (area?.responsable_user_id === usuario.id || usuario.roles?.some(
                                  (asignacion) => asignacion.role === "responsable_area" && asignacion.area_id === areaId,
                                ));
                              }).map((usuario) => <option key={usuario.id} value={usuario.id}>{usuario.nombre}</option>)}
                            </select>
                          </div>
                          <button
                            type="button"
                            className={SELECTOR}
                            disabled={!responsablesAsignacion[tarea.id] || !(areasAsignacion[tarea.id] ?? tarea.area_id)}
                            onClick={() => void ejecutar(tarea.id, () => store().assignTask(
                              tarea.id,
                              responsablesAsignacion[tarea.id],
                              areasAsignacion[tarea.id] ?? tarea.area_id ?? undefined,
                            ))}
                          >
                            Distribuir tarea
                          </button>
                        </div>
                      )}
                      <TareaCard
                      tarea={tarea}
                      acciones={permisos}
                      ocupada={estado.ocupada}
                      error={estado.error}
                      nombreArea={etiquetaArea(tarea.area_id)}
                      auditoria={
                        auditoriaAbierta === tarea.id ? auditLog.filter((evento) => evento.task_id === tarea.id) : null
                      }
                      onCambiarEstado={(nuevo) => void ejecutar(tarea.id, () => store().updateTaskStatus(tarea.id, nuevo))}
                      onEditar={(detalles: TaskDetailsUpdate) =>
                        void ejecutar(tarea.id, () => store().updateTaskDetails(tarea.id, detalles))
                      }
                      onAsignar={(usuario) => void ejecutar(
                        tarea.id,
                        () => store().assignTask(tarea.id, usuario, areasAsignacion[tarea.id] ?? tarea.area_id ?? undefined),
                      )}
                      onVerAuditoria={() => verAuditoria(tarea.id)}
                      onOcultarAuditoria={() => setAuditoriaAbierta(null)}
                      onVerEvidencia={onAbrirEvidencia ? () => onAbrirEvidencia(tarea.id) : undefined}
                      />
                    </div>
                  );
                })}
              </div>
            </section>
          );
        })}
      </div>
    </section>
  );
}

export default OlasView;
