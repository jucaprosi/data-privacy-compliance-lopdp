/**
 * Arnés de interfaz de FE-06: integración de la Hoja de Ruta en el panel.
 *
 * Abre el tablero real, configura un proyecto y entra en la pestaña «Hoja de Ruta». El servidor
 * se simula con page.route sobre /api/v1/**: el navegador llama a esa ruta antes de que Next la
 * reenvíe al backend. Cada prueba registra las llamadas que hace la interfaz.
 *
 * FE-26: el PMV no ofrece la «Custodia de Evidencias»; estas pruebas fijan el caso por omisión. Los
 * casos de custodia física (EVYDENTIA) están en `integracion-activa.spec.ts`, y el panel simulado,
 * compartido, en `panel.ts`.
 */
import { expect, test } from "@playwright/test";

import { entrarEnHojaDeRuta, prepararApi, ruta, subvista, type Rol } from "./panel";

const SUBVISTAS_POR_ROL: Array<{ rol: Rol; generar: boolean; administrar: boolean }> = [
  { rol: "implementador", generar: true, administrar: false },
  { rol: "admin_organizacion", generar: false, administrar: true },
  { rol: "coordinador", generar: false, administrar: false },
  { rol: "dpo", generar: false, administrar: false },
  { rol: "responsable_area", generar: false, administrar: false },
];

test.describe("Integración de la Hoja de Ruta en el panel (FE-06)", () => {
  for (const caso of SUBVISTAS_POR_ROL) {
    test(`el rol ${caso.rol} ve solo las subvistas que le corresponden`, async ({ page }) => {
      await prepararApi(page, { roles: [caso.rol] });
      await entrarEnHojaDeRuta(page);

      await expect(subvista(page, "Olas & Tareas")).toBeVisible();
      // === FE-26 ===
      await expect(subvista(page, "Custodia de Evidencias")).toHaveCount(0);
      // === fin FE-26 ===
      expect(await subvista(page, "Generar Hoja de Ruta").count() > 0, "generar").toBe(caso.generar);
      expect(await subvista(page, "Administración").count() > 0, "administración").toBe(caso.administrar);
    });
  }

  test("navega entre las subvistas y monta cada pantalla", async ({ page }) => {
    await prepararApi(page, { roles: ["implementador"] });
    await entrarEnHojaDeRuta(page);

    await subvista(page, "Generar Hoja de Ruta").click();
    await expect(page.getByRole("form", { name: "Variables de planeación" })).toBeVisible();

    // === FE-26 ===
    // La subvista de custodia solo existe con la evidencia física (integracion-activa.spec.ts).
    await subvista(page, "Olas & Tareas").click();
    await expect(page.getByTestId("roadmap-sin-hoja")).toBeVisible();
    // === fin FE-26 ===
  });

  test("el administrador abre la administración de la organización", async ({ page }) => {
    await prepararApi(page, { roles: ["admin_organizacion"] });
    await entrarEnHojaDeRuta(page);

    await subvista(page, "Administración").click();
    await expect(page.getByRole("region", { name: "Administración de la organización" })).toBeVisible();
    await expect(page.getByRole("tablist", { name: "Secciones de administración" })).toBeVisible();
  });

  test("con varios roles ofrece elegir con cuál actúa y las subvistas cambian con él", async ({ page }) => {
    await prepararApi(page, { roles: ["coordinador", "implementador"] });
    await entrarEnHojaDeRuta(page);

    const selector = page.getByLabel("Seleccionar rol activo");
    await expect(selector).toBeVisible();
    await expect(subvista(page, "Generar Hoja de Ruta")).toHaveCount(0);

    await selector.selectOption("implementador");
    await expect(subvista(page, "Generar Hoja de Ruta")).toBeVisible();
    await subvista(page, "Generar Hoja de Ruta").click();
    // Actuando como implementador, el formulario deja de estar en solo lectura.
    await expect(page.getByRole("button", { name: "Generar hoja de ruta", exact: true })).toBeEnabled();

    await selector.selectOption("coordinador");
    await expect(subvista(page, "Generar Hoja de Ruta")).toHaveCount(0);
  });

  test("sin roles asignados explica el motivo y no ofrece subvistas", async ({ page }) => {
    await prepararApi(page, { roles: [] });
    await entrarEnHojaDeRuta(page);

    await expect(page.getByText("Sin asignación de roles en la organización.")).toBeVisible();
    await expect(page.getByText("Rol: sin verificar")).toBeVisible();
    await expect(subvista(page, "Olas & Tareas")).toHaveCount(0);
  });

  test("si no se puede resolver la identidad, muestra la causa y NO llama al resto de la API", async ({ page }) => {
    const llamadas = await prepararApi(page, { roles: 503 });
    await entrarEnHojaDeRuta(page);

    await expect(page.getByText("No se pudo verificar tu rol en la organización.")).toBeVisible();
    await expect(page.getByText(/Causa:/)).toBeVisible();
    // Sin roles confirmados no se muestra el rol de relleno (antes decía «responsable_area»).
    await expect(page.getByText("Rol: sin verificar")).toBeVisible();
    await expect(subvista(page, "Olas & Tareas")).toHaveCount(0);

    // El tablero consulta por su cuenta otros módulos (por ejemplo /preanalisis/estado): lo que
    // exige la especificación es no llamar al resto de la API de la Hoja de Ruta ni de Organización.
    const delModulo = llamadas.map((l) => ruta(l.url())).filter((d) => d.startsWith("/roadmaps") || d.startsWith("/organizacion"));
    expect(delModulo.length).toBeGreaterThan(0);
    expect([...new Set(delModulo)], "llamadas de Hoja de Ruta y Organización").toEqual(["/organizacion/me/roles"]);
  });

  test("sin hoja de ruta cargada no pide datos de demostración al servidor", async ({ page }) => {
    const llamadas = await prepararApi(page, { roles: ["implementador"] });
    await entrarEnHojaDeRuta(page);

    await expect(page.getByTestId("roadmap-sin-hoja")).toBeVisible();
    await expect(page.getByTestId("roadmap-sin-hoja")).toContainText("Generar Hoja de Ruta");

    const destinos = llamadas.map((l) => ruta(l.url()));
    expect(destinos.filter((d) => d.includes("rm-demo-001") || d.includes("task-001"))).toEqual([]);
    expect(destinos.filter((d) => d.startsWith("/roadmaps"))).toEqual([]);
  });

  test("con una hoja de ruta cargada pide esa y no otra", async ({ page }) => {
    const llamadas = await prepararApi(page, { roles: ["implementador"], roadmapId: "rm-real-77" });
    await entrarEnHojaDeRuta(page);

    await expect.poll(() => llamadas.some((l) => ruta(l.url()).startsWith("/roadmaps/rm-real-77"))).toBe(true);
    const demo = llamadas.map((l) => ruta(l.url())).filter((d) => d.includes("rm-demo-001"));
    expect(demo).toEqual([]);
  });

  test("ninguna pantalla muestra tokens de gobernanza", async ({ page }) => {
    await prepararApi(page, { roles: ["admin_organizacion", "implementador"] });
    await entrarEnHojaDeRuta(page);

    // === FE-26 ===
    for (const nombre of ["Olas & Tareas"]) {
    // === fin FE-26 ===
      await subvista(page, nombre).click();
      const texto = await page.locator("main, body").first().innerText();
      expect(texto, nombre).not.toMatch(/[¤¦]/);
    }
  });
});
