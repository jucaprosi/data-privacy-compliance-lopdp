// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * DER-02 · Portal público de solicitudes de titulares por organización, con enlace de seguimiento.
 *
 * Contrato: governance/especificaciones/DER-02.md
 * - Carga pública de formulario /solicitud/{slug}
 * - Envío de formulario y generación de código de seguimiento
 * - Consulta de seguimiento en /solicitud/seguir/{codigo} sin exponer respuesta ni datos privados.
 */
import { expect, test } from "@playwright/test";

test.describe("Portal público de solicitudes ARCO+ (DER-02)", () => {
  test("muestra mensaje de portal no disponible cuando el slug no existe", async ({ page }) => {
    await page.route("**/api/v1/publico/solicitud/slug-inexistente", async (route) => {
      await route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({ detail: "No encontrado" }),
      });
    });

    await page.goto("/solicitud/slug-inexistente");
    await expect(page.getByText("Portal no disponible")).toBeVisible();
    await expect(
      page.getByText("El portal de privacidad solicitado no está disponible o no existe.")
    ).toBeVisible();
  });

  test("renderiza el formulario con datos de la organización y permite enviar solicitud", async ({ page }) => {
    // Interceptar tanto GET como POST para el slug acme-corp
    await page.route("**/api/v1/publico/solicitud/acme-corp", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            organizacion: "ACME Corporation Ecuador",
            derechos: ["ACCESO", "RECTIFICACION", "CANCELACION"],
            texto: "Ejerza sus derechos de privacidad bajo la LOPDP.",
          }),
        });
      } else if (route.request().method() === "POST") {
        await route.fulfill({
          status: 201,
          contentType: "application/json",
          body: JSON.stringify({
            codigo: "sol_test_1234567890abcdef",
          }),
        });
      } else {
        await route.continue();
      }
    });

    await page.goto("/solicitud/acme-corp");

    // Verificar encabezado y texto
    await expect(page.getByText("ACME Corporation Ecuador")).toBeVisible();
    await expect(page.getByText("Ejerza sus derechos de privacidad bajo la LOPDP.")).toBeVisible();

    // Rellenar formulario
    await page.getByLabel("Nombre y Apellidos del Titular").fill("Carlos Echeverría");
    await page.getByLabel("Correo Electrónico de Notificación").fill("carlos@ejemplo.com");
    await page.getByLabel("Descripción o Motivo de la Solicitud").fill("Requiero copia de mi historial de compras.");

    // Enviar
    await page.getByRole("button", { name: "Enviar Solicitud" }).click();

    // Verificar pantalla de confirmación con código
    await expect(page.getByText("Solicitud Registrada")).toBeVisible();
    await expect(page.getByText("sol_test_1234567890abcdef")).toBeVisible();
    await expect(page.getByRole("link", { name: "Consultar Seguimiento Ahora" })).toBeVisible();
  });

  test("consulta el estado de una solicitud existente en seguimiento", async ({ page }) => {
    await page.route("**/api/v1/publico/solicitud/seguir/sol_abc123", async (route) => {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          estado: "EN_ANALISIS",
          recibida_en: "2026-11-16T10:00:00Z",
          respondida_en: null,
        }),
      });
    });

    await page.goto("/solicitud/seguir/sol_abc123");

    await expect(page.getByText("Estado de su Solicitud")).toBeVisible();
    await expect(page.getByText("Código: sol_abc123")).toBeVisible();
    await expect(page.getByText("EN_ANALISIS")).toBeVisible();

    // Invariante de seguridad: no se muestra ningún campo confidencial
    await expect(page.getByText("carlos@ejemplo.com")).toBeHidden();
    await expect(page.getByText("Carlos Echeverría")).toBeHidden();
  });
});
