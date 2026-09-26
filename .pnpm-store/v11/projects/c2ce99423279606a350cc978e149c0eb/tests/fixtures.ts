/**
 * Fixtures reutilizables para tests de LOPDP 360.
 * Patrón importado de PDA: fixtures reales en lugar de mocks.
 *
 * Uso:
 * ```typescript
 * import { createTestProject, createTestAssessment } from "./fixtures";
 *
 * test("assessment calcula nivel", async ({ page }) => {
 *   const project = await createTestProject();
 *   const assessment = await createTestAssessment(project, { coverage: 0.45 });
 *   expect(assessment.level).toBe("Nivel 1");
 * });
 * ```
 */
import { expect, type Page } from "@playwright/test";
import {
  abrirAppLimpia,
  configurarProyecto,
  irASala,
  responderControlActual,
} from "./utiles";

/**
 * Configuración de proyecto de prueba.
 */
export interface TestProjectConfig {
  name?: string;
  normativa?: string;
  industria?: string;
}

/**
 * Configuración de assessment de prueba.
 */
export interface TestAssessmentConfig {
  controlsToAnswer?: number;
  responseState?: "Conforme" | "Parcial" | "No Conforme";
  coverage?: number; // 0-1
}

/**
 * Proyecto de prueba inicializado.
 */
export interface TestProject {
  name: string;
  normativa: string;
  isConfigured: boolean;
}

/**
 * Assessment de prueba.
 */
export interface TestAssessment {
  level: string;
  coverage: number;
  hasDiscrepancy: boolean;
  applicableControls: number;
  answeredControls: number;
}

/**
 * Crea un proyecto de prueba limpio con configuración por defecto.
 * Similar a PDA: fixture real que deja estado persistente en localStorage.
 */
export async function createTestProject(
  page: Page,
  config: TestProjectConfig = {}
): Promise<TestProject> {
  const {
    name = "Entidad de Prueba S.A.",
    normativa = "LOPDP",
    industria = "Finance",
  } = config;

  // Abrir app limpia
  await abrirAppLimpia(page);

  // Ir a Ficha Organizacional
  await irASala(page, /Ficha Organizacional/);

  // Completar datos
  await page.getByRole("textbox", { name: /Razón Social/ }).fill(name);

  // Guardar
  await page.getByRole("button", { name: /Guardar Configuración/ }).click();
  await expect(page.getByText(/Configuración guardada/)).toBeVisible();

  return {
    name,
    normativa,
    isConfigured: true,
  };
}

/**
 * Crea un assessment con un número específico de respuestas.
 * Simula evaluación de controles.
 */
export async function createTestAssessment(
  page: Page,
  config: TestAssessmentConfig = {}
): Promise<TestAssessment> {
  const {
    controlsToAnswer = 5,
    responseState = "Conforme",
    coverage,
  } = config;

  // Ir al Diagnóstico LOPDP
  await irASala(page, /Diagnóstico LOPDP/);

  // Responder N controles
  for (let i = 0; i < controlsToAnswer; i++) {
    try {
      await responderControlActual(page, responseState);

      // Avanzar al siguiente control (si existe)
      const nextBtn = page.getByRole("button", { name: /Siguiente/ });
      if (await nextBtn.isVisible().catch(() => false)) {
        await nextBtn.click();
      } else {
        break;
      }
    } catch (error) {
      console.log(`No hay más controles (respondidos: ${i})`);
      break;
    }
  }

  // Ir al Dashboard para verificar resultado
  await irASala(page, /Dashboard Central/);

  // Extraer información del assessment
  const levelText = await page
    .getByText(/Nivel [0-5]/)
    .first()
    .innerText()
    .catch(() => "Nivel 0");

  const levelMatch = levelText.match(/(\d)/);
  const level = levelMatch ? `Nivel ${levelMatch[1]}` : "Sin Evaluación";

  const coverageMatch = await page
    .getByText(/^\d+(\.\d+)?%$/)
    .innerText()
    .then((t) => parseFloat(t))
    .catch(() => 0);

  const hasDiscrepancy = await page
    .getByText(/Discrepancia detectada|sin evaluación suficiente/)
    .isVisible()
    .catch(() => false);

  return {
    level,
    coverage: coverageMatch || coverage || 0,
    hasDiscrepancy,
    applicableControls: 0, // TODO: extraer del UI
    answeredControls: controlsToAnswer,
  };
}

/**
 * Limpia un proyecto para que vuelva a estado inicial.
 * Útil para tests que necesitan resetear estado.
 */
export async function resetTestProject(page: Page): Promise<void> {
  await page.getByRole("button", { name: "Archivo", exact: true }).click();
  await page.getByRole("menuitem", { name: "Nuevo" }).click();
  await expect(page.getByText("Nuevo proyecto creado")).toBeVisible();
}

/**
 * Fixture para obtener el panel de assessment directamente.
 */
export async function getAssessmentPanel(page: Page) {
  return page.locator('section[aria-labelledby="assessment-story-title"]');
}

/**
 * Helper para esperar a que la app esté completamente lista (store hidratado).
 */
export async function waitForAppReady(page: Page, timeout = 30000): Promise<void> {
  await expect(
    page.getByRole("button", { name: /Dashboard Central/ })
  ).toBeVisible({ timeout });

  // Esperar a que el store se hidrate
  await irASala(page, /Ficha Organizacional/);
  await expect(
    page.getByRole("textbox", { name: /Razón Social/ })
  ).toHaveValue(/.+/);
}
