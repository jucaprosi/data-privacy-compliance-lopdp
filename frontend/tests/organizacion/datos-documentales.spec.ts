/**
 * Arnés de interfaz de ORG-14: «Datos para documentos» en la Ficha Organizacional.
 *
 * Con sesión, la ficha lee GET /organizacion/datos-documentales; solo el administrador guarda
 * (PATCH) y el cuerpo nunca lleva la organización, que sale de la sesión. Valida correo, RUC/cédula
 * y URL antes de enviar y muestra el rechazo del servidor. Sin sesión no aparece ni llama al
 * servidor. El servidor se simula con page.route sobre /api/v1/**, con la forma real de sus
 * respuestas. Todos los datos son ficticios (cédula con código 30, dominio .test).
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import { abrirAppLimpia } from "../utiles";
import { credencialSimulada, fijarAjustes, ruta, sembrarSesion } from "../auth/utilesAuth";
import { CAMPOS_DOCUMENTALES, type DatosDocumentales } from "../../src/lib/organizacion/datosDocumentales";

const CEDULA_FICTICIA = "3000000004";

interface Escenario {
  roles: string[];
  datos?: Partial<DatosDocumentales>;
  /** Respuesta del PATCH cuando no es 200. */
  rechazo?: { status: number; detail: string; code: string };
}

interface Registro {
  llamadas: Request[];
  patches: Array<{ cuerpo: Record<string, unknown>; rol: string | undefined }>;
}

function datosIniciales(parcial: Partial<DatosDocumentales> = {}): DatosDocumentales {
  const base = Object.fromEntries(CAMPOS_DOCUMENTALES.map((c) => [c, null])) as unknown as DatosDocumentales;
  const datos = { ...base, ...parcial, tenant_id: "t-prueba" } as DatosDocumentales;
  datos.faltantes = CAMPOS_DOCUMENTALES.filter((c) => datos[c] === null);
  return datos;
}

async function simular(page: Page, escenario: Escenario): Promise<Registro> {
  const registro: Registro = { llamadas: [], patches: [] };
  let datos = datosIniciales(escenario.datos);
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    registro.llamadas.push(peticion);
    const destino = ruta(peticion.url());
    const json = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (destino === "/organizacion/me/roles") {
      return json(200, { user_id: "u", tenant_id: "t-prueba", roles: escenario.roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })) });
    }
    if (destino === "/organizacion/configuracion") {
      return json(200, { id: "t-prueba", nombre_comercial: "Org", razon_social: "Org Ficticia SA", ruc_identificacion: "3000000004001", sector: null, tamano: "mediana", activo: true });
    }
    if (destino === "/organizacion/datos-documentales" && peticion.method() === "GET") return json(200, datos);
    if (destino === "/organizacion/datos-documentales" && peticion.method() === "PATCH") {
      const cuerpo = JSON.parse(peticion.postData() ?? "{}") as Record<string, string | null>;
      registro.patches.push({ cuerpo, rol: peticion.headers()["x-role"] });
      if (escenario.rechazo) {
        const { status, ...error } = escenario.rechazo;
        return json(status, { ...error, action_required: null });
      }
      datos = datosIniciales({ ...datos, ...cuerpo });
      return json(200, datos);
    }
    return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
  });
  return registro;
}

async function abrirConSesion(page: Page, escenario: Escenario): Promise<Registro> {
  await fijarAjustes(page);
  await sembrarSesion(page, credencialSimulada());
  const registro = await simular(page, escenario);
  await abrirAppLimpia(page);
  await expect(seccion(page)).toBeVisible();
  return registro;
}

const seccion = (page: Page) => page.getByTestId("datos-documentales");
const campo = (page: Page, etiqueta: string) => seccion(page).getByLabel(etiqueta, { exact: true });
const guardar = (page: Page) => seccion(page).getByRole("button", { name: "Guardar datos para documentos" });

test.describe("Con sesión: datos para documentos de la organización (ORG-14)", () => {
  test("una organización sin datos los muestra como faltantes y el administrador los guarda", async ({ page }) => {
    const registro = await abrirConSesion(page, { roles: ["admin_organizacion"] });

    await expect(page.getByTestId("datos-documentales-faltantes")).toHaveText("9 de 9 sin registrar");
    await campo(page, "Domicilio principal").fill("Av. Ficticia N10-20");
    await campo(page, "Ciudad").fill("Quito");
    await campo(page, "Correo para solicitudes de titulares").fill("privacidad@organizacion.test");
    await campo(page, "Sitio web").fill("https://organizacion.test");
    await campo(page, "Nombre del representante legal").fill("Persona Ficticia de Prueba");
    await campo(page, "Cédula o RUC del representante legal").fill(CEDULA_FICTICIA);
    await guardar(page).click();

    await expect.poll(() => registro.patches.length).toBe(1);
    const { cuerpo, rol } = registro.patches[0];
    expect(rol).toBe("admin_organizacion");
    expect(cuerpo).toEqual({
      direccion: "Av. Ficticia N10-20",
      ciudad: "Quito",
      correo_privacidad: "privacidad@organizacion.test",
      sitio_web: "https://organizacion.test",
      representante_legal_nombre: "Persona Ficticia de Prueba",
      representante_legal_identificacion: CEDULA_FICTICIA,
    });
    expect(Object.keys(cuerpo), "la organización sale de la sesión, nunca del cuerpo").not.toContain("tenant_id");
    await expect(seccion(page).getByRole("status")).toHaveText("Datos para documentos guardados.");
    await expect(page.getByTestId("datos-documentales-faltantes")).toHaveText("3 de 9 sin registrar");
  });

  test("valida correo, cédula y URL antes de enviar", async ({ page }) => {
    const registro = await abrirConSesion(page, { roles: ["admin_organizacion"] });

    await campo(page, "Correo general de contacto").fill("sin-arroba.test");
    await campo(page, "Sitio web").fill("organizacion.test");
    await campo(page, "Cédula o RUC del representante legal").fill("3000000005");
    await guardar(page).click();

    await expect(seccion(page).getByText("No es un correo electrónico válido.")).toBeVisible();
    await expect(seccion(page).getByText(/Debe ser una dirección web completa/)).toBeVisible();
    await expect(seccion(page).getByText("No es una cédula ni un RUC de persona natural válidos.")).toBeVisible();
    await expect(campo(page, "Sitio web")).toHaveAttribute("aria-invalid", "true");
    await expect(seccion(page).getByRole("alert")).toHaveText("Revise los campos marcados antes de guardar.");
    expect(registro.patches).toEqual([]);
  });

  test("vaciar un campo guardado lo borra en el servidor (null)", async ({ page }) => {
    const registro = await abrirConSesion(page, { roles: ["admin_organizacion"], datos: { ciudad: "Quito", telefono: "+593 2 000 0000" } });

    await expect(campo(page, "Ciudad")).toHaveValue("Quito");
    await campo(page, "Ciudad").fill("");
    await guardar(page).click();

    await expect.poll(() => registro.patches.length).toBe(1);
    expect(registro.patches[0].cuerpo).toEqual({ ciudad: null });
  });

  test("si el servidor rechaza el valor, muestra su mensaje", async ({ page }) => {
    await abrirConSesion(page, {
      roles: ["admin_organizacion"],
      rechazo: { status: 422, code: "DATOS_DOCUMENTALES_INVALIDOS", detail: "telefono: solo admite dígitos." },
    });

    await campo(page, "Teléfono de contacto").fill("02 000 0000");
    await guardar(page).click();

    await expect(seccion(page).getByRole("alert")).toContainText("telefono: solo admite dígitos.");
  });

  test("un rol sin administración los lee en solo lectura y no puede guardarlos", async ({ page }) => {
    const registro = await abrirConSesion(page, { roles: ["coordinador"], datos: { ciudad: "Quito" } });

    await expect(campo(page, "Ciudad")).toHaveValue("Quito");
    await expect(campo(page, "Ciudad")).toHaveAttribute("readonly", "");
    await expect(guardar(page)).toHaveCount(0);
    await expect(page.getByTestId("datos-documentales-aviso")).toContainText("Solo el administrador");
    const lectura = registro.llamadas.find((l) => ruta(l.url()) === "/organizacion/datos-documentales");
    expect(lectura?.headers()["x-role"]).toBe("coordinador");
    expect(registro.patches).toEqual([]);
  });
});

test.describe("Sin sesión (desarrollo): la sección no aparece (ORG-14)", () => {
  test("no se muestra ni consulta el servidor", async ({ page }) => {
    await fijarAjustes(page, { modo: "headers", clientId: null, tenant: null });
    const registro = await simular(page, { roles: ["admin_organizacion"] });
    await abrirAppLimpia(page);

    await expect(page.getByLabel(/Tamaño \/ Número de Empleados/)).toBeVisible();
    await expect(seccion(page)).toHaveCount(0);
    expect(registro.llamadas.filter((l) => ruta(l.url()) === "/organizacion/datos-documentales")).toEqual([]);
  });
});
