/**
 * Utilidades compartidas del arnés de interfaz.
 *
 * El estado del proyecto vive en localStorage, así que cada spec tiene que
 * partir de cero: un test que hereda la sesión del anterior comprueba el
 * arrastre, no la regla.
 */
import { expect, type Page } from "@playwright/test";

// Importar nuevas utilidades (inspiradas en ERP, Jubilo Pl, PDA)
export { ConsoleSentinel } from "./consoleSentinel";
export { AuditTrail, type ClickEntry, type SnapshotMetadata } from "./auditTrail";
export { LocatorResolver, L } from "./locatorResolver";

// Fixtures reales (inspiradas en PDA)
export {
  createTestProject,
  createTestAssessment,
  resetTestProject,
  getAssessmentPanel,
  waitForAppReady,
  type TestProjectConfig,
  type TestAssessmentConfig,
  type TestProject,
  type TestAssessment,
} from "./fixtures";

// Test Data Builders (patrón de PDA)
export {
  ProjectBuilder,
  ControlBuilder,
  AssessmentBuilder,
  ControlSetBuilder,
  TestScenario,
  type ProjectData,
  type ControlData,
  type AssessmentResultData,
} from "./testDataBuilder";

/** Claves de persistencia del store; se limpian antes de que la app arranque. */
const CLAVES_PERSISTENCIA = ["jubys-audit-storage", "jubys-proyectos-v1"];

/**
 * Abre la aplicación sobre un proyecto nuevo y vacío.
 *
 * Son dos limpiezas distintas y ambas hacen falta. Borrar localStorage descarta
 * la sesión anterior, pero el estado inicial del store trae un cuestionario de
 * referencia ya respondido; sin descartarlo, la cobertura arrancaría al 100 % y
 * ningún spec podría medir lo que él mismo responde. «Archivo › Nuevo» es la
 * vía que la propia aplicación ofrece para eso.
 */
export async function abrirAppLimpia(page: Page): Promise<void> {
  await page.addInitScript((claves: string[]) => {
    try {
      for (const clave of claves) window.localStorage.removeItem(clave);
    } catch {
      // Un navegador con almacenamiento bloqueado ya arranca limpio.
    }
  }, CLAVES_PERSISTENCIA);
  await page.goto("/");
  await expect(page.getByRole("button", { name: /Dashboard Central/ })).toBeVisible();

  // Hasta que el store se hidrata, la ficha se dibuja como esqueleto y descarta
  // lo que se escriba en ella. El campo con su valor por defecto ya cargado es
  // la señal de que la hidratación terminó; interactuar antes produce fallos
  // intermitentes que no corresponden a ningún defecto del producto.
  await irASala(page, /Ficha Organizacional/);
  await expect(page.getByRole("textbox", { name: /Razón Social/ })).toHaveValue(/.+/);

  await page.getByRole("button", { name: "Archivo", exact: true }).click();
  await page.getByRole("menuitem", { name: "Nuevo" }).click();
  await expect(page.getByText("Nuevo proyecto creado")).toBeVisible();
}

/** Navega por la barra lateral a una sala operativa. */
export async function irASala(page: Page, nombre: RegExp): Promise<void> {
  await page.getByRole("button", { name: nombre }).click();
}

/**
 * Completa la ficha organizacional y guarda la configuración.
 *
 * Sin este paso el tablero no calcula nada, así que casi todos los specs
 * empiezan aquí.
 */
export async function configurarProyecto(
  page: Page,
  razonSocial = "Entidad de Prueba S.A."
): Promise<void> {
  await irASala(page, /Ficha Organizacional/);

  // La normativa por defecto (LOPDP) ya habilita el banco de preguntas, así que
  // la ficha solo necesita la razón social para poder guardarse.
  await page.getByRole("textbox", { name: /Razón Social/ }).fill(razonSocial);

  await page.getByRole("button", { name: /Guardar Configuración/ }).click();
  await expect(page.getByText(/Configuración guardada/)).toBeVisible();
}

/** Responde el control que el cuestionario tenga en pantalla. */
export async function responderControlActual(
  page: Page,
  estado: "Conforme" | "Parcial" | "No Conforme"
): Promise<void> {
  const opcion = page.getByRole("button", { name: estado, exact: true });
  await opcion.click();
  await expect(opcion).toHaveAttribute("aria-pressed", "true");
}

/** Panel de resultados del assessment dentro del tablero. */
export function panelAssessment(page: Page) {
  return page.locator('section[aria-labelledby="assessment-story-title"]');
}
