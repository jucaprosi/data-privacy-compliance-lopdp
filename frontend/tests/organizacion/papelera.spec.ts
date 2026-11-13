// ¤arbitro
// ¤¤qa-engineer
/**
 * Arnés de interfaz de ORG-20: papelera (restaurar) y exportación de los datos de la organización.
 *
 * Con sesión, las pantallas leen GET /organizacion/papelera y las exportaciones; restaurar y solicitar son
 * llamadas al servidor y el cuerpo nunca lleva la organización ni la identidad. El servidor se simula con
 * page.route sobre /api/v1/** con la forma real de sus respuestas. Datos ficticios.
 *
 * Mutación documentada: si «Restaurar» solo quitara la fila del estado local (sin POST), «restaurar llama al
 * servidor» falla porque no habría llamada de restauración registrada.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, abrirSubmenu, barraDeMenus, configurarProyecto, submenuPorNombre } from "../utiles";
import { credencialSimulada, fijarAjustes, ruta, sembrarSesion } from "../auth/utilesAuth";

interface Servidor {
  registros: Array<{ entidad: string; id: string; nombre: string; retirado_en: string }>;
  exportacion: "ninguna" | "pendiente" | "lista" | "caducada";
  consultasPendiente: number;
  llamadas: Array<{ metodo: string; destino: string; cuerpo: Record<string, unknown> | null; rol: string | undefined }>;
}

const nuevo = (): Servidor => ({
  registros: [
    { entidad: "sedes", id: "s-1", nombre: "Sede Norte ficticia", retirado_en: "2030-01-05T10:00:00+00:00" },
    { entidad: "clientes", id: "c-1", nombre: "Cliente Ficticio S.A.", retirado_en: "2030-01-04T10:00:00+00:00" },
  ],
  exportacion: "ninguna",
  consultasPendiente: 0,
  llamadas: [],
});

const ENTIDADES = [
  { entidad: "sedes", etiqueta: "Sedes" },
  { entidad: "clientes", etiqueta: "Clientes por encargo" },
];

async function simular(page: Page, servidor: Servidor, roles: string[], enCurso = false): Promise<void> {
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    const destino = ruta(peticion.url());
    const metodo = peticion.method();
    const json = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });
    if (destino === "/organizacion/me/roles") {
      return json(200, { user_id: "u", tenant_id: "t-prueba", roles: roles.map((role) => ({ role, area_id: null, area_nombre: null, valid_to: null })) });
    }
    if (!destino.startsWith("/organizacion/papelera") && !destino.startsWith("/organizacion/exportaciones")) {
      return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
    }
    const cuerpo = metodo === "GET" || !peticion.postData() ? null : (JSON.parse(peticion.postData() ?? "{}") as Record<string, unknown>);
    servidor.llamadas.push({ metodo, destino, cuerpo, rol: peticion.headers()["x-role"] });

    if (destino === "/organizacion/papelera" && metodo === "GET") {
      const filtro = new URL(peticion.url()).searchParams.get("entidad");
      const registros = servidor.registros.filter((r) => !filtro || r.entidad === filtro);
      return json(200, { registros, entidades: ENTIDADES });
    }
    const restaurar = destino.match(/^\/organizacion\/papelera\/(\w+)\/([\w-]+)\/restaurar$/);
    if (restaurar && metodo === "POST") {
      servidor.registros = servidor.registros.filter((r) => r.id !== restaurar[2]);
      return json(200, {});
    }
    if (destino === "/organizacion/exportaciones" && metodo === "POST") {
      if (enCurso) return json(409, { detail: "Ya hay una exportación en preparación.", code: "EXPORTACION_EN_CURSO" });
      servidor.exportacion = "pendiente";
      return json(202, { id: "e-1" });
    }
    if (destino === "/organizacion/exportaciones/e-1" && metodo === "GET") {
      if (servidor.exportacion === "pendiente" && servidor.consultasPendiente++ >= 1) servidor.exportacion = "lista";
      if (servidor.exportacion === "lista") {
        return json(200, { estado: "lista", completa: false, url: "/organizacion/exportaciones/e-1/archivo", sha256: "a".repeat(64), caduca_en: "2030-02-03T00:00:00+00:00" });
      }
      return json(200, { estado: servidor.exportacion, completa: false });
    }
    return json(404, { detail: "No simulado", code: "NOT_MOCKED", action_required: null });
  });
}

async function abrir(page: Page, servidor: Servidor, roles: string[], submenu: RegExp, enCurso = false): Promise<void> {
  await fijarAjustes(page);
  await sembrarSesion(page, credencialSimulada());
  await simular(page, servidor, roles, enCurso);
  await abrirAppLimpia(page);
  if (!(await barraDeMenus(page).getByRole("button", { name: "Inventario", exact: true }).isVisible())) {
    await configurarProyecto(page, "Entidad ORG-20");
  }
  await abrirSubmenu(page, submenuPorNombre(submenu)!);
}

const PAPELERA = /Papelera/;
const EXPORTAR = /Exportar datos/;

test.describe("Papelera y exportación de datos (ORG-20)", () => {
  test("lista lo retirado, filtra por tipo y restaura llamando al servidor", async ({ page }) => {
    const servidor = nuevo();
    await abrir(page, servidor, ["admin_organizacion"], PAPELERA);
    await expect(page.getByRole("table", { name: "Elementos retirados" })).toBeVisible();
    await expect(page.getByText("05/01/2030")).toBeVisible();

    await page.getByLabel("Tipo de elemento").selectOption("clientes");
    await expect(page.getByRole("button", { name: "Restaurar Sede Norte ficticia" })).toHaveCount(0);

    await page.getByLabel("Tipo de elemento").selectOption("");
    await page.getByRole("button", { name: "Restaurar Sede Norte ficticia" }).click();
    const dialogo = page.getByRole("dialog", { name: "¿Restaurar Sede Norte ficticia?" });
    await expect(dialogo).toContainText("Vuelve a aparecer donde estaba antes de retirarlo.");
    await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
    await page.keyboard.press("Escape");
    await expect(dialogo).toHaveCount(0);
    expect(servidor.llamadas.filter((l) => l.destino.endsWith("/restaurar"))).toHaveLength(0);

    await page.getByRole("button", { name: "Restaurar Sede Norte ficticia" }).click();
    await page.getByRole("dialog").getByRole("button", { name: "Restaurar", exact: true }).click();
    await expect(page.getByRole("status").filter({ hasText: "Sede Norte ficticia restaurado." })).toBeVisible();
    const llamada = servidor.llamadas.find((l) => l.destino === "/organizacion/papelera/sedes/s-1/restaurar")!;
    expect(llamada.metodo).toBe("POST");
    expect(llamada.rol).toBe("admin_organizacion");
    expect(llamada.cuerpo).toBeNull();
    await expect(page.getByRole("button", { name: "Restaurar Sede Norte ficticia" })).toHaveCount(0);
  });

  test("una papelera vacía lo dice y el implementador la usa", async ({ page }) => {
    const servidor = nuevo();
    servidor.registros = [];
    await abrir(page, servidor, ["implementador"], PAPELERA);
    await expect(page.getByText("La papelera está vacía.")).toBeVisible();
    const texto = await page.locator("body").innerText();
    for (const jerga of ["sedes_clientes", "retirado_en", "404", "tenant"]) expect(texto).not.toContain(jerga);
  });

  test("exportar: «En preparación», luego el enlace con su fecha, y el aviso de datos personales", async ({ page }) => {
    const servidor = nuevo();
    await abrir(page, servidor, ["admin_organizacion"], EXPORTAR);
    await expect(page.getByRole("note")).toContainText("El archivo incluye datos personales.");
    await page.getByRole("button", { name: "Solicitar exportación", exact: true }).click();
    await expect(page.getByRole("status").filter({ hasText: "En preparación" })).toBeVisible();
    await expect(page.getByRole("link", { name: "Descargar la exportación" })).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText("Disponible hasta el 03/02/2030.")).toBeVisible();
    const post = servidor.llamadas.find((l) => l.metodo === "POST" && l.destino === "/organizacion/exportaciones")!;
    expect(post.cuerpo).toBeNull();
    expect(post.rol).toBe("admin_organizacion");
  });

  test("ya hay una exportación en preparación: aviso sin alarma", async ({ page }) => {
    await abrir(page, nuevo(), ["admin_organizacion"], EXPORTAR, true);
    await page.getByRole("button", { name: "Solicitar exportación", exact: true }).click();
    await expect(page.getByRole("status").filter({ hasText: "Ya hay una exportación en preparación." })).toBeVisible();
    await expect(page.getByRole("alert").filter({ hasText: /./ })).toHaveCount(0);
  });

  test("el implementador no exporta: se le explica", async ({ page }) => {
    await abrir(page, nuevo(), ["implementador"], EXPORTAR);
    await expect(page.getByText("Solo la persona administradora de la organización puede exportar los datos.")).toBeVisible();
    await expect(page.getByRole("button", { name: "Solicitar exportación" })).toHaveCount(0);
  });
});
