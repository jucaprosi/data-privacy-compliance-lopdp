// ¤adpa ¤rbac-tenant
// ¤¤qa-engineer
/**
 * BIB-401 · Plantillas de la cuenta profesional (pestaña «Mi cuenta»).
 *
 * Verifica:
 * 1. La pestaña «Mi cuenta» muestra copias con su estado y distintivo.
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
) {
  await page.addInitScript((tenant) => {
    window.__LOPDP_AUTH_PRUEBAS__ = { modo: "headers", tenant };
  }, ORGANIZACION);

  // Fallback para rutas generales
  await page.route("**/api/v1/**", (ruta) =>
    ruta.fulfill({ status: 200, json: [] }),
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

  test("Dado la pestaña «Mi cuenta» con una copia desactualizada, entonces se ve el distintivo y el botón «Comparar»", async ({
    page,
  }) => {
    const vista = await abrirSeccionPlantillas(page, ["implementador"], [COPIA_DESACTUALIZADA]);

    // Verificar pestaña y contenedor de Mi cuenta
    const contenedor = vista.getByTestId("vista-plantillas-cuenta");
    await expect(contenedor).toBeVisible();
    await expect(contenedor.getByTestId("pestana-mi-cuenta")).toBeVisible();

    // Comprobar la tarjeta de la plantilla desactualizada
    const tarjeta = contenedor.getByTestId("plantilla-cuenta-BIB-001");
    await expect(tarjeta).toBeVisible();
    await expect(tarjeta.getByTestId("badge-desactualizada")).toContainText("Desactualizada");
    await expect(tarjeta.getByTestId("boton-comparar-BIB-001")).toBeVisible();
    await expect(tarjeta.getByTestId("boton-aplicar-BIB-001")).toBeVisible();

    // Pulsar comparar y verificar diálogo de diff
    await tarjeta.getByTestId("boton-comparar-BIB-001").click();
    const modal = page.getByTestId("modal-diff-maestra");
    await expect(modal).toBeVisible();
    await expect(modal).toContainText("v2.0");
    await expect(modal.getByTestId("contenedor-diff")).toContainText("Plantilla mejorada v2.0");
  });

  test("Un usuario con rol 'dpo' no visualiza la sección de plantillas de cuenta", async ({ page }) => {
    const vista = await abrirSeccionPlantillas(page, ["dpo"], [COPIA_DESACTUALIZADA]);
    await expect(vista.getByTestId("vista-plantillas-cuenta")).toHaveCount(0);
  });
});
