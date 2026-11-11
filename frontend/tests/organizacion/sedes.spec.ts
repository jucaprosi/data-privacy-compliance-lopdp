// ¤arbitro
// ¤¤qa-engineer
/**
 * Arnés de interfaz de ORG-18: sedes de la organización y clientes cuando actúa como encargada.
 *
 * Con sesión, las pantallas leen GET /organizacion/{sedes,clientes} y cada alta o retiro se guarda en el
 * servidor; el cuerpo nunca lleva la organización ni la identidad. El servidor se simula con page.route sobre
 * /api/v1/** y UN estado compartido entre navegadores (contextos), con la forma real de sus respuestas.
 * Todos los datos son ficticios (dominio .invalid).
 *
 * Mutación documentada: si «Agregar sede» solo añadiera la fila al estado local (sin POST), «lo creado en un
 * navegador lo ve otro» falla, porque el segundo contexto leería del servidor una lista vacía.
 */
import { expect, test, type Browser, type Page } from "@playwright/test";

import { abrirAppLimpia, abrirSubmenu, barraDeMenus, configurarProyecto, submenuPorNombre } from "../utiles";
import { credencialSimulada, fijarAjustes, ruta, sembrarSesion } from "../auth/utilesAuth";

interface Servidor {
  sedes: Array<Record<string, unknown>>;
  clientes: Array<Record<string, unknown>>;
  encargada: boolean;
  llamadas: Array<{ metodo: string; destino: string; cuerpo: Record<string, unknown> | null; rol: string | undefined }>;
}

const nuevoServidor = (encargada = true): Servidor => ({ sedes: [], clientes: [], encargada, llamadas: [] });

async function simular(page: Page, servidor: Servidor, roles: string[]): Promise<void> {
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    const destino = ruta(peticion.url());
    const metodo = peticion.method();
    const json = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });
    const cuerpo = metodo === "GET" || !peticion.postData() ? null : (JSON.parse(peticion.postData() ?? "{}") as Record<string, unknown>);
    const puedeEscribir = roles.some((r) => ["admin_organizacion", "implementador", "coordinador"].includes(r));

    if (destino === "/organizacion/me/roles") {
      return json(200, { user_id: "u", tenant_id: "t-prueba", roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })) });
    }
    if (!destino.startsWith("/organizacion/sedes") && !destino.startsWith("/organizacion/clientes")) {
      return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
    }
    servidor.llamadas.push({ metodo, destino, cuerpo, rol: peticion.headers()["x-role"] });

    if (destino === "/organizacion/sedes" && metodo === "GET") return json(200, servidor.sedes);
    if (destino === "/organizacion/clientes") {
      if (!servidor.encargada) return json(409, { detail: "Los clientes solo existen cuando la organización trata datos por encargo.", code: "NO_ES_ENCARGADA" });
      if (metodo === "GET") return json(200, servidor.clientes);
    }
    if (!puedeEscribir) return json(403, { detail: "Rol no autorizado para esta operación" });

    if (destino === "/organizacion/sedes" && metodo === "POST") {
      if (cuerpo?.es_principal && servidor.sedes.some((s) => s.es_principal && s.retirada_en === null)) {
        return json(409, { detail: "La organización ya tiene una sede principal.", code: "SEDE_PRINCIPAL_DUPLICADA" });
      }
      servidor.sedes.push({ id: `s-${servidor.sedes.length + 1}`, retirada_en: null, ...cuerpo });
      return json(201, { id: `s-${servidor.sedes.length}` });
    }
    if (destino === "/organizacion/clientes" && metodo === "POST") {
      servidor.clientes.push({ id: `c-${servidor.clientes.length + 1}`, retirado_en: null, ...cuerpo });
      return json(201, { id: `c-${servidor.clientes.length}` });
    }
    const retirar = destino.match(/^\/organizacion\/(sedes|clientes)\/([\w-]+)\/retirar$/);
    if (retirar && metodo === "POST") {
      const coleccion = retirar[1] === "sedes" ? servidor.sedes : servidor.clientes;
      const fila = coleccion.find((x) => x.id === retirar[2]);
      if (!fila) return json(404, { detail: "No existe", code: "SEDE_NO_ENCONTRADA" });
      fila[retirar[1] === "sedes" ? "retirada_en" : "retirado_en"] = "2030-01-01T00:00:00+00:00";
      return json(200, { id: fila.id });
    }
    return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
  });
}

async function abrirVista(page: Page, servidor: Servidor, roles: string[], submenu: RegExp): Promise<void> {
  await fijarAjustes(page);
  await sembrarSesion(page, credencialSimulada());
  await simular(page, servidor, roles);
  await abrirAppLimpia(page);
  if (!(await barraDeMenus(page).getByRole("button", { name: "Inventario", exact: true }).isVisible())) {
    await configurarProyecto(page, "Entidad ORG-18");
  }
  await abrirSubmenu(page, submenuPorNombre(submenu)!);
}

async function otroNavegador(browser: Browser, servidor: Servidor, roles: string[], submenu: RegExp): Promise<Page> {
  const contexto = await browser.newContext();
  const pagina = await contexto.newPage();
  await abrirVista(pagina, servidor, roles, submenu);
  return pagina;
}

const SEDES = /Sedes y áreas/;
const CLIENTES = /Clientes/;

async function llenarSede(page: Page, nombre: string, principal: boolean) {
  await page.getByLabel("Nombre (obligatorio)", { exact: true }).fill(nombre);
  await page.getByLabel("Dirección (obligatorio)", { exact: true }).fill("Calle Ficticia 123");
  await page.getByLabel("Ciudad (obligatorio)", { exact: true }).fill("Ciudad Ficticia");
  await page.getByLabel("Provincia (obligatorio)", { exact: true }).fill("Provincia Ficticia");
  if (principal) await page.getByLabel("Es la sede principal").check();
  await page.getByRole("button", { name: "Agregar sede", exact: true }).click();
}

test.describe("Sedes y clientes por encargo (ORG-18)", () => {
  test("lo creado en un navegador lo ve otro, sin organización ni identidad en el cuerpo", async ({ page, browser }) => {
    const servidor = nuevoServidor();
    await abrirVista(page, servidor, ["admin_organizacion"], SEDES);
    await llenarSede(page, "Matriz ficticia", true);
    await expect(page.getByRole("listitem").filter({ hasText: "Matriz ficticia" })).toBeVisible();
    await expect(page.getByText("Sede principal", { exact: true })).toBeVisible();

    const post = servidor.llamadas.find((l) => l.metodo === "POST" && l.destino === "/organizacion/sedes")!;
    expect(post.rol).toBe("admin_organizacion");
    expect(post.cuerpo).toMatchObject({ nombre: "Matriz ficticia", es_principal: true });
    for (const prohibido of ["tenant_id", "creado_por", "user_id"]) expect(Object.keys(post.cuerpo!)).not.toContain(prohibido);

    const otra = await otroNavegador(browser, servidor, ["dpo"], SEDES);
    await expect(otra.getByRole("listitem").filter({ hasText: "Matriz ficticia" })).toBeVisible();
    await otra.context().close();
  });

  test("una segunda sede principal se rechaza con un aviso y no se agrega", async ({ page }) => {
    const servidor = nuevoServidor();
    await abrirVista(page, servidor, ["coordinador"], SEDES);
    await llenarSede(page, "Matriz ficticia", true);
    await expect(page.getByText("Sede principal", { exact: true })).toBeVisible();
    await llenarSede(page, "Sucursal ficticia", true);
    await expect(page.getByRole("alert").filter({ hasText: "La organización ya tiene una sede principal." })).toBeVisible();
    await expect(page.getByRole("listitem").filter({ hasText: "Sucursal ficticia" })).toHaveCount(0);
    expect(servidor.sedes).toHaveLength(1);
  });

  test("una sede incompleta no se envía y retirar la deja fuera de la lista", async ({ page }) => {
    const servidor = nuevoServidor();
    await abrirVista(page, servidor, ["implementador"], SEDES);
    await page.getByLabel("Nombre (obligatorio)", { exact: true }).fill("Solo nombre");
    await page.getByRole("button", { name: "Agregar sede", exact: true }).click();
    await expect(page.getByRole("alert").filter({ hasText: "Falta: dirección, ciudad y provincia." })).toBeVisible();
    await expect(page.getByLabel("Ciudad (obligatorio)", { exact: true })).toHaveAttribute("aria-invalid", "true");
    expect(servidor.llamadas.filter((l) => l.metodo === "POST")).toHaveLength(0);

    await llenarSede(page, "Sucursal ficticia", false);
    await page.getByRole("button", { name: "Retirar Sucursal ficticia" }).click();
    const confirmacion = page.getByRole("group", { name: "Confirmar el retiro de Sucursal ficticia" });
    await expect(confirmacion).toContainText("¿Retirar la sede Sucursal ficticia? Dejará de aparecer en la lista y quedará en el historial.");
    await confirmacion.getByRole("button", { name: "Cancelar" }).click();
    await expect(page.getByRole("listitem").filter({ hasText: "Sucursal ficticia" })).toBeVisible();
    expect(servidor.llamadas.filter((l) => l.destino.endsWith("/retirar"))).toHaveLength(0);

    await page.getByRole("button", { name: "Retirar Sucursal ficticia" }).click();
    await page.getByRole("group", { name: "Confirmar el retiro de Sucursal ficticia" }).getByRole("button", { name: "Retirar", exact: true }).click();
    await expect(page.getByRole("status").filter({ hasText: "Sede retirada." })).toBeVisible();
    await expect(page.getByRole("listitem").filter({ hasText: "Sucursal ficticia" })).toHaveCount(0);
  });

  test("una organización encargada crea y retira clientes", async ({ page }) => {
    const servidor = nuevoServidor(true);
    await abrirVista(page, servidor, ["admin_organizacion"], CLIENTES);
    await page.getByLabel("Razón social", { exact: true }).fill("Cliente Ficticio S.A.");
    await page.getByLabel("RUC", { exact: true }).fill("123");
    await page.getByRole("button", { name: "Agregar cliente", exact: true }).click();
    await expect(page.getByRole("alert").filter({ hasText: "El RUC debe tener 13 dígitos." })).toBeVisible();
    await expect(page.getByLabel("RUC", { exact: true })).toHaveAttribute("aria-invalid", "true");

    await page.getByLabel("RUC", { exact: true }).fill("1790000000001");
    await page.getByRole("button", { name: "Agregar cliente", exact: true }).click();
    await expect(page.getByRole("listitem").filter({ hasText: "Cliente Ficticio S.A." })).toBeVisible();
    const post = servidor.llamadas.find((l) => l.metodo === "POST" && l.destino === "/organizacion/clientes")!;
    expect(Object.keys(post.cuerpo!)).not.toContain("tenant_id");

    await expect(page.getByRole("status").filter({ hasText: "Cliente agregado." })).toBeVisible();
    await page.getByRole("button", { name: "Retirar Cliente Ficticio S.A." }).click();
    await page.getByRole("group", { name: "Confirmar el retiro de Cliente Ficticio S.A." }).getByRole("button", { name: "Retirar", exact: true }).click();
    await expect(page.getByRole("listitem").filter({ hasText: "Cliente Ficticio S.A." })).toHaveCount(0);
  });

  test("una organización que no es encargada ve la explicación y ningún formulario de clientes", async ({ page }) => {
    const servidor = nuevoServidor(false);
    await abrirVista(page, servidor, ["admin_organizacion"], CLIENTES);
    await expect(page.getByText("Esta sección es solo para organizaciones que tratan datos por encargo de otras.")).toBeVisible();
    await expect(page.getByText("aquí no hay clientes que administrar.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Agregar cliente" })).toHaveCount(0);
    await expect(page.getByRole("alert").filter({ hasText: /./ })).toHaveCount(0);
    const texto = await page.locator("body").innerText();
    for (const jerga of ["NO_ES_ENCARGADA", "409", "hexadecimales"]) expect(texto).not.toContain(jerga);
  });

  test("la vigencia se muestra en formato local y una vencida lo dice con texto", async ({ page }) => {
    const servidor = nuevoServidor(true);
    servidor.clientes.push(
      { id: "c-1", razon_social: "Cliente Vigente", ruc: "1790000000001", contrato_sha256: null, vigente_hasta: "2099-10-28", retirado_en: null },
      { id: "c-2", razon_social: "Cliente Vencido", ruc: "1790000000002", contrato_sha256: null, vigente_hasta: "2020-01-05", retirado_en: null },
    );
    await abrirVista(page, servidor, ["admin_organizacion"], CLIENTES);
    await expect(page.getByText("Vigente hasta 28/10/2099")).toBeVisible();
    await expect(page.getByText("Vigencia vencida el 05/01/2020")).toBeVisible();
    await expect(page.getByLabel("Huella de integridad del contrato (SHA-256, opcional)")).toBeVisible();
    await expect(page.getByText("Si no la tienes, déjala vacía.")).toBeVisible();
  });

  test("el dpo consulta pero no ve formularios ni botones de retirar", async ({ page }) => {
    const servidor = nuevoServidor();
    servidor.sedes.push({
      id: "s-1", nombre: "Sede solo lectura", direccion: "Calle", ciudad: "Ciudad", provincia: "Provincia",
      es_principal: true, contacto_spdp: null, contacto_titulares: null, medidas: null, retirada_en: null,
    });
    await abrirVista(page, servidor, ["dpo"], SEDES);
    await expect(page.getByRole("listitem").filter({ hasText: "Sede solo lectura" })).toBeVisible();
    await expect(page.getByText("Puedes consultar las sedes, pero no modificarlas.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Agregar sede" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: /^Retirar/ })).toHaveCount(0);
  });
});
