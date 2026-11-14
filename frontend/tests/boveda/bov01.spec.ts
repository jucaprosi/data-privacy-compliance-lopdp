// ¤arbitro
// ¤¤qa-engineer
/**
 * Arnés de interfaz de BOV-01: espacio y descargas del plan de almacenamiento, en solo lectura.
 *
 * El servidor se simula con page.route sobre /api/v1/** con la forma real de GET /boveda-cloud/suscripcion.
 * Datos ficticios. Mutación documentada: si `nivel()` usara 90 en lugar de 80 como umbral, «85 % muestra
 * Cerca del límite» falla; si el error mostrara `detail` del servidor, «500 con texto fijo» falla.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, abrirSubmenu, barraDeMenus, configurarProyecto, submenuPorNombre } from "../utiles";
import { credencialSimulada, fijarAjustes, ruta, sembrarSesion } from "../auth/utilesAuth";

const GB = 1024 ** 3;

function plan(uso: number, egress: number, extra: Record<string, unknown> = {}) {
  return {
    paquete_codigo: "INICIAL",
    paquete_nombre: "Inicial",
    cuota_almacenamiento_bytes: 50 * GB,
    uso_almacenamiento_bytes: uso,
    cuota_egress_mensual_bytes: 100 * GB,
    uso_egress_mensual_bytes: egress,
    certificaciones_heredadas: ["ISO 27001", "ISO 27701", "SOC 2"],
    estado: "ACTIVA",
    ...extra,
  };
}

type Respuesta = { status: number; cuerpo: unknown } | "pendiente";

async function abrir(page: Page, respuesta: Respuesta, roles = ["dpo"]): Promise<{ rol?: string }> {
  const visto: { rol?: string } = {};
  await fijarAjustes(page);
  await sembrarSesion(page, credencialSimulada());
  await page.route("**/api/v1/**", async (route) => {
    const destino = ruta(route.request().url());
    const json = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });
    if (destino === "/organizacion/me/roles") {
      return json(200, { user_id: "u", tenant_id: "t-prueba", roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })) });
    }
    if (destino === "/boveda-cloud/suscripcion") {
      visto.rol = route.request().headers()["x-role"];
      if (respuesta === "pendiente") return; // nunca responde: estado «cargando»
      return json(respuesta.status, respuesta.cuerpo);
    }
    return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
  });
  await abrirAppLimpia(page);
  if (!(await barraDeMenus(page).getByRole("button", { name: "Inventario", exact: true }).isVisible())) {
    await configurarProyecto(page, "Entidad BOV-01");
  }
  await abrirSubmenu(page, submenuPorNombre(/Almacenamiento/)!);
  return visto;
}

const vista = (page: Page) => page.getByRole("main", { name: "Almacenamiento y descargas" });

test.describe("Almacenamiento y descargas (BOV-01)", () => {
  test("50 % sin aviso, 85 % «Cerca del límite» y certificaciones con su nota", async ({ page }) => {
    const visto = await abrir(page, { status: 200, cuerpo: plan(25 * GB, 85 * GB) });
    const v = vista(page);
    await expect(v.getByRole("heading", { name: "Almacenamiento y descargas" })).toBeVisible();
    await expect(v.getByText("Tu plan: Inicial")).toBeVisible();
    await expect(v.getByRole("meter", { name: "Espacio usado" })).toHaveAttribute("aria-valuetext", "25,0 GB de 50,0 GB, 50 %");
    await expect(v.getByRole("meter", { name: "Descargas de este mes" })).toHaveAttribute("aria-valuetext", "85,0 GB de 100,0 GB, 85 %");
    await expect(v.getByText("Cerca del límite")).toHaveCount(1);
    await expect(v.getByText("Límite alcanzado")).toHaveCount(0);
    await expect(v.getByRole("list", { name: "Certificaciones del proveedor de nube" }).getByRole("listitem")).toHaveCount(3);
    await expect(v.getByText("No certifican a tu organización ni sustituyen tu propio cumplimiento.", { exact: false })).toBeVisible();
    expect(visto.rol).toBe("dpo");
    const texto = await v.innerText();
    expect(texto).not.toMatch(/bytes|\d{7,}|[¤¦]/);
  });

  test("100 % «Límite alcanzado», estado excedido con su línea y MB bajo 1 GB", async ({ page }) => {
    await abrir(page, { status: 200, cuerpo: plan(512 * 1024 ** 2, 100 * GB, { estado: "CUOTA_EXCEDIDA", certificaciones_heredadas: [] }) });
    const v = vista(page);
    await expect(v.getByText("Límite alcanzado")).toBeVisible();
    await expect(v.getByText("Límite excedido")).toBeVisible();
    await expect(v.getByText("Alcanzaste el límite de tu plan.", { exact: false })).toBeVisible();
    await expect(v.getByRole("meter", { name: "Espacio usado" })).toHaveAttribute("aria-valuetext", "512 MB de 50,0 GB, 1 %");
    await expect(v.getByRole("list", { name: "Certificaciones del proveedor de nube" })).toHaveCount(0);
  });

  test("suspendida muestra etiqueta y línea", async ({ page }) => {
    await abrir(page, { status: 200, cuerpo: plan(0, 0, { estado: "SUSPENDIDA" }) });
    await expect(vista(page).getByText("Suspendida", { exact: true })).toBeVisible();
    await expect(vista(page).getByText("Tu servicio de almacenamiento está suspendido.", { exact: false })).toBeVisible();
  });

  test("404, 500 con texto fijo y cargando", async ({ page }) => {
    await abrir(page, { status: 404, cuerpo: { detail: "x", code: "BOVEDA_SUSCRIPCION_NO_ENCONTRADA" } });
    await expect(vista(page).getByRole("status")).toHaveText(
      "Tu organización aún no tiene un plan de almacenamiento activo. Escribe al equipo de EVYDENTIA.",
    );
  });

  test("500 nunca muestra el texto del servidor y ofrece volver a cargar", async ({ page }) => {
    await abrir(page, { status: 500, cuerpo: { detail: "detalle interno del servidor", code: "X" } });
    await expect(vista(page).getByRole("alert")).toHaveText("No pudimos cargar tu plan de almacenamiento. Inténtalo de nuevo.");
    await expect(vista(page).getByRole("button", { name: "Volver a cargar" })).toBeVisible();
    await expect(page.getByText("detalle interno del servidor")).toHaveCount(0);
  });

  test("cargando", async ({ page }) => {
    await abrir(page, "pendiente");
    await expect(vista(page).getByRole("status")).toHaveText("Cargando tu plan de almacenamiento…");
  });

  test("a 375 px no hay desplazamiento horizontal", async ({ page }) => {
    // Se abre en escritorio (a 375 px el menú es un cajón) y luego se estrecha la ventana.
    await abrir(page, { status: 200, cuerpo: plan(25 * GB, 85 * GB) });
    await page.setViewportSize({ width: 375, height: 812 });
    await expect(vista(page).getByRole("meter", { name: "Espacio usado" })).toBeVisible();
    const desborde = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(desborde).toBeLessThanOrEqual(0);
  });
});
