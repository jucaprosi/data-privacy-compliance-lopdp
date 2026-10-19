/**
 * Arnés de interfaz de FE-03: vista de olas y tareas.
 *
 * Monta OlasView en /harness-roadmap/olas contra el servidor simulado de FE-01. Parámetros de
 * la ruta: rol, usuario, fallo (estado | editar | asignar) y roadmap.
 * Datos del simulado: tres tareas; task-001 completada y crítica (área 001), task-002 en
 * progreso y alta (área 001) y task-003 pendiente y alta (área 002). user-resp-01 es responsable de área 001.
 */
import { expect, test, type Page } from "@playwright/test";

const RUTA = "/harness-roadmap/olas";

async function abrir(page: Page, consulta = ""): Promise<void> {
  await page.goto(`${RUTA}${consulta}`);
  await expect(page.getByRole("region", { name: "Hoja de ruta" })).toBeVisible();
}

const tarea = (page: Page, id: string) => page.getByTestId(`tarea-${id}`);

test.describe("Vista de olas y tareas (FE-03)", () => {
  test("muestra las olas, sus tareas y los indicadores de avance", async ({ page }) => {
    await abrir(page);

    await expect(page.getByTestId("ola-wave-001")).toBeVisible();
    await expect(page.getByTestId("ola-wave-002")).toBeVisible();
    await expect(tarea(page, "task-001")).toBeVisible();
    await expect(tarea(page, "task-002")).toBeVisible();
    await expect(tarea(page, "task-003")).toBeVisible();

    await expect(page.getByTestId("kpi-total")).toHaveText("3");
    await expect(page.getByTestId("kpi-completadas")).toHaveText("1");
    await expect(page.getByTestId("kpi-criticas")).toHaveText("1");
    await expect(page.getByTestId("kpi-porcentaje")).toHaveText("33 %");
    await expect(page.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "33");
    // El estado se comunica con texto, no solo con color.
    await expect(page.getByTestId("estado-task-001")).toContainText("Completada");
    await expect(page.getByTestId("estado-task-002")).toContainText("En progreso");
  });

  test("los filtros por estado, prioridad y área acotan las tareas visibles", async ({ page }) => {
    await abrir(page);
    await expect(page.getByTestId("total-visibles")).toContainText("3 tareas visibles");

    await page.getByLabel("Estado", { exact: true }).selectOption("completada");
    await expect(page.getByTestId("total-visibles")).toContainText("1 tarea visible");
    await expect(tarea(page, "task-001")).toBeVisible();
    await expect(tarea(page, "task-002")).toHaveCount(0);

    await page.getByLabel("Estado", { exact: true }).selectOption("todas");
    await page.getByLabel("Prioridad", { exact: true }).selectOption("alta");
    await expect(page.getByTestId("total-visibles")).toContainText("2 tareas visibles");
    await expect(tarea(page, "task-001")).toHaveCount(0);
    await expect(tarea(page, "task-002")).toBeVisible();
    await expect(tarea(page, "task-003")).toBeVisible();

    await page.getByLabel("Prioridad", { exact: true }).selectOption("media");
    await expect(page.getByTestId("total-visibles")).toContainText("0 tareas visibles");

    await page.getByLabel("Prioridad", { exact: true }).selectOption("todas");
    await page.getByLabel("Área", { exact: true }).selectOption({ label: "Asesoría Jurídica y Cumplimiento" });
    await expect(page.getByTestId("total-visibles")).toContainText("1 tarea visible");
    await expect(tarea(page, "task-003")).toBeVisible();

    await page.getByLabel("Estado", { exact: true }).selectOption("bloqueada");
    await expect(page.getByTestId("total-visibles")).toContainText("0 tareas visibles");
    await expect(page.getByText("Ninguna tarea coincide con los filtros elegidos.")).toBeVisible();
  });

  const MATRIZ: Array<{ rol: string; estado: boolean; editar: boolean; asignar: boolean; auditoria: boolean }> = [
    { rol: "implementador", estado: true, editar: true, asignar: false, auditoria: true },
    { rol: "coordinador", estado: false, editar: false, asignar: true, auditoria: true },
    { rol: "dpo", estado: false, editar: false, asignar: false, auditoria: true },
    { rol: "admin_organizacion", estado: false, editar: false, asignar: false, auditoria: true },
    { rol: "responsable_area", estado: false, editar: false, asignar: false, auditoria: false },
  ];

  for (const caso of MATRIZ) {
    test(`el rol ${caso.rol} ve solo las acciones que la matriz del PRD le permite`, async ({ page }) => {
      await abrir(page, `?rol=${caso.rol}&usuario=user-resp-01`);
      const card = tarea(page, "task-002");
      await expect(card).toBeVisible();

      const presente = async (nombre: string) => (await card.getByRole("button", { name: nombre }).count()) > 0;
      expect(await presente("Cambiar estado"), "cambiar estado").toBe(caso.estado);
      expect(await presente("Editar detalles"), "editar detalles").toBe(caso.editar);
      expect(await presente("Asignar responsable"), "asignar responsable").toBe(caso.asignar);
      expect(await presente("Ver auditoría"), "ver auditoría").toBe(caso.auditoria);
    });
  }

  test("un responsable de área solo ve las tareas de su área", async ({ page }) => {
    await abrir(page, "?rol=responsable_area&usuario=user-resp-01");

    await expect(tarea(page, "task-001")).toBeVisible();
    await expect(tarea(page, "task-002")).toBeVisible();
    await expect(tarea(page, "task-003")).toHaveCount(0);
    await expect(page.getByTestId("total-visibles")).toContainText("2 tareas visibles");
  });

  test("un responsable de área sin área asignada no ve tareas y se le explica por qué", async ({ page }) => {
    await abrir(page, "?rol=responsable_area&usuario=user-sin-area");

    await expect(page.getByTestId("total-visibles")).toContainText("0 tareas visibles");
    await expect(page.getByText("No tienes un área asignada, por eso no hay tareas que mostrar.")).toBeVisible();
  });

  test("el implementador cambia el estado y los indicadores se actualizan", async ({ page }) => {
    await abrir(page);
    const card = tarea(page, "task-002");

    await card.getByLabel(/Nuevo estado de/).selectOption("completada");
    await card.getByRole("button", { name: "Cambiar estado" }).click();

    await expect(page.getByTestId("estado-task-002")).toContainText("Completada");
    await expect(page.getByTestId("kpi-completadas")).toHaveText("2");
  });

  test("editar detalles valida el título y las fechas, y guarda los cambios", async ({ page }) => {
    await abrir(page);
    const card = tarea(page, "task-002");

    await card.getByRole("button", { name: "Editar detalles" }).click();
    const formulario = card.getByRole("form", { name: /Editar/ });

    await formulario.getByLabel("Título").fill("   ");
    await formulario.getByRole("button", { name: "Guardar cambios" }).click();
    await expect(card.getByText("El título no puede quedar vacío.")).toBeVisible();

    await formulario.getByLabel("Título").fill("Registro de actividades de tratamiento revisado");
    await formulario.getByLabel("Inicio").fill("2026-11-10");
    await formulario.getByLabel("Fin").fill("2026-11-01");
    await formulario.getByRole("button", { name: "Guardar cambios" }).click();
    await expect(card.getByText("La fecha de fin no puede ser anterior a la de inicio.")).toBeVisible();

    await formulario.getByLabel("Fin").fill("2026-12-01");
    await formulario.getByRole("button", { name: "Guardar cambios" }).click();
    await expect(card.getByRole("heading", { name: "Registro de actividades de tratamiento revisado" })).toBeVisible();
  });

  test("el coordinador asigna una tarea y no puede dejar el responsable en blanco", async ({ page }) => {
    await abrir(page, "?rol=coordinador&usuario=user-enc-01");
    const card = tarea(page, "task-002");

    await card.getByRole("button", { name: "Asignar responsable" }).click();
    await card.getByRole("button", { name: "Confirmar asignación" }).click();
    await expect(card.getByText("Indica el identificador de la persona responsable.")).toBeVisible();

    await card.getByLabel("Identificador de la persona responsable").fill("user-resp-01");
    await card.getByRole("button", { name: "Confirmar asignación" }).click();
    await expect(page.getByTestId("responsable-task-002")).toHaveText("user-resp-01");
  });

  test("un error de negocio al cambiar el estado muestra su código y la acción requerida", async ({ page }) => {
    await abrir(page, "?fallo=estado");
    const card = tarea(page, "task-002");

    await card.getByLabel(/Nuevo estado de/).selectOption("completada");
    await card.getByRole("button", { name: "Cambiar estado" }).click();

    const error = page.getByTestId("error-task-002");
    await expect(error).toContainText("La tarea cambió mientras la editabas.");
    await expect(error).toContainText("Código: TASK_STATE_CONFLICT");
    await expect(error).toContainText("Acción requerida: refresh_and_retry");
    await expect(page.getByTestId("estado-task-002")).toContainText("En progreso");
  });

  test("un error de negocio al asignar muestra su código y deja el responsable como estaba", async ({ page }) => {
    await abrir(page, "?rol=coordinador&usuario=user-enc-01&fallo=asignar");
    const card = tarea(page, "task-002");

    await card.getByRole("button", { name: "Asignar responsable" }).click();
    await card.getByLabel("Identificador de la persona responsable").fill("user-resp-01");
    await card.getByRole("button", { name: "Confirmar asignación" }).click();

    await expect(page.getByTestId("error-task-002")).toContainText("Código: TASK_STATE_CONFLICT");
    await expect(page.getByTestId("responsable-task-002")).toHaveText("user-impl-01");
  });

  test("el DPO consulta la auditoría de una tarea y puede ocultarla", async ({ page }) => {
    await abrir(page, "?rol=dpo&usuario=dpo-corp-01");
    const card = tarea(page, "task-001");

    await card.getByRole("button", { name: "Ver auditoría" }).click();
    const auditoria = card.getByRole("region", { name: /Auditoría de/ });
    await expect(auditoria).toBeVisible();
    await expect(auditoria).toContainText("status_changed");

    await card.getByRole("button", { name: "Ocultar auditoría" }).click();
    await expect(auditoria).toHaveCount(0);
  });

  test("si la hoja de ruta no existe se muestra el error de carga con su código", async ({ page }) => {
    await page.goto(`${RUTA}?roadmap=rm-inexistente`);

    await expect(page.getByTestId("error-carga")).toBeVisible();
    await expect(page.getByText("Código: ROADMAP_NOT_FOUND")).toBeVisible();
  });

  test("ninguna pantalla muestra tokens de gobernanza", async ({ page }) => {
    await abrir(page);
    const texto = await page.locator("body").innerText();
    expect(texto).not.toMatch(/[¤¦]/);
  });
});
