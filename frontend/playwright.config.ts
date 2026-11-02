import { defineConfig, devices } from "@playwright/test";

/**
 * Arnés de verificación de interfaz. Es el árbitro exógeno del frontend: lo que
 * aquí no esté comprobado, no está comprobado.
 *
 * En local levanta el servidor de desarrollo por su cuenta y reutiliza el que ya
 * esté corriendo, de modo que `npm run test:e2e` funcione igual en una máquina
 * limpia que junto a una sesión de trabajo abierta.
 *
 * En CI (CI-04) el grueso corre contra `next build` + `next start`, sin compilar
 * rutas bajo demanda. Las pruebas de SOLO_DESARROLLO siguen en `next dev`: usan
 * lo que un build de producción elimina a propósito.
 */
const ES_CI = Boolean(process.env.CI);
const PUERTO = Number(process.env.PLAYWRIGHT_PORT ?? 3000);
const BASE_URL = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${PUERTO}`;
// `next dev` vacía `.next` al arrancar: en CI se le deja `.next` y `next start` sirve una copia.
// Dentro de node_modules está ignorada por git y sigue resolviendo las dependencias del frontend.
const PUERTO_DESARROLLO = PUERTO + 1;
const URL_DESARROLLO = `http://localhost:${PUERTO_DESARROLLO}`;
const COPIA_PRODUCCION = "node_modules/.cache/e2e-produccion";

/**
 * Dependen de `window.__LOPDP_AUTH_PRUEBAS__` o de `/harness-roadmap/*`, que solo existen fuera de
 * producción (`src/lib/auth/modo.ts`). Una prueba nueva que use `fijarAjustes` se añade aquí.
 */
const SOLO_DESARROLLO = [
  "**/arco/arco.spec.ts",
  "**/auth/datos-por-usuario.spec.ts",
  "**/auth/identidad.spec.ts",
  "**/auth/organizaciones.spec.ts",
  "**/biblioteca/acceso.spec.ts",
  "**/designaciones/designaciones.spec.ts",
  "**/estructura/estructura.spec.ts",
  "**/organizacion/alta.spec.ts",
  "**/organizacion/datos-documentales.spec.ts",
  "**/tamano/ficha.spec.ts",
  "**/roadmap/admin-colores.spec.ts",
  "**/roadmap/admin.spec.ts",
  "**/roadmap/colores-hoja-de-ruta.spec.ts",
  "**/roadmap/evidencia.spec.ts",
  "**/roadmap/olas.spec.ts",
  "**/roadmap/planeacion.spec.ts",
  "**/roadmap/tarjeta-colores.spec.ts",
  "**/roadmap/vistas.spec.ts",
];

const copiarCompilacion = [
  `const fs = require('fs');`,
  `fs.rmSync('${COPIA_PRODUCCION}', { recursive: true, force: true });`,
  `fs.mkdirSync('${COPIA_PRODUCCION}', { recursive: true });`,
  `for (const x of ['.next', 'public', 'next.config.ts', 'package.json'])`,
  `fs.cpSync(x, '${COPIA_PRODUCCION}/' + x, { recursive: true });`,
].join(" ");

export default defineConfig({
  testDir: "./tests",
  // Las pruebas de integración (TEST-03) levantan backend y base de datos reales con su propia
  // configuración: playwright.integracion.config.ts. Este arnés simula la API y no puede ejecutarlas.
  // Lo mismo las de humo: playwright.humo.config.ts.
  testIgnore: ["**/integracion/**", "**/humo/**"],
  // Cada spec parte de un estado limpio y no depende del orden de ejecución.
  fullyParallel: true,
  // Sin compilación bajo demanda la máquina del CI aguanta sus 4 núcleos. El proyecto de desarrollo
  // conserva su límite: con demasiados contextos simultáneos la primera visita a una ruta tarda
  // más que cualquier espera razonable y el arnés falla por lentitud, no por regresión.
  workers: ES_CI ? 4 : 3,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  // Un test marcado como `only` delata una sesión de depuración a medio cerrar.
  forbidOnly: ES_CI,
  retries: ES_CI ? 1 : 0,
  reporter: ES_CI ? [["github"], ["list"]] : [["list"]],
  // El diagnóstico se guarda solo cuando algo falla: un fallo verde no deja rastro.
  use: {
    baseURL: BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "off",
  },
  projects: ES_CI
    ? [
        {
          name: "produccion",
          testIgnore: ["**/integracion/**", "**/humo/**", ...SOLO_DESARROLLO],
          use: { ...devices["Desktop Chrome"] },
        },
        {
          name: "desarrollo",
          testMatch: SOLO_DESARROLLO,
          workers: 2,
          use: { ...devices["Desktop Chrome"], baseURL: URL_DESARROLLO },
        },
      ]
    : [
        {
          name: "chromium",
          use: { ...devices["Desktop Chrome"] },
        },
      ],
  webServer: ES_CI
    ? [
        {
          command:
            `npx next build --no-lint && node -e "${copiarCompilacion}"` +
            ` && npx next start ${COPIA_PRODUCCION} --port ${PUERTO}`,
          url: BASE_URL,
          reuseExistingServer: false,
          timeout: 300_000,
          stdout: "ignore",
          stderr: "pipe",
          // Sin esto el build arranca en "oidc" y exige sesión. Vive solo en este runner.
          env: { NEXT_PUBLIC_AUTH_MODE: "headers", NEXT_TELEMETRY_DISABLED: "1" },
        },
        {
          command: `npm run dev -- --port ${PUERTO_DESARROLLO}`,
          url: URL_DESARROLLO,
          reuseExistingServer: false,
          timeout: 180_000,
          stdout: "ignore",
          stderr: "pipe",
        },
      ]
    : {
        command: `npm run dev -- --port ${PUERTO}`,
        url: BASE_URL,
        reuseExistingServer: true,
        timeout: 180_000,
        stdout: "ignore",
        stderr: "pipe",
      },
});
