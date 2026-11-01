/**
 * Arnés de interfaz de ORG-16: alta de la organización en siete pasos (Ficha Organizacional).
 *
 * Con sesión, la ficha lee GET /organizacion/alta y cada paso se guarda con POST
 * /organizacion/alta/paso/{id}; el cuerpo nunca lleva la organización ni una identificación. El
 * progreso es el del servidor: un navegador nuevo ve lo guardado por otro. El servidor se simula con
 * page.route sobre /api/v1/** y UN estado compartido entre navegadores (contextos), con la forma real
 * de sus respuestas. Todos los datos son ficticios (dominio .test).
 *
 * Mutación documentada: si el asistente guardara solo en el navegador (sin POST), «el alta sobrevive a
 * otro navegador» falla, porque el segundo contexto leería del servidor un alta sin pasos completos.
 */
import { expect, test, type Browser, type Page, type Request } from "@playwright/test";

import { abrirAppLimpia } from "../utiles";
import { credencialSimulada, fijarAjustes, ruta, sembrarSesion } from "../auth/utilesAuth";

interface Servidor {
  completos: Set<string>;
  posts: Array<{ paso: string; cuerpo: Record<string, unknown>; rol: string | undefined }>;
  llamadas: Request[];
}

const nuevoServidor = (): Servidor => ({ completos: new Set(), posts: [], llamadas: [] });

const ORDEN = ["perfil", "sedes", "areas", "tratamientos", "terceros", "personas", "resumen"];

function estadoDe(servidor: Servidor) {
  const completo = servidor.completos.has("perfil") && servidor.completos.has("areas");
  return { pasos: ORDEN.map((id) => ({ id, completo: id === "resumen" ? completo : servidor.completos.has(id) })), completo };
}

async function simular(page: Page, servidor: Servidor, roles: string[]): Promise<void> {
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    servidor.llamadas.push(peticion);
    const destino = ruta(peticion.url());
    const json = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (destino === "/organizacion/me/roles") {
      return json(200, { user_id: "u", tenant_id: "t-prueba", roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })) });
    }
    if (destino === "/organizacion/configuracion") {
      return json(200, { id: "t-prueba", nombre_comercial: "Org", razon_social: "Org Ficticia SA", ruc_identificacion: "1790000000001", sector: "salud", tamano: "mediana", activo: true });
    }
    if (destino === "/organizacion/datos-documentales") {
      return json(200, { tenant_id: "t-prueba", direccion: null, ciudad: null, provincia: null, telefono: null, correo_contacto: null, correo_privacidad: null, sitio_web: null, representante_legal_nombre: null, representante_legal_identificacion: null, representante_legal_cargo: null, faltantes: [] });
    }
    if (destino === "/organizacion/areas") return json(200, []);
    if (destino === "/organizacion/alta" && peticion.method() === "GET") return json(200, estadoDe(servidor));
    if (destino === "/organizacion/alta/sugerencias") {
      return json(200, {
        tratamientos: [{ indice: 0, nombre: "Admisión de pacientes", finalidad: "Identificar al paciente.", base_legal: "OBLIGACION_LEGAL" }],
        terceros: [{ indice: 0, tipo: "Laboratorio clínico", descripcion: "Recibe órdenes." }],
      });
    }
    const paso = destino.match(/^\/organizacion\/alta\/paso\/(\w+)$/);
    if (paso && peticion.method() === "POST") {
      if (!roles.some((r) => r === "admin_organizacion" || r === "implementador")) {
        return json(403, { detail: "Rol no autorizado para esta operación" });
      }
      const cuerpo = JSON.parse(peticion.postData() ?? "{}") as Record<string, unknown>;
      servidor.posts.push({ paso: paso[1], cuerpo, rol: peticion.headers()["x-role"] });
      servidor.completos.add(paso[1]);
      return json(200, { paso: paso[1], completo: true });
    }
    return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
  });
}

async function abrirConSesion(page: Page, servidor: Servidor, roles: string[]): Promise<void> {
  await fijarAjustes(page);
  await sembrarSesion(page, credencialSimulada());
  await simular(page, servidor, roles);
  await abrirAppLimpia(page);
  await expect(seccion(page)).toBeVisible();
}

async function otroNavegador(browser: Browser, servidor: Servidor, roles: string[]): Promise<Page> {
  const contexto = await browser.newContext();
  const pagina = await contexto.newPage();
  await abrirConSesion(pagina, servidor, roles);
  return pagina;
}

const seccion = (page: Page) => page.getByTestId("alta-organizacion");
const boton = (page: Page, nombre: string) => seccion(page).getByRole("button", { name: nombre, exact: true });
const progreso = (page: Page) => seccion(page).getByTestId("asistente-progreso");

async function completarPerfil(page: Page) {
  const s = seccion(page);
  await s.getByLabel("Razón social").fill("Organización Ficticia de Prueba S.A.");
  await s.getByLabel("RUC").fill("1790000000001");
  await s.getByLabel("Sector").fill("Salud");
  await s.getByLabel("Tamaño").selectOption("pequena");
  await s.getByLabel("Naturaleza").selectOption("privada");
  await s.getByLabel("Rol frente a los datos").selectOption("responsable");
  await boton(page, "Siguiente").click();
}

test.describe("Con sesión: alta de la organización en siete pasos (ORG-16)", () => {
  test("completar el paso 1 y saltar el 2 deja activo el 3 con «Paso 3 de 7»", async ({ page }) => {
    const servidor = nuevoServidor();
    await abrirConSesion(page, servidor, ["admin_organizacion"]);

    await boton(page, "Iniciar el alta").click();
    await expect(progreso(page)).toHaveText("Paso 1 de 7");
    await completarPerfil(page);
    await expect(page.getByRole("heading", { name: "Sedes" })).toBeVisible();
    await boton(page, "Saltar").click();

    await expect(progreso(page)).toHaveText("Paso 3 de 7");
    await expect(page.getByRole("heading", { name: "Áreas" })).toBeVisible();
    expect(servidor.posts.map((p) => p.paso)).toEqual(["perfil"]);
  });

  test("cada paso se guarda en el servidor, sin organización ni identificación en el cuerpo", async ({ page }) => {
    const servidor = nuevoServidor();
    await abrirConSesion(page, servidor, ["implementador"]);

    await boton(page, "Iniciar el alta").click();
    await completarPerfil(page);
    await boton(page, "Saltar").click();
    await seccion(page).getByLabel("Nombre del área 1").fill("Administración");
    await seccion(page).getByLabel("Código del área 1").fill("ADM");
    await boton(page, "Siguiente").click();
    await boton(page, "Saltar").click(); // tratamientos
    await boton(page, "Saltar").click(); // terceros
    await boton(page, "Agregar persona").click();
    await seccion(page).getByLabel("Nombre de la persona 1").fill("Persona Ficticia");
    await seccion(page).getByLabel("Cargo de la persona 1").fill("Coordinadora");
    await seccion(page).getByLabel("Correo de la persona 1").fill("persona@organizacion.test");
    await boton(page, "Siguiente").click();
    await boton(page, "Terminar").click();

    await expect.poll(() => servidor.posts.map((p) => p.paso)).toEqual(["perfil", "areas", "personas", "resumen"]);
    for (const { cuerpo, rol } of servidor.posts) {
      expect(rol).toBe("implementador");
      expect(Object.keys(cuerpo)).not.toContain("tenant_id");
      expect(JSON.stringify(cuerpo)).not.toMatch(/cedula|identificacion/i);
    }
    expect(servidor.posts[1].cuerpo).toEqual({ areas: [{ nombre: "Administración", codigo: "ADM" }] });
    await expect(page.getByTestId("alta-estado")).toHaveText(/Alta completa/);
  });

  test("el alta sobrevive a otro navegador", async ({ page, browser }) => {
    const servidor = nuevoServidor();
    await abrirConSesion(page, servidor, ["admin_organizacion"]);

    await boton(page, "Iniciar el alta").click();
    await completarPerfil(page);
    await boton(page, "Saltar").click();
    await seccion(page).getByLabel("Nombre del área 1").fill("Atención");
    await boton(page, "Siguiente").click();
    await expect(progreso(page)).toHaveText("Paso 4 de 7");

    // Sesión nueva en otro navegador: ningún estado local compartido, solo el servidor.
    const otra = await otroNavegador(browser, servidor, ["dpo"]);
    await expect(otra.getByTestId("alta-estado")).toHaveText(/Alta completa/);
    await expect(otra.getByTestId("alta-paso-perfil")).toHaveAttribute("data-completo", "true");
    await expect(otra.getByTestId("alta-paso-areas")).toHaveAttribute("data-completo", "true");
    await expect(otra.getByTestId("alta-paso-personas")).toHaveAttribute("data-completo", "false");
    await otra.context().close();
  });

  test("el dpo ve el estado del alta sin botones para escribir", async ({ page }) => {
    const servidor = nuevoServidor();
    servidor.completos.add("perfil");
    await abrirConSesion(page, servidor, ["dpo"]);

    await expect(page.getByTestId("alta-estado")).toHaveText(/Alta pendiente/);
    await expect(boton(page, "Iniciar el alta")).toHaveCount(0);
    await expect(boton(page, "Continuar el alta")).toHaveCount(0);
    expect(servidor.posts).toEqual([]);
  });

  test("retoma el alta en el primer paso sin completar", async ({ page }) => {
    const servidor = nuevoServidor();
    servidor.completos.add("perfil");
    servidor.completos.add("sedes");
    await abrirConSesion(page, servidor, ["admin_organizacion"]);

    await boton(page, "Continuar el alta").click();
    await expect(progreso(page)).toHaveText("Paso 3 de 7");
  });

  test("valida antes de enviar y no llama al servidor con datos inválidos", async ({ page }) => {
    const servidor = nuevoServidor();
    await abrirConSesion(page, servidor, ["admin_organizacion"]);

    await boton(page, "Iniciar el alta").click();
    await seccion(page).getByLabel("Razón social").fill("Org Ficticia");
    await seccion(page).getByLabel("RUC").fill("123");
    await boton(page, "Siguiente").click();

    await expect(seccion(page).getByRole("alert")).toHaveText("El RUC debe tener 13 dígitos.");
    expect(servidor.posts).toEqual([]);
  });
});
