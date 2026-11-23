// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
/**
 * FE-29 §5: el inicio de sesión explica por qué una cuenta de Google no entra.
 *
 * Google y la API se simulan (../auth/utilesAuth.ts) en modo «oidc», fijado con `fijarAjustes`: este
 * archivo corre en el proyecto «desarrollo» (playwright.config.ts, CI-30). La credencial es simulada.
 *
 * Mutaciones (FE-29), cada una aplicada, ejecutada y revertida:
 *  - m2: decidir por el texto de `detail` en `clasificarRespuesta` (lib/auth/organizacion.ts) ⟹ rojo en
 *    «el código manda, no el texto».
 *  - m3: tratar el 503 como `no_registrado` ⟹ rojo en «503 y red con Reintentar».
 *  - m4: dejar sin aviso el camino de `entrarComoOperador` en «no» ⟹ rojo en «cada camino navega o avisa».
 *  - m5: no borrar la credencial pendiente en «Usar otra cuenta de Google» (quitar `cerrarSesion()`, que la
 *    borra con la sesión) ⟹ rojo en «otra cuenta».
 */
import { expect, test, type Page, type Route } from "@playwright/test";

import {
  credencialSimulada,
  fijarAjustes,
  ORGANIZACION_PRUEBA,
  simularApi,
  type OrganizacionSimulada,
} from "../auth/utilesAuth";
import { medirContraste } from "../contraste";

const CORREO = "persona@empresa.test";
const credencial = credencialSimulada({ email: CORREO, nombre: "Persona Prueba" });
const BOTON = "Continuar con Google (simulado)";
const CLAVE_PENDIENTE = "lopdp-credencial-pendiente-v1";
const PROHIBIDOS = [/403/, /servidor respondió/i, /EVYDENTIA/i];

/** Respuesta simulada: un estado con su cuerpo, una lista de organizaciones o una petición abortada. */
type Respuesta = { estado: number; cuerpo?: unknown; crudo?: string } | OrganizacionSimulada[] | "abortar";

const error = (estado: number, code: string | null, detail = "texto del servidor") => ({
  estado,
  cuerpo: { detail, code, action_required: null },
});

const NO_REGISTRADO = error(403, "USUARIO_NO_REGISTRADO", "Usuario no registrado en la plataforma.");
const NO_OPERADOR = error(403, "OPERADOR_NO_AUTORIZADO", "Acceso restringido: no tiene permisos de operador de la plataforma.");

/** Google simulado que cuenta las llamadas a `disableAutoSelect` y repinta su botón en cada `renderButton`. */
async function googleQueCuenta(page: Page, token: string): Promise<void> {
  const script = `
    window.__desactivaciones = 0;
    window.google = { accounts: { id: {
      initialize(opciones) { window.__gsi = opciones; },
      renderButton(elemento) {
        const boton = document.createElement("button");
        boton.type = "button";
        boton.textContent = ${JSON.stringify(BOTON)};
        boton.onclick = () => window.__gsi.callback({ credential: ${JSON.stringify(token)} });
        elemento.appendChild(boton);
      },
      disableAutoSelect() { window.__desactivaciones += 1; },
    } } };
  `;
  await page.route("https://accounts.google.com/gsi/client", (route: Route) =>
    route.fulfill({ status: 200, contentType: "text/javascript", body: script }),
  );
}

async function responder(route: Route, respuesta: Respuesta): Promise<void> {
  if (respuesta === "abortar") return route.abort("failed");
  if (Array.isArray(respuesta)) {
    return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ organizaciones: respuesta }) });
  }
  if (respuesta.crudo !== undefined) return route.fulfill({ status: respuesta.estado, contentType: "text/html", body: respuesta.crudo });
  return route.fulfill({ status: respuesta.estado, contentType: "application/json", body: JSON.stringify(respuesta.cuerpo ?? {}) });
}

interface Escenario {
  /** Respuestas sucesivas de mis-organizaciones; la última se repite. */
  misOrganizaciones: Respuesta[];
  plataforma?: Respuesta;
  token?: string;
}

async function preparar(page: Page, escenario: Escenario): Promise<void> {
  await fijarAjustes(page, { modo: "oidc", tenant: null });
  await googleQueCuenta(page, escenario.token ?? credencial.token);
  await simularApi(page, { organizaciones: [ORGANIZACION_PRUEBA] });
  // Registradas después de simularApi: Playwright aplica primero la última ruta que coincide.
  const pendientes = [...escenario.misOrganizaciones];
  await page.route("**/api/v1/organizacion/mis-organizaciones", (route) =>
    responder(route, pendientes.length > 1 ? pendientes.shift()! : pendientes[0]),
  );
  await page.route("**/api/v1/plataforma/organizaciones", (route) => responder(route, escenario.plataforma ?? NO_OPERADOR));
}

async function entrar(page: Page, escenario: Escenario): Promise<void> {
  await preparar(page, escenario);
  await page.goto("/login");
  await page.getByRole("button", { name: BOTON }).click();
}

// El anunciador de rutas de Next también es role="alert": el aviso es el que lleva data-tipo (§4).
const aviso = (page: Page) => page.locator('[role="alert"][data-tipo]');

async function sinTextosProhibidos(page: Page): Promise<void> {
  const texto = await page.locator("main").innerText();
  for (const prohibido of PROHIBIDOS) expect(texto).not.toMatch(prohibido);
}

test.describe("Login que explica por qué una cuenta no entra (FE-29)", () => {
  test("no registrado: título, correo y «Usar otra cuenta de Google»", async ({ page }) => {
    await entrar(page, { misOrganizaciones: [NO_REGISTRADO] });

    const titulo = page.getByRole("heading", { name: "Esta cuenta no tiene acceso" });
    await expect(titulo).toBeVisible();
    await expect(titulo).toBeFocused();
    await expect(aviso(page)).toHaveAttribute("data-tipo", "no_registrado");
    await expect(aviso(page).locator("strong")).toHaveText(CORREO);
    await expect(page.getByRole("button", { name: "Usar otra cuenta de Google" })).toBeVisible();
    await expect(aviso(page)).toContainText("Si Google vuelve a ofrecerte la misma cuenta");
    await expect(page).toHaveURL(/\/login$/);
    await sinTextosProhibidos(page);
  });

  test("el código manda, no el texto de detail (m2)", async ({ page }) => {
    // El detail dice «no registrado», pero el código es el de cuenta vinculada: gana el código.
    await entrar(page, {
      misOrganizaciones: [error(403, "CUENTA_VINCULADA_OTRA_IDENTIDAD", "Usuario no registrado en la plataforma.")],
    });
    await expect(page.getByRole("heading", { name: "Este correo usa otra cuenta de Google" })).toBeVisible();
    await expect(aviso(page)).toHaveAttribute("data-tipo", "vinculada_otra");
    await expect(aviso(page).locator("strong")).toHaveText(CORREO);
  });

  test("vinculada a otra identidad", async ({ page }) => {
    await entrar(page, { misOrganizaciones: [error(403, "CUENTA_VINCULADA_OTRA_IDENTIDAD")] });
    await expect(page.getByRole("heading", { name: "Este correo usa otra cuenta de Google" })).toBeVisible();
    await sinTextosProhibidos(page);
  });

  test("otra cuenta: olvida la credencial, llama a disableAutoSelect y repinta el botón con el foco (m5)", async ({ page }) => {
    await page.addInitScript((clave) => window.sessionStorage.setItem(clave, "credencial-anterior"), CLAVE_PENDIENTE);
    await entrar(page, { misOrganizaciones: [NO_REGISTRADO] });
    await page.getByRole("button", { name: "Usar otra cuenta de Google" }).click();

    await expect(aviso(page)).toHaveCount(0);
    expect(await page.evaluate(() => (window as unknown as { __desactivaciones: number }).__desactivaciones)).toBe(1);
    const botonGoogle = page.getByTestId("login-boton-google");
    await expect(botonGoogle).toBeVisible();
    await expect(botonGoogle).toBeFocused();
    await expect(botonGoogle.getByRole("button", { name: BOTON })).toHaveCount(1);
    expect(await page.evaluate((c) => window.sessionStorage.getItem(c), CLAVE_PENDIENTE)).toBeNull();
  });

  test("503 y red con «Reintentar»; el reintento con una organización lleva al panel (m3)", async ({ page }) => {
    await entrar(page, { misOrganizaciones: [{ estado: 503, cuerpo: { detail: "x" } }, "abortar"] });
    await expect(aviso(page)).toHaveAttribute("data-tipo", "servidor");
    await expect(aviso(page)).toContainText("La plataforma no pudo responder. Inténtalo de nuevo en unos minutos.");
    const reintentar = page.getByRole("button", { name: "Reintentar" });
    await expect(reintentar).toBeFocused();

    await reintentar.click();
    await expect(aviso(page)).toHaveAttribute("data-tipo", "red");
    await expect(aviso(page)).toContainText("No pudimos conectar con la plataforma. Revisa tu conexión e inténtalo de nuevo.");

    // El siguiente reintento tarda: mientras, el botón espera y se anuncia la consulta.
    let soltar: () => void = () => {};
    const espera = new Promise<void>((r) => (soltar = r));
    await page.route("**/api/v1/organizacion/mis-organizaciones", async (route) => {
      await espera;
      await responder(route, [ORGANIZACION_PRUEBA]);
    });
    await page.getByRole("button", { name: "Reintentar" }).click();
    const esperando = page.getByRole("button", { name: "Reintentando…" });
    await expect(esperando).toHaveAttribute("aria-disabled", "true");
    await expect(page.getByRole("status").filter({ hasText: "Consultando tus organizaciones…" })).toBeVisible();
    soltar();
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("lista vacía y sin permiso de operador: aún no pertenece a ninguna organización", async ({ page }) => {
    await entrar(page, { misOrganizaciones: [[]] });
    await expect(page.getByRole("heading", { name: "Aún no perteneces a ninguna organización" })).toBeVisible();
    await expect(aviso(page)).toHaveAttribute("data-tipo", "sin_organizaciones");
    await expect(aviso(page)).not.toContainText("invitación");
  });

  test("en /organizaciones, un 503 muestra el aviso del servidor y la lista guardada", async ({ page }) => {
    await preparar(page, { misOrganizaciones: [{ estado: 503 }] });
    const guardada: OrganizacionSimulada[] = [ORGANIZACION_PRUEBA, { ...ORGANIZACION_PRUEBA, tenant_id: "otra", nombre_comercial: "Otra" }];
    await page.addInitScript(
      ({ pendiente, lista }) => {
        window.sessionStorage.setItem("lopdp-credencial-pendiente-v1", pendiente);
        window.sessionStorage.setItem("lopdp-mis-organizaciones-v1", lista);
      },
      { pendiente: credencial.token, lista: JSON.stringify(guardada) },
    );
    await page.goto("/organizaciones");

    await expect(aviso(page)).toHaveAttribute("data-tipo", "servidor");
    await expect(page.getByRole("button", { name: "Reintentar" })).toBeVisible();
    await expect(page.getByText("Lista guardada en este navegador; puede no estar al día.")).toBeVisible();
    await expect(page.getByRole("list", { name: "Tus organizaciones" })).toBeVisible();
    await sinTextosProhibidos(page);
  });

  test("sesión guardada que el panel rechaza: vuelve con motivo=expirada y su aviso", async ({ page }) => {
    // `haCaducado` descuenta 30 s de margen: con 36 s el login la ve vigente y la manda al panel, y el
    // panel la descarta al llegar `exp` y vuelve a /login a secas (dashboard/page.tsx).
    test.setTimeout(120_000);
    const corta = credencialSimulada({ email: CORREO, expiraEnSegundos: 36 });
    await fijarAjustes(page, { modo: "oidc", tenant: null });
    await googleQueCuenta(page, corta.token);
    await simularApi(page);
    await page.addInitScript(
      ({ sesion, org }) => {
        if (window.sessionStorage.getItem("__fe29_sembrada")) return;
        window.sessionStorage.setItem("lopdp-sesion-v1", sesion);
        window.sessionStorage.setItem("lopdp-organizacion-activa-v1", org);
        window.sessionStorage.setItem("__fe29_sembrada", "1");
      },
      { sesion: JSON.stringify(corta), org: JSON.stringify(ORGANIZACION_PRUEBA) },
    );
    await page.goto("/login");
    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page).toHaveURL(/\/login\?motivo=expirada/, { timeout: 90_000 });
    await expect(page.getByRole("status").filter({ hasText: "Tu sesión terminó. Vuelve a iniciar sesión." })).toBeVisible();
  });

  const CAMINOS: { nombre: string; escenario?: Escenario; tipo: string; googleNoCarga?: boolean }[] = [
    { nombre: "no registrado y no operador", escenario: { misOrganizaciones: [NO_REGISTRADO] }, tipo: "no_registrado" },
    { nombre: "otro 403 sin código", escenario: { misOrganizaciones: [{ estado: 403, cuerpo: { detail: "x" } }] }, tipo: "sin_permiso" },
    { nombre: "vinculada", escenario: { misOrganizaciones: [error(403, "CUENTA_VINCULADA_OTRA_IDENTIDAD")] }, tipo: "vinculada_otra" },
    { nombre: "lista vacía", escenario: { misOrganizaciones: [[]] }, tipo: "sin_organizaciones" },
    { nombre: "401", escenario: { misOrganizaciones: [error(401, "AUTH")] }, tipo: "sesion" },
    { nombre: "503", escenario: { misOrganizaciones: [{ estado: 503 }] }, tipo: "servidor" },
    { nombre: "cuerpo ilegible", escenario: { misOrganizaciones: [{ estado: 403, crudo: "<html>bloqueado</html>" }] }, tipo: "servidor" },
    { nombre: "red caída", escenario: { misOrganizaciones: ["abortar"] }, tipo: "red" },
    { nombre: "operador con red caída", escenario: { misOrganizaciones: [NO_REGISTRADO], plataforma: "abortar" }, tipo: "red" },
    { nombre: "operador con 5xx", escenario: { misOrganizaciones: [[]], plataforma: { estado: 502 } }, tipo: "servidor" },
    { nombre: "credencial caducada", escenario: { misOrganizaciones: [[]], token: credencialSimulada({ expiraEnSegundos: -60 }).token }, tipo: "sesion" },
    { nombre: "Google no carga", tipo: "google_no_carga", googleNoCarga: true },
  ];

  for (const camino of CAMINOS) {
    test(`cada camino navega o avisa (m4): ${camino.nombre}`, async ({ page }) => {
      if (camino.googleNoCarga) {
        await fijarAjustes(page, { modo: "oidc", tenant: null });
        await simularApi(page);
        await page.route("https://accounts.google.com/gsi/client", (route) => route.abort("failed"));
        await page.goto("/login");
      } else {
        await entrar(page, camino.escenario!);
      }
      await expect(aviso(page)).toBeVisible();
      await expect(aviso(page)).toHaveAttribute("data-tipo", camino.tipo);
      await expect(page).toHaveURL(/\/login$/);
      await sinTextosProhibidos(page);

      // Contraste de 4,5:1 o más en el aviso y sin desplazamiento horizontal a 375 px.
      expect(await medirContraste(page, '[role="alert"][data-tipo]')).toEqual([]);
      await page.setViewportSize({ width: 375, height: 800 });
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth)).toBe(true);
    });
  }
});
