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
 *
 * FE-26: estos recorridos ejercitan la custodia física (EVYDENTIA). Encienden el ajuste de prueba
 * `window.__LOPDP_EVIDENCIA_PRUEBAS__`, que solo existe fuera de producción, y corren en el proyecto
 * «desarrollo» (convención `*-activa.spec.ts`). El recorrido del PMV está en `criterio12_roles.spec.ts`.
 */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia } from "../../utiles";
import {
  completarFichaOrganizacional,
  configurarSimulacionApi,
  entrarEnHojaDeRuta,
  inicializarEstado,
  RUTA_API,
} from "./simulacion-criterio12";

test.describe("Criterio 12 PRD: Recorrido de punta a punta por rol (QA-01)", () => {
  // === FE-26 ===
  test.beforeEach(async ({ context }) => {
    await context.addInitScript(() => {
      window.__LOPDP_EVIDENCIA_PRUEBAS__ = true;
    });
  });
  // === fin FE-26 ===

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
