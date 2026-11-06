/**
 * ORG-21: el operador de la plataforma entra aunque no pertenezca a ninguna organización.
 *
 * Google y la API se simulan (utilesAuth.ts), en modo «oidc» fijado con `window.__LOPDP_AUTH_PRUEBAS__`,
 * que solo existe fuera de producción: por eso el archivo lleva el sufijo `-activa` y corre en el
 * proyecto «desarrollo» (playwright.config.ts, CI-16). La credencial es simulada.
 *
 * - `mis-organizaciones` 403 y `plataforma` 200 ⟹ llega a /plataforma y ve el listado.
 * - `mis-organizaciones` con la lista vacía y `plataforma` 200 ⟹ llega a /plataforma.
 * - `mis-organizaciones` 403 y `plataforma` 403 ⟹ se queda en la entrada, con el mensaje de hoy y sin sesión.
 * - `mis-organizaciones` con una organización ⟹ entra en ella como hoy, aunque `plataforma` responda 200.
 * - Al cerrarse la sesión (un 401 de la plataforma), `/plataforma` deja de llevar `Authorization`.
 *
 * Pruebas de mutación documentadas (ORG-21), ejecutadas y restauradas:
 *  - En `entrarComoOperador` (src/app/login/page.tsx) se abrió la sesión y se fue a /plataforma sin
 *    preguntar al servidor (`operador = true` en lugar de `await esOperadorDeLaPlataforma(credential)`).
 *    Falló «403 y 403» (y también «403 y 200», que espera la pregunta de la entrada).
 *  - `cabecerasDePlataforma` (src/lib/auth/cabeceras.ts) volvió a usar `leerSesion()`. Falló «403 y 200»:
 *    el listado de /plataforma sale sin `Authorization`, porque `leerSesion` descarta y borra la sesión
 *    sin organización activa.
 *  - `cerrarSesion` (src/lib/auth/sesion.ts) sin `olvidarSesionDeOperador()`. Falló «al cerrarse la
 *    sesión»: la sesión del operador seguía guardada y /plataforma volvía a llevar el token.
 *
 * La sesión del operador sin organización vive en su propia clave (`lopdp-sesion-operador-v1`): los
 * stores globales llaman a `leerSesion` en cualquier página y borrarían una sesión sin organización
 * guardada en la clave de siempre.
 */
import { expect, test, type Page, type Request } from "@playwright/test";

import {
  BOTON_GOOGLE,
  CLAVE_SESION,
  credencialSimulada,
  fijarAjustes,
  googleSimulado,
  ORGANIZACION_PRUEBA,
  ruta,
  simularApi,
  type OrganizacionSimulada,
} from "./utilesAuth";

const operador = credencialSimulada({ email: "operador@plataforma.test", nombre: "Operador Prueba" });

const ORGANIZACION_REGISTRADA = {
  id: "tenant-registrado",
  nombre_comercial: "Cooperativa Registrada",
  razon_social: "Cooperativa Registrada S.A.",
  ruc_identificacion: "0990000000001",
  activo: true,
  created_at: "2026-11-01T10:00:00Z",
  email_admin_inicial: "admin@cooperativa.test",
  invitacion_id: null,
  invitacion_expira_en: null,
  invitacion_estado: "aceptada",
};

interface Escenario {
  /** Lo que responde mis-organizaciones: un estado de error o la lista. */
  misOrganizaciones: number | OrganizacionSimulada[];
  /** Estado de GET /plataforma/organizaciones. */
  plataforma: number;
}

async function entrar(page: Page, escenario: Escenario): Promise<Request[]> {
  await fijarAjustes(page, { modo: "oidc", tenant: null });
  await googleSimulado(page, operador.token);
  const organizaciones = Array.isArray(escenario.misOrganizaciones) ? escenario.misOrganizaciones : [];
  const llamadas = await simularApi(page, { organizaciones });
  // Registradas después de simularApi: Playwright aplica primero la última ruta que coincide.
  await page.route("**/api/v1/organizacion/mis-organizaciones", (route) => {
    if (typeof escenario.misOrganizaciones === "number") {
      return route.fulfill({
        status: escenario.misOrganizaciones,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Usuario no registrado en la plataforma." }),
      });
    }
    return route.fallback();
  });
  await page.route("**/api/v1/plataforma/organizaciones", (route) => {
    llamadas.push(route.request());
    if (escenario.plataforma === 200) {
      return route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify([ORGANIZACION_REGISTRADA]) });
    }
    return route.fulfill({
      status: escenario.plataforma,
      contentType: "application/json",
      body: JSON.stringify({ detail: "Solo el operador de la plataforma puede hacer esto.", code: "PLATAFORMA_SOLO_OPERADOR" }),
    });
  });
  await page.goto("/login");
  await page.getByRole("button", { name: BOTON_GOOGLE }).click();
  return llamadas;
}

const aPlataforma = (llamadas: Request[]) => llamadas.filter((l) => ruta(l.url()) === "/plataforma/organizaciones");
/** Clave de la sesión del operador sin organización (src/lib/auth/sesion.ts#ORG-21). */
const CLAVE_SESION_OPERADOR = "lopdp-sesion-operador-v1";
const leer = (page: Page, clave: string) => page.evaluate((c) => window.sessionStorage.getItem(c), clave);

test.describe("Operador de la plataforma sin organización (ORG-21)", () => {
  test("mis-organizaciones 403 y plataforma 200: llega a /plataforma y ve el listado", async ({ page }) => {
    const llamadas = await entrar(page, { misOrganizaciones: 403, plataforma: 200 });

    await expect(page).toHaveURL(/\/plataforma$/);
    await expect(page.getByRole("heading", { name: "Organizaciones registradas" })).toBeVisible();
    await expect(page.getByTestId(`organizacion-${ORGANIZACION_REGISTRADA.id}`)).toContainText("Cooperativa Registrada");
    // La pregunta de la entrada y el listado de la pantalla llevan el token de la persona.
    expect(aPlataforma(llamadas).length).toBeGreaterThanOrEqual(2);
    for (const llamada of aPlataforma(llamadas)) {
      expect(llamada.headers()["authorization"]).toBe(`Bearer ${operador.token}`);
    }
    // La sesión del operador vive en su clave; la de las organizaciones queda vacía.
    expect(JSON.parse((await leer(page, CLAVE_SESION_OPERADOR)) ?? "{}").email).toBe(operador.email);
    expect(await leer(page, CLAVE_SESION)).toBeNull();
  });

  test("mis-organizaciones con la lista vacía y plataforma 200: llega a /plataforma", async ({ page }) => {
    await entrar(page, { misOrganizaciones: [], plataforma: 200 });

    await expect(page).toHaveURL(/\/plataforma$/);
    await expect(page.getByRole("heading", { name: "Organizaciones registradas" })).toBeVisible();
  });

  test("mis-organizaciones 403 y plataforma 403: se queda en la entrada con el mensaje de hoy y sin sesión", async ({ page }) => {
    const llamadas = await entrar(page, { misOrganizaciones: 403, plataforma: 403 });

    await expect(page.getByTestId("login-error")).toHaveText(
      "No se pudieron consultar tus organizaciones: el servidor respondió 403.",
    );
    await expect.poll(() => aPlataforma(llamadas).length).toBe(1);
    await expect(page).toHaveURL(/\/login$/);
    expect(await leer(page, CLAVE_SESION)).toBeNull();
    expect(await leer(page, CLAVE_SESION_OPERADOR)).toBeNull();
  });

  test("con una organización entra en ella como hoy, aunque plataforma responda 200", async ({ page }) => {
    const llamadas = await entrar(page, { misOrganizaciones: [ORGANIZACION_PRUEBA], plataforma: 200 });

    await expect(page).toHaveURL(/\/dashboard/);
    await expect(page.getByTestId("organizacion-activa")).toContainText(ORGANIZACION_PRUEBA.nombre_comercial);
    expect(aPlataforma(llamadas)).toEqual([]);
  });

  test("al cerrarse la sesión, /plataforma deja de llevar Authorization", async ({ page }) => {
    const escenario: Escenario = { misOrganizaciones: 403, plataforma: 200 };
    const llamadas = await entrar(page, escenario);
    await expect(page).toHaveURL(/\/plataforma$/);
    await expect(page.getByRole("heading", { name: "Organizaciones registradas" })).toBeVisible();
    expect(await leer(page, CLAVE_SESION_OPERADOR)).not.toBeNull();

    // Un 401 cierra la sesión (fetchAutenticado → cerrarSesion) y lleva a la entrada.
    escenario.plataforma = 401;
    await page.reload();
    await expect(page).toHaveURL(/\/login\?motivo=expirada/);
    expect(await leer(page, CLAVE_SESION_OPERADOR)).toBeNull();

    escenario.plataforma = 200;
    const antes = aPlataforma(llamadas).length;
    await page.goto("/plataforma");
    await expect.poll(() => aPlataforma(llamadas).length).toBeGreaterThan(antes);
    for (const llamada of aPlataforma(llamadas).slice(antes)) {
      expect(llamada.headers()["authorization"]).toBeUndefined();
    }
  });
});
