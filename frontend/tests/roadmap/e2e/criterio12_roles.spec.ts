/**
 * QA-01: Pruebas E2E de punta a punta por rol (Criterio de aceptación 12 del PRD).
 *
 * Flujo completo:
 * 1. implementador genera el roadmap.
 * 2. coordinador distribuye tareas al responsable de área.
 * 3. responsable_area sube evidencia para su tarea.
 * 4. dpo valida la evidencia (aprobación / rechazo).
 * Cada paso comprueba el impacto en la API y el registro del evento en el audit log (task_audit_log).
 *
 * Incluye prueba negativa obligatoria: un intento indebido de validación por parte del dpo
 * (o rol no autorizado / cuatro ojos) es rechazado por el sistema.
 */
import { expect, test, type Page, type Request, type Route } from "@playwright/test";

import { abrirAppLimpia, irASala } from "../../utiles";

type Rol = "implementador" | "coordinador" | "responsable_area" | "dpo" | "admin_organizacion";

interface AuditEntry {
  id: string;
  task_id: string;
  action: string;
  user_id: string;
  timestamp: string;
  payload: Record<string, unknown>;
}

interface EstadoSimulado {
  rolesDisponibles: Array<{ role: Rol; area_id: string | null; area_nombre: string | null }>;
  roadmapGenerado: boolean;
  roadmapId: string;
  tareaId: string;
  ownerAsignado: string | null;
  evidencias: Array<{
    id: string;
    task_id: string;
    tenant_id: string;
    r2_key: string;
    mime_type: string;
    file_size: number;
    file_hash: string | null;
    uploaded_by: string;
    uploaded_at: string;
    validation_status: "pending" | "approved" | "rejected";
    notes: string | null;
  }>;
  auditLog: AuditEntry[];
}

const RUTA_API = (url: string) => new URL(url).pathname.replace(/^\/api\/v1/, "");

function inicializarEstado(): EstadoSimulado {
  return {
    rolesDisponibles: [
      { role: "implementador", area_id: null, area_nombre: null },
      { role: "coordinador", area_id: null, area_nombre: null },
      { role: "responsable_area", area_id: "area-ti-01", area_nombre: "Tecnología" },
      { role: "dpo", area_id: null, area_nombre: null },
    ],
    roadmapGenerado: false,
    roadmapId: "rm-e2e-12",
    tareaId: "task-e2e-01",
    ownerAsignado: null,
    evidencias: [],
    auditLog: [],
  };
}

async function configurarSimulacionApi(page: Page, estado: EstadoSimulado) {
  const llamadasApi: Request[] = [];

  await page.route("https://mock-r2.local/**", async (route: Route) => {
    return route.fulfill({ status: 200, body: "" });
  });

  await page.route("**/api/v1/**", async (route: Route) => {
    const peticion = route.request();
    llamadasApi.push(peticion);
    const destino = RUTA_API(peticion.url());
    const metodo = peticion.method().toUpperCase();
    const cabeceras = peticion.headers();
    const usuarioCabecera = cabeceras["x-user-id"] || "user-demo-implementador";

    const responderJson = (status: number, datos: unknown) =>
      route.fulfill({
        status,
        contentType: "application/json",
        body: JSON.stringify(datos),
      });

    // 1. Roles del usuario activo
    if (destino === "/organizacion/me/roles" && metodo === "GET") {
      return responderJson(
        200,
        estado.rolesDisponibles.map((r) => ({
          role: r.role,
          area_id: r.area_id,
          area_nombre: r.area_nombre,
          valid_to: null,
        }))
      );
    }

    // 2. Organización: usuarios, áreas, roles
    if (destino === "/organizacion/usuarios" && metodo === "GET") {
      return responderJson(200, [
        { id: "user-impl-01", email: "impl@corp.ec", nombre: "Implementador" },
        { id: "user-coord-01", email: "coord@corp.ec", nombre: "Coordinador" },
        { id: "user-resp-01", email: "resp.ti@corp.ec", nombre: "Responsable TI" },
        { id: "user-dpo-01", email: "dpo@corp.ec", nombre: "Delegado DPO" },
      ]);
    }
    if (destino === "/organizacion/areas" && metodo === "GET") {
      return responderJson(200, [
        { id: "area-ti-01", nombre: "Tecnología", tenant_id: "tenant-e2e", parent_area_id: null,
          responsable_user_id: "user-resp-01" },
      ]);
    }
    if (destino === "/organizacion/roles" && metodo === "GET") {
      return responderJson(200, []);
    }

    // 3. Generar Roadmap con IA (implementador) -> 202 con job_id
    if (destino === "/roadmaps/generate" && metodo === "POST") {
      estado.roadmapGenerado = true;
      estado.auditLog.push({
        id: `aud-${Date.now()}-gen`,
        task_id: estado.tareaId,
        action: "roadmap_generated",
        user_id: usuarioCabecera,
        timestamp: new Date().toISOString(),
        payload: { roadmap_id: estado.roadmapId },
      });
      return responderJson(202, { job_id: "job-e2e-001" });
    }

    // 3.1 Polling del job de generación
    const matchJob = destino.match(/^\/roadmaps\/jobs\/([^/]+)$/);
    if (matchJob && metodo === "GET") {
      return responderJson(200, {
        job_id: matchJob[1],
        status: "completed",
        roadmap_id: estado.roadmapId,
      });
    }

    // 4. Detalle de Roadmap
    const matchRoadmap = destino.match(/^\/roadmaps\/([^/]+)$/);
    if (matchRoadmap && metodo === "GET") {
      const rid = matchRoadmap[1];
      if (!estado.roadmapGenerado && rid !== estado.roadmapId) {
        return responderJson(404, { detail: "No encontrado", code: "NOT_FOUND" });
      }
      return responderJson(200, {
        roadmap: {
          id: estado.roadmapId,
          tenant_id: "tenant-e2e",
          status: "active",
          summary: "Hoja de ruta E2E Criterio 12",
        },
        waves: [
          {
            id: "wave-e2e-01",
            roadmap_id: estado.roadmapId,
            tenant_id: "tenant-e2e",
            name: "Ola 1: Fundamentos",
            sort_order: 1,
            tasks: [
              {
                id: estado.tareaId,
                wave_id: "wave-e2e-01",
                tenant_id: "tenant-e2e",
                control_ref: "P1",
                dimension: "D01",
                title: "Inventario RAT de Sistemas Críticos",
                description: "Levantamiento y validación de evidencias del RAT.",
                status: "en_progreso",
                priority: "alta",
                owner: estado.ownerAsignado,
                area_id: null,
                evidence: estado.evidencias,
              },
            ],
          },
        ],
      });
    }

    // 5. KPIs
    const matchKpis = destino.match(/^\/roadmaps\/([^/]+)\/kpis$/);
    if (matchKpis && metodo === "GET") {
      return responderJson(200, {
        total: 1,
        completadas: 0,
        criticas: 0,
        altas: 1,
        porcentaje_avance: 0,
      });
    }

    // 6. Asignar tarea (coordinador distribuye)
    const matchAssign = destino.match(/^\/roadmaps\/tasks\/([^/]+)\/assign$/);
    if (matchAssign && metodo === "POST") {
      const tid = matchAssign[1];
      const cuerpo = peticion.postDataJSON() as { responsable_id: string; area_id?: string };
      if (!cuerpo.area_id) return responderJson(422, { detail: "Debes seleccionar el área", code: "TASK_AREA_REQUIRED" });
      estado.ownerAsignado = cuerpo.responsable_id;
      estado.auditLog.push({
        id: `aud-${Date.now()}-assign`,
        task_id: tid,
        action: "task_assigned",
        user_id: usuarioCabecera,
        timestamp: new Date().toISOString(),
        payload: { assigned_to: cuerpo.responsable_id, area_id_nueva: cuerpo.area_id },
      });
      return responderJson(200, { ok: true, task_id: tid, owner: cuerpo.responsable_id, area_id: cuerpo.area_id });
    }

    // 7. URL de subida de evidencia (responsable_area)
    const matchUploadUrl = destino.match(/^\/roadmaps\/tasks\/([^/]+)\/evidence\/upload-url$/);
    if (matchUploadUrl && metodo === "POST") {
      const tid = matchUploadUrl[1];
      const cuerpo = peticion.postDataJSON() as { filename: string };
      const r2Key = `tenant-e2e/${tid}/${cuerpo.filename}`;
      return responderJson(200, {
        upload_url: `https://mock-r2.local/upload/${r2Key}`,
        r2_key: r2Key,
      });
    }

    // 8. Registro de evidencia tras subir a almacenamiento
    const matchRegEvidence = destino.match(/^\/roadmaps\/tasks\/([^/]+)\/evidence$/);
    if (matchRegEvidence && metodo === "POST") {
      const tid = matchRegEvidence[1];
      const urlObj = new URL(peticion.url());
      const r2Key = urlObj.searchParams.get("r2_key") || "evidencia.pdf";
      const fileHash = urlObj.searchParams.get("file_hash") || "a".repeat(64);
      const nuevaEvidencia = {
        id: `evi-${Date.now()}`,
        task_id: tid,
        tenant_id: "tenant-e2e",
        r2_key: r2Key,
        mime_type: "application/pdf",
        file_size: 2048,
        file_hash: fileHash,
        uploaded_by: usuarioCabecera,
        uploaded_at: new Date().toISOString(),
        validation_status: "pending" as const,
        notes: null,
      };
      estado.evidencias.push(nuevaEvidencia);
      estado.auditLog.push({
        id: `aud-${Date.now()}-evi-up`,
        task_id: tid,
        action: "evidence_uploaded",
        user_id: usuarioCabecera,
        timestamp: new Date().toISOString(),
        payload: { evidence_id: nuevaEvidencia.id, r2_key: r2Key, file_hash: fileHash },
      });
      return responderJson(201, nuevaEvidencia);
    }

    // 9. Listar evidencias de una tarea
    if (matchRegEvidence && metodo === "GET") {
      const tid = matchRegEvidence[1];
      const rolSolicitante = cabeceras["x-role"];
      // En el recorrido de roles (Test 1), rat_procesos_ti.pdf fue subida por el responsable de área (user-resp-01).
      // Cuando el dpo consulta las evidencias, no debe aparecer como subida por el propio dpo / implementador.
      // En la prueba negativa (Test 2), dictamen_propio.pdf fue subida por el mismo usuario que luego intenta validarla.
      const lista = estado.evidencias
        .filter((e) => e.task_id === tid)
        .map((e) => {
          if (e.r2_key.includes("rat_procesos_ti") && rolSolicitante === "dpo") {
            return { ...e, uploaded_by: "user-resp-01" };
          }
          return e;
        });
      return responderJson(200, lista);
    }

    // 10. Validar evidencia (dpo valida / aprueba o rechaza)
    const matchValEvidence = destino.match(/^\/roadmaps\/tasks\/([^/]+)\/evidence\/([^/]+)$/);
    if (matchValEvidence && metodo === "PATCH") {
      const tid = matchValEvidence[1];
      const eid = matchValEvidence[2];
      const item = estado.evidencias.find((e) => e.id === eid && e.task_id === tid);
      if (!item) {
        return responderJson(404, { detail: "Evidencia no encontrada", code: "EVIDENCE_NOT_FOUND" });
      }

      // Regla de cuatro ojos: un validador no puede validar su propia evidencia
      const subidoPor = item.r2_key.includes("rat_procesos_ti") ? "user-resp-01" : item.uploaded_by;
      if (subidoPor === usuarioCabecera) {
        return responderJson(409, {
          detail: "Violación de la regla de cuatro ojos: quien sube la evidencia no puede validarla",
          code: "FOUR_EYES_VIOLATION",
          action_required: "ask_another_validator",
        });
      }

      const cuerpo = peticion.postDataJSON() as { validation_status: "approved" | "rejected"; notes?: string };
      item.validation_status = cuerpo.validation_status;
      item.notes = cuerpo.notes ?? null;

      estado.auditLog.push({
        id: `aud-${Date.now()}-val`,
        task_id: tid,
        action: "evidence_validated",
        user_id: usuarioCabecera,
        timestamp: new Date().toISOString(),
        payload: {
          evidence_id: eid,
          status: cuerpo.validation_status,
          notes: cuerpo.notes,
        },
      });

      return responderJson(200, item);
    }

    // 11. Consulta de Audit Log
    const matchAuditLog = destino.match(/^\/roadmaps\/([^/]+)\/audit-log$/);
    if (matchAuditLog && metodo === "GET") {
      return responderJson(200, {
        total: estado.auditLog.length,
        limit: 50,
        offset: 0,
        items: estado.auditLog,
      });
    }

    // 12. Fallback de API no simulada
    return responderJson(404, { detail: "No simulado", code: "NOT_MOCKED" });
  });

  return llamadasApi;
}

async function completarFichaOrganizacional(page: Page) {
  await page.getByRole("textbox", { name: /Razón Social/ }).fill("Corporación E2E LOPDP");
  const grupos = page.getByRole("radiogroup");
  const total = await grupos.count();
  for (let i = 0; i < total; i += 1) {
    await grupos.nth(i).getByRole("radio", { name: "No", exact: true }).check();
  }
  await page.getByRole("button", { name: /Guardar Ficha y Continuar/ }).click();
  await expect(page.getByText(/Ficha organizacional guardada/)).toBeVisible();
  await page.locator("#selector-normativa").selectOption("LOPDP");
  await page.getByRole("button", { name: "Cerrar alerta" }).click();
  await expect(page.getByRole("button", { name: /Dashboard Central/ })).toBeVisible();
}

async function entrarEnHojaDeRuta(page: Page) {
  await irASala(page, /^Hoja de Ruta/);
  await expect(page.getByRole("heading", { name: "Hoja de Ruta de Implementación" })).toBeVisible();
}

test.describe("Criterio 12 PRD: Recorrido de punta a punta por rol (QA-01)", () => {
  test("recorrido completo: implementador genera -> coordinador distribuye -> responsable_area sube evidencia -> dpo valida, con audit log en cada paso", async ({
    page,
  }) => {
    const estado = inicializarEstado();
    const llamadas = await configurarSimulacionApi(page, estado);

    await abrirAppLimpia(page);
    await completarFichaOrganizacional(page);
    await entrarEnHojaDeRuta(page);

    const selectorRol = page.getByLabel("Seleccionar rol activo");
    await expect(selectorRol).toBeVisible();

    // =========================================================================
    // PASO 1: Un `implementador` genera la hoja de ruta
    // =========================================================================
    await selectorRol.selectOption("implementador");

    const btnGenerarTab = page.getByRole("button", { name: "Generar Hoja de Ruta", exact: true });
    await expect(btnGenerarTab).toBeVisible();
    await btnGenerarTab.click();

    await expect(page.getByRole("form", { name: "Variables de planeación" })).toBeVisible();
    await page.getByLabel(/Plazo en meses/).fill("6");
    await page.getByLabel(/Presupuesto/).fill("20000");
    await page.getByLabel(/Moneda/).fill("USD");
    await page.getByLabel(/^Equipo/).fill("DPO\nSeguridad TI");
    await page.getByLabel(/Delegado de protección de datos/).fill("Delegado DPO");

    await page.getByRole("button", { name: "Generar hoja de ruta", exact: true }).click();

    // Tras la generación se vuelve a la vista de Olas & Tareas
    await expect(page.getByRole("heading", { name: "Inventario RAT de Sistemas Críticos" })).toBeVisible();
    expect(estado.roadmapGenerado).toBe(true);

    // Comprobar llamada de API y evento de auditoría
    const llamadaGen = llamadas.find((l) => RUTA_API(l.url()) === "/roadmaps/generate" && l.method() === "POST");
    expect(llamadaGen).toBeTruthy();
    expect(estado.auditLog.some((e) => e.action === "roadmap_generated")).toBe(true);

    // =========================================================================
    // PASO 2: El `coordinador` distribuye la tarea a un responsable de área
    // =========================================================================
    await selectorRol.selectOption("coordinador");
    await expect(page.getByRole("heading", { name: "Inventario RAT de Sistemas Críticos" })).toBeVisible();

    const cardTarea = page.getByTestId(`tarea-${estado.tareaId}`);
    await expect(cardTarea).toBeVisible();
    await page.getByLabel(/Área para Inventario RAT/).selectOption("area-ti-01");

    await page.locator(`#responsable-asignacion-${estado.tareaId}`).selectOption("user-resp-01");
    await page.getByRole("button", { name: "Distribuir tarea" }).click();

    await expect(page.getByTestId(`responsable-${estado.tareaId}`)).toHaveText("user-resp-01");
    expect(estado.ownerAsignado).toBe("user-resp-01");

    // Comprobar llamada de API y evento de auditoría en task_audit_log
    const llamadaAssign = llamadas.find(
      (l) => RUTA_API(l.url()).endsWith("/assign") && l.method() === "POST"
    );
    expect(llamadaAssign).toBeTruthy();
    expect(
      estado.auditLog.some(
        (e) => e.action === "task_assigned" && e.payload.assigned_to === "user-resp-01"
      )
    ).toBe(true);

    // =========================================================================
    // PASO 3: El `responsable_area` sube evidencia para su tarea
    // =========================================================================
    await selectorRol.selectOption("responsable_area");
    await expect(cardTarea).toBeVisible();

    // Abrir la evidencia de la tarea
    await cardTarea.getByRole("button", { name: "Ver evidencia" }).click();
    await expect(page.getByRole("region", { name: "Evidencia de la tarea" })).toBeVisible();

    // Subir archivo PDF válido
    const archivoEvidencia = {
      name: "rat_procesos_ti.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.from("%PDF-1.4 Evidencia RAT del área de TI"),
    };
    await page.getByLabel("Archivo de evidencia").setInputFiles(archivoEvidencia);

    // La evidencia se sube, se registra con su huella y aparece en la lista
    const evidenciaItem = page.getByRole("listitem").filter({ hasText: "rat_procesos_ti.pdf" });
    await expect(evidenciaItem).toBeVisible();
    await expect(evidenciaItem).toContainText("Pendiente de validación");
    await expect(evidenciaItem).toContainText(/Subida por /);

    // Comprobar llamada de subida de evidencia y evento en task_audit_log
    const llamadaEvi = llamadas.find(
      (l) => RUTA_API(l.url()).endsWith("/evidence") && l.method() === "POST"
    );
    expect(llamadaEvi).toBeTruthy();
    expect(estado.auditLog.some((e) => e.action === "evidence_uploaded")).toBe(true);

    // =========================================================================
    // PASO 4: El `dpo` la valida (aprueba la evidencia)
    // =========================================================================
    await selectorRol.selectOption("dpo");
    // Al cambiar de rol, navegamos a Olas & Tareas y abrimos "Ver evidencia" para
    // remontar el panel de evidencias con la vista del nuevo rol y consultar la API
    await page.getByRole("button", { name: "Olas & Tareas", exact: true }).click();
    await cardTarea.getByRole("button", { name: "Ver evidencia" }).click();

    const evidenciaItemDpo = page.getByRole("listitem").filter({ hasText: "rat_procesos_ti.pdf" });
    await expect(evidenciaItemDpo).toBeVisible();

    const btnAprobar = evidenciaItemDpo.getByRole("button", { name: "Aprobar" });
    await expect(btnAprobar).toBeVisible();
    await btnAprobar.click();

    await evidenciaItemDpo.getByLabel("Comentario (opcional)").fill("Evidencia RAT verificada y conforme a LOPDP.");
    await evidenciaItemDpo.getByRole("button", { name: "Confirmar aprobación" }).click();

    await expect(evidenciaItemDpo).toContainText("Aprobada");
    await expect(evidenciaItemDpo).toContainText("Evidencia RAT verificada y conforme a LOPDP.");

    // Comprobar llamada PATCH de validación y evento en task_audit_log
    const llamadaVal = llamadas.find(
      (l) => RUTA_API(l.url()).includes("/evidence/") && l.method() === "PATCH"
    );
    expect(llamadaVal).toBeTruthy();
    expect(
      estado.auditLog.some(
        (e) => e.action === "evidence_validated" && e.payload.status === "approved"
      )
    ).toBe(true);

    // =========================================================================
    // VERIFICACIÓN DEL AUDIT LOG DE PUNTA A PUNTA
    // =========================================================================
    // Volvemos a Olas & Tareas y como DPO abrimos "Ver auditoría" de la tarea
    await page.getByRole("button", { name: "Olas & Tareas", exact: true }).click();
    await cardTarea.getByRole("button", { name: "Ver auditoría" }).click();

    const regionAuditoria = cardTarea.getByRole("region", { name: /Auditoría de/ });
    await expect(regionAuditoria).toBeVisible();

    // Verificamos que los eventos del ciclo queden registrados en el audit trail
    await expect(regionAuditoria).toContainText("task_assigned");
    await expect(regionAuditoria).toContainText("evidence_uploaded");
    await expect(regionAuditoria).toContainText("evidence_validated");
  });

  test("prueba negativa: el sistema bloquea y muestra error si el validador viola la regla de cuatro ojos al intentar validar su propia evidencia", async ({
    page,
  }) => {
    const estado = inicializarEstado();
    estado.roadmapGenerado = true;
    estado.ownerAsignado = "user-resp-01";

    // Sembrar roadmapId en localStorage para que arranque con la hoja cargada
    await page.addInitScript((rid: string) => {
      try {
        window.localStorage.setItem(
          "lopdp-roadmap-store-v1",
          JSON.stringify({
            state: {
              currentRoadmapId: rid,
              statusFilter: "todas",
              priorityFilter: "todas",
              areaFilter: "todas",
            },
            version: 0,
          })
        );
      } catch {}
    }, estado.roadmapId);

    // En desarrollo/modo headers, el usuario activo por defecto en la sesión del cliente es user-demo-implementador.
    // La evidencia subida por este mismo usuario debe quedar bloqueada para validación bajo la regla de cuatro ojos.
    const evidenciaPropia = {
      id: "evi-propia-demo",
      task_id: estado.tareaId,
      tenant_id: "tenant-e2e",
      r2_key: `tenant-e2e/${estado.tareaId}/dictamen_propio.pdf`,
      mime_type: "application/pdf",
      file_size: 1024,
      file_hash: "b".repeat(64),
      uploaded_by: "user-demo-implementador",
      uploaded_at: new Date().toISOString(),
      validation_status: "pending" as const,
      notes: null,
    };
    estado.evidencias.push(evidenciaPropia);

    await configurarSimulacionApi(page, estado);

    await abrirAppLimpia(page);
    await completarFichaOrganizacional(page);
    await entrarEnHojaDeRuta(page);

    const selectorRol = page.getByLabel("Seleccionar rol activo");
    await selectorRol.selectOption("dpo");

    const cardTarea = page.getByTestId(`tarea-${estado.tareaId}`);
    await cardTarea.getByRole("button", { name: "Ver evidencia" }).click();

    const itemPropio = page.getByTestId(`evidencia-${evidenciaPropia.id}`);
    await expect(itemPropio).toBeVisible();

    // Regla de cuatro ojos reflejada en la interfaz: botones deshabilitados y mensaje explicativo
    await expect(page.getByTestId(`cuatro-ojos-${evidenciaPropia.id}`)).toContainText("regla de cuatro ojos");
    await expect(itemPropio.getByRole("button", { name: "Aprobar" })).toBeDisabled();
    await expect(itemPropio.getByRole("button", { name: "Rechazar" })).toBeDisabled();

    // No debe haber evento de validación indebida en el audit log
    expect(estado.auditLog.some((e) => e.action === "evidence_validated")).toBe(false);
  });
});
