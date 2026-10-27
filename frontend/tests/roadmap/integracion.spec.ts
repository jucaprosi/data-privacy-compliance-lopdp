/**
 * Arnés de interfaz de FE-06: integración de la Hoja de Ruta en el panel.
 *
 * Abre el tablero real, configura un proyecto y entra en la pestaña «Hoja de Ruta». El servidor
 * se simula con page.route sobre /api/v1/**: el navegador llama a esa ruta antes de que Next la
 * reenvíe al backend. Cada prueba registra las llamadas que hace la interfaz.
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import { abrirAppLimpia, irASala } from "../utiles";

type Rol = "responsable_area" | "coordinador" | "dpo" | "implementador" | "admin_organizacion";

interface Escenario {
  /** Respuesta de /organizacion/me/roles. Un número es un estado HTTP de error. */
  roles: Rol[] | number;
  /** Hoja de ruta con la que arranca el almacén persistido, si la hay. */
  roadmapId?: string;
}

const ruta = (url: string) => new URL(url).pathname.replace(/^\/api\/v1/, "");

async function prepararApi(page: Page, escenario: Escenario): Promise<Request[]> {
  const llamadas: Request[] = [];
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    llamadas.push(peticion);
    const destino = ruta(peticion.url());

    if (destino === "/organizacion/me/roles") {
      if (typeof escenario.roles === "number") {
        return route.fulfill({
          status: escenario.roles,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Servicio no disponible", code: "ORG_UNAVAILABLE", action_required: null }),
        });
      }
      const cuerpo = escenario.roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null }));
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(cuerpo) });
    }
    if (["/organizacion/usuarios", "/organizacion/areas", "/organizacion/roles"].includes(destino)) {
      return route.fulfill({ status: 200, contentType: "application/json", body: "[]" });
    }
    // Cualquier otra llamada al backend en estas pruebas es inesperada: se responde 404 y queda registrada.
    return route.fulfill({
      status: 404,
      contentType: "application/json",
      body: JSON.stringify({ detail: "No simulado", code: "NOT_MOCKED", action_required: null }),
    });
  });

  if (escenario.roadmapId) {
    await page.addInitScript((id: string) => {
      try {
        window.localStorage.setItem(
          "lopdp-roadmap-store-v1",
          JSON.stringify({ state: { currentRoadmapId: id, statusFilter: "todas", priorityFilter: "todas", areaFilter: "todas" }, version: 0 }),
        );
      } catch {
        // Sin almacenamiento, la prueba lo detectará al no ver la hoja de ruta.
      }
    }, escenario.roadmapId);
  }
  return llamadas;
}

/**
 * Completa la ficha del proyecto como lo exige la interfaz actual.
 *
 * No se usa configurarProyecto de ../utiles porque rellena solo la razón social, y desde que el
 * perfil de operación es obligatorio (commit c92490e) el botón «Guardar Ficha» sigue desactivado
 * hasta responder todas sus preguntas Sí/No. Ese helper compartido no es de esta tarea; el resto del
 * flujo (guardar, elegir normativa, cerrar la alerta de la primera pregunta) es el mismo.
 */
async function completarFicha(page: Page): Promise<void> {
  await page.getByRole("textbox", { name: /Razón Social/ }).fill("Entidad de Prueba S.A.");

  const grupos = page.getByRole("radiogroup");
  const total = await grupos.count();
  expect(total, "la ficha debe traer preguntas de perfil").toBeGreaterThan(0);
  for (let i = 0; i < total; i += 1) {
    await grupos.nth(i).getByRole("radio", { name: "No", exact: true }).check();
  }

  await page.getByRole("button", { name: /Guardar Ficha y Continuar/ }).click();
  await expect(page.getByText(/Ficha organizacional guardada/)).toBeVisible();
  await page.locator("#selector-normativa").selectOption("LOPDP");
  await page.getByRole("button", { name: "Cerrar alerta" }).click();
  await expect(page.getByRole("button", { name: /Dashboard Central/ })).toBeVisible();
}

async function entrarEnHojaDeRuta(page: Page): Promise<void> {
  await abrirAppLimpia(page);
  await completarFicha(page);
  await irASala(page, /^Hoja de Ruta/);
  await expect(page.getByRole("heading", { name: "Hoja de Ruta de Implementación" })).toBeVisible();
}

const subvista = (page: Page, nombre: string) => page.getByRole("button", { name: nombre, exact: true });

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
      await expect(subvista(page, "Custodia de Evidencias")).toBeVisible();
      expect(await subvista(page, "Generar Hoja de Ruta").count() > 0, "generar").toBe(caso.generar);
      expect(await subvista(page, "Administración").count() > 0, "administración").toBe(caso.administrar);
    });
  }

  test("navega entre las subvistas y monta cada pantalla", async ({ page }) => {
    await prepararApi(page, { roles: ["implementador"] });
    await entrarEnHojaDeRuta(page);

    await subvista(page, "Generar Hoja de Ruta").click();
    await expect(page.getByRole("form", { name: "Variables de planeación" })).toBeVisible();

    await subvista(page, "Custodia de Evidencias").click();
    await expect(page.getByTestId("roadmap-sin-tarea")).toBeVisible();
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

    await subvista(page, "Custodia de Evidencias").click();
    await expect(page.getByTestId("roadmap-sin-tarea")).toBeVisible();

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

    for (const nombre of ["Olas & Tareas", "Custodia de Evidencias"]) {
      await subvista(page, nombre).click();
      const texto = await page.locator("main, body").first().innerText();
      expect(texto, nombre).not.toMatch(/[¤¦]/);
    }
  });
});
