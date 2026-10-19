/**
 * Recorrido 2 de Integración (TEST-03):
 * Tamaño de la organización: PATCH /api/v1/organizacion/configuracion como administrador
 * persiste en Neon PostgreSQL y la ficha/panel refleja la talla guardada.
 *
 * Sin page.route: llamada directa al backend real (FastAPI + Neon PostgreSQL).
 */
import { expect, test } from "@playwright/test";
import { crearTenantConAdmin, limpiarTenant } from "./dbHelper";

test.describe("Recorrido 2: Tamaño de la organización (TEST-03)", () => {
  let fixture: ReturnType<typeof crearTenantConAdmin>;

  test.beforeEach(() => {
    fixture = crearTenantConAdmin("tamano");
  });

  test.afterEach(() => {
    if (fixture) {
      limpiarTenant(fixture.tenantId, fixture.domain);
    }
  });

  test("PATCH /api/v1/organizacion/configuracion como administrador persiste y la interfaz lo refleja", async ({
    page,
    request,
  }) => {
    // 1. Ejecutar PATCH real como admin_organizacion cambiando el tamaño a 'mediana'
    const respuestaPatch = await request.patch("/api/v1/organizacion/configuracion", {
      headers: {
        "X-Tenant-ID": fixture.tenantId,
        "X-User-ID": fixture.adminUserId,
        "X-Role": "admin_organizacion",
        "Content-Type": "application/json",
      },
      data: {
        tamano: "mediana",
        sector: "Tecnología",
      },
    });

    expect(respuestaPatch.status()).toBe(200);
    const cuerpoPatch = await respuestaPatch.json();
    expect(cuerpoPatch.tamano).toBe("mediana");
    expect(cuerpoPatch.sector).toBe("Tecnología");

    // 2. Verificar vía GET /organizacion/configuracion real que la BD devolvió la talla guardada
    const respuestaGet = await request.get("/api/v1/organizacion/configuracion", {
      headers: {
        "X-Tenant-ID": fixture.tenantId,
        "X-User-ID": fixture.adminUserId,
        "X-Role": "admin_organizacion",
      },
    });
    expect(respuestaGet.status()).toBe(200);
    const cuerpoGet = await respuestaGet.json();
    expect(cuerpoGet.tamano).toBe("mediana");

    // 3. Abrir la interfaz con sesión de administrador y verificar que el componente refleja la talla
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

    await page.goto("/");
    await expect(page.getByRole("textbox", { name: /Razón Social/ })).toBeVisible();

    // Completar datos mínimos requeridos
    await page.getByRole("textbox", { name: /Razón Social/ }).fill(`Empresa ${fixture.tenantId}`);
    const grupos = page.getByRole("radiogroup");
    const total = await grupos.count();
    expect(total).toBeGreaterThan(0);
    for (let i = 0; i < total; i++) {
      await grupos.nth(i).getByRole("radio", { name: "No", exact: true }).check();
    }
    await page.getByRole("button", { name: /Guardar Ficha y Continuar/ }).click();
    await expect(page.getByText(/Ficha organizacional guardada/)).toBeVisible();

    await page.locator("#selector-normativa").selectOption("LOPDP");
    await page.getByRole("button", { name: "Cerrar alerta" }).click();

    // Ir a Hoja de Ruta
    await page.getByRole("button", { name: /^Hoja de Ruta/i }).click();

    // Subvista Administración (disponible para admin_organizacion)
    await page.getByRole("button", { name: "Administración" }).click();

    // Ir a la pestaña Configuración
    await page.getByRole("tab", { name: "Configuración" }).click();

    // El selector de tamaño debe mostrar 'mediana' cargado desde el backend real
    const selectorTamano = page.getByLabel("Tamaño de la organización");
    await expect(selectorTamano).toBeVisible();
    await expect(selectorTamano).toHaveValue("mediana");

    // Ahora cambiamos interactivamente en la interfaz a 'pequena' y guardamos contra el backend real
    await selectorTamano.selectOption("pequena");
    await page.getByRole("button", { name: "Guardar configuración" }).click();

    // Comprobamos confirmación visual en el panel
    await expect(page.getByTestId("configuracion-guardada")).toBeVisible();
    await expect(selectorTamano).toHaveValue("pequena");

    // 4. Verificar que el backend real tiene ahora 'pequena' en la BD
    const verificacionBackend = await request.get("/api/v1/organizacion/configuracion", {
      headers: {
        "X-Tenant-ID": fixture.tenantId,
        "X-User-ID": fixture.adminUserId,
        "X-Role": "admin_organizacion",
      },
    });
    expect(verificacionBackend.status()).toBe(200);
    expect((await verificacionBackend.json()).tamano).toBe("pequena");
  });
});
