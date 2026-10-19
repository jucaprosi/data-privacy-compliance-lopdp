/**
 * Configuración de Playwright para pruebas de integración contra backend real (TEST-03).
 *
 * Comando exacto:
 *   cd frontend
 *   npx playwright test -c playwright.integracion.config.ts
 *
 * Rama Neon necesaria:
 *   test-rm07 (o la asignada a la sesión en rama-<rama>.txt).
 *
 * Precondiciones duras (sin omitir):
 *   - Requiere TEST_DATABASE_URL definida.
 *   - Falla si TEST_DATABASE_URL apunta al host de producción (ep-late-hall-b50bpbk5).
 */
import { defineConfig, devices } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

function resolverTestDatabaseUrl(): string {
  if (process.env.TEST_DATABASE_URL && process.env.TEST_DATABASE_URL.trim()) {
    return process.env.TEST_DATABASE_URL.trim();
  }
  const archivoRama = "C:\\Users\\Juan Carlos\\Desktop\\herramientas\\rama-test-rm07.txt";
  if (fs.existsSync(archivoRama)) {
    const contenido = fs.readFileSync(archivoRama, "utf-8");
    for (const linea of contenido.split("\n")) {
      const match = linea.match(/^\s*TEST_DATABASE_URL\s*=\s*(.+)$/);
      if (match) {
        return match[1].trim();
      }
    }
  }
  return "";
}

const dbUrl = resolverTestDatabaseUrl();

if (!dbUrl) {
  throw new Error(
    "[PRECONDICION FALLIDA] TEST_DATABASE_URL no está configurada. " +
      "Se requiere una base de datos real (rama Neon propia) para el arnés de integración."
  );
}

if (dbUrl.includes("ep-late-hall-b50bpbk5")) {
  throw new Error(
    "[PRECONDICION FALLIDA] TEST_DATABASE_URL apunta a la base de PRODUCCIÓN (ep-late-hall-b50bpbk5). " +
      "Abortando inmediatamente por seguridad."
  );
}

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
