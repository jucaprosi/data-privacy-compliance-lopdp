// ¤adpa ¤rbac-tenant
// ¤¤qa-engineer
/**
 * BIB-401 · Plantillas de la cuenta profesional (pestaña «Plantillas»).
 *
 * Verifica:
 * 1. La pestaña «Plantillas» muestra copias con su estado y distintivo.
 * 2. Con una copia desactualizada, se visualiza el distintivo 'Desactualizada' y el botón «Comparar con la maestra».
 * 3. Al pulsar «Comparar», se abre el diálogo modal con el diff unificado de la maestra vigente.
 * 4. Al pulsar «Aplicar», se actualiza la copia a estado vigente.
 * 5. Si el usuario no tiene rol 'implementador' (ej. 'dpo'), la sección de cuenta profesional no se muestra.
 */
import { expect, test, type Page, type Route } from "@playwright/test";
import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

const ORGANIZACION = "org-prueba-bib401";
const RUTA_ROLES = "**/api/v1/organizacion/me/roles**";
const RUTA_CUENTA = "**/api/v1/biblioteca/plantillas-cuenta**";
const RUTA_DIFF = "**/api/v1/biblioteca/plantillas-cuenta/*/diff**";
const RUTA_APLICAR = "**/api/v1/biblioteca/plantillas-cuenta/*/aplicar-maestra**";

const COPIA_DESACTUALIZADA = {
  id: "copia-001",
  cuenta_id: "user-imp",
  maestra_codigo: "BIB-001",
  maestra_version: "1.0",
  contenido_key: "# Plantilla original v1.0",
  marca: { logo: "test-logo.png" },
  estado: "desactualizada",
  creado_por: "user-imp",
  creado_en: "2026-11-01T10:00:00Z",
  actualizado_en: "2026-11-01T10:00:00Z",
};

async function abrirSeccionPlantillas(
  page: Page,
  roles: string[] = ["implementador"],
  copias: typeof COPIA_DESACTUALIZADA[] = [COPIA_DESACTUALIZADA],
  estadoLista = 200,
) {
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, ORGANIZACION);

  // Fallback para rutas generales
  await page.route("**/api/v1/**", (ruta) =>
    ruta.fulfill({ status: 404, json: {} }),
  );

  // Mock de roles del usuario
  await page.route(RUTA_ROLES, (ruta) =>
    ruta.fulfill({
      status: 200,
      json: { user_id: "user-imp", tenant_id: ORGANIZACION, roles },
    }),
  );

  // Mock de plantillas de cuenta
  await page.route(RUTA_CUENTA, (ruta) => {
    if (ruta.request().method() === "GET") {
      if (estadoLista !== 200) return ruta.fulfill({ status: estadoLista, json: { detail: "texto interno del servidor" } });
      return ruta.fulfill({ status: 200, json: copias });
    }
    return ruta.fulfill({ status: 201, json: COPIA_DESACTUALIZADA });
  });

  // Mock de diff
  await page.route(RUTA_DIFF, (ruta) =>
    ruta.fulfill({
      status: 200,
      json: {
        maestra_vigente: "2.0",
        cambios: [
          "--- cuenta/BIB-001 (v1.0)",
          "+++ maestra/BIB-001 (v2.0)",
          "@@ -1,1 +1,1 @@",
          "-# Plantilla original v1.0",
          "+# Plantilla mejorada v2.0",
        ],
      },
    }),
  );

  // Mock de aplicar
  await page.route(RUTA_APLICAR, (ruta) =>
    ruta.fulfill({
      status: 200,
      json: {
        ...COPIA_DESACTUALIZADA,
        maestra_version: "2.0",
        estado: "vigente",
      },
    }),
  );

  await abrirAppLimpia(page);
  await configurarProyecto(page, "Entidad BIB-401");
  await barraDeMenus(page).getByRole("button", { name: "Biblioteca", exact: true }).click();
  await page
    .getByRole("group", { name: "Submenús de Biblioteca" })
    .getByRole("button", { name: /^Documentos y plantillas/ })
    .click();
  const vista = page.getByRole("region", { name: "Biblioteca", exact: true });
  await vista.getByRole("tab", { name: "Plantillas" }).click();
  return vista;
}

test.describe("Biblioteca: plantillas de la cuenta profesional (BIB-401)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "produccion", "El gancho de prueba no existe en producción.");
  });

  test("Con una copia desactualizada se ve la etiqueta, se compara y se aplica", async ({ page }) => {
    const vista = await abrirSeccionPlantillas(page);
    const seccion = vista.getByRole("region", { name: "Plantillas de tu cuenta profesional" });
    await expect(seccion).toBeVisible();

    const tarjeta = seccion.getByTestId("plantilla-cuenta-BIB-001");
    await expect(tarjeta.getByTestId("badge-desactualizada")).toContainText("Desactualizada");
    await expect(tarjeta).toContainText("basada en la versión 1.0 de la maestra");
    await expect(tarjeta.getByRole("button", { name: "Aplicar la maestra vigente a BIB-001" })).toBeVisible();

    const comparar = tarjeta.getByRole("button", { name: "Comparar BIB-001 con la maestra" });
    await comparar.click();
    const modal = page.getByRole("dialog");
    await expect(modal).toBeVisible();
    await expect(modal.getByTestId("contenedor-diff")).toContainText("Plantilla mejorada v2.0");
    await expect(modal.getByRole("button", { name: "Cerrar la comparación" })).toBeFocused();

    // Escape cierra y devuelve el foco al botón que lo abrió.
    await page.keyboard.press("Escape");
    await expect(modal).toHaveCount(0);
    await expect(comparar).toBeFocused();

    // Aplicar desde el modal.
    await comparar.click();
    await page.getByTestId("boton-confirmar-aplicar-maestra").click();
    await expect(modal).toHaveCount(0);
  });

  test("Si el servidor falla se muestra un mensaje fijo, nunca el texto del servidor", async ({ page }) => {
    const vista = await abrirSeccionPlantillas(page, ["implementador"], [COPIA_DESACTUALIZADA], 500);
    const seccion = vista.getByRole("region", { name: "Plantillas de tu cuenta profesional" });
    await expect(seccion.getByRole("alert")).toHaveText("No pudimos cargar tus plantillas. Inténtalo de nuevo.");
  });

  test("Un usuario con rol 'dpo' no visualiza la sección de plantillas de cuenta", async ({ page }) => {
    const vista = await abrirSeccionPlantillas(page, ["dpo"]);
    await expect(vista.getByRole("region", { name: "Plantillas de tu cuenta profesional" })).toHaveCount(0);
  });
});
