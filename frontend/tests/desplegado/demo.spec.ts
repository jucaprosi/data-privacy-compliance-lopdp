// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤arbitro ¤demo
/**
 * QA-17 · Humo contra la demo desplegada, en los cuatro proyectos de playwright.desplegado.config.ts.
 * Contrato: governance/especificaciones/QA-17.md (R3, R5 y §4).
 *
 * Una entrada por proyecto (`POST /api/v1/demo/entrar`) con el ID token de HUMO_DEMO_TOKEN, y cada prueba
 * abre el tablero con la sesión que deja la app al entrar (EntradaDemo.tsx: persona, organización y sesión
 * en sessionStorage). Al final, `POST /api/v1/demo/terminar`. Solo lectura: nada se confirma por pantalla.
 * El token nunca se imprime: ni en los mensajes de fallo ni en las anotaciones.
 */
import { expect, test, type Page } from "@playwright/test";

import { medirContraste } from "../contraste";

// Textos tomados del código (AvisoEntorno.tsx, AccionesDemo.tsx, menus/base.ts, ArmazonResponsive.tsx).
const FRANJA_ESCRITORIO = "Demostración · datos ficticios";
const FRANJA_MOVIL = "Demo · ficticio";
const MENUS = [
  "Inicio",
  "Diagnóstico",
  "Inventario",
  "Biblioteca",
  "Operación",
  "Riesgos y auditoría",
  "DPO",
  "Conocimiento",
  "Configuración",
];
const ROLES = ["admin_organizacion", "dpo", "coordinador", "implementador", "responsable_area", "auditor"];
const NAVEGACION = "Menús principales";
const BOTON_CAJON = "Menú";
const CAJON = "Menú de navegación";
const CERRAR_CAJON = "Cerrar menú";
const LISTA_PERSONAS = "Personas de la demostración";
const PROHIBIDOS = ["undefined", "null", "[object Object]", "(403)", "(500)", "Entorno de pruebas"];

interface PersonaDemo {
  usuario_id: string;
  nombre: string;
  rol: string;
  rol_etiqueta: string;
  unidad?: string | null;
}

interface EstadoDemo {
  organizacion: { tenant_id: string; nombre: string };
  persona_activa: PersonaDemo;
  personas: PersonaDemo[];
}

interface Entrada {
  token: string;
  email: string;
  nombre: string;
  exp: number;
  estado: EstadoDemo;
}

let entrada: Entrada | null = null;

function exigirToken(): string {
  const token = (process.env.HUMO_DEMO_TOKEN ?? "").trim();
  if (!token) {
    throw new Error(
      "[PRECONDICION FALLIDA] falta HUMO_DEMO_TOKEN: el ID token de la cuenta de servicio de pruebas de la demo " +
        "(comando en la cabecera de playwright.desplegado.config.ts).",
    );
  }
  return token;
}

/** La carga del JWT, sin verificarla: la verifica el servidor. Es lo que hace `leerCredencial`. */
function cargaDe(token: string): { email: string; nombre: string; exp: number } {
  const carga = JSON.parse(Buffer.from(token.split(".")[1] ?? "", "base64url").toString("utf-8")) as Record<string, unknown>;
  const email = typeof carga.email === "string" ? carga.email : "";
  return { email, nombre: typeof carga.name === "string" ? carga.name : email, exp: Number(carga.exp) };
}

const etiquetaDe = (p: PersonaDemo) => (p.unidad ? `${p.rol_etiqueta} · ${p.unidad}` : p.rol_etiqueta);
const temaDelProyecto = () => (test.info().project.name.endsWith("-oscuro") ? "dark" : "light");
const esMovil = () => test.info().project.name.startsWith("movil-");

test.describe.configure({ mode: "serial" });

test.beforeAll(async ({ playwright }, info) => {
  const token = exigirToken();
  const api = await playwright.request.newContext({ baseURL: info.project.use.baseURL });
  try {
    const r = await api.post("/api/v1/demo/entrar", {
      headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
    });
    expect(r.status(), `POST /api/v1/demo/entrar: ${await r.text()}`).toBe(200);
    entrada = { token, ...cargaDe(token), estado: (await r.json()) as EstadoDemo };
  } finally {
    await api.dispose();
  }
});

test.afterAll(async ({ playwright }, info) => {
  if (!entrada) return;
  const api = await playwright.request.newContext({ baseURL: info.project.use.baseURL });
  try {
    const r = await api.post("/api/v1/demo/terminar", {
      headers: {
        Authorization: `Bearer ${entrada.token}`,
        "X-Tenant-ID": entrada.estado.organizacion.tenant_id,
        Accept: "application/json",
      },
    });
    expect([200, 401], `POST /api/v1/demo/terminar respondió ${r.status()}`).toContain(r.status());
  } finally {
    entrada = null;
    await api.dispose();
  }
});

/** Abre el tablero con la sesión de la entrada y recoge los errores de página desde el primer script. */
async function abrirTablero(page: Page): Promise<string[]> {
  if (!entrada) throw new Error("[PRECONDICION FALLIDA] no hubo entrada en la demo.");
  const errores: string[] = [];
  page.on("pageerror", (e) => errores.push(e.message));
  const { token, email, nombre, exp, estado } = entrada;
  const activa = estado.persona_activa;
  await page.addInitScript(
    (s) => {
      if (window.sessionStorage.getItem("lopdp-sesion-v1")) return;
      window.sessionStorage.setItem("lopdp-sesion-v1", JSON.stringify(s.sesion));
      window.sessionStorage.setItem("lopdp-organizacion-activa-v1", JSON.stringify(s.organizacion));
      window.sessionStorage.setItem("evydentia.demo.persona", JSON.stringify(s.persona));
      window.localStorage.setItem("lopdp-dueno-datos-v1", s.dueno);
    },
    {
      sesion: { token, email, nombre, exp },
      organizacion: { tenant_id: estado.organizacion.tenant_id, nombre_comercial: estado.organizacion.nombre, roles: [activa.rol] },
      persona: { usuario_id: activa.usuario_id, rol: activa.rol },
      dueno: `${email.trim().toLowerCase()}|${estado.organizacion.tenant_id.trim()}`,
    },
  );
  await page.goto("/dashboard");
  await page.reload();
  await expect(page.getByTestId("demo-ver-como")).toBeVisible();
  return errores;
}

async function sinTextosRotos(page: Page, donde: string): Promise<void> {
  const texto = await page.locator("body").innerText();
  for (const prohibido of PROHIBIDOS) expect(texto, `${donde}: aparece «${prohibido}»`).not.toContain(prohibido);
  expect(texto, `${donde}: aparecen llaves sin sustituir`).not.toMatch(/\{[^}\n]*\}/);
}

test.beforeEach(async () => {
  test.info().annotations.push(
    { type: "calentamiento-ms", description: process.env.HUMO_CALENTAMIENTO_MS ?? "sin medir" },
    { type: "tema", description: `theme-${temaDelProyecto()}` },
  );
});

test("§4.1 · la clase del <html> es la del tema del proyecto", async ({ page }) => {
  await abrirTablero(page);
  const tema = temaDelProyecto();
  const otro = tema === "dark" ? "light" : "dark";
  await expect(page.locator("html")).toHaveClass(new RegExp(`(^|\\s)theme-${tema}(\\s|$)`));
  await expect(page.locator("html")).not.toHaveClass(new RegExp(`(^|\\s)theme-${otro}(\\s|$)`));
  test.info().annotations.push({ type: "clase-html", description: (await page.locator("html").getAttribute("class")) ?? "" });
});

test("§4.2 y §4.7 · la franja de la demo se ve sin desplazarse y la pantalla no trae textos rotos", async ({ page }) => {
  const errores = await abrirTablero(page);
  const franja = page.getByTestId("aviso-entorno");
  await expect(franja).toHaveAttribute("data-entorno", "demo");
  await expect(franja).toBeInViewport();
  await expect(franja.getByText(esMovil() ? FRANJA_MOVIL : FRANJA_ESCRITORIO, { exact: true })).toBeVisible();
  await expect(page.getByText("Entorno de pruebas")).toHaveCount(0);
  await expect(page.getByRole("alert")).toHaveCount(0);
  await sinTextosRotos(page, "tablero");
  expect(errores, "errores de página").toEqual([]);
});

test("§4.3 · el selector «Ver como» lista las seis personas y Escape lo cierra", async ({ page }) => {
  await abrirTablero(page);
  const activa = entrada!.estado.persona_activa;
  const boton = page.getByTestId("demo-ver-como");
  await expect(boton).toHaveAccessibleName(`Ver como: ${activa.nombre} · ${etiquetaDe(activa)}`);
  if (esMovil()) {
    await expect(page.getByTestId("demo-persona-activa")).toBeHidden();
  } else {
    await expect(page.getByTestId("demo-persona-activa")).toBeVisible();
    await expect(page.getByTestId("demo-persona-activa")).toHaveText(`Ver como: ${activa.nombre} · ${activa.rol_etiqueta}`);
  }

  await boton.click();
  const lista = page.getByRole("listbox", { name: LISTA_PERSONAS });
  await expect(lista).toBeVisible();
  const opciones = lista.getByRole("option");
  await expect(opciones).toHaveCount(6);
  expect(await lista.getByTestId("demo-persona").evaluateAll((b) => b.map((x) => x.getAttribute("data-rol")))).toEqual(ROLES);
  await expect(lista.getByRole("option", { selected: true })).toHaveCount(1);
  await expect(lista.getByRole("option", { selected: true })).toContainText(activa.nombre);
  await sinTextosRotos(page, "selector abierto");

  await page.keyboard.press("Escape");
  await expect(lista).toBeHidden();
  await expect(boton).toBeFocused();
});

test("§4.4 · los nueve menús, en orden, e «Inicio» abre el tablero; en móvil, el cajón y sin desplazamiento horizontal", async ({ page }) => {
  await abrirTablero(page);
  const navegacion = page.getByRole("navigation", { name: NAVEGACION });
  const menus = navegacion.getByRole("button");
  await expect(menus).toHaveText(MENUS);
  if (!esMovil()) {
    for (const nombre of MENUS) await expect(navegacion.getByRole("button", { name: nombre, exact: true })).toBeInViewport();
  }

  await navegacion.getByRole("button", { name: "Inicio", exact: true }).click();
  if (esMovil()) {
    const abrir = page.getByRole("button", { name: BOTON_CAJON, exact: true });
    await abrir.click();
    const cajon = page.getByRole("dialog", { name: CAJON });
    await expect(cajon).toBeVisible();
    await expect(cajon.getByRole("button", { name: CERRAR_CAJON })).toBeVisible();
    // El cajón trae los submenús del menú abierto; los nueve menús siguen en «Menús principales» (UX/UI, 2026-11-28).
    await expect(cajon.getByRole("group", { name: "Submenús de Inicio" }).getByRole("button", { name: /Tablero de la organización/ })).toBeVisible();
    await sinTextosRotos(page, "cajón del menú");
    await page.keyboard.press("Escape");
    await expect(cajon).toBeHidden();
    await expect(abrir).toBeFocused();
    const { ancho, visible } = await page.evaluate(() => ({
      ancho: document.documentElement.scrollWidth,
      visible: document.documentElement.clientWidth,
    }));
    expect(ancho, `desplazamiento horizontal: scrollWidth ${ancho} > clientWidth ${visible}`).toBeLessThanOrEqual(visible);
  } else {
    await expect(page.getByRole("button", { name: /Tablero de la organización/ })).toBeVisible();
  }
  await expect(page.getByTestId("aviso-entorno")).toBeInViewport();
});

test("§4.5 · «Terminar demo» abre el diálogo con el foco en «Cancelar» y Escape lo cierra", async ({ page }) => {
  await abrirTablero(page);
  if (esMovil()) {
    await page.getByTestId("demo-ver-como").click();
    await page.getByTestId("demo-terminar-panel").click();
  } else {
    await page.getByRole("button", { name: "Terminar demo", exact: true }).click();
  }
  const dialogo = page.getByRole("alertdialog", { name: "¿Terminar la demostración?" });
  await expect(dialogo).toBeVisible();
  await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
  await page.keyboard.press("Escape");
  await expect(dialogo).toBeHidden();
  // La demo sigue abierta: el cierre lo hace afterAll por API (R5).
  await expect(page.getByTestId("demo-ver-como")).toBeVisible();
});

test("§4.6 · la franja y el selector llegan a 4,5:1 en el tema del proyecto", async ({ page }) => {
  await abrirTablero(page);
  expect(await medirContraste(page, '[data-testid="aviso-entorno"]'), "franja").toEqual([]);
  expect(await medirContraste(page, '[data-testid="demo-ver-como"]'), "selector").toEqual([]);
});
