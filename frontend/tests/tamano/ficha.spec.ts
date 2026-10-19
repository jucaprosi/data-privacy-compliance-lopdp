/**
 * Arnés de interfaz de FE-08: el tamaño de la ficha es el de la organización en el servidor.
 *
 * Con sesión (modo "oidc") la ficha lee `tenants.tamano` y solo el administrador lo cambia; sin sesión
 * (desarrollo) se comporta como siempre y no llama al servidor. El servidor se simula con
 * page.route sobre /api/v1/**, con la forma real de sus respuestas.
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import { abrirAppLimpia } from "../utiles";
import { CLAVES_DE_TAMANO, etiquetaDeFicha } from "../../src/lib/tamanoOrganizacion";
import { credencialSimulada, esApi, fijarAjustes, ruta, sembrarSesion } from "../auth/utilesAuth";

interface Escenario {
  roles: string[] | number;
  /** `tenants.tamano` en el servidor. */
  tamano: string | null;
  /** Estado con el que responde el PATCH; 200 por defecto. */
  estadoPatch?: number;
}

interface Registro {
  llamadas: Request[];
  cuerpos: Array<{ metodo: string; cuerpo: string | null; cabeceras: Record<string, string> }>;
}

const configuracion = (tamano: string | null) => ({
  id: "t-prueba", nombre_comercial: "Org", razon_social: "Org SA", ruc_identificacion: "1790000000001",
  sector: null, tamano, activo: true,
});

async function simular(page: Page, escenario: Escenario): Promise<Registro> {
  const registro: Registro = { llamadas: [], cuerpos: [] };
  let tamano = escenario.tamano;
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    registro.llamadas.push(peticion);
    const destino = ruta(peticion.url());
    const json = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (destino === "/organizacion/me/roles") {
      if (typeof escenario.roles === "number") return json(escenario.roles, { detail: "Servicio no disponible" });
      return json(200, { user_id: "u", tenant_id: "t", roles: escenario.roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })) });
    }
    if (destino === "/organizacion/configuracion" && peticion.method() === "GET") return json(200, configuracion(tamano));
    if (destino === "/organizacion/configuracion" && peticion.method() === "PATCH") {
      registro.cuerpos.push({ metodo: "PATCH", cuerpo: peticion.postData(), cabeceras: peticion.headers() });
      if ((escenario.estadoPatch ?? 200) !== 200) return json(escenario.estadoPatch!, { detail: "No autorizado para cambiar la configuración." });
      tamano = (JSON.parse(peticion.postData() ?? "{}") as { tamano?: string }).tamano ?? tamano;
      return json(200, configuracion(tamano));
    }
    return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
  });
  return registro;
}

const selector = (page: Page) => page.getByLabel(/Tamaño \/ Número de Empleados/);
const deConfiguracion = (r: Registro, metodo: string) =>
  r.llamadas.filter((l) => ruta(l.url()) === "/organizacion/configuracion" && l.method() === metodo);
const delServidor = (r: Registro) => r.llamadas.filter(esApi).map((l) => `${l.method()} ${ruta(l.url())}`);

async function abrirFichaConSesion(page: Page, escenario: Escenario): Promise<Registro> {
  await fijarAjustes(page);
  await sembrarSesion(page, credencialSimulada());
  const registro = await simular(page, escenario);
  await abrirAppLimpia(page);
  return registro;
}

test.describe("Con sesión: el tamaño es el de la organización (FE-08)", () => {
  test("el administrador ve el tamaño registrado, lo cambia y queda guardado en el servidor", async ({ page }) => {
    const registro = await abrirFichaConSesion(page, { roles: ["coordinador", "admin_organizacion"], tamano: "mediana" });

    await expect(selector(page)).toHaveValue("mediana");
    await expect(selector(page)).toBeEnabled();
    const lectura = deConfiguracion(registro, "GET")[0];
    expect(lectura.headers()["x-role"], "para leer actúa con el rol de administrador").toBe("admin_organizacion");
    expect(lectura.headers()["authorization"]).toMatch(/^Bearer /);

    await selector(page).selectOption("pequena");

    await expect.poll(() => registro.cuerpos.length).toBe(1);
    expect(JSON.parse(registro.cuerpos[0].cuerpo ?? "{}")).toEqual({ tamano: "pequena" });
    expect(registro.cuerpos[0].cabeceras["x-role"]).toBe("admin_organizacion");
    await expect(selector(page)).toHaveValue("pequena");
    // La ficha guarda la etiqueta de la talla elegida, la que usa el banco de preguntas para podar.
    const guardado = await page.evaluate(() => window.localStorage.getItem("jubys-audit-storage") ?? "");
    expect(guardado).toContain(etiquetaDeFicha("pequena"));
  });

  test("un rol sin administración lo ve en solo lectura y no puede cambiarlo", async ({ page }) => {
    const registro = await abrirFichaConSesion(page, { roles: ["coordinador"], tamano: "micro" });

    await expect(selector(page)).toHaveValue("micro");
    await expect(selector(page)).toBeDisabled();
    // «Archivo > Nuevo» devolvió el proyecto a su valor por defecto; la copia local vuelve a ser la del servidor.
    await expect.poll(() => page.evaluate(() => window.localStorage.getItem("jubys-audit-storage") ?? "")).toContain(etiquetaDeFicha("micro"));
    await expect(page.getByTestId("tamano-estado")).toContainText("Solo el administrador");
    expect(deConfiguracion(registro, "GET")[0].headers()["x-role"]).toBe("coordinador");
    expect(deConfiguracion(registro, "PATCH")).toEqual([]);
  });

  test("si la organización no tiene tamaño, lo dice y solo el administrador puede fijarlo", async ({ page }) => {
    await abrirFichaConSesion(page, { roles: ["coordinador"], tamano: null });
    await expect(selector(page)).toHaveValue("");
    await expect(selector(page)).toBeDisabled();
    await expect(page.getByTestId("tamano-estado")).toContainText("Aún no está configurado");
  });

  test("el administrador fija el tamaño de una organización sin configurar", async ({ page }) => {
    const registro = await abrirFichaConSesion(page, { roles: ["admin_organizacion"], tamano: null });

    await expect(selector(page)).toHaveValue("");
    await expect(selector(page).locator("option", { hasText: "Sin configurar" })).toHaveCount(1);
    await selector(page).selectOption("corporativo");

    await expect.poll(() => registro.cuerpos.length).toBe(1);
    expect(JSON.parse(registro.cuerpos[0].cuerpo ?? "{}")).toEqual({ tamano: "corporativo" });
    await expect(selector(page)).toHaveValue("corporativo");
  });

  test("el conteo de personas no pisa el tamaño del servidor: solo lo contrasta", async ({ page }) => {
    const registro = await abrirFichaConSesion(page, { roles: ["admin_organizacion"], tamano: "mediana" });
    await expect(selector(page)).toHaveValue("mediana");

    await page.getByLabel("Empleados directos afiliados al IESS").fill("300");

    await expect(selector(page)).toHaveValue("mediana");
    await expect(selector(page)).toBeEnabled();
    await expect(page.getByRole("note")).toContainText("300 personas");
    await expect(page.getByRole("note")).toContainText(etiquetaDeFicha("corporativo"));
    expect(deConfiguracion(registro, "PATCH")).toEqual([]);
  });

  test("si el servidor rechaza el cambio, lo dice y el tamaño no cambia", async ({ page }) => {
    await abrirFichaConSesion(page, { roles: ["admin_organizacion"], tamano: "mediana", estadoPatch: 403 });

    await selector(page).selectOption("micro");

    await expect(page.getByRole("alert").filter({ hasText: "No autorizado" })).toBeVisible();
    await expect(selector(page)).toHaveValue("mediana");
  });

  test("si no se puede consultar el servidor, la ficha avisa y sigue usable con su valor", async ({ page }) => {
    const registro = await abrirFichaConSesion(page, { roles: 503, tamano: "mediana" });

    await expect(page.getByRole("alert").filter({ hasText: "No se pudo consultar el tamaño" })).toBeVisible();
    await expect(selector(page)).toBeEnabled();
    expect(deConfiguracion(registro, "GET"), "sin roles no se intenta leer la configuración").toEqual([]);
    await selector(page).selectOption({ label: etiquetaDeFicha("pequena") });
    await expect(selector(page)).toHaveValue(etiquetaDeFicha("pequena"));
  });
});

test.describe("Sin sesión (desarrollo): la ficha no depende del servidor (FE-08)", () => {
  test("no llama a Organización, ofrece las cuatro tallas y calcula el tamaño por personas", async ({ page }) => {
    await fijarAjustes(page, { modo: "headers", clientId: null, tenant: null });
    const registro = await simular(page, { roles: ["admin_organizacion"], tamano: "micro" });
    await abrirAppLimpia(page);

    const opciones = await selector(page).locator("option").allTextContents();
    expect(opciones).toEqual(CLAVES_DE_TAMANO.map(etiquetaDeFicha));

    await page.getByLabel("Empleados directos afiliados al IESS").fill("120");
    await page.getByLabel(/contratadas por servicios|contratadas|servicios/i).first().fill("80");

    // 120 + 80 = 200 personas: corporativo. La etiqueta ya no excluye el 200.
    await expect(selector(page)).toHaveValue(etiquetaDeFicha("corporativo"));
    await expect(selector(page)).toBeDisabled();
    expect(delServidor(registro).filter((l) => l.includes("/organizacion/"))).toEqual([]);
  });
});
