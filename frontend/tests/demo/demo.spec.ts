/**
 * DEMO-04 · Interfaz demo: «Ver como», «Terminar demo» y pantallas de error. ¤demo
 *
 * Los 7 criterios de UX_DEMO_EVYDENTIA.md §6 más los de la ficha. Como EP-02, compila UNA vez en
 * una copia aislada y arranca la misma compilación con APP_ENV production, pruebas y demo. La API
 * de la demo (contrato congelado §1.7) y Google se simulan en el navegador: no hay backend, ni base,
 * ni datos reales. Solo valores generados y correos `.invalid`.
 */
import { type ChildProcess, execSync, spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { expect, test, type Page, type Request } from "@playwright/test";

const RAIZ = path.resolve(__dirname, "..", "..");
const COPIA = path.join(os.tmpdir(), "lopdp-e2e-demo04");
const BASE = Number(process.env.PLAYWRIGHT_PORT ?? 3000) + 50;
const ENTORNOS = { production: BASE, pruebas: BASE + 1, demo: BASE + 2 } as const;
type Caso = keyof typeof ENTORNOS;
const url = (caso: Caso, ruta = "/login") => `http://localhost:${ENTORNOS[caso]}${ruta}`;
const EXCLUIR = new Set(["node_modules", ".next", "test-results", "playwright-report", "tests"]);
const servidores: ChildProcess[] = [];

const ROLES = ["admin_organizacion", "dpo", "coordinador", "implementador", "responsable_area", "auditor"];
const ETIQUETAS: Record<string, string> = {
  admin_organizacion: "Administrador de la organización",
  dpo: "DPO",
  coordinador: "Coordinador",
  implementador: "Implementador",
  responsable_area: "Responsable de área",
  auditor: "Auditor",
};
const NOMBRES = ["Ana Torres", "Diego Salas", "Luis Paredes", "Marta Ríos", "Sofía León", "Raúl Vega"];
// Desordenadas a propósito: la interfaz ordena por rol.
const PERSONAS = [...ROLES].reverse().map((rol) => ({
  usuario_id: `persona-${rol}`,
  nombre: NOMBRES[ROLES.indexOf(rol)],
  rol,
  rol_etiqueta: ETIQUETAS[rol],
  unidad: rol === "responsable_area" ? "Talento Humano" : null,
}));
const persona = (rol: string) => PERSONAS.find((p) => p.rol === rol)!;
const estado = (rol = "admin_organizacion") => ({
  demo: true,
  organizacion: { tenant_id: "tenant-demo-generado", nombre: "Cooperativa Demo" },
  persona_activa: persona(rol),
  personas: PERSONAS,
  vence_en: null,
});

function tokenFalso(): string {
  const b64 = (o: object) => Buffer.from(JSON.stringify(o)).toString("base64url");
  const carga = { sub: "vendedor-generado", email: "vendedor@ventas.invalid", name: "Vendedor Prueba", exp: Math.floor(Date.now() / 1000) + 3600 };
  return `${b64({ alg: "none", typ: "JWT" })}.${b64(carga)}.firma`;
}

function compilarUnaVez(): void {
  const enlace = path.join(COPIA, "node_modules");
  if (fs.existsSync(enlace)) fs.unlinkSync(enlace);
  fs.rmSync(COPIA, { recursive: true, force: true });
  fs.mkdirSync(COPIA, { recursive: true });
  for (const nombre of fs.readdirSync(RAIZ)) {
    if (!EXCLUIR.has(nombre)) fs.cpSync(path.join(RAIZ, nombre), path.join(COPIA, nombre), { recursive: true });
  }
  fs.symlinkSync(path.join(RAIZ, "node_modules"), enlace, "junction");
  const env: NodeJS.ProcessEnv = { ...process.env, NEXT_TELEMETRY_DISABLED: "1", NEXT_PUBLIC_GOOGLE_CLIENT_ID: "cliente-generado.invalid" };
  delete env.APP_ENV;
  execSync("npx next build --no-lint", { cwd: COPIA, env, stdio: "ignore" });
}

async function esperar(direccion: string): Promise<void> {
  for (let i = 0; i < 120; i++) {
    try {
      if ((await fetch(direccion)).status < 500) return;
    } catch {
      // Arrancando.
    }
    await new Promise((r) => setTimeout(r, 500));
  }
  throw new Error(`No arrancó ${direccion}`);
}

test.describe.configure({ mode: "serial" });

test.beforeAll(async () => {
  test.setTimeout(600_000);
  compilarUnaVez();
  for (const [caso, puerto] of Object.entries(ENTORNOS) as [Caso, number][]) {
    const env: NodeJS.ProcessEnv = { ...process.env, NEXT_TELEMETRY_DISABLED: "1", APP_ENV: caso };
    servidores.push(spawn(`npx next start --port ${puerto}`, { cwd: COPIA, env, shell: true, stdio: "ignore" }));
  }
  await Promise.all((Object.keys(ENTORNOS) as Caso[]).map((c) => esperar(url(c, "/robots.txt"))));
});

test.afterAll(() => {
  for (const s of servidores) {
    if (s.pid === undefined) continue;
    if (process.platform === "win32") execSync(`taskkill /pid ${s.pid} /T /F`, { stdio: "ignore" });
    else s.kill("SIGTERM");
  }
});

const json = (status: number, cuerpo: unknown) => ({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });

interface Simulacion {
  entorno?: string | null;
  estado?: number;
  entrar?: Array<number | "colgar">;
  persona?: number;
}

/** API simulada. Devuelve las peticiones vistas para inspeccionar cabeceras. */
async function simular(page: Page, s: Simulacion = {}): Promise<Request[]> {
  const vistas: Request[] = [];
  const entrar = [...(s.entrar ?? [201])];
  page.on("request", (r) => {
    if (r.url().includes("/api/v1/")) vistas.push(r);
  });
  await page.route("https://accounts.google.com/gsi/client", (r) =>
    r.fulfill({
      contentType: "application/javascript",
      body: `window.google={accounts:{id:{initialize:function(o){window.__cb=o.callback},renderButton:function(el){var b=document.createElement('button');b.textContent='Continuar con Google';b.setAttribute('data-testid','google-falso');b.onclick=function(){window.__cb({credential:${JSON.stringify(tokenFalso())}})};el.appendChild(b)},disableAutoSelect:function(){}}}};`,
    }),
  );
  await page.route("**/api/v1/entorno", (r) =>
    s.entorno === null ? r.fulfill({ status: 503, body: "" }) : r.fulfill(json(200, { entorno: s.entorno ?? "demo" })),
  );
  await page.route("**/api/v1/demo/estado", (r) => {
    const rol = r.request().headers()["x-role"] ?? "admin_organizacion";
    const st = s.estado ?? 200;
    return r.fulfill(st === 200 ? json(200, estado(rol)) : json(st, { codigo: st === 401 ? "DEMO_VENCIDA" : "NO" }));
  });
  await page.route("**/api/v1/demo/persona", (r) => {
    const st = s.persona ?? 200;
    if (st !== 200) return r.fulfill(json(st, { codigo: st === 403 ? "DEMO_PERSONA_AJENA" : "DEMO_VENCIDA" }));
    const id = (r.request().postDataJSON() as { persona_usuario_id: string }).persona_usuario_id;
    return r.fulfill(json(200, { persona_activa: PERSONAS.find((p) => p.usuario_id === id) }));
  });
  await page.route("**/api/v1/demo/terminar", (r) => r.fulfill(json(200, { estado: "vencida" })));
  await page.route("**/api/v1/demo/entrar", async (r) => {
    const paso = entrar.length > 1 ? entrar.shift()! : entrar[0];
    if (paso === "colgar") return; // Nunca responde: la interfaz corta a los 60 s.
    return r.fulfill(paso === 201 ? json(201, estado()) : json(paso, { codigo: paso === 503 ? "DEMO_NO_DISPONIBLE" : "DEMO_OCUPADA" }));
  });
  return vistas;
}

const aviso = (p: Page) => p.getByTestId("aviso-entorno");
const verComo = (p: Page) => p.getByTestId("demo-ver-como");

async function sinFiltraciones(page: Page): Promise<void> {
  const texto = await page.locator("body").innerText();
  expect(texto).not.toMatch(/@.*\.invalid/);
  expect(texto).not.toMatch(/[¤¦]/);
}

test("1 · production: sin aviso ni piezas de demo", async ({ page }) => {
  await simular(page, { entorno: "production" });
  await page.goto(url("production"));
  await expect(page.getByTestId("login-boton-google")).toBeAttached();
  await expect(aviso(page)).toHaveCount(0);
  await expect(verComo(page)).toHaveCount(0);
  await expect(page.getByTestId("demo-terminar")).toHaveCount(0);
});

test("1 · si /api/v1/entorno falla, no se montan las piezas de demo", async ({ page }) => {
  await simular(page, { entorno: null });
  await page.goto(url("demo"));
  await page.waitForLoadState("networkidle");
  await expect(verComo(page)).toHaveCount(0);
  await expect(page.getByTestId("demo-terminar")).toHaveCount(0);
});

test("2 · pruebas: texto propio, sin selector ni «Terminar demo»", async ({ page }) => {
  await simular(page, { entorno: "pruebas" });
  await page.goto(url("pruebas"));
  await expect(aviso(page)).toContainText("Entorno de pruebas · datos ficticios");
  await page.waitForLoadState("networkidle");
  await expect(verComo(page)).toHaveCount(0);
  await expect(page.getByTestId("demo-terminar")).toHaveCount(0);
});

test("fuera de demo, aunque el backend diga pruebas, no hay piezas de demo", async ({ page }) => {
  await simular(page, { entorno: "pruebas" });
  await page.goto(url("demo"));
  await page.waitForLoadState("networkidle");
  await expect(verComo(page)).toHaveCount(0);
});

test("3 · demo: seis personas en orden, con su línea y la unidad", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await simular(page);
  await page.goto(url("demo"));
  await expect(aviso(page)).toContainText("Demostración · datos ficticios");
  await expect(page.getByTestId("demo-persona-activa")).toHaveText("Ver como: Ana Torres · Administrador de la organización");
  await verComo(page).click();
  const filas = page.getByTestId("demo-persona");
  await expect(filas).toHaveCount(6);
  expect(await filas.evaluateAll((els) => els.map((e) => e.getAttribute("data-rol")))).toEqual(ROLES);
  await expect(page.locator('[data-rol="responsable_area"] [data-testid=demo-persona-rol]')).toHaveText("Responsable de área · Talento Humano");
  await expect(page.getByTestId("demo-panel")).toContainText("Supervisa con independencia: reúne el soporte del diagnóstico, lo sella y valida la evidencia.");
  await sinFiltraciones(page);
});

test("cambio de persona: el servidor decide y la siguiente petición lleva su X-Role", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  const vistas = await simular(page);
  await page.goto(url("demo"));
  await verComo(page).click();
  await page.locator('[data-rol="coordinador"]').click();
  await expect(page.getByTestId("demo-persona-activa")).toContainText("Coordinador");
  await expect(page.getByTestId("demo-toast")).toHaveText("Ahora ves la plataforma como Coordinador");
  vistas.length = 0;
  await page.reload();
  await expect(page.getByTestId("demo-persona-activa")).toContainText("Coordinador");
  const consulta = vistas.find((r) => r.url().endsWith("/api/v1/demo/estado"));
  expect(consulta?.headers()["x-role"]).toBe("coordinador");
});

test("recorrido sugerido: cambia a Responsable de área", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await simular(page);
  await page.goto(url("demo"));
  await verComo(page).click();
  await expect(page.getByTestId("demo-recorrido")).toHaveText("Recorrido sugerido: Responsable de área → Coordinador → DPO → Auditor");
  await page.getByTestId("demo-recorrido").click();
  await expect(page.getByTestId("demo-persona-activa")).toContainText("Responsable de área");
});

test("403 DEMO_PERSONA_AJENA: mensaje y la persona no cambia", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await simular(page, { persona: 403 });
  await page.goto(url("demo"));
  await verComo(page).click();
  await page.locator('[data-rol="dpo"]').click();
  await expect(page.getByTestId("demo-panel-error")).toContainText("Esa persona no pertenece a tu demostración");
  await expect(page.getByTestId("demo-persona-activa")).toContainText("Administrador de la organización");
});

test("4 · 375 px: aviso y selector visibles; «Terminar demo» desde el panel", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 740 });
  await simular(page);
  await page.goto(url("demo"));
  await expect(aviso(page)).toBeVisible();
  await expect(verComo(page)).toBeVisible();
  await verComo(page).click();
  await expect(page.getByTestId("demo-terminar-panel")).toBeVisible();
  await page.getByTestId("demo-terminar-panel").click();
  await expect(page.getByTestId("demo-terminar-dialogo")).toBeVisible();
  const ancho = await page.evaluate(() => document.documentElement.scrollWidth);
  expect(ancho).toBeLessThanOrEqual(375);
});

test("terminar: diálogo sin «inmediat» y aviso literal en la entrada", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await simular(page);
  await page.goto(url("demo"));
  await page.getByTestId("demo-terminar").click();
  const dialogo = page.getByTestId("demo-terminar-dialogo");
  await expect(dialogo).toContainText("¿Terminar la demostración?");
  await expect(dialogo).not.toContainText(/inmediat/i);
  await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
  await page.getByTestId("demo-terminar-confirmar").click();
  await page.waitForURL(/\/login\?demo=terminada/);
  await expect(page.getByTestId("demo-terminada")).toHaveText("La demo se cerró y sus datos se eliminan esta noche");
});

test("5 · 503 DEMO_NO_DISPONIBLE: texto literal y «Intentar de nuevo» repite la entrada", async ({ page }) => {
  const vistas = await simular(page, { entrar: [503, 503, 503, 201] });
  await page.goto(url("demo"));
  await page.getByTestId("google-falso").click();
  const mensaje = page.getByTestId("demo-mensaje");
  await expect(mensaje).toHaveAttribute("data-codigo", "DEMO_NO_DISPONIBLE");
  await expect(mensaje).toContainText("No pudimos preparar la demo; intenta de nuevo");
  await expect(mensaje).not.toContainText("DEMO_NO_DISPONIBLE");
  await page.getByTestId("demo-reintentar").click();
  await expect(page.getByTestId("demo-reintentar")).toBeVisible();
  await page.getByTestId("demo-reintentar").click();
  await expect(mensaje).toContainText("Si el problema sigue, avisa al equipo de EVYDENTIA");
  expect(vistas.filter((r) => r.url().endsWith("/api/v1/demo/entrar") && r.method() === "POST")).toHaveLength(3);
  await sinFiltraciones(page);
});

test("entrada: cinco pasos y, pasados 60 s sin respuesta, el 503", async ({ page }) => {
  await page.clock.install();
  await simular(page, { entrar: ["colgar"] });
  await page.goto(url("demo"));
  await page.getByTestId("google-falso").click();
  const progreso = page.getByTestId("demo-progreso");
  await expect(progreso.locator("li")).toHaveCount(5);
  await expect(progreso).toContainText("Creando la Cooperativa Demo y sus dos unidades");
  await page.clock.runFor(21_000);
  await expect(progreso).toContainText("Está tardando un poco más de lo habitual");
  await expect(progreso.locator('[aria-current="step"]')).toHaveText("Abriendo la plataforma como Administrador");
  await page.clock.runFor(40_000);
  await expect(page.getByTestId("demo-mensaje")).toHaveAttribute("data-codigo", "DEMO_NO_DISPONIBLE");
});

test("6 · [data-slot=organizacion] existe y no es interactivo", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 800 });
  await simular(page);
  await page.goto(url("demo"));
  const ranura = aviso(page).locator("[data-slot=organizacion]");
  await expect(ranura).toHaveText("Cooperativa Demo");
  await expect(ranura.locator("button, a, select, input, [tabindex], [role=button], [role=combobox]")).toHaveCount(0);
});

test("7 · dos pestañas: al entrar en la segunda, la primera ve DEMO_VENCIDA", async ({ context }) => {
  const primera = await context.newPage();
  await primera.setViewportSize({ width: 1280, height: 800 });
  let reemplazada = false;
  await simular(primera);
  await primera.route("**/api/v1/demo/persona", (r) =>
    r.fulfill(reemplazada ? json(401, { codigo: "DEMO_VENCIDA" }) : json(200, { persona_activa: persona("dpo") })),
  );
  await primera.goto(url("demo"));
  await expect(verComo(primera)).toBeVisible();

  const segunda = await context.newPage();
  const vistas = await simular(segunda);
  await segunda.goto(url("demo"));
  await segunda.getByTestId("google-falso").click();
  await expect.poll(() => vistas.some((r) => r.url().endsWith("/api/v1/demo/entrar"))).toBe(true);
  reemplazada = true;

  await verComo(primera).click();
  await primera.locator('[data-rol="dpo"]').click();
  const fin = primera.getByTestId("demo-mensaje");
  await expect(fin).toHaveAttribute("data-codigo", "DEMO_VENCIDA");
  await expect(fin).toContainText("Tu demostración terminó");
  await expect(primera.getByRole("button", { name: "Empezar una nueva" })).toBeVisible();
  await sinFiltraciones(primera);
});
