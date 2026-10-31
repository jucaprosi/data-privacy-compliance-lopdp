/**
 * Arnés de interfaz de RM-22: vistas de lista, tablero y cronograma.
 *
 * Monta VistasTareas en /harness-roadmap/vistas contra el servidor simulado. Datos (fechas relativas a hoy):
 * task-001 completada; task-002 en progreso con origen «diagnóstico»; task-003 pendiente sin fechas;
 * task-vencida-1 (pendiente) y task-vencida-2 (en progreso) con fin ayer.
 *
 * Mutación documentada (cada una se aplicó, la prueba nombrada falló y se revirtió):
 *  - logica.ts esVencida: `!== "completada"` por `=== "completada"` → falla «vencidas».
 *  - VistasTareas.tsx: añadir `vista` a las dependencias de la lectura inicial → falla «una fuente».
 *  - VistasTareas.tsx: no pasar `origen` a la tarjeta → falla «origen».
 */
import { expect, test, type Page } from "@playwright/test";

const RUTA = "/harness-roadmap/vistas";

async function abrir(page: Page, consulta = ""): Promise<void> {
  await page.goto(`${RUTA}${consulta}`);
  await expect(page.getByRole("region", { name: "Vistas del plan de acción" })).toBeVisible();
}

const peticiones = (page: Page) => page.evaluate(() => (window as unknown as { __peticiones: string[] }).__peticiones);
const tarea = (page: Page, id: string) => page.getByTestId(`tarea-${id}`);
const IDS = ["task-001", "task-002", "task-003", "task-vencida-1", "task-vencida-2"];

test.describe("Vistas del plan de acción (RM-22)", () => {
  test("una fuente: las 5 tareas están en cada vista y cambiar de vista no vuelve a pedir datos", async ({ page }) => {
    await abrir(page);
    // El modo estricto de React en desarrollo monta el efecto dos veces: se cuenta desde la carga ya hecha.
    const lecturas = async () => (await peticiones(page)).filter((p) => /GET .*\/roadmaps\/rm-demo-001$/.test(p)).length;
    await expect(page.getByTestId("total-vistas")).toContainText("5 tareas");
    const antes = await lecturas();
    expect(antes).toBeGreaterThan(0);

    await expect(page.getByTestId("total-vistas")).toContainText("5 tareas");
    for (const id of IDS) await expect(tarea(page, id)).toBeVisible();

    await page.getByTestId("vista-tablero").click();
    for (const id of IDS) await expect(tarea(page, id)).toBeVisible();
    await expect(page.getByTestId("cuenta-pendiente")).toHaveText("(2)");
    await expect(page.getByTestId("cuenta-en_progreso")).toHaveText("(2)");
    await expect(page.getByTestId("cuenta-completada")).toHaveText("(1)");
    await expect(page.getByTestId("cuenta-bloqueada")).toHaveText("(0)");

    await page.getByTestId("vista-cronograma").click();
    for (const id of ["task-001", "task-002", "task-vencida-1", "task-vencida-2"]) {
      await expect(page.getByTestId(`barra-${id}`)).toBeVisible();
    }
    await expect(page.getByTestId("sinfecha-task-003")).toBeVisible();

    await page.getByTestId("vista-lista").click();
    await expect(tarea(page, "task-001")).toBeVisible();
    expect(await lecturas()).toBe(antes);
  });

  test("vencidas: el filtro deja las 2 tareas con fin ayer y el contador coincide", async ({ page }) => {
    await abrir(page);
    await expect(page.getByTestId("contador-vencidas")).toHaveText("2");

    await page.getByTestId("filtro-vencidas").click();
    await expect(page.getByTestId("total-vistas")).toContainText("2 tareas");
    await expect(tarea(page, "task-vencida-1")).toBeVisible();
    await expect(tarea(page, "task-vencida-2")).toBeVisible();
    await expect(tarea(page, "task-001")).toHaveCount(0);
    await expect(tarea(page, "task-002")).toHaveCount(0);

    await page.getByTestId("vista-tablero").click();
    await expect(page.getByTestId("cuenta-pendiente")).toHaveText("(1)");
    await expect(page.getByTestId("cuenta-en_progreso")).toHaveText("(1)");
  });

  test("origen: la tarjeta con hallazgo muestra «Origen: diagnóstico» y la demás no", async ({ page }) => {
    await abrir(page);
    await expect(page.getByTestId("origen-task-002")).toContainText("Origen: diagnóstico");
    await expect(page.getByTestId("origen-task-001")).toHaveCount(0);
  });

  test("la vista elegida se conserva al recargar", async ({ page }) => {
    await abrir(page);
    await page.getByTestId("vista-cronograma").click();
    await page.reload();
    await expect(page.getByTestId("vista-cronograma")).toHaveAttribute("aria-pressed", "true");
    await expect(page.getByTestId("barra-task-002")).toBeVisible();
  });

  test("tablero: arrastrar una tarjeta cambia su estado en el servidor", async ({ page }) => {
    await abrir(page);
    await page.getByTestId("vista-tablero").click();
    await tarea(page, "task-003").dragTo(page.getByTestId("columna-en_progreso"));
    await expect(page.getByTestId("columna-en_progreso").getByTestId("tarea-task-003")).toBeVisible();
    expect((await peticiones(page)).filter((p) => /^PATCH .*\/roadmaps\/tasks\/task-003$/.test(p))).toHaveLength(1);
  });

  test("tablero: si el cambio falla, la tarjeta vuelve a su columna y muestra el error", async ({ page }) => {
    await abrir(page, "?fallo=estado");
    await page.getByTestId("vista-tablero").click();
    await tarea(page, "task-003").dragTo(page.getByTestId("columna-en_progreso"));
    await expect(page.getByTestId("error-task-003")).toContainText("La tarea cambió mientras la movías.");
    await expect(page.getByTestId("columna-pendiente").getByTestId("tarea-task-003")).toBeVisible();
  });

  test("un rol sin permiso de cambiar estado no puede arrastrar", async ({ page }) => {
    await abrir(page, "?rol=dpo");
    await page.getByTestId("vista-tablero").click();
    await expect(page.getByTestId("tarea-task-003").locator("xpath=..")).toHaveAttribute("draggable", "false");
  });
});
