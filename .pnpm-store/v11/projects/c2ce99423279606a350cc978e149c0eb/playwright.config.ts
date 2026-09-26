import { defineConfig, devices } from "@playwright/test";

/**
 * Arnés de verificación de interfaz. Es el árbitro exógeno del frontend: lo que
 * aquí no esté comprobado, no está comprobado.
 *
 * Levanta el servidor de desarrollo por su cuenta y reutiliza el que ya esté
 * corriendo, de modo que `npm run test:e2e` funcione igual en una máquina
 * limpia que junto a una sesión de trabajo abierta.
 */
const PUERTO = Number(process.env.PLAYWRIGHT_PORT ?? 3000);
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${PUERTO}`;

export default defineConfig({
  testDir: "./tests",
  // Cada spec parte de un estado limpio y no depende del orden de ejecución.
  fullyParallel: true,
  // El servidor de desarrollo compila cada ruta bajo demanda: con demasiados
  // contextos simultáneos la primera visita tarda más que cualquier espera
  // razonable y el arnés falla por lentitud, no por regresión.
  workers: process.env.CI ? 2 : 3,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  // Un test marcado como `only` delata una sesión de depuración a medio cerrar.
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["github"], ["list"]] : [["list"]],
  // El diagnóstico se guarda solo cuando algo falla: un fallo verde no deja rastro.
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
  webServer: {
    command: `npm run dev -- --port ${PUERTO}`,
    url: BASE_URL,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
    stdout: "ignore",
    stderr: "pipe",
  },
});
