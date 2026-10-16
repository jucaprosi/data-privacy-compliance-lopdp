/**
 * Cliente HTTP tipado para el módulo Hoja de Ruta e interfaces de Organización.
 *
 * Principios:
 * 1. Aislamiento estricto de cabeceras de identidad (getIdentityHeaders / setIdentitySession)
 *    para facilitar la transición futura a tokens/cookies en SEC-03.
 * 2. Manejo estandarizado de errores de negocio con ApiError (detail, code, action_required).
 * 3. Cero tokens estigmérgicos (¤) en la interfaz ni textos públicos.
 */
import type {
  ApiErrorPayload,
  AreaCreate,
  AreaItem,
  AreaUpdate,
  GenerateRoadmapRequest,
  IdentityHeaders,
  OrganizacionRole,
  PlanningVariables,
  RoadmapAuditLogResponse,
  RoadmapJobStatus,
  RoadmapKpis,
  RoadmapResponse,
  RoleGrant,
  RoleGrantItem,
  SessionIdentity,
  TaskAssignRequest,
  TaskDetailsUpdate,
  TaskEvidence,
  TaskEvidenceUploadRequest,
  TaskEvidenceUploadResponse,
  TaskEvidenceValidationRequest,
  TaskStatus,
  TaskStatusUpdate,
  UserCreate,
  UserItem,
  UserRoleContext,
} from "../../types/roadmap";
import { ApiError } from "../../types/roadmap";

const DEFAULT_API_BASE_URL = "/api/v1";

// ============================================================================
// 1. Aislamiento centralizado de cabeceras de identidad (Punto único de cambio)
// ============================================================================

let currentSession: SessionIdentity = {
  userId: process.env.NEXT_PUBLIC_USER_ID || "user-demo-implementador",
  tenantId: process.env.NEXT_PUBLIC_TENANT_ID || "tenant-corp-demo",
  role: (process.env.NEXT_PUBLIC_USER_ROLE as OrganizacionRole) || "implementador",
};

/**
 * Obtiene las cabeceras de identidad actuales.
 * Aislado en UNA sola función para que la tarea SEC-03 solo deba actualizar este punto.
 */
export function getIdentityHeaders(): IdentityHeaders {
  return {
    "X-User-ID": currentSession.userId,
    "X-Tenant-ID": currentSession.tenantId,
    "X-Role": currentSession.role,
  };
}

/**
 * Configura o conmuta la identidad activa en la sesión del cliente.
 */
export function setIdentitySession(session: Partial<SessionIdentity>): void {
  currentSession = {
    ...currentSession,
    ...session,
  };
}

/**
 * Retorna la identidad actualmente configurada.
 */
export function getCurrentSession(): SessionIdentity {
  return { ...currentSession };
}

// ============================================================================
// 2. Ejecutor de peticiones con parseo resiliente de errores
// ============================================================================

export interface RequestOptions extends Omit<RequestInit, "headers"> {
  headers?: Record<string, string>;
  baseUrl?: string;
  customFetch?: typeof fetch;
}

export async function requestJson<T>(endpoint: string, options: RequestOptions = {}): Promise<T> {
  const baseUrl = options.baseUrl ?? DEFAULT_API_BASE_URL;
  const fetchFn = options.customFetch ?? (typeof fetch !== "undefined" ? fetch : undefined);

  if (!fetchFn) {
    throw new Error("No hay una función fetch disponible en este entorno.");
  }

  const identityHeaders = getIdentityHeaders();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...identityHeaders,
    ...(options.headers || {}),
  };

  const url = `${baseUrl}${endpoint}`;
  let response: Response;

  try {
    response = await fetchFn(url, {
      ...options,
      headers,
    });
  } catch (networkError: unknown) {
    const msg = networkError instanceof Error ? networkError.message : "Error de red";
    throw new ApiError(0, `Fallo de conexión al servidor: ${msg}`);
  }

  if (!response.ok) {
    let errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    let errorCode: string | undefined;
    let actionRequired: string | null = null;

    try {
      const errorJson = (await response.json()) as ApiErrorPayload;
      if (errorJson && typeof errorJson === "object") {
        if (typeof errorJson.detail === "string") {
          errorDetail = errorJson.detail;
        } else if (errorJson.detail) {
          errorDetail = JSON.stringify(errorJson.detail);
        }
        errorCode = errorJson.code;
        actionRequired = errorJson.action_required ?? null;
      }
    } catch {
      // Si la respuesta no es JSON, conservar errorDetail genérico
    }

    throw new ApiError(response.status, errorDetail, errorCode, actionRequired);
  }

  if (response.status === 204) {
    return undefined as unknown as T;
  }

  return (await response.json()) as T;
}

// ============================================================================
// 3. Cliente de API para Hoja de Ruta
// ============================================================================

export const roadmapApi = {
  // Generación y consulta
  async generate(variables: PlanningVariables, assessment: Record<string, unknown> = {}, options?: RequestOptions): Promise<{ job_id: string }> {
    const session = getCurrentSession();
    const payload: GenerateRoadmapRequest = {
      tenant_id: session.tenantId,
      user_id: session.userId,
      variables,
      assessment,
    };
    return requestJson<{ job_id: string }>("/roadmaps/generate", {
      method: "POST",
      body: JSON.stringify(payload),
      ...options,
    });
  },

  async getJob(jobId: string, options?: RequestOptions): Promise<RoadmapJobStatus> {
    return requestJson<RoadmapJobStatus>(`/roadmaps/jobs/${encodeURIComponent(jobId)}`, {
      method: "GET",
      ...options,
    });
  },

  async getRoadmap(roadmapId: string, options?: RequestOptions): Promise<RoadmapResponse> {
    return requestJson<RoadmapResponse>(`/roadmaps/${encodeURIComponent(roadmapId)}`, {
      method: "GET",
      ...options,
    });
  },

  async getKpis(roadmapId: string, options?: RequestOptions): Promise<RoadmapKpis> {
    return requestJson<RoadmapKpis>(`/roadmaps/${encodeURIComponent(roadmapId)}/kpis`, {
      method: "GET",
      ...options,
    });
  },

  // Gestión de tareas
  async updateTaskStatus(taskId: string, status: TaskStatus, options?: RequestOptions): Promise<{ status: TaskStatus }> {
    const payload: TaskStatusUpdate = { status };
    return requestJson<{ status: TaskStatus }>(`/roadmaps/tasks/${encodeURIComponent(taskId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
      ...options,
    });
  },

  async updateTaskDetails(taskId: string, details: TaskDetailsUpdate, options?: RequestOptions): Promise<Record<string, unknown>> {
    return requestJson<Record<string, unknown>>(`/roadmaps/tasks/${encodeURIComponent(taskId)}/details`, {
      method: "PATCH",
      body: JSON.stringify(details),
      ...options,
    });
  },

  async assignTask(taskId: string, userId: string, options?: RequestOptions): Promise<Record<string, unknown>> {
    const payload: TaskAssignRequest = { user_id: userId };
    return requestJson<Record<string, unknown>>(`/roadmaps/tasks/${encodeURIComponent(taskId)}/assign`, {
      method: "POST",
      body: JSON.stringify(payload),
      ...options,
    });
  },

  // Evidencias (R2)
  async getEvidenceUploadUrl(taskId: string, uploadReq: TaskEvidenceUploadRequest, options?: RequestOptions): Promise<TaskEvidenceUploadResponse> {
    return requestJson<TaskEvidenceUploadResponse>(`/roadmaps/tasks/${encodeURIComponent(taskId)}/evidence/upload-url`, {
      method: "POST",
      body: JSON.stringify(uploadReq),
      ...options,
    });
  },

  async registerEvidence(
    taskId: string,
    params: { r2_key: string; mime_type: string; file_size: number; file_hash?: string | null },
    options?: RequestOptions
  ): Promise<TaskEvidence> {
    const query = new URLSearchParams({
      r2_key: params.r2_key,
      mime_type: params.mime_type,
      file_size: params.file_size.toString(),
    });
    if (params.file_hash) {
      query.set("file_hash", params.file_hash);
    }
    return requestJson<TaskEvidence>(`/roadmaps/tasks/${encodeURIComponent(taskId)}/evidence?${query.toString()}`, {
      method: "POST",
      ...options,
    });
  },

  async listEvidence(taskId: string, options?: RequestOptions): Promise<TaskEvidence[]> {
    return requestJson<TaskEvidence[]>(`/roadmaps/tasks/${encodeURIComponent(taskId)}/evidence`, {
      method: "GET",
      ...options,
    });
  },

  async validateEvidence(
    taskId: string,
    evidenceId: string,
    validationReq: TaskEvidenceValidationRequest,
    options?: RequestOptions
  ): Promise<TaskEvidence> {
    return requestJson<TaskEvidence>(
      `/roadmaps/tasks/${encodeURIComponent(taskId)}/evidence/${encodeURIComponent(evidenceId)}`,
      {
        method: "PATCH",
        body: JSON.stringify(validationReq),
        ...options,
      }
    );
  },

  // Auditoría
  async getAuditLog(
    roadmapId: string,
    pagination: { limit?: number; offset?: number } = {},
    options?: RequestOptions
  ): Promise<RoadmapAuditLogResponse> {
    const query = new URLSearchParams();
    if (pagination.limit !== undefined) query.set("limit", pagination.limit.toString());
    if (pagination.offset !== undefined) query.set("offset", pagination.offset.toString());
    const qs = query.toString() ? `?${query.toString()}` : "";
    return requestJson<RoadmapAuditLogResponse>(`/roadmaps/${encodeURIComponent(roadmapId)}/audit-log${qs}`, {
      method: "GET",
      ...options,
    });
  },
};

// ============================================================================
// 4. Cliente de API para Organización
// ============================================================================

export const organizacionApi = {
  async getMyRoles(options?: RequestOptions): Promise<UserRoleContext[]> {
    return requestJson<UserRoleContext[]>("/organizacion/me/roles", {
      method: "GET",
      ...options,
    });
  },

  async listUsers(options?: RequestOptions): Promise<UserItem[]> {
    return requestJson<UserItem[]>("/organizacion/usuarios", {
      method: "GET",
      ...options,
    });
  },

  async createUser(payload: UserCreate, options?: RequestOptions): Promise<UserItem> {
    return requestJson<UserItem>("/organizacion/usuarios", {
      method: "POST",
      body: JSON.stringify(payload),
      ...options,
    });
  },

  async listAreas(options?: RequestOptions): Promise<AreaItem[]> {
    return requestJson<AreaItem[]>("/organizacion/areas", {
      method: "GET",
      ...options,
    });
  },

  async createArea(payload: AreaCreate, options?: RequestOptions): Promise<AreaItem> {
    return requestJson<AreaItem>("/organizacion/areas", {
      method: "POST",
      body: JSON.stringify(payload),
      ...options,
    });
  },

  async updateArea(areaId: string, payload: AreaUpdate, options?: RequestOptions): Promise<AreaItem> {
    return requestJson<AreaItem>(`/organizacion/areas/${encodeURIComponent(areaId)}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
      ...options,
    });
  },

  async listRoles(options?: RequestOptions): Promise<RoleGrantItem[]> {
    return requestJson<RoleGrantItem[]>("/organizacion/roles", {
      method: "GET",
      ...options,
    });
  },

  async grantRole(payload: RoleGrant, options?: RequestOptions): Promise<RoleGrantItem> {
    return requestJson<RoleGrantItem>("/organizacion/roles", {
      method: "POST",
      body: JSON.stringify(payload),
      ...options,
    });
  },

  async revokeRole(assignmentId: string, options?: RequestOptions): Promise<void> {
    return requestJson<void>(`/organizacion/roles/${encodeURIComponent(assignmentId)}`, {
      method: "DELETE",
      ...options,
    });
  },
};
