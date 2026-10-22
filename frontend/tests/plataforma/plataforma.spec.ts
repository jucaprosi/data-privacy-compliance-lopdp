import { expect, test, type Page, type Request } from "@playwright/test";

const CODIGO = "codigo-secreto-de-invitacion-1234567890";

interface Escenario {
  accesoDenegado?: boolean;
  aceptarEstado?: number;
  aceptarDetalle?: string;
}

async function simularApi(page: Page, escenario: Escenario = {}): Promise<Request[]> {
  const llamadas: Request[] = [];
  const organizaciones = [{
    id: "tenant-001",
    nombre_comercial: "Acme Ecuador",
    razon_social: "Acme Ecuador S.A.",
    ruc_identificacion: "0999999999001",
    activo: true,
    created_at: "2026-10-20T12:00:00Z",
    email_admin_inicial: "admin@acme.ec",
    invitacion_estado: "pendiente",
  }];

  await page.route("**/api/v1/plataforma/**", async (route) => {
    const peticion = route.request();
    llamadas.push(peticion);
    const destino = new URL(peticion.url()).pathname.replace("/api/v1/plataforma", "");
    const metodo = peticion.method();
    const responder = (status: number, cuerpo: unknown) => route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

    if (destino === "/organizaciones" && metodo === "GET") {
      if (escenario.accesoDenegado) return responder(403, { detail: "No autorizado como operador_plataforma." });
      return responder(200, organizaciones);
    }
    if (destino === "/organizaciones" && metodo === "POST") {
      const datos = JSON.parse(peticion.postData() ?? "{}");
      organizaciones.push({
        id: "tenant-002",
        nombre_comercial: datos.nombre_comercial,
        razon_social: datos.razon_social,
        ruc_identificacion: datos.ruc_identificacion,
        activo: true,
        created_at: "2026-10-22T10:00:00Z",
        email_admin_inicial: datos.email_admin_inicial,
        invitacion_estado: "pendiente",
      });
      return responder(201, { tenant_id: "tenant-002", invitacion_id: "inv-002", codigo_invitacion: CODIGO, expira_en: "2026-10-24T10:00:00Z", email_invitado: datos.email_admin_inicial });
    }
    if (destino === "/invitaciones/inv-002/revocar" && metodo === "POST") {
      organizaciones[1].invitacion_estado = "revocada";
      return responder(200, { ok: true, estado: "revocada" });
    }
    if (destino === "/invitaciones/aceptar" && metodo === "POST") {
      if (escenario.aceptarEstado) return responder(escenario.aceptarEstado, { detail: escenario.aceptarDetalle });
      return responder(200, { tenant_id: "tenant-001", user_id: "user-001", email: "admin@acme.ec", rol_asignado: "admin_organizacion", mensaje: "Ya formas parte de Acme Ecuador." });
    }
    return responder(404, { detail: "No simulado" });
  });
  return llamadas;
}

test("lista organizaciones sin exponer claves técnicas ni tokens de gobernanza", async ({ page }) => {
  await simularApi(page);
  await page.goto("/plataforma");
  await expect(page.getByRole("heading", { name: "Organizaciones", exact: true })).toBeVisible();
  await expect(page.getByText("Acme Ecuador", { exact: true })).toBeVisible();
  await expect(page.getByText("Acme Ecuador S.A.")).toBeVisible();
  await expect(page.getByText("admin@acme.ec")).toBeVisible();
  await expect(page.getByText("Pendiente")).toBeVisible();
  const texto = await page.locator("main").innerText();
  expect(texto).not.toContain("tenant-001");
  expect(texto).not.toContain("inv-002");
  expect(texto).not.toContain("¤");
  expect(texto).not.toContain("¦");
});

test("crea, muestra el código una sola vez y permite revocar la invitación emitida", async ({ page }) => {
  const llamadas = await simularApi(page);
  await page.goto("/plataforma");
  await page.getByLabel("Nombre comercial").fill("Nueva Empresa");
  await page.getByLabel("Razón social").fill("Nueva Empresa S.A.");
  await page.getByLabel("RUC o identificación").fill("1799999999001");
  await page.getByLabel("Sector").fill("Tecnología");
  await page.getByLabel("Correo del administrador inicial").fill("admin@nueva.ec");
  await page.getByLabel("Tamaño").selectOption("mediana");
  await page.getByRole("button", { name: "Crear y emitir invitación" }).click();

  await expect(page.getByTestId("codigo-invitacion")).toHaveText(CODIGO);
  await expect(page.getByText("visible una sola vez", { exact: false })).toBeVisible();
  const alta = llamadas.find((llamada) => llamada.method() === "POST" && new URL(llamada.url()).pathname.endsWith("/organizaciones"));
  expect(JSON.parse(alta?.postData() ?? "{}")).toMatchObject({ nombre_comercial: "Nueva Empresa", tamano: "mediana", email_admin_inicial: "admin@nueva.ec" });

  await page.getByRole("button", { name: "Revocar invitación" }).click();
  await expect(page.getByTestId("codigo-invitacion")).toHaveCount(0);
  expect(llamadas.some((llamada) => new URL(llamada.url()).pathname.endsWith("/invitaciones/inv-002/revocar"))).toBe(true);

  await page.reload();
  await expect(page.getByTestId("codigo-invitacion")).toHaveCount(0);
});

test("un usuario no operador ve acceso denegado y nunca recibe la lista", async ({ page }) => {
  await simularApi(page, { accesoDenegado: true });
  await page.goto("/plataforma");
  await expect(page.getByRole("heading", { name: "Acceso denegado" })).toBeVisible();
  await expect(page.getByText("Acme Ecuador", { exact: true })).toHaveCount(0);
});

test("lee el código de la URL, lo retira y acepta la invitación", async ({ page }) => {
  const llamadas = await simularApi(page);
  await page.goto(`/invitacion?codigo=${encodeURIComponent(CODIGO)}`);
  await expect(page).toHaveURL(/\/invitacion$/);
  await expect(page.getByLabel("Código de invitación")).toHaveValue(CODIGO);
  await page.getByLabel("Nombre para mostrar").fill("Ana Administradora");
  await page.getByRole("button", { name: "Aceptar e ingresar" }).click();
  await expect(page.getByRole("heading", { name: "Invitación aceptada" })).toBeVisible();
  const aceptar = llamadas.find((llamada) => new URL(llamada.url()).pathname.endsWith("/invitaciones/aceptar"));
  expect(JSON.parse(aceptar?.postData() ?? "{}")).toEqual({ codigo: CODIGO, nombre_usuario: "Ana Administradora" });
  expect(await page.locator("main").innerText()).not.toMatch(/[¤¦]/);
});

for (const caso of [
  { nombre: "correo distinto", status: 403, detalle: "El correo no coincide.", mensaje: "correo distinto" },
  { nombre: "caducada", status: 400, detalle: "La invitación está caducada.", mensaje: "ha caducado" },
  { nombre: "revocada", status: 400, detalle: "La invitación fue revocada.", mensaje: "fue revocada" },
  { nombre: "ya usada", status: 400, detalle: "La invitación ya fue aceptada.", mensaje: "ya fue utilizada" },
  { nombre: "código inválido", status: 404, detalle: "Código no encontrado.", mensaje: "no es válido" },
]) {
  test(`explica el error de invitación ${caso.nombre}`, async ({ page }) => {
    await simularApi(page, { aceptarEstado: caso.status, aceptarDetalle: caso.detalle });
    await page.goto("/invitacion");
    await page.getByLabel("Código de invitación").fill(CODIGO);
    await page.getByRole("button", { name: "Aceptar e ingresar" }).click();
    await expect(page.locator('p[role="alert"]')).toContainText(caso.mensaje);
  });
}
