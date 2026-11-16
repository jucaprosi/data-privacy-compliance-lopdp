// ¤arbitro
// ¤¤qa-engineer
/**
 * Arnés de interfaz de ORG-17: inventario de activos, soportes y personas (menú Inventario).
 *
 * Con sesión, la pantalla lee GET /organizacion/inventario/{activos,personas,tratamientos} y cada alta,
 * archivo o vínculo se guarda en el servidor; el cuerpo nunca lleva la organización ni la identidad. El
 * servidor se simula con page.route sobre /api/v1/** y UN estado compartido entre navegadores (contextos),
 * con la forma real de sus respuestas. Todos los datos son ficticios (dominio .invalid).
 *
 * Mutación documentada: si «Agregar» solo añadiera la fila al estado local (sin POST), «lo creado en un
 * navegador lo ve otro» falla, porque el segundo contexto leería del servidor un inventario vacío.
 */
import { expect, test, type Browser, type Page } from "@playwright/test";

import { abrirAppLimpia, abrirSubmenu, barraDeMenus, configurarProyecto, submenuPorNombre } from "../utiles";
import { credencialSimulada, fijarAjustes, ruta, sembrarSesion } from "../auth/utilesAuth";

interface Servidor {
  activos: Array<Record<string, unknown>>;
  personas: Array<Record<string, unknown>>;
  sinClave?: boolean;
  llamadas: Array<{ metodo: string; destino: string; cuerpo: Record<string, unknown> | null; rol: string | undefined }>;
}

const nuevoServidor = (): Servidor => ({ activos: [], personas: [], llamadas: [] });

async function simular(page: Page, servidor: Servidor, roles: string[]): Promise<void> {
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    const destino = ruta(peticion.url());
    const metodo = peticion.method();
    const json = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });
    const cuerpo = metodo === "GET" ? null : (JSON.parse(peticion.postData() ?? "{}") as Record<string, unknown>);
    const puedeEscribir = roles.some((r) => ["admin_organizacion", "implementador", "coordinador"].includes(r));

    if (destino === "/organizacion/me/roles") {
      return json(200, { user_id: "u", tenant_id: "t-prueba", roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })) });
    }
    if (destino === "/organizacion/areas") return json(200, [{ id: "ar-1", nombre: "Administración", codigo: "ADM" }]);
    if (!destino.startsWith("/organizacion/inventario")) {
      return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
    }
    servidor.llamadas.push({ metodo, destino, cuerpo, rol: peticion.headers()["x-role"] });

    if (destino === "/organizacion/inventario/activos" && metodo === "GET") return json(200, servidor.activos);
    if (destino === "/organizacion/inventario/personas" && metodo === "GET") return json(200, servidor.personas);
    if (destino === "/organizacion/inventario/tratamientos") return json(200, [{ id: "rat-1", codigo: "T-01", nombre: "Admisión de pacientes" }]);
    if (!puedeEscribir) return json(403, { detail: "Rol no autorizado para esta operación" });

    if (destino === "/organizacion/inventario/activos" && metodo === "POST") {
      servidor.activos.push({
        id: `a-${servidor.activos.length + 1}`, descripcion: null, ubicacion: null, area_id: null, responsable_id: null,
        archivado: false, tratamiento_ids: [], ...cuerpo,
      });
      return json(201, { id: `a-${servidor.activos.length}` });
    }
    if (destino === "/organizacion/inventario/personas" && metodo === "POST") {
      const { cedula, ...resto } = cuerpo ?? {};
      if (cedula && servidor.sinClave) {
        return json(503, { detail: "No configurado", code: "INVENTARIO_CIFRADO_NO_CONFIGURADO" });
      }
      servidor.personas.push({ id: `p-${servidor.personas.length + 1}`, area_id: null, archivada: false, tiene_cedula: Boolean(cedula), ...resto });
      return json(201, { id: `p-${servidor.personas.length}` });
    }
    const activo = destino.match(/^\/organizacion\/inventario\/activos\/([\w-]+)(\/tratamientos)?$/);
    if (activo) {
      const fila = servidor.activos.find((a) => a.id === activo[1]);
      if (!fila) return json(404, { detail: "No existe", code: "INVENTARIO_NO_ENCONTRADO" });
      if (activo[2]) fila.tratamiento_ids = (cuerpo?.tratamiento_ids as string[]) ?? [];
      else Object.assign(fila, cuerpo);
      return json(200, { id: fila.id });
    }
    return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
  });
}

async function abrirInventario(page: Page, servidor: Servidor, roles: string[]): Promise<void> {
  await fijarAjustes(page);
  await sembrarSesion(page, credencialSimulada());
  await simular(page, servidor, roles);
  await abrirAppLimpia(page);
  const barra = barraDeMenus(page);
  if (!(await barra.getByRole("button", { name: "Inventario", exact: true }).isVisible())) {
    await configurarProyecto(page, "Entidad ORG-17");
  }
  await abrirSubmenu(page, submenuPorNombre(/Activos y personas/)!);
  await expect(page.getByRole("heading", { name: "Inventario de la organización" })).toBeVisible();
}

async function otroNavegador(browser: Browser, servidor: Servidor, roles: string[]): Promise<Page> {
  const contexto = await browser.newContext();
  const pagina = await contexto.newPage();
  await abrirInventario(pagina, servidor, roles);
  return pagina;
}

const pestana = (page: Page, nombre: string) => page.getByRole("tab", { name: nombre, exact: true });

async function agregarSistema(page: Page, nombre: string) {
  await page.getByLabel("Nombre", { exact: true }).fill(nombre);
  await page.getByRole("button", { name: "Agregar activo", exact: true }).click();
}

test.describe("Inventario de activos, soportes y personas (ORG-17)", () => {
  test("lo creado en un navegador lo ve otro, sin organización ni identidad en el cuerpo", async ({ page, browser }) => {
    const servidor = nuevoServidor();
    await abrirInventario(page, servidor, ["admin_organizacion"]);

    await agregarSistema(page, "Sistema de citas ficticio");
    await expect(page.getByRole("listitem").filter({ hasText: "Sistema de citas ficticio" })).toBeVisible();

    const post = servidor.llamadas.find((l) => l.metodo === "POST" && l.destino.endsWith("/activos"))!;
    expect(post.rol).toBe("admin_organizacion");
    expect(post.cuerpo).toMatchObject({ tipo: "sistema", nombre: "Sistema de citas ficticio" });
    for (const prohibido of ["tenant_id", "created_by", "user_id"]) expect(Object.keys(post.cuerpo!)).not.toContain(prohibido);

    // «Otro navegador»: contexto nuevo, sin estado compartido más que el servidor.
    const otra = await otroNavegador(browser, servidor, ["dpo"]);
    await expect(otra.getByRole("listitem").filter({ hasText: "Sistema de citas ficticio" })).toBeVisible();
    await otra.context().close();
  });

  test("los soportes se crean con su tipo y las personas, sin enviar la cédula vacía", async ({ page }) => {
    const servidor = nuevoServidor();
    await abrirInventario(page, servidor, ["coordinador"]);

    await pestana(page, "Soportes").click();
    await page.getByLabel("Tipo de soporte").selectOption("soporte_digital");
    await page.getByLabel("Nombre", { exact: true }).fill("Copia de respaldo ficticia");
    await page.getByRole("button", { name: "Agregar activo", exact: true }).click();
    await expect(page.getByRole("listitem").filter({ hasText: "Copia de respaldo ficticia" })).toBeVisible();
    expect(servidor.activos[0]).toMatchObject({ tipo: "soporte_digital" });

    await pestana(page, "Personas").click();
    await page.getByLabel("Nombre", { exact: true }).fill("Persona Ficticia");
    await page.getByLabel("Cargo", { exact: true }).fill("Coordinadora");
    await page.getByLabel("Correo", { exact: true }).fill("persona@organizacion.invalid");
    await page.getByRole("button", { name: "Agregar persona", exact: true }).click();
    await expect(page.getByText("persona@organizacion.invalid")).toBeVisible();
    const post = servidor.llamadas.find((l) => l.metodo === "POST" && l.destino.endsWith("/personas"))!;
    expect(Object.keys(post.cuerpo!)).not.toContain("cedula");
  });

  test("una persona con cédula inválida o correo inválido no se envía", async ({ page }) => {
    const servidor = nuevoServidor();
    await abrirInventario(page, servidor, ["admin_organizacion"]);
    await pestana(page, "Personas").click();
    await page.getByLabel("Nombre", { exact: true }).fill("Persona Ficticia");
    await page.getByLabel("Cargo", { exact: true }).fill("Gerente");
    await page.getByLabel("Correo", { exact: true }).fill("sin-arroba");
    await page.getByRole("button", { name: "Agregar persona", exact: true }).click();
    await expect(page.getByRole("alert").filter({ hasText: "Revisa el correo." })).toBeVisible();
    await page.getByLabel("Correo", { exact: true }).fill("p@organizacion.invalid");
    await page.getByLabel("Cédula (solo si la firma la exige)").fill("123");
    await page.getByRole("button", { name: "Agregar persona", exact: true }).click();
    await expect(page.getByRole("alert").filter({ hasText: "La cédula debe tener 10 dígitos." })).toBeVisible();
    expect(servidor.llamadas.filter((l) => l.metodo === "POST")).toHaveLength(0);
  });

  test("vincular tratamientos y archivar se guardan en el servidor", async ({ page }) => {
    const servidor = nuevoServidor();
    servidor.activos.push({
      id: "a-1", tipo: "sistema", nombre: "Historia clínica ficticia", descripcion: null, ubicacion: null,
      area_id: null, responsable_id: null, archivado: false, tratamiento_ids: [],
    });
    await abrirInventario(page, servidor, ["implementador"]);

    await page.getByRole("button", { name: "Vincular tratamientos", exact: true }).click();
    await page.getByLabel("T-01 · Admisión de pacientes").check();
    await page.getByRole("button", { name: "Guardar vínculos" }).click();
    await expect.poll(() => servidor.activos[0].tratamiento_ids).toEqual(["rat-1"]);
    await expect(page.getByText("Tratamientos vinculados: 1")).toBeVisible();

    await page.getByRole("button", { name: "Archivar" }).click();
    await expect.poll(() => servidor.activos[0].archivado).toBe(true);
    await expect(page.getByText("(archivado)")).toBeVisible();
  });

  test("sin clave en el servidor, la cédula avisa sin vaciar el formulario y se guarda sin ella", async ({ page }) => {
    const servidor = { ...nuevoServidor(), sinClave: true };
    await abrirInventario(page, servidor, ["admin_organizacion"]);
    await pestana(page, "Personas").click();
    await page.getByLabel("Nombre", { exact: true }).fill("Persona Ficticia");
    await page.getByLabel("Cargo", { exact: true }).fill("Gerente");
    await page.getByLabel("Correo", { exact: true }).fill("p@organizacion.invalid");
    await page.getByLabel("Cédula (solo si la firma la exige)").fill("1710034065");
    await page.getByRole("button", { name: "Agregar persona", exact: true }).click();

    await expect(page.getByRole("alert").filter({ hasText: "No pudimos guardar la cédula en este momento." })).toBeVisible();
    await expect(page.getByLabel("Nombre", { exact: true })).toHaveValue("Persona Ficticia");
    await expect(page.getByLabel("Cédula (solo si la firma la exige)")).toHaveValue("1710034065");

    await page.getByRole("button", { name: "Guardar sin cédula" }).click();
    await expect(page.getByText("p@organizacion.invalid")).toBeVisible();
    await expect(page.getByText("Cédula guardada")).toHaveCount(0);
    const ultimo = servidor.llamadas.filter((l) => l.metodo === "POST").at(-1)!;
    expect(Object.keys(ultimo.cuerpo!)).not.toContain("cedula");
  });

  test("con cédula guardada la fila lo dice y el número no aparece en la página ni en los textos", async ({ page }) => {
    const servidor = nuevoServidor();
    await abrirInventario(page, servidor, ["admin_organizacion"]);
    await pestana(page, "Personas").click();
    await page.getByLabel("Nombre", { exact: true }).fill("Persona Ficticia");
    await page.getByLabel("Cargo", { exact: true }).fill("Gerente");
    await page.getByLabel("Correo", { exact: true }).fill("p@organizacion.invalid");
    await page.getByLabel("Cédula (solo si la firma la exige)").fill("1710034065");
    await page.getByRole("button", { name: "Agregar persona", exact: true }).click();
    await expect(page.getByText("Cédula guardada")).toBeVisible();
    const texto = await page.locator("body").innerText();
    expect(texto).not.toContain("1710034065");
    for (const jerga of ["503", "cifra ", "clave del servidor", "INVENTARIO_"]) expect(texto).not.toContain(jerga);
    await expect(page.getByText("Se guarda cifrada y no se vuelve a mostrar.")).toBeVisible();
  });

  test("el dpo consulta pero no ve botones ni formularios de escritura", async ({ page }) => {
    const servidor = nuevoServidor();
    servidor.activos.push({
      id: "a-1", tipo: "sistema", nombre: "Sistema solo lectura", descripcion: null, ubicacion: null,
      area_id: null, responsable_id: null, archivado: false, tratamiento_ids: [],
    });
    await abrirInventario(page, servidor, ["dpo"]);
    await expect(page.getByRole("listitem").filter({ hasText: "Sistema solo lectura" })).toBeVisible();
    await expect(page.getByText("Puedes consultar el inventario, pero no modificarlo.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Agregar persona", exact: true })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Agregar activo" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /^Archivar/ })).toHaveCount(0);
  });
});
