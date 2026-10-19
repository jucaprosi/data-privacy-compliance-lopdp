/**
 * Recorrido 3 de Integración (TEST-03):
 * Aislamiento: Una llamada sin X-Tenant-ID recibe 401 del backend real
 * tanto a nivel HTTP directo como en el comportamiento de la interfaz.
 *
 * Sin page.route: llamada directa al backend real.
 */
import { expect, test } from "@playwright/test";

test.describe("Recorrido 3: Aislamiento sin X-Tenant-ID (TEST-03)", () => {
  test("llamada sin X-Tenant-ID responde 401 desde el backend real", async ({
    request,
    page,
  }) => {
    // 1. Petición directa al backend real sin X-Tenant-ID
    const respuestaSinTenant = await request.get("/api/v1/ai/mitigaciones", {
      headers: {
        // Sin X-Tenant-ID
        Authorization: "Bearer token-cualquiera",
      },
    });

    // En SEC-07: get_current_tenant exige X-Tenant-ID y devuelve 401 si falta
    expect(respuestaSinTenant.status()).toBe(401);
    const cuerpoError = await respuestaSinTenant.json();
    expect(cuerpoError.detail).toContain("Falta el tenant (X-Tenant-ID)");

    // 2. Verificar otra ruta protegida por get_tenant_session / get_current_tenant
    const respuestaTercerosSinTenant = await request.get("/api/v1/terceros/encargados", {
      headers: {
        Authorization: "Bearer token-cualquiera",
      },
    });
    expect(respuestaTercerosSinTenant.status()).toBe(401);

    // 3. Comportamiento en la interfaz cuando se intenta consumir la API sin tenant válido
    await page.goto("/");
    const estadoCliente = await page.evaluate(async () => {
      const res = await fetch("/api/v1/terceros/encargados", {
        headers: {
          Authorization: "Bearer token-invalido",
        },
      });
      return res.status;
    });

    expect(estadoCliente).toBe(401);
  });
});
