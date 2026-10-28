/**
 * Arnés de FE-20: los datos de trabajo del navegador pertenecen a quien los creó.
 *
 * Caso real (2026-10-26): quien entró después en el mismo navegador vio la ficha de otra
 * organización. Cada prueba recorre la interfaz: una persona llena la ficha, cierra la sesión y
 * entra otra. Google y la API se simulan (utilesAuth.ts).
 *
 * Prueba de mutación (FE-20): quitar la llamada a `reclamarDatosDeTrabajo` en `entrarEnOrganizacion`
 * (`store/datosDeTrabajo.ts`, que usa el inicio de sesión desde FE-21) hace
 * fallar las tres primeras pruebas (llega la ficha de demostración, la ficha anterior sigue visible y
 * la respuesta ajena se sube al servidor); la cuarta, que conserva los datos propios, sigue pasando.
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import { configurarProyecto } from "../utiles";
import { BOTON_GOOGLE, TENANT_PRUEBA, credencialSimulada, fijarAjustes, googleSimulado, simularApi } from "./utilesAuth";

const EMPRESA_ANTERIOR = "Empresa Anterior S.A.";
const CLAVE_DUENO = "lopdp-dueno-datos-v1";
const ana = credencialSimulada({ email: "ana@empresa.test", nombre: "Ana Prueba" });
const beto = credencialSimulada({ email: "beto@otra.test", nombre: "Beto Otro" });

/** Responde la caché de respuestas del servidor vacía y registra cada envío. */
async function simularRespuestas(page: Page): Promise<Request[]> {
  const envios: Request[] = [];
  await page.route("**/api/v1/diagnostico/respuestas", async (route) => {
    if (route.request().method() === "PUT") envios.push(route.request());
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ respuestas: [] }) });
  });
  return envios;
}

async function entrarCon(page: Page, token: string) {
  await page.evaluate((t) => {
    (window as unknown as { __credencialSimulada: string }).__credencialSimulada = t;
  }, token);
  await page.getByRole("button", { name: BOTON_GOOGLE }).click();
  await expect(page).toHaveURL(/\/dashboard/);
}

/** Ana entra y guarda la ficha de su organización. */
async function anaLlenaLaFicha(page: Page) {
  await fijarAjustes(page);
  await googleSimulado(page, ana.token);
  await simularApi(page);
  await page.goto("/login");
  await entrarCon(page, ana.token);
  await configurarProyecto(page, EMPRESA_ANTERIOR);
  await expect(page.getByTitle(EMPRESA_ANTERIOR)).toBeVisible();
}

async function cerrarLaSesion(page: Page) {
  await page.getByRole("button", { name: /Cerrar sesión/ }).click();
  await expect(page).toHaveURL(/\/login/);
}

const fichaGuardada = (page: Page) =>
  page.evaluate(() => JSON.parse(window.localStorage.getItem("jubys-audit-storage") ?? "{}")?.state?.companyData?.razonSocial ?? "");

test.describe("Datos de trabajo por persona y organización (FE-20)", () => {
  test("la primera vez que alguien entra, la ficha llega vacía: sin la organización de demostración", async ({ page }) => {
    await fijarAjustes(page);
    await googleSimulado(page, ana.token);
    await simularApi(page);
    await page.goto("/login");

    await entrarCon(page, ana.token);

    await expect(page.getByRole("textbox", { name: /Razón Social/ })).toHaveValue("");
    await expect(page.getByText("Corporación Demo LOPDP 360")).toHaveCount(0);
  });

  test("otra persona entra en el mismo navegador: el panel arranca sin los datos anteriores", async ({ page }) => {
    await anaLlenaLaFicha(page);
    await cerrarLaSesion(page);

    await entrarCon(page, beto.token);

    await expect(page.getByText(EMPRESA_ANTERIOR)).toHaveCount(0);
    await expect(page.getByRole("button", { name: /PERFIL ORGANIZACIONAL/ })).toBeVisible();
    expect(await fichaGuardada(page)).toBe("");
    expect(await page.evaluate((c) => window.localStorage.getItem(c), CLAVE_DUENO)).toBe(`beto@otra.test|${TENANT_PRUEBA}`);
  });

  test("los datos sin dueño conocido se descartan y nada ajeno se sube al servidor", async ({ page }) => {
    await anaLlenaLaFicha(page);
    await cerrarLaSesion(page);
    // Navegador con datos de antes de FE-20: sin dueño y con una respuesta propia en caché.
    await page.evaluate((c) => {
      const guardado = JSON.parse(window.localStorage.getItem("jubys-audit-storage") ?? "{}");
      guardado.state.respuestas = [
        { preguntaId: 1, cumple: "Cumple", evidenciaNivel: 2, esCritica: false, riesgoBase: 3, dimensionId: "D01", control: "Inventario de datos" },
      ];
      window.localStorage.setItem("jubys-audit-storage", JSON.stringify(guardado));
      window.localStorage.setItem("jubys-proyectos-v1", JSON.stringify({ proyectos: [] }));
      window.localStorage.setItem("lopdp-maturity-history:previo", "[]");
      window.localStorage.removeItem(c);
    }, CLAVE_DUENO);
    const envios = await simularRespuestas(page);

    await page.goto("/login"); // otra persona abre el navegador: los stores se cargan del almacenamiento
    await entrarCon(page, beto.token);

    await expect(page.getByText(EMPRESA_ANTERIOR)).toHaveCount(0);
    expect(await fichaGuardada(page)).toBe("");
    const sueltas = await page.evaluate(() => [
      window.localStorage.getItem("jubys-proyectos-v1"),
      window.localStorage.getItem("lopdp-maturity-history:previo"),
    ]);
    expect(sueltas).toEqual([null, null]);
    expect(envios.map((e) => e.postData() ?? ""), "respuestas ajenas enviadas al servidor").toEqual([]);
  });

  test("la misma persona en la misma organización conserva sus datos al volver a entrar", async ({ page }) => {
    await anaLlenaLaFicha(page);
    await cerrarLaSesion(page);

    await entrarCon(page, ana.token);

    await expect(page.getByTitle(EMPRESA_ANTERIOR)).toBeVisible();
    expect(await fichaGuardada(page)).toBe(EMPRESA_ANTERIOR);
  });
});
