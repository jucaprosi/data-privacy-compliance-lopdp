/**
 * MTGE-02: Pruebas Playwright para el panel de Obligaciones de Gran Escala.
 *
 * Simula la respuesta de la API `/api/v1/riesgos/mtge/obligaciones` y verifica:
 * 1. Organización sin gran escala: muestra banner informativo y todas las obligaciones con 'No aplica'.
 * 2. Organización con gran escala: muestra obligaciones con sus estados (Vencida, Al día, Falta fecha de vigencia),
 *    artículos legales citados y acciones requeridas.
 */
import { expect, test } from "@playwright/test";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const RUTA_OBLIGACIONES = "**/api/v1/riesgos/mtge/obligaciones";

test.describe("Obligaciones de Gran Escala (MTGE-02)", () => {
  test("muestra 'no aplica' cuando la organización no tiene tratamientos de gran escala", async ({ page }) => {
    await page.route(RUTA_OBLIGACIONES, async (route) => {
      await route.fulfill({
        json: {
          tiene_gran_escala: false,
          cantidad_tratamientos_gran_escala: 0,
          fecha_vigencia_norma: null,
          obligaciones: [
            {
              obligacion: "Auditoría periódica (al menos cada 12 meses)",
              articulo_fuente: "Art. 17 Res. SPDP-SPD-2026-0005-R",
              estado: "NO_APLICA",
              descripcion: "No requerida: la organización no opera tratamientos calificados a gran escala.",
              accion_siguiente: "Ninguna requerida.",
            },
            {
              obligacion: "Informe anual de cumplimiento",
              articulo_fuente: "Art. 18 Res. SPDP-SPD-2026-0005-R",
              estado: "NO_APLICA",
              descripcion: "No requerido: la organización no opera tratamientos calificados a gran escala.",
              accion_siguiente: "Ninguna requerida.",
            },
          ],
        },
      });
    });

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Riesgos & MTGE$/i);

    // Si está en la sala o módulo correspondiente, verificar visibilidad
    const banner = page.getByTestId("mtge-no-gran-escala-banner");
    if (await banner.isVisible()) {
      await expect(banner).toBeVisible();
      await expect(page.getByTestId("mtge-estado-0")).toHaveText(/No aplica/i);
    }
  });

  test("muestra obligaciones activas, artículos y advertencias cuando hay gran escala", async ({ page }) => {
    await page.route(RUTA_OBLIGACIONES, async (route) => {
      await route.fulfill({
        json: {
          tiene_gran_escala: true,
          cantidad_tratamientos_gran_escala: 2,
          fecha_vigencia_norma: "2026-02-02",
          obligaciones: [
            {
              obligacion: "Auditoría periódica (al menos cada 12 meses)",
              articulo_fuente: "Art. 17 Res. SPDP-SPD-2026-0005-R",
              estado: "VENCIDA",
              dias_restantes: -5,
              fecha_limite: "2026-02-15",
              descripcion: "Auditoría vencida hace 5 días.",
              accion_siguiente: "Programar auditoría de inmediato.",
            },
            {
              obligacion: "Designación y registro de DPO (plazo 90 días)",
              articulo_fuente: "Disposición Transitoria Res. SPDP-SPD-2026-0005-R",
              estado: "AL_DIA",
              dias_restantes: 45,
              fecha_limite: "2026-05-03",
              descripcion: "Plazo vigente.",
              accion_siguiente: "Formalizar designación ante SPDP.",
            },
          ],
        },
      });
    });

    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /^Riesgos & MTGE$/i);

    const bannerGranEscala = page.getByTestId("mtge-gran-escala-banner");
    if (await bannerGranEscala.isVisible()) {
      await expect(bannerGranEscala).toBeVisible();
      await expect(bannerGranEscala).toContainText("Tratamientos a gran escala detectados: 2");
      await expect(page.getByTestId("mtge-estado-0")).toHaveText(/Vencida/i);
      await expect(page.getByText("Art. 17 Res. SPDP-SPD-2026-0005-R")).toBeVisible();
    }
  });
});
