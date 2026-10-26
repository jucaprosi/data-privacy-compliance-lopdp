/**
 * MTGE-02: panel de obligaciones de gran escala en la sala «Riesgos & MTGE».
 *
 * Simula `/api/v1/riesgos/mtge/obligaciones` y exige que el panel se vea:
 * 1. Sin gran escala: aviso informativo y obligaciones «No aplica».
 * 2. Con gran escala: estados, artículo citado y acción siguiente.
 * 3. Rol sin permiso (403): el panel no se muestra ni muestra error.
 */
import { expect, test, type Page } from "@playwright/test";
import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const RUTA_OBLIGACIONES = "**/api/v1/riesgos/mtge/obligaciones";

const NO_APLICA = {
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
  ],
};

const CON_GRAN_ESCALA = {
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
      obligacion: "Privacidad desde el diseño y por defecto",
      articulo_fuente: "Art. 16 Res. SPDP-SPD-2026-0005-R",
      estado: "RECORDATORIO",
      descripcion: "Obligación permanente.",
      accion_siguiente: "Verificar medidas preventivas.",
    },
  ],
};

async function abrirSala(page: Page, respuesta: { status?: number; json?: unknown }) {
  await page.route(RUTA_OBLIGACIONES, (route) => route.fulfill(respuesta));
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Riesgos & MTGE/i);
}

test.describe("Obligaciones de Gran Escala (MTGE-02)", () => {
  test("sin gran escala: aviso y obligaciones «No aplica»", async ({ page }) => {
    await abrirSala(page, { json: NO_APLICA });
    await expect(page.getByTestId("mtge-no-gran-escala-banner")).toBeVisible();
    await expect(page.getByTestId("mtge-estado-0")).toHaveText(/No aplica/i);
  });

  test("con gran escala: estado, artículo y recordatorio del art. 16", async ({ page }) => {
    await abrirSala(page, { json: CON_GRAN_ESCALA });
    await expect(page.getByTestId("mtge-gran-escala-banner")).toContainText("2");
    await expect(page.getByTestId("mtge-estado-0")).toHaveText(/Vencida/i);
    await expect(page.getByTestId("mtge-estado-1")).toHaveText(/Recordatorio/i);
    await expect(page.getByText("Art. 17 Res. SPDP-SPD-2026-0005-R")).toBeVisible();
  });

  test("rol sin permiso: el panel no aparece", async ({ page }) => {
    await abrirSala(page, { status: 403, json: { detail: "Forbidden" } });
    await expect(page.getByRole("heading", { name: /Calculadora|gran escala/i }).first()).toBeVisible();
    await expect(page.getByLabel("Obligaciones del tratamiento a gran escala")).toHaveCount(0);
    await expect(page.getByText("Error al consultar obligaciones")).toHaveCount(0);
  });
});
