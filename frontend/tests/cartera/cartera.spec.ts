/**
 * ORG-15: Inicio › Tablero de cartera. Una fila por organización de la persona, con las cuatro dimensiones
 * como semáforo, brechas, hallazgos abiertos y tareas vencidas; sin cifra única. Google y la API se simulan.
 *
 * Prueba de mutación (ORG-15), ejecutada y restaurada:
 *  - `cambiarDeOrganizacion` (store/datosDeTrabajo.ts) sin `guardarOrganizacionActiva`: al elegir B el
 *    encabezado sigue en A y «elegir la segunda fila entra en esa organización» falla (toContainText).
 */
import { expect, test, type Page } from "@playwright/test";

import { SUBMENUS_ORG_15 } from "../../src/components/layout/menus/ORG-15";
import { configurarProyecto, abrirSubmenu } from "../utiles";
import {
  BOTON_GOOGLE,
  credencialSimulada,
  fijarAjustes,
  googleSimulado,
  simularApi,
  type OrganizacionSimulada,
} from "../auth/utilesAuth";

const A: OrganizacionSimulada = { tenant_id: "org-a", nombre_comercial: "Cooperativa Andina", roles: ["dpo"] };
const B: OrganizacionSimulada = { tenant_id: "org-b", nombre_comercial: "Banco Bolívar", roles: ["implementador"] };
const dpo = credencialSimulada({ email: "dpo@externo.invalid", nombre: "DPO Externo" });

const DIAGNOSTICO = {
  escala: "smartcidi_1_5",
  niveles_por_dimension: [
    { dimension: "D01", nivel: 4 },
    { dimension: "D02", nivel: 2 },
  ],
  cumplimiento: false,
  respaldo_documental: 55,
  brechas_criticas: 3,
  brechas_altas: 5,
  sellado_en: "2026-11-09T12:00:00+00:00",
};

const FILA_A = { tenant_id: A.tenant_id, nombre: A.nombre_comercial, roles: A.roles, diagnostico: DIAGNOSTICO,
  hallazgos_abiertos: 4, tareas_vencidas: 2, cadena_integra: true };
const FILA_B = { tenant_id: B.tenant_id, nombre: B.nombre_comercial, roles: B.roles, diagnostico: null,
  hallazgos_abiertos: 0, tareas_vencidas: 0, cadena_integra: true };

async function abrirCartera(page: Page, filas: unknown[], organizaciones = [A, B]) {
  await fijarAjustes(page, { modo: "oidc", tenant: null });
  await googleSimulado(page, dpo.token);
  const llamadas = await simularApi(page, { organizaciones, roles: ["dpo"] });
  await page.route("**/api/v1/organizacion/cartera", (route) => {
    llamadas.push(route.request());
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ organizaciones: filas }) });
  });
  await page.goto("/login");
  await page.getByRole("button", { name: BOTON_GOOGLE }).click();
  await expect(page).toHaveURL(/\/organizaciones/);
  await page.getByRole("button", { name: new RegExp(A.nombre_comercial) }).click();
  await expect(page).toHaveURL(/\/dashboard/);
  await configurarProyecto(page, "Empresa A S.A.");
  await abrirSubmenu(page, SUBMENUS_ORG_15[0]);
  return llamadas;
}

test.describe("Tablero de cartera (ORG-15)", () => {
  test("una fila por organización con cuatro semáforos, contadores y sin cifra única", async ({ page }) => {
    await abrirCartera(page, [FILA_A, FILA_B]);
    const tablero = page.getByRole("region", { name: "Tablero de cartera" });
    await expect(tablero.getByRole("heading", { name: A.nombre_comercial })).toBeVisible();
    await expect(tablero.getByRole("heading", { name: B.nombre_comercial })).toBeVisible();

    const filaA = page.getByTestId(`fila-${A.tenant_id}`);
    for (const id of ["madurez", "conformidad", "evidencia", "riesgo"]) {
      await expect(filaA.getByTestId(`dimension-${id}`)).toBeVisible();
    }
    await expect(filaA.getByTestId("brechas-criticas")).toContainText("3");
    await expect(filaA.getByTestId("hallazgos-abiertos")).toContainText("4");
    await expect(filaA.getByTestId("tareas-vencidas")).toContainText("2");
    expect(await tablero.innerText(), "ningún porcentaje ni puntaje único").not.toMatch(/%|puntaje|promedio/i);
    await expect(filaA.getByTestId("dimension-conformidad")).toContainText("Con incumplimientos críticos abiertos");
    const texto = await tablero.innerText();
    expect(texto).not.toMatch(/Conforme|sellos|org-a|org-b/);
    expect(texto.replace(/Organización actual/g, "")).not.toMatch(/activa/i);
    await expect(filaA.getByRole("button", { name: /Entrar en/ })).toHaveCount(0);
    await expect(filaA.getByTestId("dimension-riesgo")).toContainText("3 riesgos críticos y 5 altos");

    const filaB = page.getByTestId(`fila-${B.tenant_id}`);
    await expect(filaB).toContainText("aún no tiene un diagnóstico sellado");
    await expect(filaB.getByTestId("dimension-madurez")).toHaveCount(0);
  });

  test("elegir la segunda fila entra en esa organización y el encabezado la muestra", async ({ page }) => {
    const llamadas = await abrirCartera(page, [FILA_A, FILA_B]);
    await expect(page.getByTestId(`fila-${A.tenant_id}`)).toContainText("Organización actual");

    await page.getByRole("button", { name: `Entrar en ${B.nombre_comercial}` }).click();
    await page.getByRole("alertdialog").getByRole("button", { name: "Descartar y cambiar" }).click();
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByTestId("organizacion-activa")).toContainText(B.nombre_comercial);
    const tenantsPosteriores = llamadas.slice(-3).map((l) => l.headers()["x-tenant-id"]).filter(Boolean);
    expect(tenantsPosteriores.every((t) => t === B.tenant_id)).toBe(true);
  });

  test("una organización sin datos lo dice y no tumba a las demás", async ({ page }) => {
    const sinDatos = { tenant_id: B.tenant_id, nombre: B.nombre_comercial, roles: B.roles, diagnostico: null,
      hallazgos_abiertos: null, tareas_vencidas: null, cadena_integra: null, error: "SIN_DATOS" };
    await abrirCartera(page, [FILA_A, sinDatos]);
    await expect(page.getByTestId(`fila-${B.tenant_id}`)).toContainText("No se pudieron calcular los indicadores");
    await expect(page.getByTestId(`fila-${A.tenant_id}`).getByTestId("dimension-riesgo")).toBeVisible();
  });

  test("una cadena de diagnósticos alterada se avisa en su fila", async ({ page }) => {
    await abrirCartera(page, [{ ...FILA_A, cadena_integra: false }, FILA_B]);
    await expect(page.getByTestId(`fila-${A.tenant_id}`).getByRole("note")).toContainText("no coinciden con su registro de integridad");
  });

  test("sin organizaciones, pide una invitación", async ({ page }) => {
    await abrirCartera(page, []);
    await expect(page.getByRole("region", { name: "Tablero de cartera" })).toContainText(
      "Tu cuenta todavía no pertenece a ninguna organización. Pide una invitación a quien administra tu cuenta.",
    );
  });

  test("si el servidor falla, lo dice sin ocultar el panel", async ({ page }) => {
    await fijarAjustes(page, { modo: "oidc", tenant: null });
    await googleSimulado(page, dpo.token);
    await simularApi(page, { organizaciones: [A], roles: ["dpo"] });
    await page.route("**/api/v1/organizacion/cartera", (route) => route.fulfill({ status: 500, json: { detail: "x" } }));
    await page.goto("/login");
    await page.getByRole("button", { name: BOTON_GOOGLE }).click();
    await expect(page).toHaveURL(/\/dashboard/);
    await configurarProyecto(page, "Empresa A S.A.");
    await abrirSubmenu(page, SUBMENUS_ORG_15[0]);
    await expect(page.getByRole("alert").filter({ hasText: "No pudimos cargar tu cartera. Inténtalo de nuevo." })).toBeVisible();
    await expect(page.getByRole("button", { name: "Reintentar" })).toBeVisible();
  });
});
