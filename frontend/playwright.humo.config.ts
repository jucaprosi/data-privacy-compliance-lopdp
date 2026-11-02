/**
 * Pruebas de humo de extremo a extremo: compuerta de fallo rápido antes de Pytest y Playwright.
 * Metodología: governance/operaciones/PRUEBAS_DE_HUMO.md.
 *
 * Next.js de producción y FastAPI reales contra una rama Neon de prueba, en modo `oidc`, sin `page.route`.
 *
 * Comandos, desde frontend/ y con TEST_DATABASE_URL en el entorno:
 *   $env:BACKEND_URL = "http://127.0.0.1:5200"; $env:NEXT_PUBLIC_GOOGLE_CLIENT_ID = "humo-ci"; npm run build
 *   npx playwright test -c playwright.humo.config.ts
 *
 * Next fija el destino del proxy /api/v1 al compilar: por eso el build lleva BACKEND_URL y aquí se comprueba.
 */
import { defineConfig, devices } from "@playwright/test";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

const PUERTO_API = 5200;
const PUERTO_WEB = 3300;
const ORIGEN_API = `http://127.0.0.1:${PUERTO_API}`;
const BASE_URL = `http://127.0.0.1:${PUERTO_WEB}`;
const CLIENT_ID = "humo-ci";

function precondicion(motivo: string): never {
  throw new Error(`[PRECONDICION FALLIDA] ${motivo}`);
}

const dbUrl = (process.env.TEST_DATABASE_URL ?? "").trim();
if (!dbUrl) precondicion("TEST_DATABASE_URL no está configurada: el humo exige una rama Neon de prueba.");
if (dbUrl.includes("ep-late-hall")) precondicion("TEST_DATABASE_URL apunta a PRODUCCIÓN.");

const manifiesto = path.join(__dirname, ".next", "routes-manifest.json");
if (!fs.existsSync(manifiesto) || !fs.readFileSync(manifiesto, "utf-8").includes(ORIGEN_API)) {
  precondicion(`falta un build con BACKEND_URL=${ORIGEN_API}: sin él el proxy /api/v1 apunta a otro servidor.`);
}

// Playwright reevalúa esta configuración en cada worker: la carpeta se crea una vez y se hereda por el entorno.
process.env.HUMO_DIR ??= fs.mkdtempSync(path.join(os.tmpdir(), "lopdp-humo-"));
process.env.HUMO_CLIENT_ID = CLIENT_ID;
const HUMO_CLAVE_PRIVADA = path.join(process.env.HUMO_DIR, "clave.pem");
process.env.HUMO_CLAVE_PRIVADA = HUMO_CLAVE_PRIVADA;

export default defineConfig({
  testDir: "./tests/humo",
  globalSetup: "./tests/humo/preparacion.ts",
  globalTeardown: "./tests/humo/limpieza.ts",
  // Orden de archivo, de rápido a lento, y parada en el primer fallo: es lo que hace rápida a la compuerta.
  fullyParallel: false,
  workers: 1,
  maxFailures: 1,
  // Sin reintentos: un flujo intermitente no sirve de compuerta y debe verse como fallo.
  retries: 0,
  timeout: 30_000,
  expect: { timeout: 10_000 },
  forbidOnly: Boolean(process.env.CI),
  reporter: process.env.CI ? [["github"], ["list"]] : [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "python tests/humo/servidor_humo.py",
      url: `${ORIGEN_API}/health`,
      cwd: "..",
      env: {
        HUMO_E2E: "1",
        HUMO_PUERTO_API: String(PUERTO_API),
        HUMO_CLAVE_PRIVADA,
        GOOGLE_CLIENT_ID: CLIENT_ID,
        DATABASE_URL: dbUrl,
        TEST_DATABASE_URL: dbUrl,
      },
      reuseExistingServer: false,
      timeout: 60_000,
      stdout: "ignore",
      stderr: "pipe",
    },
    {
      command: `npx next start --port ${PUERTO_WEB} --hostname 127.0.0.1`,
      url: BASE_URL,
      reuseExistingServer: false,
      timeout: 30_000,
      stdout: "ignore",
      stderr: "pipe",
    },
  ],
});
