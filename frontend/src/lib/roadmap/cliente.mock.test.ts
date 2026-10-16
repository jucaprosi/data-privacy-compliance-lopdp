import test from "node:test";
import assert from "node:assert/strict";

import { createMockFetch, createInitialMockDatabase } from "./mockServer";
import {
  roadmapApi,
  organizacionApi,
  setIdentitySession,
  getIdentityHeaders,
  requestJson,
} from "./cliente";
import { ApiError } from "../../types/roadmap";

test("Aislamiento de cabeceras de identidad", () => {
  setIdentitySession({
    userId: "u-test-99",
    tenantId: "t-test-corp",
    role: "implementador",
  });

  const headers = getIdentityHeaders();
  assert.equal(headers["X-User-ID"], "u-test-99");
  assert.equal(headers["X-Tenant-ID"], "t-test-corp");
  assert.equal(headers["X-Role"], "implementador");
});

test("Manejo estructurado de errores con ApiError (detail, code, action_required)", async () => {
  const customFetch: typeof fetch = async () => {
    return new Response(
      JSON.stringify({
        detail: "Violación de regla de cuatro ojos",
        code: "FOUR_EYES_VIOLATION",
        action_required: "Solicite a otro usuario validar",
      }),
      {
        status: 409,
        headers: { "Content-Type": "application/json" },
      }
    );
  };

  await assert.rejects(
    async () => {
      await requestJson("/test-error", { customFetch });
    },
    (err: unknown) => {
      assert(err instanceof ApiError);
      assert.equal(err.status, 409);
      assert.equal(err.message, "Violación de regla de cuatro ojos");
      assert.equal(err.code, "FOUR_EYES_VIOLATION");
      assert.equal(err.action_required, "Solicite a otro usuario validar");
      return true;
    }
  );
});

test("Prueba de integración: roadmapApi contra MockServer", async () => {
  const db = createInitialMockDatabase();
  const mockFetch = createMockFetch(db);
  const options = { customFetch: mockFetch };

  setIdentitySession({
    userId: "user-impl-01",
    tenantId: "tenant-corp-demo",
    role: "implementador",
  });

  // 1. Consultar Roadmap
  const rmRes = await roadmapApi.getRoadmap("rm-demo-001", options);
  assert.equal(rmRes.roadmap.id, "rm-demo-001");
  assert.equal(rmRes.waves.length, 2);
  assert.equal(rmRes.waves[0].tasks?.length, 2);

  // 2. Consultar KPIs
  const kpis = await roadmapApi.getKpis("rm-demo-001", options);
  assert.equal(kpis.total, 3);
  assert.equal(kpis.completadas, 1);
  assert.equal(kpis.criticas, 1);

  // 3. Actualizar estado de una tarea
  const updateRes = await roadmapApi.updateTaskStatus("task-002", "completada", options);
  assert.equal(updateRes.status, "completada");
  const taskUpdated = db.tasks.get("task-002");
  assert.equal(taskUpdated?.status, "completada");

  // 4. Actualizar detalles de tarea
  await roadmapApi.updateTaskDetails("task-002", { title: "Nuevo Título RAT" }, options);
  assert.equal(taskUpdated?.title, "Nuevo Título RAT");

  // 5. Asignar tarea: la matriz del PRD §5.2 la reserva al encargado; el implementador no puede
  await assert.rejects(
    roadmapApi.assignTask("task-002", "user-resp-01", options),
    (err: unknown) => err instanceof ApiError && err.status === 403,
  );
  assert.notEqual(taskUpdated?.owner, "user-resp-01");
  await roadmapApi.assignTask("task-002", "user-resp-01", { ...options, headers: { "X-Role": "encargado" } });
  assert.equal(taskUpdated?.owner, "user-resp-01");

  // 6. Consultar auditoría
  const audit = await roadmapApi.getAuditLog("rm-demo-001", { limit: 10 }, options);
  assert(audit.total >= 4);
  assert(audit.items.length >= 4);

  // 7. Generar roadmap
  const genRes = await roadmapApi.generate(
    {
      plazo_meses: 6,
      presupuesto: 20000,
      moneda: "USD",
      equipo: ["DPO"],
      dpo: "dpo-corp-01",
    },
    {},
    options
  );
  assert(genRes.job_id.startsWith("job-"));

  // 8. Consultar estado del job
  const job = await roadmapApi.getJob(genRes.job_id, options);
  assert.equal(job.status, "completed");
  assert(job.roadmap_id);
});

test("Prueba de integración: Evidencias y Regla de Cuatro Ojos contra MockServer", async () => {
  const db = createInitialMockDatabase();
  const mockFetch = createMockFetch(db);
  const options = { customFetch: mockFetch };

  // Subir evidencia como responsable_area
  setIdentitySession({
    userId: "user-resp-01",
    tenantId: "tenant-corp-demo",
    role: "responsable_area",
  });

  const uploadUrlInfo = await roadmapApi.getEvidenceUploadUrl(
    "task-002",
    { filename: "politica.pdf", mime_type: "application/pdf", file_size: 2048 },
    options
  );
  assert(uploadUrlInfo.upload_url.includes("mock-r2.local"));
  assert(uploadUrlInfo.r2_key.includes("politica.pdf"));

  const registered = await roadmapApi.registerEvidence(
    "task-002",
    { r2_key: uploadUrlInfo.r2_key, mime_type: "application/pdf", file_size: 2048 },
    options
  );
  assert.equal(registered.validation_status, "pending");
  assert.equal(registered.uploaded_by, "user-resp-01");

  // Validación: Cuatro ojos - Quien subió (user-resp-01) intenta validar como implementador -> debe fallar con 409
  setIdentitySession({
    userId: "user-resp-01",
    tenantId: "tenant-corp-demo",
    role: "implementador",
  });

  await assert.rejects(
    async () => {
      await roadmapApi.validateEvidence(
        "task-002",
        registered.id,
        { validation_status: "approved", notes: "Aprobación propia" },
        options
      );
    },
    (err: unknown) => {
      assert(err instanceof ApiError);
      assert.equal(err.status, 409);
      assert.equal(err.code, "FOUR_EYES_VIOLATION");
      assert(err.action_required);
      return true;
    }
  );

  // Validación válida por parte del DPO (diferente usuario)
  setIdentitySession({
    userId: "dpo-corp-01",
    tenantId: "tenant-corp-demo",
    role: "dpo",
  });

  const validated = await roadmapApi.validateEvidence(
    "task-002",
    registered.id,
    { validation_status: "approved", notes: "Aprobado por DPO formal" },
    options
  );
  assert.equal(validated.validation_status, "approved");
  assert.equal(validated.validated_by, "dpo-corp-01");
});

test("Prueba de integración: organizacionApi contra MockServer", async () => {
  const db = createInitialMockDatabase();
  const mockFetch = createMockFetch(db);
  const options = { customFetch: mockFetch };

  setIdentitySession({
    userId: "user-admin-01",
    tenantId: "tenant-corp-demo",
    role: "admin_organizacion",
  });

  // 1. Roles del usuario actual
  const myRoles = await organizacionApi.getMyRoles(options);
  assert.equal(myRoles.length, 1);
  assert.equal(myRoles[0].role, "admin_organizacion");

  // 2. Áreas
  const areas = await organizacionApi.listAreas(options);
  assert.equal(areas.length, 2);

  const newArea = await organizacionApi.createArea({ nombre: "Auditoría Interna", codigo: "AUD-01" }, options);
  assert.equal(newArea.nombre, "Auditoría Interna");

  // 3. Usuarios
  const users = await organizacionApi.listUsers(options);
  assert.equal(users.length, 4);

  const newUser = await organizacionApi.createUser({ email: "auditor@corp.ec", nombre: "Auditor Interno" }, options);
  assert.equal(newUser.email, "auditor@corp.ec");

  // 4. Asignación de roles
  const grant = await organizacionApi.grantRole(
    { user_id: newUser.id, role: "encargado", area_id: newArea.id },
    options
  );
  assert.equal(grant.role, "encargado");
  assert.equal(grant.user_id, newUser.id);
});
