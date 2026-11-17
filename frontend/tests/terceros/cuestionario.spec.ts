import { test, expect } from "@playwright/test";

test.describe("TER-02: Portal externo y cuestionario de garantías", () => {
  test("Criterio 1: Token no válido (404/410) muestra 'Este enlace ya no está disponible' sin datos de la organización", async ({
    page,
  }) => {
    // Interceptar API pública para devolver 404
    await page.route("**/api/v1/publico/proveedor/token-invalido", async (route) => {
      await route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({ detail: "CODIGO_ENLACE_NO_VALIDO" }),
      });
    });

    await page.goto("/proveedor/token-invalido");

    // Título y mensaje exactos
    await expect(page.getByText("Este enlace ya no está disponible")).toBeVisible();
    await expect(
      page.getByText(
        "Puede que haya vencido o que ya se hayan enviado las respuestas. Si necesitas responder, pide un enlace nuevo a la organización que te lo envió."
      )
    ).toBeVisible();

    // No debe mostrar ningún nombre de organización
    await expect(page.getByText("Organización Test")).not.toBeVisible();
  });

  test("Criterio 2 y 3: Con token válido muestra nombre de organización, responde cuestionario y pasa a respondido", async ({
    page,
  }) => {
    const mockPreguntas = [
      {
        id: "G01",
        enunciado: "¿Existe un contrato vigente con el responsable que regula el tratamiento de los datos personales?",
        tipo: "si_no_evidencia",
        obligatoria: true,
        cita: "LOPDP art. 34; Reglamento art. 41",
      },
    ];

    await page.route("**/api/v1/publico/proveedor/token-valido", async (route) => {
      if (route.request().method() === "GET") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({
            id: "cues-1",
            tenant_id: "tenant-1",
            organizacion: "Empresa Proveedora S.A.",
            caduca_en: new Date(Date.now() + 86400000).toISOString(),
            version_cuestionario: "TER-02.1",
            preguntas: mockPreguntas,
          }),
        });
      } else if (route.request().method() === "POST") {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ estado: "respondido" }),
        });
      }
    });

    await page.goto("/proveedor/token-valido");

    // Encabezado con nombre de la organización
    await expect(
      page.getByRole("main", { name: "Cuestionario de garantías para Empresa Proveedora S.A." })
    ).toBeVisible();

    // Seleccionar 'No' para no exigir evidencia en este paso
    await page.getByLabel("No").click();

    // Avanzar a revisar y enviar
    await page.getByRole("button", { name: "Siguiente" }).click();
    await expect(page.getByRole("heading", { name: "Revisar y enviar" })).toBeVisible();

    // Enviar respuestas y confirmar
    await page.getByRole("button", { name: "Enviar respuestas" }).click();
    await expect(page.getByText("¿Enviar tus respuestas?")).toBeVisible();

    // Confirmar en el modal
    await page.locator("div[role='dialog'], div.fixed").getByRole("button", { name: "Enviar respuestas" }).click();

    // Mensaje de éxito
    await expect(page.getByRole("status")).toHaveText("Respuestas enviadas");
    await expect(
      page.getByText("Recibimos tus respuestas. Empresa Proveedora S.A. las revisará. Ya puedes cerrar esta página.")
    ).toBeVisible();
  });
});
