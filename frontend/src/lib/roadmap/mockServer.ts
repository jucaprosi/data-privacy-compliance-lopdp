/**
 * Servidor simulado en memoria (Mock) del contrato OpenAPI para Hoja de Ruta y Organización.
 * Permite desarrollo frontend desacoplado y pruebas unitarias deterministas sin base de datos.
 */
import type {
  AreaCreate,
  AreaItem,
  AreaUpdate,
  AuditLogItem,
  GenerateRoadmapRequest,
  OrganizacionRole,
  PlanningVariables,
  RoadmapAuditLogResponse,
  RoadmapDetails,
  RoadmapJobStatus,
  RoadmapKpis,
  RoadmapResponse,
  RoadmapTask,
  RoadmapWave,
  RoleGrant,
  RoleGrantItem,
  TaskDetailsUpdate,
  TaskEvidence,
  TaskEvidenceUploadRequest,
  TaskEvidenceUploadResponse,
  TaskEvidenceValidationRequest,
  TaskStatus,
  UserCreate,
  UserItem,
  UserRoleContext,
} from "../../types/roadmap.ts";
import type { HallazgoItem } from "../../components/modules/roadmap/vistas/tipos.ts";

export interface MockDatabase {
  roadmaps: Map<string, RoadmapDetails>;
  waves: Map<string, RoadmapWave[]>;
  tasks: Map<string, RoadmapTask>;
  evidence: Map<string, TaskEvidence[]>;
  auditLog: AuditLogItem[];
  jobs: Map<string, RoadmapJobStatus>;
  areas: Map<string, AreaItem>;
  users: Map<string, UserItem>;
  roleAssignments: Map<string, RoleGrantItem>;
  /** Hallazgos de RM-21 para GET /roadmaps/hallazgos; sin ellos la lista sale vacía. */
  hallazgos?: HallazgoItem[];
}

export function createInitialMockDatabase(): MockDatabase {
  const defaultRoadmapId = "rm-demo-001";
  const defaultTenantId = "tenant-corp-demo";

  const defaultVariables: PlanningVariables = {
    plazo_meses: 6,
    presupuesto: 25000,
    moneda: "USD",
    equipo: ["DPO", "Ingeniero de Seguridad", "Oficial de Cumplimiento"],
    dpo: "dpo-corp-01",
    sistemas_proveedores: "ERP SAP, Google Workspace, CRM HubSpot",
    contratos_relevantes: "Cláusulas tipo DPA con proveedores clave",
    prioridades_negocio: ["Evitar sanciones graves", "Cumplir plazos SPDP"],
    evidencia_por_control: { P1: true, P2: false, P3: true },
    idioma: "ES",
  };

  const roadmap: RoadmapDetails = {
    id: defaultRoadmapId,
    tenant_id: defaultTenantId,
    status: "active",
    created_at: new Date(Date.now() - 86400000 * 5).toISOString(),
    updated_at: new Date().toISOString(),
    summary: "Plan Estratégico de Adecuación LOPDP Ecuador en 3 Olas de Transformación.",
    score_objetivo: 85.5,
    variables_json: defaultVariables,
  };

  const task1: RoadmapTask = {
    id: "task-001",
    wave_id: "wave-001",
    tenant_id: defaultTenantId,
    control_ref: "P1",
    dimension: "D01",
    title: "Formalizar la designación del Delegado de Protección de Datos (DPO)",
    description: "Inscribir al DPO ante la Autoridad de Protección de Datos Personales (SPDP).",
    owner: "user-admin-01",
    priority: "critica",
    status: "completada",
    effort_hours: 16,
    start_date: "2026-10-01",
    end_date: "2026-10-15",
    kpi: "Notificación y acuse de recibo de la SPDP",
    deliverable: "Oficio formal de inscripción y acta de directorio",
    evidence_required: ["Acuse formal SPDP", "Acta Directorio"],
    evidence: [],
  };

  const task2: RoadmapTask = {
    id: "task-002",
    wave_id: "wave-001",
    tenant_id: defaultTenantId,
    control_ref: "P2",
    dimension: "D02",
    title: "Inventario y Registro de Actividades de Tratamiento (RAT)",
    description: "Completar la ficha RAT para los procesos corporativos críticos.",
    owner: "user-impl-01",
    priority: "alta",
    status: "en_progreso",
    effort_hours: 40,
    start_date: "2026-10-10",
    end_date: "2026-11-15",
    kpi: "100% de áreas con tratamiento catastradas",
    deliverable: "Registro RAT firmado por responsables de área",
    evidence_required: ["Documento RAT consolidado", "Validación jurídica"],
    evidence: [],
  };

  const task3: RoadmapTask = {
    id: "task-003",
    wave_id: "wave-002",
    tenant_id: defaultTenantId,
    control_ref: "P3",
    dimension: "D03",
    title: "Política General de Privacidad y Avisos por Canal",
    description: "Actualizar textos en web, apps y contratos según la Ley Orgánica.",
    owner: "user-impl-01",
    priority: "alta",
    status: "pendiente",
    effort_hours: 24,
    start_date: "2026-11-15",
    end_date: "2026-12-15",
    kpi: "Avisos publicados en todos los puntos de captación",
    deliverable: "Política de Privacidad v2.0 aprobada",
    evidence_required: ["Enlaces públicos verificados"],
    evidence: [],
  };

  const wave1: RoadmapWave = {
    id: "wave-001",
    roadmap_id: defaultRoadmapId,
    tenant_id: defaultTenantId,
    name: "Ola 1: Gobierno y Cimientos Jurídicos",
    start_date: "2026-10-01",
    end_date: "2026-11-15",
    objective: "Estructurar la gobernanza, designación de DPO y formalización inicial.",
    sort_order: 1,
    tasks: [task1, task2],
  };

  const wave2: RoadmapWave = {
    id: "wave-002",
    roadmap_id: defaultRoadmapId,
    tenant_id: defaultTenantId,
    name: "Ola 2: Operación y Protección de Derechos ARCO",
    start_date: "2026-11-16",
    end_date: "2026-12-31",
    objective: "Despliegue de procedimientos operativos y canales de atención.",
    sort_order: 2,
    tasks: [task3],
  };

  const evidence1: TaskEvidence = {
    id: "evi-001",
    task_id: "task-001",
    tenant_id: defaultTenantId,
    r2_key: `${defaultTenantId}/task-001/oficio_spdp.pdf`,
    mime_type: "application/pdf",
    file_size: 154200,
    file_hash: "a1b2c3d4e5f67890123456789abcdef0123456789abcdef0123456789abcdef0",
    uploaded_by: "user-impl-01",
    uploaded_at: new Date(Date.now() - 86400000 * 2).toISOString(),
    validation_status: "approved",
    validated_by: "dpo-corp-01",
    validated_at: new Date(Date.now() - 86400000).toISOString(),
    notes: "Oficio revisado con sello de ventanilla electrónica SPDP.",
  };
  task1.evidence = [evidence1];

  const db: MockDatabase = {
    roadmaps: new Map([[defaultRoadmapId, roadmap]]),
    waves: new Map([[defaultRoadmapId, [wave1, wave2]]]),
    tasks: new Map([
      [task1.id, task1],
      [task2.id, task2],
      [task3.id, task3],
    ]),
    evidence: new Map([[task1.id, [evidence1]]]),
    auditLog: [
      {
        id: "aud-001",
        task_id: "task-001",
        action: "task_created",
        user_id: "user-admin-01",
        timestamp: new Date(Date.now() - 86400000 * 5).toISOString(),
        payload: { titulo: task1.title },
      },
      {
        id: "aud-002",
        task_id: "task-001",
        action: "evidence_uploaded",
        user_id: "user-impl-01",
        timestamp: new Date(Date.now() - 86400000 * 2).toISOString(),
        payload: { evidence_id: "evi-001", filename: "oficio_spdp.pdf" },
      },
      {
        id: "aud-003",
        task_id: "task-001",
        action: "evidence_validated",
        user_id: "dpo-corp-01",
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        payload: { status: "approved" },
      },
      {
        id: "aud-004",
        task_id: "task-001",
        action: "status_changed",
        user_id: "user-admin-01",
        timestamp: new Date(Date.now() - 86400000).toISOString(),
        payload: { status: "completada" },
      },
    ],
    jobs: new Map(),
    areas: new Map([
      [
        "area-001",
        {
          id: "area-001",
          tenant_id: defaultTenantId,
          nombre: "Dirección de Tecnología y Ciberseguridad",
          codigo: "TI-01",
          responsable_user_id: "user-resp-01",
          created_at: new Date().toISOString(),
        },
      ],
      [
        "area-002",
        {
          id: "area-002",
          tenant_id: defaultTenantId,
          nombre: "Asesoría Jurídica y Cumplimiento",
          codigo: "AJ-01",
          created_at: new Date().toISOString(),
        },
      ],
    ]),
    users: new Map([
      [
        "user-admin-01",
        { id: "user-admin-01", email: "admin@corp.ec", nombre: "Administrador de Organización" },
      ],
      [
        "dpo-corp-01",
        { id: "dpo-corp-01", email: "dpo@corp.ec", nombre: "Delegado de Protección de Datos" },
      ],
      [
        "user-impl-01",
        { id: "user-impl-01", email: "implementador@corp.ec", nombre: "Líder de Implementación" },
      ],
      [
        "user-resp-01",
        { id: "user-resp-01", email: "responsable.ti@corp.ec", nombre: "Responsable de Área TI" },
      ],
    ]),
    roleAssignments: new Map([
      [
        "assign-001",
        {
          id: "assign-001",
          user_id: "user-admin-01",
          tenant_id: defaultTenantId,
          role: "admin_organizacion",
        },
      ],
      [
        "assign-002",
        {
          id: "assign-002",
          user_id: "dpo-corp-01",
          tenant_id: defaultTenantId,
          role: "dpo",
        },
      ],
      [
        "assign-003",
        {
          id: "assign-003",
          user_id: "user-impl-01",
          tenant_id: defaultTenantId,
          role: "implementador",
        },
      ],
      [
        "assign-004",
        {
          id: "assign-004",
          user_id: "user-resp-01",
          tenant_id: defaultTenantId,
          role: "responsable_area",
          area_id: "area-001",
        },
      ],
    ]),
  };

  return db;
}

/**
 * Crea una función fetch simulada (mockFetch) conectada al estado en memoria.
 */
export function createMockFetch(db: MockDatabase = createInitialMockDatabase()): typeof fetch {
  return async function mockFetch(input: RequestInfo | URL, init: RequestInit = {}): Promise<Response> {
    const rawUrl = typeof input === "string" ? input : input instanceof URL ? input.toString() : input.url;
    const urlObj = new URL(rawUrl, "http://localhost");
    const pathname = urlObj.pathname.replace(/^\/api\/v1/, "");
    const method = (init.method || "GET").toUpperCase();

    // Extraer cabeceras
    const headers = new Headers(init.headers);
    const tenantId = headers.get("X-Tenant-ID") || "tenant-corp-demo";
    const userId = headers.get("X-User-ID") || "user-demo";
    const role = (headers.get("X-Role") as OrganizacionRole) || "implementador";

    // Helper de respuesta JSON
    function jsonResponse(data: unknown, status = 200): Response {
      return new Response(JSON.stringify(data), {
        status,
        headers: { "Content-Type": "application/json" },
      });
    }

    // Helper de error de negocio
    function errorResponse(status: number, detail: string, code?: string, action_required?: string | null): Response {
      return new Response(
        JSON.stringify({
          detail,
          code,
          action_required: action_required ?? null,
        }),
        {
          status,
          headers: { "Content-Type": "application/json" },
        }
      );
    }

    // Parsear body si aplica
    let bodyJson: Record<string, unknown> = {};
    if (init.body && typeof init.body === "string") {
      try {
        bodyJson = JSON.parse(init.body);
      } catch {
        bodyJson = {};
      }
    }

    // ========================================================================
    // Enrutamiento de Roadmaps
    // ========================================================================

    // POST /roadmaps/generate
    if (pathname === "/roadmaps/generate" && method === "POST") {
      if (role !== "implementador") {
        return errorResponse(403, `Rol ${role} no autorizado para generar roadmaps`, "FORBIDDEN");
      }
      const jobId = `job-${Date.now()}`;
      const newRoadmapId = `rm-${Date.now()}`;
      const req = bodyJson as unknown as GenerateRoadmapRequest;

      db.jobs.set(jobId, {
        job_id: jobId,
        status: "completed",
        roadmap_id: newRoadmapId,
        created_at: new Date().toISOString(),
        finished_at: new Date().toISOString(),
      });

      const newRoadmap: RoadmapDetails = {
        id: newRoadmapId,
        tenant_id: tenantId,
        status: "active",
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        summary: "Hoja de ruta generada por copiloto en base a variables de planeación.",
        score_objetivo: 80.0,
        variables_json: req.variables,
      };
      db.roadmaps.set(newRoadmapId, newRoadmap);
      db.waves.set(newRoadmapId, []);

      return jsonResponse({ job_id: jobId }, 202);
    }

    // GET /roadmaps/hallazgos (RM-21): antes de /roadmaps/:id, que también casaría con «hallazgos».
    if (pathname === "/roadmaps/hallazgos" && method === "GET") {
      if (!["implementador", "coordinador", "dpo", "admin_organizacion"].includes(role)) {
        return errorResponse(403, `Rol ${role} no autorizado para consultar hallazgos`, "FORBIDDEN");
      }
      return jsonResponse({ hallazgos: db.hallazgos ?? [] });
    }

    // GET /roadmaps/jobs/:id
    const jobMatch = pathname.match(/^\/roadmaps\/jobs\/([^/]+)$/);
    if (jobMatch && method === "GET") {
      const jobId = jobMatch[1];
      const job = db.jobs.get(jobId);
      if (!job) {
        return errorResponse(404, "Job no encontrado", "JOB_NOT_FOUND");
      }
      return jsonResponse(job);
    }

    // GET /roadmaps/:id/audit-log
    const auditMatch = pathname.match(/^\/roadmaps\/([^/]+)\/audit-log$/);
    if (auditMatch && method === "GET") {
      const allowed = ["coordinador", "dpo", "implementador", "admin_organizacion"];
      if (!allowed.includes(role)) {
        return errorResponse(403, `Rol ${role} no autorizado para consultar auditoría`, "FORBIDDEN");
      }
      const roadmapId = auditMatch[1];
      const rm = db.roadmaps.get(roadmapId);
      if (!rm || rm.tenant_id !== tenantId) {
        return errorResponse(404, "Roadmap no encontrado", "ROADMAP_NOT_FOUND");
      }
      const limit = parseInt(urlObj.searchParams.get("limit") || "50", 10);
      const offset = parseInt(urlObj.searchParams.get("offset") || "0", 10);
      const items = db.auditLog.slice(offset, offset + limit);
      const response: RoadmapAuditLogResponse = {
        total: db.auditLog.length,
        limit,
        offset,
        items,
      };
      return jsonResponse(response);
    }

    // GET /roadmaps/:id/kpis
    const kpisMatch = pathname.match(/^\/roadmaps\/([^/]+)\/kpis$/);
    if (kpisMatch && method === "GET") {
      const roadmapId = kpisMatch[1];
      const rm = db.roadmaps.get(roadmapId);
      if (!rm || rm.tenant_id !== tenantId) {
        return errorResponse(404, "Roadmap no encontrado", "ROADMAP_NOT_FOUND");
      }
      const waves = db.waves.get(roadmapId) || [];
      const allTasks = waves.flatMap((w) => w.tasks || []);
      const completadas = allTasks.filter((t) => t.status === "completada").length;
      const criticas = allTasks.filter((t) => t.priority === "critica").length;
      const altas = allTasks.filter((t) => t.priority === "alta").length;
      const kpis: RoadmapKpis = {
        total: allTasks.length,
        completadas,
        criticas,
        altas,
        porcentaje_avance: allTasks.length > 0 ? Math.round((completadas / allTasks.length) * 100) : 0,
      };
      return jsonResponse(kpis);
    }

    // GET /roadmaps/:id
    const roadmapMatch = pathname.match(/^\/roadmaps\/([^/]+)$/);
    if (roadmapMatch && method === "GET") {
      const roadmapId = roadmapMatch[1];
      const rm = db.roadmaps.get(roadmapId);
      if (!rm || rm.tenant_id !== tenantId) {
        return errorResponse(404, "Roadmap no encontrado", "ROADMAP_NOT_FOUND");
      }
      const waves = db.waves.get(roadmapId) || [];
      const response: RoadmapResponse = {
        roadmap: rm,
        waves,
      };
      return jsonResponse(response);
    }

    // PATCH /roadmaps/tasks/:id/details
    const taskDetailsMatch = pathname.match(/^\/roadmaps\/tasks\/([^/]+)\/details$/);
    if (taskDetailsMatch && method === "PATCH") {
      if (role !== "implementador") {
        return errorResponse(403, `Rol ${role} no autorizado para editar detalles`, "FORBIDDEN");
      }
      const taskId = taskDetailsMatch[1];
      const task = db.tasks.get(taskId);
      if (!task || task.tenant_id !== tenantId) {
        return errorResponse(404, "Tarea no encontrada", "TASK_NOT_FOUND");
      }
      const details = bodyJson as TaskDetailsUpdate;
      if (details.title !== undefined) task.title = details.title;
      if (details.description !== undefined) task.description = details.description;
      if (details.priority !== undefined) task.priority = details.priority;
      if (details.start_date !== undefined) task.start_date = details.start_date;
      if (details.end_date !== undefined) task.end_date = details.end_date;
      if (details.effort_hours !== undefined) task.effort_hours = details.effort_hours;
      if (details.kpi !== undefined) task.kpi = details.kpi;
      if (details.deliverable !== undefined) task.deliverable = details.deliverable;
      return jsonResponse({ ok: true, task });
    }

    // POST /roadmaps/tasks/:id/assign
    const taskAssignMatch = pathname.match(/^\/roadmaps\/tasks\/([^/]+)\/assign$/);
    if (taskAssignMatch && method === "POST") {
      // Matriz del PRD §5.2: distribuir tareas a los responsables es del coordinador.
      if (role !== "coordinador") {
        return errorResponse(403, `Rol ${role} no autorizado para asignar tareas`, "FORBIDDEN");
      }
      const taskId = taskAssignMatch[1];
      const task = db.tasks.get(taskId);
      if (!task || task.tenant_id !== tenantId) {
        return errorResponse(404, "Tarea no encontrada", "TASK_NOT_FOUND");
      }
      const assign = bodyJson as { responsable_id: string; area_id?: string };
      const targetUserId = assign.responsable_id;
      const targetAreaId = assign.area_id ?? task.area_id;
      if (!targetAreaId) {
        return errorResponse(422, "Debes seleccionar el área de la tarea antes de asignar al responsable", "TASK_AREA_REQUIRED");
      }
      if (!db.areas.has(targetAreaId)) {
        return errorResponse(404, "Área no encontrada en la organización", "AREA_NOT_FOUND");
      }
      const assignment = Array.from(db.roleAssignments.values()).find(
        (item) => item.user_id === targetUserId && item.role === "responsable_area" && item.area_id === targetAreaId,
      );
      if (!assignment) {
        return errorResponse(422, "El responsable no pertenece al área asignada a la tarea", "RESPONSABLE_AREA_MISMATCH");
      }
      const previousAreaId = task.area_id ?? null;
      task.owner = targetUserId;
      task.area_id = targetAreaId;
      db.auditLog.push({
        id: `aud-${Date.now()}-assign`, task_id: taskId, action: "task_assigned", user_id: userId,
        timestamp: new Date().toISOString(),
        payload: { responsable_id: targetUserId, area_id_anterior: previousAreaId, area_id_nueva: targetAreaId },
      });
      return jsonResponse({ ok: true, task_id: taskId, owner: targetUserId, area_id: targetAreaId });
    }

    // PATCH /roadmaps/tasks/:id
    const taskMatch = pathname.match(/^\/roadmaps\/tasks\/([^/]+)$/);
    if (taskMatch && method === "PATCH") {
      if (role !== "implementador") {
        return errorResponse(403, `Rol ${role} no autorizado para cambiar estado`, "FORBIDDEN");
      }
      const taskId = taskMatch[1];
      const task = db.tasks.get(taskId);
      if (!task || task.tenant_id !== tenantId) {
        return errorResponse(404, "Tarea no encontrada", "TASK_NOT_FOUND");
      }
      const newStatus = (bodyJson as { status: TaskStatus }).status;
      task.status = newStatus;
      db.auditLog.push({
        id: `aud-${Date.now()}`,
        task_id: taskId,
        action: "status_changed",
        user_id: userId,
        timestamp: new Date().toISOString(),
        payload: { status: newStatus },
      });
      return jsonResponse({ status: newStatus });
    }

    // POST /roadmaps/tasks/:id/evidence/upload-url
    const uploadUrlMatch = pathname.match(/^\/roadmaps\/tasks\/([^/]+)\/evidence\/upload-url$/);
    if (uploadUrlMatch && method === "POST") {
      const allowed = ["responsable_area", "coordinador"];
      if (!allowed.includes(role)) {
        return errorResponse(403, `Rol ${role} no autorizado para solicitar subida`, "FORBIDDEN");
      }
      const taskId = uploadUrlMatch[1];
      const task = db.tasks.get(taskId);
      if (!task || task.tenant_id !== tenantId) {
        return errorResponse(404, "Tarea no encontrada", "TASK_NOT_FOUND");
      }
      const uploadReq = bodyJson as unknown as TaskEvidenceUploadRequest;
      const r2Key = `${tenantId}/${taskId}/${uploadReq.filename}`;
      const res: TaskEvidenceUploadResponse = {
        upload_url: `https://mock-r2.local/upload/${r2Key}?signature=valid`,
        r2_key: r2Key,
      };
      return jsonResponse(res);
    }

    // POST /roadmaps/tasks/:id/evidence
    const regEvidenceMatch = pathname.match(/^\/roadmaps\/tasks\/([^/]+)\/evidence$/);
    if (regEvidenceMatch && method === "POST") {
      const allowed = ["responsable_area", "coordinador"];
      if (!allowed.includes(role)) {
        return errorResponse(403, `Rol ${role} no autorizado para registrar evidencia`, "FORBIDDEN");
      }
      const taskId = regEvidenceMatch[1];
      const task = db.tasks.get(taskId);
      if (!task || task.tenant_id !== tenantId) {
        return errorResponse(404, "Tarea no encontrada", "TASK_NOT_FOUND");
      }
      const r2Key = urlObj.searchParams.get("r2_key") || "default.pdf";
      const mimeType = urlObj.searchParams.get("mime_type") || "application/pdf";
      const fileSize = parseInt(urlObj.searchParams.get("file_size") || "1024", 10);
      const fileHash = urlObj.searchParams.get("file_hash") || null;

      const newEvidence: TaskEvidence = {
        id: `evi-${Date.now()}`,
        task_id: taskId,
        tenant_id: tenantId,
        r2_key: r2Key,
        mime_type: mimeType,
        file_size: fileSize,
        file_hash: fileHash,
        uploaded_by: userId,
        uploaded_at: new Date().toISOString(),
        validation_status: "pending",
        notes: null,
      };

      const existing = db.evidence.get(taskId) || [];
      existing.push(newEvidence);
      db.evidence.set(taskId, existing);
      if (task.evidence) {
        task.evidence.push(newEvidence);
      } else {
        task.evidence = [newEvidence];
      }

      return jsonResponse(newEvidence, 201);
    }

    // GET /roadmaps/tasks/:id/evidence
    const listEvidenceMatch = pathname.match(/^\/roadmaps\/tasks\/([^/]+)\/evidence$/);
    if (listEvidenceMatch && method === "GET") {
      const taskId = listEvidenceMatch[1];
      const task = db.tasks.get(taskId);
      if (!task || task.tenant_id !== tenantId) {
        return errorResponse(404, "Tarea no encontrada", "TASK_NOT_FOUND");
      }
      const list = db.evidence.get(taskId) || [];
      return jsonResponse(list);
    }

    // PATCH /roadmaps/tasks/:id/evidence/:evidence_id
    const valEvidenceMatch = pathname.match(/^\/roadmaps\/tasks\/([^/]+)\/evidence\/([^/]+)$/);
    if (valEvidenceMatch && method === "PATCH") {
      const allowed = ["coordinador", "dpo", "implementador"];
      if (!allowed.includes(role)) {
        return errorResponse(403, `Rol ${role} no autorizado para validar evidencia`, "FORBIDDEN");
      }
      const taskId = valEvidenceMatch[1];
      const evidenceId = valEvidenceMatch[2];
      const list = db.evidence.get(taskId) || [];
      const item = list.find((e) => e.id === evidenceId);
      if (!item) {
        return errorResponse(404, "Evidencia no encontrada", "EVIDENCE_NOT_FOUND");
      }

      // Regla Cuatro Ojos: quien subió no puede validar
      if (item.uploaded_by === userId) {
        return errorResponse(
          409,
          "Violación de la regla de cuatro ojos: quien sube la evidencia no puede validarla",
          "FOUR_EYES_VIOLATION",
          "Solicite a otro usuario calificado (DPO o coordinador) validar este entregable"
        );
      }

      const valReq = bodyJson as unknown as TaskEvidenceValidationRequest;
      item.validation_status = valReq.validation_status;
      item.notes = valReq.notes || null;
      item.validated_by = userId;
      item.validated_at = new Date().toISOString();

      return jsonResponse(item);
    }

    // ========================================================================
    // Enrutamiento de Organización
    // ========================================================================

    // GET /organizacion/me/roles
    if (pathname === "/organizacion/me/roles" && method === "GET") {
      const assignments = Array.from(db.roleAssignments.values()).filter(
        (a) => a.user_id === userId && a.tenant_id === tenantId
      );
      const rolesContext: UserRoleContext[] = assignments.map((a) => ({
        role: a.role,
        area_id: a.area_id ?? null,
        area_nombre: a.area_id ? db.areas.get(a.area_id)?.nombre ?? null : null,
        valid_to: a.valid_to ?? null,
      }));
      return jsonResponse(rolesContext);
    }

    // GET /organizacion/usuarios
    if (pathname === "/organizacion/usuarios" && method === "GET") {
      return jsonResponse(Array.from(db.users.values()));
    }

    // POST /organizacion/usuarios
    if (pathname === "/organizacion/usuarios" && method === "POST") {
      const uReq = bodyJson as unknown as UserCreate;
      const newUser: UserItem = {
        id: `user-${Date.now()}`,
        email: uReq.email,
        nombre: uReq.nombre,
      };
      db.users.set(newUser.id, newUser);
      return jsonResponse(newUser, 201);
    }

    // GET /organizacion/areas
    if (pathname === "/organizacion/areas" && method === "GET") {
      return jsonResponse(Array.from(db.areas.values()));
    }

    // POST /organizacion/areas
    if (pathname === "/organizacion/areas" && method === "POST") {
      const aReq = bodyJson as unknown as AreaCreate;
      const newArea: AreaItem = {
        id: `area-${Date.now()}`,
        tenant_id: tenantId,
        nombre: aReq.nombre,
        codigo: aReq.codigo ?? null,
        parent_area_id: aReq.parent_area_id ?? null,
        created_at: new Date().toISOString(),
      };
      db.areas.set(newArea.id, newArea);
      return jsonResponse(newArea, 201);
    }

    // PATCH /organizacion/areas/:id
    const areaPatchMatch = pathname.match(/^\/organizacion\/areas\/([^/]+)$/);
    if (areaPatchMatch && method === "PATCH") {
      const areaId = areaPatchMatch[1];
      const area = db.areas.get(areaId);
      if (!area || area.tenant_id !== tenantId) {
        return errorResponse(404, "Área no encontrada", "AREA_NOT_FOUND");
      }
      const aUpdate = bodyJson as unknown as AreaUpdate;
      if (aUpdate.nombre) area.nombre = aUpdate.nombre;
      if (aUpdate.codigo !== undefined) area.codigo = aUpdate.codigo;
      if (aUpdate.responsable_user_id !== undefined) area.responsable_user_id = aUpdate.responsable_user_id;
      return jsonResponse(area);
    }

    // GET /organizacion/roles
    if (pathname === "/organizacion/roles" && method === "GET") {
      return jsonResponse(Array.from(db.roleAssignments.values()));
    }

    // POST /organizacion/roles
    if (pathname === "/organizacion/roles" && method === "POST") {
      const rReq = bodyJson as unknown as RoleGrant;
      const newGrant: RoleGrantItem = {
        id: `grant-${Date.now()}`,
        user_id: rReq.user_id,
        tenant_id: tenantId,
        role: rReq.role,
        area_id: rReq.area_id ?? null,
        valid_to: rReq.valid_to ?? null,
        valid_from: new Date().toISOString(),
      };
      db.roleAssignments.set(newGrant.id, newGrant);
      return jsonResponse(newGrant, 201);
    }

    // DELETE /organizacion/roles/:id
    const roleDelMatch = pathname.match(/^\/organizacion\/roles\/([^/]+)$/);
    if (roleDelMatch && method === "DELETE") {
      const grantId = roleDelMatch[1];
      db.roleAssignments.delete(grantId);
      return new Response(null, { status: 204 });
    }

    // Endpoint no mapeado
    return errorResponse(404, `Ruta no encontrada en mock: ${method} ${pathname}`, "NOT_FOUND");
  };
}
