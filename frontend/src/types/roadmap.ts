/**
 * Tipos TypeScript para el módulo Hoja de Ruta Inteligente y Organización.
 * Derivados automáticamente desde governance/contratos/hoja_de_ruta.openapi.json.
 * Generador: frontend/src/lib/roadmap/generar_tipos.js (Node sin dependencias).
 */

// ============================================================================
// Manejo estándar de Errores de Negocio (Backend Plataforma LOPDP 360)
// ============================================================================
export interface ApiErrorPayload {
  detail: string;
  code?: string;
  action_required?: string | null;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly action_required?: string | null;

  constructor(status: number, message: string, code?: string, action_required?: string | null) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.action_required = action_required;
  }
}

// ============================================================================
// Enums derivados del contrato
// ============================================================================
export type RoadmapStatus = 'draft' | 'generated' | 'active' | 'completed';
export type TaskPriority = 'critica' | 'alta' | 'media';
export type TaskStatus = 'pendiente' | 'en_progreso' | 'completada' | 'bloqueada';
export type EvidenceValidationStatus = 'pending' | 'approved' | 'rejected';
export type OrganizacionRole = 'responsable_area' | 'coordinador' | 'dpo' | 'implementador' | 'admin_organizacion';

// ============================================================================
// Modelos de Hoja de Ruta y Tareas
// ============================================================================
export interface PlanningVariables {
  plazo_meses: number;
  presupuesto: number;
  moneda: string;
  equipo: string[];
  dpo: string;
  sistemas_proveedores?: string;
  contratos_relevantes?: string;
  prioridades_negocio?: string[];
  evidencia_por_control?: Record<string, boolean>;
  restricciones_locales?: string;
  idioma?: string;
}

export interface GenerateRoadmapRequest {
  tenant_id: string;
  user_id: string;
  variables: PlanningVariables;
  assessment?: Record<string, unknown>;
}

export interface TaskEvidence {
  id: string;
  task_id: string;
  tenant_id: string;
  r2_key: string;
  mime_type?: string | null;
  file_size?: number | null;
  file_hash?: string | null;
  uploaded_by?: string | null;
  uploaded_at?: string | null;
  validation_status: EvidenceValidationStatus;
  validated_by?: string | null;
  validated_at?: string | null;
  notes?: string | null;
}

export interface TaskEvidenceUploadRequest {
  filename: string;
  mime_type: string;
  file_size: number;
}

export interface TaskEvidenceUploadResponse {
  upload_url: string;
  r2_key: string;
}

export interface TaskEvidenceValidationRequest {
  validation_status: EvidenceValidationStatus;
  notes?: string;
}

export interface RoadmapTask {
  id: string;
  wave_id?: string;
  tenant_id?: string;
  control_ref: string;
  dimension: string;
  title: string;
  description?: string | null;
  owner?: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  effort_hours?: number | null;
  start_date?: string | null;
  end_date?: string | null;
  kpi?: string | null;
  deliverable?: string | null;
  area_id?: string | null;
  evidence_required?: string[] | null;
  evidence?: TaskEvidence[];
  dependencias?: string[];
}

export interface RoadmapWave {
  id: string;
  roadmap_id?: string;
  tenant_id?: string;
  name: string;
  start_date?: string | null;
  end_date?: string | null;
  objective?: string | null;
  sort_order: number;
  tasks?: RoadmapTask[];
}

export interface RoadmapDetails {
  id: string;
  tenant_id: string;
  status: RoadmapStatus;
  created_at: string;
  updated_at: string;
  summary?: string | null;
  score_objetivo?: number | null;
  variables_json: PlanningVariables;
}

export interface RoadmapResponse {
  roadmap: RoadmapDetails;
  waves: RoadmapWave[];
}

export interface RoadmapKpis {
  completadas: number;
  total: number;
  criticas: number;
  altas: number;
  porcentaje_avance?: number;
}

export interface RoadmapJobStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  roadmap_id?: string | null;
  error?: string | null;
  created_at?: string;
  finished_at?: string | null;
}

export interface TaskStatusUpdate {
  status: TaskStatus;
}

export interface TaskDetailsUpdate {
  title?: string;
  description?: string;
  priority?: TaskPriority;
  start_date?: string | null;
  end_date?: string | null;
  effort_hours?: number | null;
  kpi?: string;
  deliverable?: string;
}

export interface TaskAssignRequest {
  user_id: string;
}

export interface AuditLogItem {
  id: string;
  task_id: string;
  action: string;
  user_id: string | null;
  timestamp: string;
  payload: Record<string, unknown>;
}

export interface RoadmapAuditLogResponse {
  total: number;
  limit: number;
  offset: number;
  items: AuditLogItem[];
}

// ============================================================================
// Modelos de Organización
// ============================================================================
export interface AreaItem {
  id: string;
  tenant_id: string;
  nombre: string;
  codigo?: string | null;
  parent_area_id?: string | null;
  responsable_user_id?: string | null;
  created_at?: string;
}

export interface AreaCreate {
  nombre: string;
  codigo?: string | null;
  parent_area_id?: string | null;
}

export interface AreaUpdate {
  nombre?: string | null;
  codigo?: string | null;
  responsable_user_id?: string | null;
}

export interface UserItem {
  id: string;
  email: string;
  nombre: string;
}

export interface UserCreate {
  email: string;
  nombre: string;
}

export interface RoleGrantItem {
  id: string;
  user_id: string;
  tenant_id: string;
  role: OrganizacionRole;
  area_id?: string | null;
  valid_from?: string | null;
  valid_to?: string | null;
}

export interface RoleGrant {
  user_id: string;
  role: OrganizacionRole;
  area_id?: string | null;
  valid_to?: string | null;
}

export interface UserRoleContext {
  role: OrganizacionRole;
  area_id?: string | null;
  area_nombre?: string | null;
  valid_to?: string | null;
}

// ============================================================================
// Configuración de Identidad de Sesión Frontend
// ============================================================================
export interface IdentityHeaders {
  'X-User-ID': string;
  'X-Tenant-ID': string;
  'X-Role': string;
}

export interface SessionIdentity {
  userId: string;
  tenantId: string;
  role: OrganizacionRole;
}

