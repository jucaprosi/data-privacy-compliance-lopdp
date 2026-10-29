/**
 * Recorrido 1 de Integración (TEST-03):
 * Roles reales: GET /api/v1/organizacion/me/roles con la identidad de desarrollo
 * devuelve la forma que espera el cliente ({ user_id, tenant_id, roles: [...] })
 * y el panel de Hoja de Ruta lo refleja con el rol activo real.
 *
 * Sin page.route: llamada directa al backend real (FastAPI + Neon PostgreSQL).
 */
import { expect, test } from "@playwright/test";
import { crearTenantConAdmin, limpiarTenant } from "./dbHelper";
import { irASala } from "../utiles";

test.describe("Recorrido 1: Roles reales desde el backend (TEST-03)", () => {
  let fixture: ReturnType<typeof crearTenantConAdmin>;

  test.beforeEach(() => {
    fixture = crearTenantConAdmin("roles");
  });

  test.afterEach(() => {
    if (fixture) {
      limpiarTenant(fixture.tenantId, fixture.domain);
    }
  });

  test("GET /api/v1/organizacion/me/roles real devuelve los roles y el panel los muestra", async ({
    page,
    request,
  }) => {
    // 1. Verificación directa del contrato de la API contra el backend real (puerto 5100 reescrito en /api/v1)
    const respuestaApi = await request.get("/api/v1/organizacion/me/roles", {
      headers: {
        "X-Tenant-ID": fixture.tenantId,
        "X-User-ID": fixture.adminUserId,
      },
    });

    expect(respuestaApi.status()).toBe(200);
    const cuerpoApi = await respuestaApi.json();
    expect(cuerpoApi.tenant_id).toBe(fixture.tenantId);
    expect(cuerpoApi.user_id).toBe(fixture.adminUserId);
    expect(Array.isArray(cuerpoApi.roles)).toBe(true);
    expect(cuerpoApi.roles.length).toBeGreaterThan(0);
    expect(cuerpoApi.roles[0].role).toBe("admin_organizacion");

    // 2. Configurar la sesión de desarrollo en el frontend para el tenant y usuario creados
    await page.addInitScript((datos) => {
      window.__LOPDP_AUTH_PRUEBAS__ = {
        modo: "headers",
        tenant: datos.tenantId,
      };
      try {
        window.localStorage.clear();
        window.sessionStorage.clear();
      } catch {}
    }, { tenantId: fixture.tenantId, userId: fixture.adminUserId });

    // 3. Abrir la aplicación y configurar proyecto
    await page.goto("/");
    await expect(page.getByRole("textbox", { name: /Razón Social/ })).toBeVisible();

    // Completar datos mínimos requeridos
    await page.getByRole("textbox", { name: /Razón Social/ }).fill(`Empresa ${fixture.tenantId}`);
    
    // Responder preguntas obligatorias del perfil de operación con 'No'
    const grupos = page.getByRole("radiogroup");
    const total = await grupos.count();
    expect(total).toBeGreaterThan(0);
    for (let i = 0; i < total; i++) {
      await grupos.nth(i).getByRole("radio", { name: "No", exact: true }).check();
    }

    await page.getByRole("button", { name: /Guardar Ficha y Continuar/ }).click();
    await expect(page.getByText(/Ficha organizacional guardada/)).toBeVisible();

    // Seleccionar normativa LOPDP
    await page.locator("#selector-normativa").selectOption("LOPDP");
    await page.getByRole("button", { name: "Cerrar alerta" }).click();

    // 4. Navegar a la sala "Hoja de Ruta"
    await irASala(page, /^Hoja de Ruta/i);

    // 5. El panel debe consultar /me/roles real y mostrar el rol asignado en la BD
    await expect(page.getByText(/Rol:/i)).toBeVisible();
    await expect(page.getByText("admin_organizacion")).toBeVisible();
  });
});
