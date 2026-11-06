/**
 * QA-01: recorrido de punta a punta por rol (criterio de aceptación 12 del PRD) en el PMV.
 *
 * 1. implementador genera la hoja de ruta.
 * 2. coordinador distribuye la tarea al responsable de área.
 * 3. responsable_area y dpo ven la tarea, sin custodia física de evidencias.
 * Cada paso comprueba el impacto en la API y el evento en el audit log (task_audit_log).
 *
 * FE-26: el PMV no sube archivos de evidencia (la evidencia del diagnóstico es declarada). La subida
 * por responsable_area, la validación del dpo y la regla de cuatro ojos ejercitan la custodia física
 * de EVYDENTIA y están en `criterio12_roles-activa.spec.ts`.
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

test.describe("Criterio 12 PRD: Recorrido de punta a punta por rol en el PMV (QA-01, FE-26)", () => {
  test("implementador genera -> coordinador distribuye -> responsable y dpo sin custodia física, con audit log", async ({
    page,
  }) => {
    const estado = inicializarEstado();
    const llamadas = await configurarSimulacionApi(page, estado);

    await abrirAppLimpia(page);
    await completarFichaOrganizacional(page);
    await entrarEnHojaDeRuta(page);

    const selectorRol = page.getByLabel("Seleccionar rol activo");
    await expect(selectorRol).toBeVisible();

    // PASO 1: un `implementador` genera la hoja de ruta.
    await selectorRol.selectOption("implementador");
    await page.getByRole("button", { name: "Generar Hoja de Ruta", exact: true }).click();
    await expect(page.getByRole("form", { name: "Variables de planeación" })).toBeVisible();
    await page.getByLabel(/Plazo en meses/).fill("6");
    await page.getByLabel(/Presupuesto/).fill("20000");
    await page.getByLabel(/Moneda/).fill("USD");
    await page.getByLabel(/^Equipo/).fill("DPO\nSeguridad TI");
    await page.getByLabel(/Delegado de protección de datos/).fill("Delegado DPO");
    await page.getByRole("button", { name: "Generar hoja de ruta", exact: true }).click();

    await expect(page.getByRole("heading", { name: "Inventario RAT de Sistemas Críticos" })).toBeVisible();
    expect(estado.roadmapGenerado).toBe(true);
    expect(llamadas.some((l) => RUTA_API(l.url()) === "/roadmaps/generate" && l.method() === "POST")).toBe(true);
    expect(estado.auditLog.some((e) => e.action === "roadmap_generated")).toBe(true);

    // PASO 2: el `coordinador` distribuye la tarea a un responsable de área.
    await selectorRol.selectOption("coordinador");
    const cardTarea = page.getByTestId(`tarea-${estado.tareaId}`);
    await expect(cardTarea).toBeVisible();
    await page.getByLabel(/Área para Inventario RAT/).selectOption("area-ti-01");
    await page.locator(`#responsable-asignacion-${estado.tareaId}`).selectOption("user-resp-01");
    await page.getByRole("button", { name: "Distribuir tarea" }).click();

    await expect(page.getByTestId(`responsable-${estado.tareaId}`)).toHaveText("user-resp-01");
    expect(estado.ownerAsignado).toBe("user-resp-01");
    expect(llamadas.some((l) => RUTA_API(l.url()).endsWith("/assign") && l.method() === "POST")).toBe(true);
    expect(
      estado.auditLog.some((e) => e.action === "task_assigned" && e.payload.assigned_to === "user-resp-01"),
    ).toBe(true);

    // PASO 3: ni el `responsable_area` ni el `dpo` encuentran custodia física de evidencias.
    for (const rol of ["responsable_area", "dpo"]) {
      await selectorRol.selectOption(rol);
      await expect(cardTarea, rol).toBeVisible();
      await expect(cardTarea.getByRole("button", { name: "Ver evidencia" }), rol).toHaveCount(0);
      await expect(page.getByRole("button", { name: "Custodia de Evidencias", exact: true }), rol).toHaveCount(0);
    }

    // Audit log de punta a punta: la distribución queda registrada y ninguna subida de evidencia.
    await cardTarea.getByRole("button", { name: "Ver auditoría" }).click();
    const regionAuditoria = cardTarea.getByRole("region", { name: /Auditoría de/ });
    await expect(regionAuditoria).toContainText("task_assigned");
    await expect(regionAuditoria).not.toContainText("evidence_uploaded");
    expect(llamadas.some((l) => /\/evidence(\/|$)/.test(RUTA_API(l.url())) && l.method() !== "GET")).toBe(false);
  });
});
