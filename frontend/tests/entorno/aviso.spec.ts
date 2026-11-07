/**
 * EP-02 · Aviso fijo del entorno y `noindex` fuera de producción (PRD §5.5 y §5.6.1.6).
 *
 * El entorno se lee al ejecutar. Para probarlo como en Cloud Run (misma imagen en todos los
 * entornos), esta especificación compila UNA vez en una copia aislada del frontend (no toca el
 * `.next` del servidor de desarrollo) y arranca esa misma compilación con cuatro `APP_ENV`:
 * production, pruebas, demo y ninguno. `GET /api/v1/entorno` (EP-01) se simula en el navegador.
 */
import { type ChildProcess, execSync, spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";

const RAIZ = path.resolve(__dirname, "..", "..");
// Fuera de node_modules: allí webpack no aplica los alias `@/` de tsconfig.
const COPIA = path.join(os.tmpdir(), "lopdp-e2e-entorno");
const BASE = Number(process.env.PLAYWRIGHT_PORT ?? 3000) + 40;
const ENTORNOS = { production: BASE, pruebas: BASE + 1, demo: BASE + 2, ninguno: BASE + 3 } as const;
type Caso = keyof typeof ENTORNOS;
const url = (caso: Caso, ruta = "/") => `http://localhost:${ENTORNOS[caso]}${ruta}`;

const EXCLUIR = new Set(["node_modules", ".next", "test-results", "playwright-report", "tests"]);
const servidores: ChildProcess[] = [];

function compilarUnaVez(): void {
  // El enlace a node_modules se quita primero: el borrado recursivo nunca debe seguirlo.
  const enlace = path.join(COPIA, "node_modules");
  if (fs.existsSync(enlace)) fs.unlinkSync(enlace);
  fs.rmSync(COPIA, { recursive: true, force: true });
  fs.mkdirSync(COPIA, { recursive: true });
  for (const nombre of fs.readdirSync(RAIZ)) {
    if (!EXCLUIR.has(nombre)) fs.cpSync(path.join(RAIZ, nombre), path.join(COPIA, nombre), { recursive: true });
  }
  fs.symlinkSync(path.join(RAIZ, "node_modules"), path.join(COPIA, "node_modules"), "junction");
  const env: NodeJS.ProcessEnv = { ...process.env, NEXT_TELEMETRY_DISABLED: "1" };
  delete env.APP_ENV;
  execSync("npx next build --no-lint", { cwd: COPIA, env, stdio: "ignore" });
}

async function esperar(direccion: string): Promise<void> {
  for (let i = 0; i < 120; i++) {
    try {
      if ((await fetch(direccion)).status < 500) return;
    } catch {
      // Todavía arrancando.
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
    const env: NodeJS.ProcessEnv = { ...process.env, NEXT_TELEMETRY_DISABLED: "1" };
    if (caso === "ninguno") delete env.APP_ENV;
    else env.APP_ENV = caso;
    servidores.push(
      spawn(`npx next start --port ${puerto}`, { cwd: COPIA, env, shell: true, stdio: "ignore" }),
    );
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

async function simularBackend(page: Page, entorno: string | null): Promise<void> {
  await page.route("**/api/v1/entorno", (ruta) =>
    entorno === null
      ? ruta.fulfill({ status: 503, body: "" })
      : ruta.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ entorno, datos_ficticios: entorno === "pruebas" || entorno === "demo" }),
        }),
  );
}

const aviso = (page: Page) => page.getByTestId("aviso-entorno");

test.describe("Indexación según APP_ENV, con una sola compilación", () => {
  test("production: Allow y sin noindex", async ({ request, page }) => {
    const cuerpo = await (await request.get(url("production", "/robots.txt"))).text();
    expect(cuerpo).toMatch(/Allow:\s*\/\s*$/m);
    expect(cuerpo).not.toMatch(/Disallow:/);
    await page.goto(url("production", "/login"));
    await expect(page.locator('meta[name="robots"]')).toHaveCount(0);
  });

  for (const caso of ["pruebas", "demo", "ninguno"] as const) {
    test(`${caso}: Disallow y noindex`, async ({ request, page }) => {
      const cuerpo = await (await request.get(url(caso, "/robots.txt"))).text();
      expect(cuerpo).toMatch(/Disallow:\s*\/\s*$/m);
      await page.goto(url(caso, "/login"));
      await expect(page.locator('meta[name="robots"]')).toHaveAttribute("content", /noindex.*nofollow/);
    });
  }
});

test.describe("Aviso según APP_ENV", () => {
  for (const ruta of ["/login", "/dashboard"]) {
    test(`pruebas: aparece en ${ruta}`, async ({ page }) => {
      await simularBackend(page, "pruebas");
      await page.goto(url("pruebas", ruta));
      await expect(aviso(page)).toBeVisible();
      await expect(aviso(page)).toHaveAttribute("role", "status");
      await expect(aviso(page)).toContainText("Entorno de pruebas · datos ficticios");
      await expect(aviso(page)).not.toContainText("¤");
      await expect(aviso(page).locator("[data-slot=organizacion]")).toHaveCount(1);
      await expect(aviso(page)).toHaveCSS("background-color", "rgb(232, 238, 247)");
    });
  }

  test("demo: variante ámbar", async ({ page }) => {
    await simularBackend(page, "demo");
    await page.goto(url("demo", "/login"));
    await expect(aviso(page)).toContainText("Demostración · datos ficticios");
    await expect(aviso(page)).toHaveAttribute("data-entorno", "demo");
    await expect(aviso(page)).toHaveCSS("background-color", "rgb(255, 244, 214)");
  });

  test("si el backend dice otra variante, gana el backend", async ({ page }) => {
    await simularBackend(page, "demo");
    await page.goto(url("pruebas", "/login"));
    await expect(aviso(page)).toHaveAttribute("data-entorno", "demo");
  });

  test("si la confirmación falla, el aviso sigue visible", async ({ page }) => {
    await simularBackend(page, null);
    await page.goto(url("pruebas", "/login"));
    await page.waitForLoadState("networkidle");
    await expect(aviso(page)).toContainText("Entorno de pruebas · datos ficticios");
  });

  for (const caso of ["production", "ninguno"] as const) {
    test(`${caso}: sin aviso y sin consultar al backend`, async ({ page }) => {
      const llamadas: string[] = [];
      await page.route("**/api/v1/entorno", (r) => {
        llamadas.push(r.request().url());
        return r.fulfill({ status: 200, json: { entorno: "pruebas", datos_ficticios: true } });
      });
      await page.goto(url(caso, "/login"));
      await page.waitForLoadState("networkidle");
      await expect(aviso(page)).toHaveCount(0);
      expect(llamadas).toEqual([]);
    });
  }

  test("pantalla estrecha: sigue visible con el texto corto", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await simularBackend(page, "pruebas");
    await page.goto(url("pruebas", "/login"));
    await expect(aviso(page)).toBeVisible();
    await expect(aviso(page)).toContainText("Pruebas · ficticio");
  });
});
