"use client";

import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";
import type {
  AuditLogItem,
  PlanningVariables,
  RoadmapDetails,
  RoadmapKpis,
  RoadmapWave,
  SessionIdentity,
  TaskDetailsUpdate,
  TaskEvidence,
  TaskEvidenceValidationRequest,
  TaskPriority,
  TaskStatus,
} from "../types/roadmap";
import { ApiError } from "../types/roadmap";
import {
  getCurrentSession,
  setIdentitySession,
  roadmapApi,
} from "../lib/roadmap/cliente";

// ============================================================================
// Tipos del Estado Global de Hoja de Ruta
// ============================================================================

export interface RoadmapState {
  // Datos principales
  currentRoadmapId: string | null;
  roadmap: RoadmapDetails | null;
  waves: RoadmapWave[];
  kpis: RoadmapKpis | null;
  auditLog: AuditLogItem[];

  // Variables activas de planeación
  variables: PlanningVariables | null;

  // Filtros y UI
  selectedTaskId: string | null;
  selectedWaveId: string | null;
  statusFilter: TaskStatus | "todas";
  priorityFilter: TaskPriority | "todas";
  areaFilter: string | "todas";

  // Estado de carga y error
  isLoading: boolean;
  isGenerating: boolean;
  lastError: {
    message: string;
    code?: string;
    action_required?: string | null;
  } | null;

  // Identidad de sesión
  session: SessionIdentity;

  // Acciones de Identidad
  setSession: (session: Partial<SessionIdentity>) => void;

  // Acciones de Consulta y Carga
  loadRoadmap: (roadmapId: string) => Promise<void>;
  loadKpis: (roadmapId: string) => Promise<void>;
  loadAuditLog: (roadmapId: string, limit?: number, offset?: number) => Promise<void>;

  // Acciones de Generación
  generateRoadmap: (variables: PlanningVariables, assessment?: Record<string, unknown>) => Promise<string>;

  // Acciones de Tareas
  updateTaskStatus: (taskId: string, status: TaskStatus) => Promise<void>;
  updateTaskDetails: (taskId: string, details: TaskDetailsUpdate) => Promise<void>;
  assignTask: (taskId: string, userId: string, areaId?: string) => Promise<void>;

  // Acciones de Evidencias
  uploadEvidence: (taskId: string, file: File) => Promise<TaskEvidence>;
  validateEvidence: (taskId: string, evidenceId: string, req: TaskEvidenceValidationRequest) => Promise<void>;

  // Acciones de Filtro y Selección
  setSelectedTask: (taskId: string | null) => void;
  setSelectedWave: (waveId: string | null) => void;
  setStatusFilter: (filter: TaskStatus | "todas") => void;
  setPriorityFilter: (filter: TaskPriority | "todas") => void;
  setAreaFilter: (filter: string | "todas") => void;
  clearError: () => void;
  reset: () => void;
}

const DEFAULT_VARIABLES: PlanningVariables = {
  plazo_meses: 6,
  presupuesto: 15000,
  moneda: "USD",
  equipo: ["DPO", "Implementador"],
  dpo: "dpo-default",
  idioma: "ES",
};

export const useRoadmapStore = create<RoadmapState>()(
  persist(
    (set, get) => ({
      // Estado Inicial
      currentRoadmapId: null,
      roadmap: null,
      waves: [],
      kpis: null,
      auditLog: [],
      variables: DEFAULT_VARIABLES,

      selectedTaskId: null,
      selectedWaveId: null,
      statusFilter: "todas",
      priorityFilter: "todas",
      areaFilter: "todas",

      isLoading: false,
      isGenerating: false,
      lastError: null,

      session: getCurrentSession(),

      // Acciones de Identidad
      setSession: (newSession) => {
        setIdentitySession(newSession);
        set({ session: getCurrentSession() });
      },

      // Acciones de Consulta y Carga
      loadRoadmap: async (roadmapId: string) => {
        set({ isLoading: true, lastError: null });
        try {
          const res = await roadmapApi.getRoadmap(roadmapId);
          set({
            currentRoadmapId: roadmapId,
            roadmap: res.roadmap,
            waves: res.waves,
            variables: res.roadmap.variables_json || null,
            isLoading: false,
          });
          // Cargar KPIs en paralelo de forma resiliente
          get().loadKpis(roadmapId);
        } catch (err: unknown) {
          const apiErr = err instanceof ApiError ? err : new ApiError(500, String(err));
          set({
            isLoading: false,
            lastError: {
              message: apiErr.message,
              code: apiErr.code,
              action_required: apiErr.action_required,
            },
          });
          throw err;
        }
      },

      loadKpis: async (roadmapId: string) => {
        try {
          const kpis = await roadmapApi.getKpis(roadmapId);
          set({ kpis });
        } catch (err) {
          console.warn("[RoadmapStore] No se pudieron cargar los KPIs:", err);
        }
      },

      loadAuditLog: async (roadmapId: string, limit = 50, offset = 0) => {
        try {
          const res = await roadmapApi.getAuditLog(roadmapId, { limit, offset });
          set({ auditLog: res.items });
        } catch (err: unknown) {
          console.warn("[RoadmapStore] No se pudo cargar el audit log:", err);
        }
      },

      // Acciones de Generación
      generateRoadmap: async (variables: PlanningVariables, assessment: Record<string, unknown> = {}) => {
        set({ isGenerating: true, lastError: null });
        try {
          const { job_id } = await roadmapApi.generate(variables, assessment);

          // Espera determinista del resultado del job
          let attempts = 0;
          const maxAttempts = 30;
          let roadmapId = "";

          while (attempts < maxAttempts) {
            attempts++;
            const job = await roadmapApi.getJob(job_id);
            if (job.status === "completed" && job.roadmap_id) {
              roadmapId = job.roadmap_id;
              break;
            }
            if (job.status === "failed") {
              throw new Error(job.error || "Falló la generación del roadmap");
            }
            await new Promise((r) => setTimeout(r, 1000));
          }

          if (!roadmapId) {
            throw new ApiError(504, "Tiempo de espera agotado al generar el roadmap", "TIMEOUT");
          }

          await get().loadRoadmap(roadmapId);
          set({ isGenerating: false });
          return roadmapId;
        } catch (err: unknown) {
          const apiErr = err instanceof ApiError
            ? err
            : { message: err instanceof Error ? err.message : String(err), code: undefined, action_required: null };
          set({
            isGenerating: false,
            lastError: {
              message: apiErr.message,
              code: apiErr.code,
              action_required: apiErr.action_required,
            },
          });
          throw err;
        }
      },

      // Acciones de Tareas
      updateTaskStatus: async (taskId: string, status: TaskStatus) => {
        set({ isLoading: true, lastError: null });
        try {
          await roadmapApi.updateTaskStatus(taskId, status);

          // Actualización optimista local en waves
          set((state) => ({
            isLoading: false,
            waves: state.waves.map((w) => ({
              ...w,
              tasks: (w.tasks || []).map((t) => (t.id === taskId ? { ...t, status } : t)),
            })),
          }));

          // Refrescar KPIs
          if (get().currentRoadmapId) {
            get().loadKpis(get().currentRoadmapId!);
          }
        } catch (err: unknown) {
          const apiErr = err instanceof ApiError ? err : new ApiError(500, String(err));
          set({
            isLoading: false,
            lastError: {
              message: apiErr.message,
              code: apiErr.code,
              action_required: apiErr.action_required,
            },
          });
          throw err;
        }
      },

      updateTaskDetails: async (taskId: string, details: TaskDetailsUpdate) => {
        set({ isLoading: true, lastError: null });
        try {
          await roadmapApi.updateTaskDetails(taskId, details);
          set((state) => ({
            isLoading: false,
            waves: state.waves.map((w) => ({
              ...w,
              tasks: (w.tasks || []).map((t) => (t.id === taskId ? { ...t, ...details } : t)),
            })),
          }));
        } catch (err: unknown) {
          const apiErr = err instanceof ApiError ? err : new ApiError(500, String(err));
          set({
            isLoading: false,
            lastError: {
              message: apiErr.message,
              code: apiErr.code,
              action_required: apiErr.action_required,
            },
          });
          throw err;
        }
      },

      assignTask: async (taskId: string, userId: string, areaId?: string) => {
        set({ isLoading: true, lastError: null });
        try {
          await roadmapApi.assignTask(taskId, userId, areaId);
          set((state) => ({
            isLoading: false,
            waves: state.waves.map((w) => ({
              ...w,
              tasks: (w.tasks || []).map((t) => (t.id === taskId ? { ...t, owner: userId, area_id: areaId ?? t.area_id } : t)),
            })),
          }));
        } catch (err: unknown) {
          const apiErr = err instanceof ApiError ? err : new ApiError(500, String(err));
          set({
            isLoading: false,
            lastError: {
              message: apiErr.message,
              code: apiErr.code,
              action_required: apiErr.action_required,
            },
          });
          throw err;
        }
      },

      // Acciones de Evidencias
      uploadEvidence: async (taskId: string, file: File): Promise<TaskEvidence> => {
        set({ isLoading: true, lastError: null });
        try {
          // 1. Obtener URL de subida prefirmada
          const uploadInfo = await roadmapApi.getEvidenceUploadUrl(taskId, {
            filename: file.name,
            mime_type: file.type || "application/octet-stream",
            file_size: file.size,
          });

          // 2. Simular o realizar subida directa a R2
          if (uploadInfo.upload_url.startsWith("http")) {
            await fetch(uploadInfo.upload_url, {
              method: "PUT",
              headers: { "Content-Type": file.type || "application/octet-stream" },
              body: file,
            });
          }

          // 3. Registrar evidencia en backend
          const registered = await roadmapApi.registerEvidence(taskId, {
            r2_key: uploadInfo.r2_key,
            mime_type: file.type || "application/octet-stream",
            file_size: file.size,
          });

          // Actualizar estado local
          set((state) => ({
            isLoading: false,
            waves: state.waves.map((w) => ({
              ...w,
              tasks: (w.tasks || []).map((t) =>
                t.id === taskId
                  ? { ...t, evidence: [...(t.evidence || []), registered] }
                  : t
              ),
            })),
          }));

          return registered;
        } catch (err: unknown) {
          const apiErr = err instanceof ApiError ? err : new ApiError(500, String(err));
          set({
            isLoading: false,
            lastError: {
              message: apiErr.message,
              code: apiErr.code,
              action_required: apiErr.action_required,
            },
          });
          throw err;
        }
      },

      validateEvidence: async (taskId: string, evidenceId: string, req: TaskEvidenceValidationRequest) => {
        set({ isLoading: true, lastError: null });
        try {
          const validated = await roadmapApi.validateEvidence(taskId, evidenceId, req);

          set((state) => ({
            isLoading: false,
            waves: state.waves.map((w) => ({
              ...w,
              tasks: (w.tasks || []).map((t) =>
                t.id === taskId
                  ? {
                      ...t,
                      evidence: (t.evidence || []).map((e) => (e.id === evidenceId ? validated : e)),
                    }
                  : t
              ),
            })),
          }));
        } catch (err: unknown) {
          const apiErr = err instanceof ApiError ? err : new ApiError(500, String(err));
          set({
            isLoading: false,
            lastError: {
              message: apiErr.message,
              code: apiErr.code,
              action_required: apiErr.action_required,
            },
          });
          throw err;
        }
      },

      // Acciones de Filtro y Selección
      setSelectedTask: (taskId) => set({ selectedTaskId: taskId }),
      setSelectedWave: (waveId) => set({ selectedWaveId: waveId }),
      setStatusFilter: (filter) => set({ statusFilter: filter }),
      setPriorityFilter: (filter) => set({ priorityFilter: filter }),
      setAreaFilter: (filter) => set({ areaFilter: filter }),
      clearError: () => set({ lastError: null }),
      reset: () =>
        set({
          currentRoadmapId: null,
          roadmap: null,
          waves: [],
          kpis: null,
          auditLog: [],
          selectedTaskId: null,
          selectedWaveId: null,
          lastError: null,
        }),
    }),
    {
      name: "lopdp-roadmap-store-v1",
      storage: createJSONStorage(() => (typeof window !== "undefined" ? localStorage : (undefined as unknown as Storage))),
      partialize: (state) => ({
        currentRoadmapId: state.currentRoadmapId,
        statusFilter: state.statusFilter,
        priorityFilter: state.priorityFilter,
        areaFilter: state.areaFilter,
      }),
    }
  )
);
