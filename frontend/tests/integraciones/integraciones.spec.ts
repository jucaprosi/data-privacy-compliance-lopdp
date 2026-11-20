/**
 * API-02: Pruebas de integración de interfaz para Claves de Integración y Techos.
 */
import { test } from "@playwright/test";

test.describe("API-02: Claves de integración", () => {
  test("renderiza panel de claves y techos de paquete", async ({ page }) => {
    await page.route("**/api/v1/integraciones/techos", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          claves: { maximo: 10, activas: 2 },
          webhooks: { maximo: 10, activos: 0 },
        }),
      });
    });

    await page.route("**/api/v1/integraciones/claves", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          claves: [
            {
              id: "clave-1",
              nombre: "ERP Finanzas",
              prefijo: "evk_a1b2c3d4...",
              alcances: ["rat:lectura"],
              creada_en: "2026-11-16T10:00:00Z",
              rotada_en: null,
              revocada_en: null,
            },
          ],
        }),
      });
    });

    // Mock auth
    await page.route("**/api/v1/organizacion/me/roles", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          user_id: "u-admin",
          tenant_id: "t-1",
          roles: [{ role: "admin_organizacion" }],
        }),
      });
    });

    await page.goto("/dashboard");

    // Verificar que el submenú de claves de integración existe en el menú
    // o navegar directamente a la vista de integración
  });
});
