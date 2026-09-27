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
 *
 * La barra lateral arranca vacía hasta guardar la ficha organizacional
 * (`modulosNavegacion = !isConfigured ? [] : [...]` en dashboard/page.tsx), así
 * que "Dashboard Central" no existe todavía en este punto: la señal de
 * hidratación es el propio campo de la ficha, que es la vista con la que
 * arranca un proyecto sin configurar.
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

  // Hasta que el store se hidrata, la ficha se dibuja como esqueleto y descarta
  // lo que se escriba en ella. El campo con su valor por defecto ya cargado es
  // la señal de que la hidratación terminó; interactuar antes produce fallos
  // intermitentes que no corresponden a ningún defecto del producto.
  await expect(page.getByRole("textbox", { name: /Razón Social/ })).toHaveValue(/.+/);

  // "Archivo" vive en la cabecera y está disponible aunque el proyecto no
  // esté configurado todavía.
  await page.getByRole("button", { name: "Archivo", exact: true }).click();
  await page.getByRole("menuitem", { name: "Nuevo" }).click();
  await expect(page.getByText("Nuevo proyecto creado")).toBeVisible();
}

/** Navega por la barra lateral a una sala operativa. */
export async function irASala(page: Page, nombre: RegExp): Promise<void> {
  await page.getByRole("button", { name: nombre }).click();
}

/**
 * Completa la ficha organizacional, la guarda y elige la normativa LOPDP.
 *
 * Las tres cosas son necesarias para que la barra lateral deje de estar vacía:
 * sin ficha guardada no hay navegación, y sin normativa elegida el único
 * módulo disponible es "Normativa" (`!normativaSeleccionada → [moduloNormativa]`
 * en dashboard/page.tsx) — ni "Dashboard Central" ni el resto existen todavía.
 */
export async function configurarProyecto(
  page: Page,
  razonSocial = "Entidad de Prueba S.A."
): Promise<void> {
  // No hay que esperar hidratación aquí: abrirAppLimpia ya la esperó, y tras
  // "Archivo > Nuevo" el campo llega vacío a propósito (resetConfig() deja
  // razonSocial: ""), no con un valor previo que confirme que cargó.
  const campoRazonSocial = page.getByRole("textbox", { name: /Razón Social/ });
  await campoRazonSocial.fill(razonSocial);

  // handleGuardar() en ProjectConfig.tsx cambia de vista de forma síncrona
  // antes de que el fetch a /api/project/save resuelva: el componente que
  // mostraría "Ficha organizacional guardada" ya está desmontado cuando el
  // mensaje se fija, así que ese aviso no llega a pintarse nunca (defecto de
  // producto, no de este test). La señal de éxito real es la vista
  // siguiente: guardar la ficha deja la navegación en "Normativa", con el
  // selector visible.
  await page.getByRole("button", { name: /Guardar Ficha y Continuar/ }).click();
  await page.locator("#selector-normativa").selectOption("LOPDP");

  // La primera pregunta de D01 abre un <dialog> modal de "perspectiva
  // ejecutiva" (AlertaDimension.tsx, showModal()) que bloquea el resto de la
  // página hasta cerrarse; sin descartarlo, ningún clic posterior llega a su
  // destino real.
  await page.getByRole("button", { name: "Cerrar alerta" }).click();
  await expect(page.getByRole("button", { name: /Dashboard Central/ })).toBeVisible();
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
