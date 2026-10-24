import { defineConfig } from "@playwright/test";

import base from "../../playwright.config";

/**
 * Configuración de QA-08 para worktrees con node_modules enlazado.
 *
 * Turbopack rechaza junctions que salen de la raíz del worktree. La prueba usa
 * un servidor Next (Webpack) iniciado por el comando documentado de QA-08 y
 * evita que el webServer general intente levantar otro proceso con Turbopack.
 */
export default defineConfig({
  ...base,
  testDir: ".",
  testMatch: "purga-normativa.spec.ts",
  use: {
    ...base.use,
    baseURL: process.env.PLAYWRIGHT_BASE_URL ?? "http://127.0.0.1:3000",
  },
  webServer: undefined,
});
