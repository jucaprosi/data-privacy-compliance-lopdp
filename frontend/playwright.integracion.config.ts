// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * Configuración de Playwright para pruebas de integración contra backend real (TEST-03).
 *
 * Comando exacto:
 *   cd frontend
 *   npx playwright test -c playwright.integracion.config.ts
 *
 * Base necesaria:
 *   PostgreSQL 16 local (127.0.0.1) o el servicio PostgreSQL 16 del CI.
 *
 * Precondiciones duras (sin omitir):
 *   - Requiere TEST_DATABASE_URL definida.
 *   - Falla si TEST_DATABASE_URL no apunta a un host PostgreSQL local permitido (localhost, 127.0.0.1 o ::1).
 */
import { defineConfig, devices } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

const HOSTS_DE_PRUEBAS = new Set(["localhost", "127.0.0.1", "::1", "[::1]"]);

function precondicion(motivo: string): never {
  throw new Error(`[PRECONDICION FALLIDA] ${motivo}`);
}

function exigirBaseDePruebas(urlCruda: string): void {
  let parsed: URL;
  try {
    parsed = new URL(urlCruda);
  } catch {
    precondicion("TEST_DATABASE_URL no es una URL válida.");
  }
  if (parsed.protocol !== "postgres:" && !parsed.protocol.startsWith("postgresql")) {
    precondicion("TEST_DATABASE_URL no usa esquema PostgreSQL.");
  }
  if (!HOSTS_DE_PRUEBAS.has(parsed.hostname.toLowerCase())) {
    precondicion("TEST_DATABASE_URL no apunta a un host PostgreSQL local permitido (localhost, 127.0.0.1 o ::1).");
  }
  const hostParam = parsed.searchParams.get("host");
  if (hostParam !== null && !HOSTS_DE_PRUEBAS.has(hostParam.toLowerCase())) {
    precondicion("TEST_DATABASE_URL especifica un parámetro host fuera de la lista permitida.");
  }
}

const dbUrl = (process.env.TEST_DATABASE_URL ?? "").trim();

if (!dbUrl) {
  precondicion(
    "TEST_DATABASE_URL no está configurada. " +
      "Se requiere PostgreSQL 16 local o el servicio PostgreSQL 16 del CI para el arnés de integración."
  );
}

exigirBaseDePruebas(dbUrl);

process.env.TEST_DATABASE_URL = dbUrl;
process.env.DATABASE_URL = dbUrl;

const PUERTO_BACKEND = 5100;
const PUERTO_FRONTEND = 3200;
const BASE_URL = `http://127.0.0.1:${PUERTO_FRONTEND}`;

function resolverPythonBin(): string {
  const venvPython = path.resolve(__dirname, "..", ".venv", "Scripts", "python.exe");
  if (fs.existsSync(venvPython)) {
    return `"${venvPython}"`;
  }
  return "python";
}

const pythonBin = resolverPythonBin();

export default defineConfig({
  testDir: "./tests/integracion",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  forbidOnly: Boolean(process.env.CI),
  retries: 0,
  reporter: [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: [
    {
      command: `${pythonBin} -m uvicorn main:app --host 127.0.0.1 --port ${PUERTO_BACKEND} --loop none`,
      url: `http://127.0.0.1:${PUERTO_BACKEND}/health`,
      cwd: "..",
      env: {
        AUTH_MODE: "headers",
        DATABASE_URL: dbUrl,
        TEST_DATABASE_URL: dbUrl,
        PYTHONPATH: "..",
      },
      reuseExistingServer: false,
      timeout: 60_000,
      stdout: "pipe",
      stderr: "pipe",
    },
    {
      command: `npm run dev -- --port ${PUERTO_FRONTEND}`,
      url: BASE_URL,
      cwd: ".",
      env: {
        BACKEND_URL: `http://127.0.0.1:${PUERTO_BACKEND}`,
        NEXT_PUBLIC_AUTH_MODE: "headers",
        PORT: String(PUERTO_FRONTEND),
      },
      reuseExistingServer: false,
      timeout: 120_000,
      stdout: "ignore",
      stderr: "pipe",
    },
  ],
});
