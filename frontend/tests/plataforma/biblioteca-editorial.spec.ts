// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤arbitro
// ¤¤developer-architect
/**
 * BIB-412 · Biblioteca editorial desde Plataforma (governance/especificaciones/BIB-412.md). API simulada:
 * no acredita persistencia ni RLS. Corre en el proyecto «desarrollo» (usa `fijarAjustes`).
 *
 * Mutaciones (cada una hace fallar la prueba que se indica):
 *  - m1: exigir una organización activa en `/plataforma/biblioteca` -> «llega desde /plataforma…».
 *  - m2: enviar `X-Tenant-ID` en las rutas editoriales -> «ninguna petición editorial lleva X-Tenant-ID».
 *  - m3: mostrar «Publicar versión» sin capacidades -> «un operador sin capacidades…».
 *  - m4: mandar al operador a la entrada de la demo -> «la entrada del equipo editorial lleva…».
 */
import { expect, test, type Page, type Request } from "@playwright/test";
import { BOTON_GOOGLE, credencialSimulada, fijarAjustes, googleSimulado, ruta, TENANT_PRUEBA } from "../auth/utilesAuth";

const SIN_PERMISOS = "No tienes permisos editoriales en la Biblioteca. Los asigna el equipo de la plataforma.";
const version = { id: "v1", codigo: "BIB-001", version: "1.0", formato: "DOCX", ficha: null, responsable_id: "otro",
  autores: ["otro"], estado: "en_revision", generacion: 1, sha256: null, nombre_archivo: null, sustituye_id: null,
  creada_en: "2026-11-25T12:00:00Z" };

async function simular(page: Page, capacidades: string[]): Promise<Request[]> {
  const llamadas: Request[] = [];
  page.on("request", (r) => { if (r.url().includes("/api/v1/")) llamadas.push(r); });
  await page.route("**/api/v1/**", (r) => r.fulfill({ status: 404, json: { detail: "No simulado" } }));
  await page.route("**/api/v1/plataforma/organizaciones", (r) => r.fulfill({ json: [] }));
  await page.route("**/api/v1/biblioteca/editorial", (r) => r.fulfill({ json: {
    actor_id: "operador", capacidades, versiones: capacidades.length ? [version] : [], revisiones: [] } }));
  return llamadas;
}

const editoriales = (llamadas: Request[]) => llamadas.filter((l) => ruta(l.url()).startsWith("/biblioteca/"));

test.describe("Biblioteca editorial desde Plataforma (BIB-412)", () => {
  test("un operador con editor llega desde /plataforma a la administración, sin selector de organización", async ({ page }) => {
    await fijarAjustes(page, { modo: "headers", tenant: TENANT_PRUEBA });
    await simular(page, ["editor"]);
    await page.goto("/plataforma");
    const nav = page.getByRole("navigation", { name: "Plataforma" });
    await expect(nav.getByRole("link", { name: "Organizaciones" })).toHaveAttribute("aria-current", "page");
    await nav.getByRole("link", { name: "Biblioteca editorial" }).click();
    await expect(page).toHaveURL(/\/plataforma\/biblioteca$/);
    await expect(nav.getByRole("link", { name: "Biblioteca editorial" })).toHaveAttribute("aria-current", "page");
    await expect(page.getByRole("heading", { name: "Administración editorial", level: 1 })).toBeVisible();
    await expect(page.getByText("Administración editorial · Plataforma")).toBeVisible();
    await expect(page.getByRole("button", { name: /BIB-001 · 1.0/ })).toBeVisible();
    await expect(page.getByRole("combobox", { name: /organizaci/i })).toHaveCount(0);
  });

  test("ninguna petición editorial lleva X-Tenant-ID ni X-Role", async ({ page }) => {
    await fijarAjustes(page, { modo: "headers", tenant: TENANT_PRUEBA });
    const llamadas = await simular(page, ["editor"]);
    await page.goto("/plataforma/biblioteca");
    await expect(page.getByRole("heading", { name: "Administración editorial", level: 1 })).toBeVisible();
    await expect.poll(() => editoriales(llamadas).length).toBeGreaterThan(0);
    const lista = editoriales(llamadas);
    for (const l of lista) {
      expect(l.headers()["x-tenant-id"], ruta(l.url())).toBeUndefined();
      expect(l.headers()["x-role"], ruta(l.url())).toBeUndefined();
    }
  });

  test("un operador sin capacidades ve el texto y ninguna acción", async ({ page }) => {
    await fijarAjustes(page, { modo: "headers", tenant: TENANT_PRUEBA });
    await simular(page, []);
    await page.goto("/plataforma/biblioteca");
    await expect(page.getByText(SIN_PERMISOS)).toBeVisible();
    await expect(page.getByRole("button", { name: "Publicar versión" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Crear versión en revisión" })).toHaveCount(0);
  });

  test.describe("entradas del login en la demo", () => {
    const operador = credencialSimulada({ email: "operador@plataforma.test", nombre: "Operador Prueba" });

    async function login(page: Page, plataforma: number): Promise<Request[]> {
      await fijarAjustes(page, { modo: "oidc", tenant: null });
      await googleSimulado(page, operador.token);
      const llamadas: Request[] = [];
      page.on("request", (r) => { if (r.url().includes("/api/v1/")) llamadas.push(r); });
      await page.route("**/api/v1/**", (r) => r.fulfill({ status: 404, json: { detail: "No simulado" } }));
      await page.route("**/api/v1/entorno", (r) => r.fulfill({ json: { entorno: "demo", datos_ficticios: true } }));
      await page.route("**/api/v1/organizacion/mis-organizaciones", (r) => r.fulfill({ status: 403, json: { detail: "No registrado." } }));
      await page.route("**/api/v1/demo/entrar", (r) => r.fulfill({ status: 503, json: { codigo: "DEMO_NO_DISPONIBLE" } }));
      await page.route("**/api/v1/plataforma/organizaciones", (r) => r.fulfill({
        status: plataforma, json: plataforma === 200 ? [] : { detail: "Solo el operador." } }));
      await page.route("**/api/v1/biblioteca/editorial", (r) => r.fulfill({ json: {
        actor_id: "operador", capacidades: ["editor"], versiones: [], revisiones: [] } }));
      // QA-14: en `next dev` cada ruta se compila bajo demanda, y la navegación del cliente a /login pide, aparte del HTML,
      // la carga RSC (`/login?_rsc=`) y el chunk cliente de la página; con varios workers a la vez eso superaba el `expect`.
      // Se calientan las tres cosas antes de medir (sin tocar timeouts ni reintentos): el HTML y el chunk, con una
      // navegación real a /login; la carga RSC, con su petición; y /plataforma/biblioteca, que usa la prueba de más abajo.
      await page.goto("/login");
      await page.request.get("/login", { headers: { RSC: "1" } });
      await page.request.get("/plataforma/biblioteca");
      // El servidor pinta el aviso de entorno de la demo; aquí se pinta ya hidratada la página y se llega al login
      // por navegación del cliente (si se añadiera antes de hidratar, React lo descartaría).
      await page.goto("/plataforma");
      await expect(page.getByRole("navigation", { name: "Plataforma" })).toBeVisible();
      await page.evaluate(() => {
        const aviso = document.createElement("div");
        aviso.setAttribute("data-testid", "aviso-entorno");
        aviso.setAttribute("data-entorno", "demo");
        document.body.append(aviso);
        (window as unknown as { next: { router: { push(r: string): void } } }).next.router.push("/login");
      });
      await expect(page.getByRole("heading", { name: "Plataforma LOPDP 360" })).toBeVisible();
      return llamadas;
    }

    test("las dos entradas tienen la misma forma, con su etiqueta y su ayuda", async ({ page }) => {
      await login(page, 200);
      const comercial = page.getByRole("group", { name: "Entrar como equipo comercial" });
      const editorial = page.getByRole("group", { name: "Entrar como equipo editorial" });
      await expect(comercial).toContainText("Soy del equipo comercial");
      await expect(comercial).toContainText("Para quienes presentan la demo a una organización. Entras con tu cuenta de Google.");
      await expect(editorial).toContainText("Soy del equipo editorial");
      await expect(editorial).toContainText("Para quienes mantienen el catálogo de plantillas de la plataforma. Entras con tu cuenta de Google de operador.");
      await expect(comercial).toHaveAccessibleDescription(/Para quienes presentan la demo/);
      await expect(editorial).toHaveAccessibleDescription(/Para quienes mantienen el catálogo/);
      // Etiqueta y ayuda encima del botón de Google de cada entrada; la comercial va antes que la editorial.
      const y = async (donde: ReturnType<Page["getByText"]>) => (await donde.boundingBox())!.y;
      const botonComercial = await y(page.getByTestId("login-boton-google"));
      expect(await y(page.getByText("Soy del equipo comercial"))).toBeLessThan(botonComercial);
      expect(await y(page.getByText("Soy del equipo editorial"))).toBeLessThan(await y(page.getByTestId("login-boton-google-editorial")));
      expect(botonComercial).toBeLessThan(await y(page.getByText("Soy del equipo editorial")));
    });

    test("la entrada del equipo editorial lleva al operador a /plataforma/biblioteca", async ({ page }) => {
      const llamadas = await login(page, 200);
      llamadas.length = 0;
      await page.getByTestId("login-boton-google-editorial").getByRole("button", { name: BOTON_GOOGLE }).click();
      await expect(page).toHaveURL(/\/plataforma\/biblioteca$/);
      await expect(page.getByRole("heading", { name: "Administración editorial", level: 1 })).toBeVisible();
      expect(llamadas.some((l) => ruta(l.url()) === "/demo/entrar")).toBe(false);
    });

    test("sin cuenta vinculada, la entrada editorial muestra el aviso «no registrada»", async ({ page }) => {
      await login(page, 403);
      await page.getByTestId("login-boton-google-editorial").getByRole("button", { name: BOTON_GOOGLE }).click();
      await expect(page.getByRole("heading", { name: "Esta cuenta no tiene acceso" })).toBeVisible();
      await expect(page).toHaveURL(/\/login$/);
    });

    test("un vendedor sigue entrando por la entrada de la demo", async ({ page }) => {
      const llamadas = await login(page, 200);
      llamadas.length = 0;  // solo lo que ocurre al pulsar
      await page.getByTestId("login-boton-google").getByRole("button", { name: BOTON_GOOGLE }).click();
      await expect.poll(() => llamadas.some((l) => ruta(l.url()) === "/demo/entrar")).toBe(true);
      expect(llamadas.some((l) => ruta(l.url()) === "/plataforma/organizaciones")).toBe(false);
    });
  });
});
