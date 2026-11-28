// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * Humo contra la demo desplegada (QA-17): escritorio y móvil, en tema claro y oscuro.
 * Contrato: governance/especificaciones/QA-17.md.
 *
 * Solo la demo. Fuera de sus hosts, app.evydentia.com incluido, se para antes de pedir nada (R1).
 * No arranca servidores ni reintenta: un fallo de la demo se ve como fallo (R4).
 * El ID token se emite en cada corrida para la cuenta de servicio de pruebas y solo vive en la variable de
 * entorno: no se guarda ni se imprime, y la traza va apagada porque grabaría las cabeceras (R5).
 *
 * Comando local (R6), en PowerShell desde frontend/:
 *   cd "<repositorio>\frontend"
 *   $cuenta = "<cuenta de servicio de pruebas de la demo>"
 *   $cliente = "<GOOGLE_CLIENT_ID de la demo>"
 *   $env:HUMO_DEMO_TOKEN = gcloud auth print-identity-token --impersonate-service-account=$cuenta --audiences=$cliente --include-email
 *   npx playwright test -c playwright.desplegado.config.ts
 *   Remove-Item Env:HUMO_DEMO_TOKEN
 *
 * Otra web de la demo: $env:HUMO_DESPLEGADO_URL = "https://<servicio>-demo-<…>.run.app" antes de lanzarlo.
 */
import { defineConfig, devices } from "@playwright/test";

const URL_DEMO = "https://evydentia-web-demo-517105327086.us-central1.run.app";
const HOST_DEMO = new URL(URL_DEMO).hostname;

function precondicion(motivo: string): never {
  throw new Error(`[PRECONDICION FALLIDA] ${motivo}`);
}

/** R1: el host de la demo o uno de Cloud Run cuyo servicio termine en `-demo-…`. */
function esHostDeDemo(host: string): boolean {
  return host === HOST_DEMO || /^[a-z0-9-]+-demo-[a-z0-9-]+(\.[a-z0-9-]+)*\.run\.app$/.test(host);
}

function destino(crudo: string): string {
  let url: URL;
  try {
    url = new URL(crudo);
  } catch {
    precondicion(`HUMO_DESPLEGADO_URL no es una URL válida: «${crudo}».`);
  }
  if (url.protocol !== "https:") precondicion(`HUMO_DESPLEGADO_URL tiene que ser https: «${url.origin}».`);
  if (!esHostDeDemo(url.hostname)) {
    precondicion(`«${url.hostname}» no es un host de la demo. El humo desplegado solo corre contra la demo.`);
  }
  return url.origin;
}

const BASE_URL = destino((process.env.HUMO_DESPLEGADO_URL ?? "").trim() || URL_DEMO);
process.env.HUMO_DESPLEGADO_ORIGEN = BASE_URL;

export default defineConfig({
  testDir: "./tests/desplegado",
  globalSetup: "./tests/desplegado/calentamiento.ts",
  fullyParallel: false,
  workers: 1,
  // Sin reintentos: un reintento ocultaría justo el arranque en frío que este humo vigila (R4).
  retries: 0,
  // Plazos normales del humo; el arranque en frío lo absorbe el calentamiento, con el suyo (R4).
  timeout: 30_000,
  expect: { timeout: 10_000 },
  forbidOnly: Boolean(process.env.CI),
  reporter: process.env.CI ? [["github"], ["list"]] : [["list"]],
  use: {
    baseURL: BASE_URL,
    trace: "off",
    screenshot: "only-on-failure",
    video: "off",
  },
  // R2 y R3: escritorio y móvil, en claro y en oscuro. El tema se guarda donde lo guarda la app
  // (jubys-audit-storage, FE-41) antes de cargar la página: tema-inicial.js lo pone en <html> al pintar.
  projects: [
    {
      name: "escritorio-claro",
      use: {
        ...devices["Desktop Chrome"],
        storageState: { cookies: [], origins: [{ origin: BASE_URL, localStorage: [{ name: "jubys-audit-storage", value: '{"state":{"theme":"light"},"version":6}' }] }] },
      },
    },
    {
      name: "escritorio-oscuro",
      use: {
        ...devices["Desktop Chrome"],
        storageState: { cookies: [], origins: [{ origin: BASE_URL, localStorage: [{ name: "jubys-audit-storage", value: '{"state":{"theme":"dark"},"version":6}' }] }] },
      },
    },
    {
      name: "movil-claro",
      use: {
        ...devices["Pixel 7"],
        storageState: { cookies: [], origins: [{ origin: BASE_URL, localStorage: [{ name: "jubys-audit-storage", value: '{"state":{"theme":"light"},"version":6}' }] }] },
      },
    },
    {
      name: "movil-oscuro",
      use: {
        ...devices["Pixel 7"],
        storageState: { cookies: [], origins: [{ origin: BASE_URL, localStorage: [{ name: "jubys-audit-storage", value: '{"state":{"theme":"dark"},"version":6}' }] }] },
      },
    },
  ],
  webServer: [],
});
