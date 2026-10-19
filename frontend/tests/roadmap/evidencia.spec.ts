/**
 * Arnés de interfaz de FE-04: panel de evidencia.
 *
 * Monta EvidenciaPanel en /harness-roadmap/evidencia contra el servidor simulado de FE-01.
 * Parámetros de la ruta: rol, usuario, tarea y fallo (subida | url | cuatroojos | lista | vacia).
 * Datos sembrados en task-002: evi-ajena, subida por user-resp-01, y evi-propia, subida por
 * user-enc-01 (el usuario por defecto), ambas pendientes de validación.
 */
import { expect, test, type Page } from "@playwright/test";

const RUTA = "/harness-roadmap/evidencia";

async function abrir(page: Page, consulta = ""): Promise<void> {
  await page.goto(`${RUTA}${consulta}`);
  await expect(page.getByRole("region", { name: "Evidencia de la tarea" })).toBeVisible();
}

const evidencia = (page: Page, id: string) => page.getByTestId(`evidencia-${id}`);

const PDF_VALIDO = { name: "politica_privacidad.pdf", mimeType: "application/pdf", buffer: Buffer.from("%PDF-1.4 evidencia") };

async function elegirArchivo(page: Page, archivo: { name: string; mimeType: string; buffer: Buffer }): Promise<void> {
  await page.getByLabel("Archivo de evidencia").setInputFiles(archivo);
}

test.describe("Panel de evidencia (FE-04)", () => {
  test("lista la evidencia de la tarea con su estado en texto", async ({ page }) => {
    await abrir(page);

    await expect(evidencia(page, "evi-ajena")).toContainText("rat_consolidado.pdf");
    await expect(evidencia(page, "evi-ajena")).toContainText("Subida por user-resp-01");
    await expect(evidencia(page, "evi-ajena")).toContainText("huella 9f86d081884c");
    await expect(page.getByTestId("validacion-evi-ajena")).toContainText("Pendiente de validación");
    await expect(evidencia(page, "evi-propia")).toBeVisible();
  });

  test("una tarea sin evidencia lo dice en lugar de mostrar una lista vacía", async ({ page }) => {
    await abrir(page, "?fallo=vacia");

    await expect(page.getByTestId("sin-evidencia")).toHaveText("Esta tarea todavía no tiene evidencia registrada.");
    await expect(page.getByRole("list", { name: "Evidencias registradas" }).getByRole("listitem")).toHaveCount(0);
  });

  test("rechaza una extensión no permitida y dice cuáles se admiten", async ({ page }) => {
    await abrir(page);
    await elegirArchivo(page, { name: "instalador.exe", mimeType: "application/x-msdownload", buffer: Buffer.from("MZ") });

    const rechazos = page.getByTestId("rechazos");
    await expect(rechazos).toContainText("«instalador.exe»: tipo de archivo no permitido");
    await expect(rechazos).toContainText(".pdf");
    await expect(page.getByTestId("subida-progreso")).toHaveCount(0);
    await expect(page.getByTestId("evidencia-evi-ajena")).toBeVisible();
  });

  test("rechaza un archivo que supera el tamaño máximo", async ({ page }) => {
    await abrir(page);
    await elegirArchivo(page, {
      name: "contrato_enorme.pdf",
      mimeType: "application/pdf",
      buffer: Buffer.alloc(11 * 1024 * 1024),
    });

    await expect(page.getByTestId("rechazos")).toContainText("«contrato_enorme.pdf»: supera el tamaño máximo de 10.0 MB.");
  });

  test("sube un archivo válido, lo registra con su huella y aparece en el listado", async ({ page }) => {
    await abrir(page);
    await expect(page.getByRole("list", { name: "Evidencias registradas" }).getByRole("listitem")).toHaveCount(2);

    await elegirArchivo(page, PDF_VALIDO);

    const nueva = page.getByRole("list", { name: "Evidencias registradas" }).getByRole("listitem").filter({ hasText: "politica_privacidad.pdf" });
    await expect(nueva).toBeVisible();
    await expect(nueva).toContainText("Pendiente de validación");
    await expect(nueva).toContainText("Subida por user-enc-01");
    // El registro lleva la huella SHA-256 del contenido: no es una cadena vacía ni inventada.
    await expect(nueva).toContainText(/huella [0-9a-f]{12}…/);
    await expect(page.getByRole("list", { name: "Evidencias registradas" }).getByRole("listitem")).toHaveCount(3);
  });

  test("si la subida al almacenamiento falla no registra la evidencia y permite reintentar", async ({ page }) => {
    await abrir(page, "?fallo=subida");
    await elegirArchivo(page, PDF_VALIDO);

    const error = page.getByTestId("error-subida");
    await expect(error).toContainText("El almacenamiento rechazó el archivo (HTTP 500).");
    await expect(error).toContainText("Código: UPLOAD_FAILED");
    await expect(error).toContainText("Acción requerida: retry_upload");
    // Nada quedó registrado: el archivo nunca llegó.
    await expect(page.getByRole("list", { name: "Evidencias registradas" }).getByRole("listitem")).toHaveCount(2);

    await page.getByRole("button", { name: /Reintentar la subida de politica_privacidad.pdf/ }).click();
    await expect(page.getByRole("list", { name: "Evidencias registradas" }).getByRole("listitem")).toHaveCount(3);
    await expect(page.getByTestId("error-subida")).toHaveCount(0);
  });

  test("si no se puede autorizar la subida muestra el error de negocio", async ({ page }) => {
    await abrir(page, "?fallo=url");
    await elegirArchivo(page, PDF_VALIDO);

    await expect(page.getByTestId("error-subida")).toContainText("Código: UPLOAD_URL_UNAVAILABLE");
    await expect(page.getByRole("list", { name: "Evidencias registradas" }).getByRole("listitem")).toHaveCount(2);
  });

  test("cuatro ojos: el coordinador no puede validar lo que él mismo subió y se le explica", async ({ page }) => {
    await abrir(page);
    const propia = evidencia(page, "evi-propia");

    await expect(page.getByTestId("cuatro-ojos-evi-propia")).toContainText("regla de cuatro ojos");
    await expect(propia.getByRole("button", { name: "Aprobar" })).toBeDisabled();
    await expect(propia.getByRole("button", { name: "Rechazar" })).toBeDisabled();

    // La evidencia de otra persona sí se puede validar.
    await expect(page.getByTestId("cuatro-ojos-evi-ajena")).toHaveCount(0);
    await expect(evidencia(page, "evi-ajena").getByRole("button", { name: "Aprobar" })).toBeEnabled();
  });

  test("aprueba la evidencia de otra persona, con comentario opcional", async ({ page }) => {
    await abrir(page);
    const ajena = evidencia(page, "evi-ajena");

    await ajena.getByRole("button", { name: "Aprobar" }).click();
    await ajena.getByLabel("Comentario (opcional)").fill("Documento completo y vigente.");
    await ajena.getByRole("button", { name: "Confirmar aprobación" }).click();

    await expect(page.getByTestId("validacion-evi-ajena")).toContainText("Aprobada");
    await expect(ajena).toContainText("Documento completo y vigente.");
    await expect(ajena.getByRole("button", { name: "Aprobar" })).toHaveCount(0);
  });

  test("rechazar exige el motivo y deja la evidencia como rechazada", async ({ page }) => {
    await abrir(page);
    const ajena = evidencia(page, "evi-ajena");

    await ajena.getByRole("button", { name: "Rechazar" }).click();
    await ajena.getByRole("button", { name: "Confirmar rechazo" }).click();
    await expect(ajena.getByText("Para rechazar una evidencia indica el motivo en el comentario.")).toBeVisible();
    await expect(page.getByTestId("validacion-evi-ajena")).toContainText("Pendiente de validación");

    await ajena.getByLabel("Motivo del rechazo (obligatorio)").fill("Falta la firma del responsable.");
    await ajena.getByRole("button", { name: "Confirmar rechazo" }).click();
    await expect(page.getByTestId("validacion-evi-ajena")).toContainText("Rechazada");
    await expect(ajena).toContainText("Falta la firma del responsable.");
  });

  test("si el servidor responde con la violación de cuatro ojos muestra su código y la acción", async ({ page }) => {
    await abrir(page, "?fallo=cuatroojos");
    const ajena = evidencia(page, "evi-ajena");

    await ajena.getByRole("button", { name: "Aprobar" }).click();
    await ajena.getByRole("button", { name: "Confirmar aprobación" }).click();

    const error = page.getByTestId("error-validacion-evi-ajena");
    await expect(error).toContainText("regla de cuatro ojos");
    await expect(error).toContainText("Código: FOUR_EYES_VIOLATION");
    await expect(error).toContainText("Acción requerida: ask_another_validator");
    await expect(page.getByTestId("validacion-evi-ajena")).toContainText("Pendiente de validación");
  });

  const ROLES: Array<{ rol: string; usuario: string; sube: boolean; valida: boolean }> = [
    { rol: "responsable_area", usuario: "user-resp-01", sube: true, valida: false },
    { rol: "coordinador", usuario: "user-enc-02", sube: true, valida: true },
    { rol: "dpo", usuario: "dpo-corp-01", sube: false, valida: true },
    { rol: "implementador", usuario: "user-impl-01", sube: false, valida: true },
    { rol: "admin_organizacion", usuario: "user-admin-01", sube: false, valida: false },
  ];

  for (const caso of ROLES) {
    test(`el rol ${caso.rol} ${caso.sube ? "sube" : "no sube"} y ${caso.valida ? "valida" : "no valida"} evidencia`, async ({ page }) => {
      await abrir(page, `?rol=${caso.rol}&usuario=${caso.usuario}`);

      expect(await page.getByLabel("Archivo de evidencia").count() > 0, "zona de subida").toBe(caso.sube);
      if (!caso.sube) await expect(page.getByRole("note")).toContainText("no sube evidencia");

      const ajena = evidencia(page, "evi-ajena");
      if (caso.rol === "responsable_area") {
        // Solo ve la que subió él (PRD §5.2): la del coordinador queda fuera.
        await expect(ajena).toBeVisible();
        await expect(evidencia(page, "evi-propia")).toHaveCount(0);
      } else {
        await expect(ajena).toBeVisible();
      }
      expect((await ajena.getByRole("button", { name: "Aprobar" }).count()) > 0, "botón aprobar").toBe(caso.valida);
    });
  }

  test("si falla la carga del listado muestra el error y permite reintentar", async ({ page }) => {
    await page.goto(`${RUTA}?fallo=lista`);

    await expect(page.getByTestId("error-lista")).toContainText("Código: EVIDENCE_UNAVAILABLE");
    await page.getByRole("button", { name: "Reintentar la carga" }).click();
    await expect(evidencia(page, "evi-ajena")).toBeVisible();
    await expect(page.getByTestId("error-lista")).toHaveCount(0);
  });

  test("ninguna pantalla muestra tokens de gobernanza", async ({ page }) => {
    await abrir(page);
    const texto = await page.locator("body").innerText();
    expect(texto).not.toMatch(/[¤¦]/);
  });
});
