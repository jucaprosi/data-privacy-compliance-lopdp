// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤arbitro
// ¤¤frontend-ide
/**
 * FE-32 · Contraste en todas las rutas y vistas (GOB-07, criterio 23 del PRD; governance/especificaciones/FE-32.md).
 * API simulada, sin backend. Corre en el proyecto «desarrollo» (usa `fijarAjustes`). Mide con `tests/contraste.ts`.
 *
 * Qué mide: cada ruta `page.tsx` de producto (sin `/harness-*`) y cada vista registrada en el tablero, primero en claro
 * y después en oscuro, a 375 y 1280 px, con sus estados (carga, vacío, error, datos, foco). Texto de al menos 4,5:1 y
 * bordes de controles de al menos 3:1 (R2). Lo que aparece en `pendientes/FE-33.txt` a `FE-39.txt` queda como
 * `test.fixme`; lo que no aparece en ninguna lista se mide desde que nace (R3).
 *
 * Los controles desactivados y los textos de relleno quedan fuera del medidor por criterio WCAG 1.4.3 (exentos).
 * Los estados que la prueba no alcanza sola (diálogos, vistas NIIF) los declara cada ficha en `estados/FE-NN.ts` (`ESTADOS`).
 *
 * Mutaciones (cada una hace fallar la prueba que se indica):
 *  - m1: bajar un texto de `/plataforma` a 3:1 -> «/plataforma · datos».
 *  - m2: ignorar los archivos de pendientes -> las rutas y vistas sin migrar se miden y dan rojo.
 *  - m3: medir solo `/dashboard` y no cada vista -> «cada vista del tablero se mide por separado».
 */
import { readdirSync, readFileSync } from "node:fs";
import { join, relative, sep } from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { medirContraste } from "../contraste";
import { fijarAjustes, TENANT_PRUEBA } from "../auth/utilesAuth";
import { barraDeMenus, configurarProyecto } from "../utiles";
import { ajenasDe, leerFichas, pendientesPropias, type Ajena } from "./ajenas";
import { MENUS, SUBMENUS, type Submenu } from "@/components/layout/menus";
import { modulosNavegacionNIIF } from "@/components/layout/dashboardNavigation";
import * as M33 from "./estados/FE-33";
import * as M34 from "./estados/FE-34";
import * as M35 from "./estados/FE-35";
import * as M36 from "./estados/FE-36";
import * as M37 from "./estados/FE-37";
import * as M38 from "./estados/FE-38";
import * as M39 from "./estados/FE-39";

const RAIZ = join(__dirname, "..", "..");
const TEMAS = ["theme-light", "theme-dark"] as const; // claro primero (R1)
const ANCHOS = [375, 1280] as const;
const ESTADOS = ["carga", "vacio", "error", "datos", "foco"] as const;
type Estado = (typeof ESTADOS)[number];
const FICHAS: { ESTADOS: Record<string, (page: Page) => Promise<void>>; APERTURAS?: Record<string, (page: Page) => Promise<void>>; PREPARACIONES?: Record<string, (page: Page) => Promise<void>>; SIN_CONFIGURAR?: Set<string> }[] = [M33, M34, M35, M36, M37, M38, M39];
const MODULOS = FICHAS.map((m) => m.ESTADOS);
/** Aperturas de vistas que no son submenús (p. ej. las NIIF), declaradas por los módulos de estados (clave `vista:<id>`). */
const APERTURAS = Object.assign({}, ...FICHAS.map((m) => m.APERTURAS ?? {})) as Record<string, (page: Page) => Promise<void>>;
/** Preparaciones de las rutas (clave: la ruta), que se ejecutan antes de `page.goto` (R5): p. ej. simular la respuesta de un token. */
const PREPARACIONES = Object.assign({}, ...FICHAS.map((m) => m.PREPARACIONES ?? {})) as Record<string, (page: Page) => Promise<void>>;
/** R5 (FE-44): vistas (`vista:<id>`) que se miden sin `configurarProyecto`: marca explícita de cada `estados/FE-NN.ts`, no se deduce de una preparación. */
const SIN_CONFIGURAR = new Set<string>(FICHAS.flatMap((m) => [...(m.SIN_CONFIGURAR ?? [])]));
/** Estados que declaran los módulos de cada ficha para una ruta o vista (clave «<unidad> · <estado>»). */
export function estadosDeclarados(unidad: string): [string, (page: Page) => Promise<void>][] {
  return MODULOS.flatMap((m) => Object.entries(m)).filter(([k]) => k.startsWith(`${unidad} · `)).map(([k, f]) => [k.slice(unidad.length + 3), f]);
}

// ---------------------------------------------------------------- inventario
/** Rutas `page.tsx` de producto, como se nombran en los archivos de pendientes (`/aceptar/[token]`). */
export function rutasDeProducto(): string[] {
  const base = join(RAIZ, "src", "app");
  const rutas: string[] = [];
  const recorrer = (dir: string) => {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (e.isDirectory()) recorrer(join(dir, e.name));
      else if (e.name === "page.tsx") {
        const r = "/" + relative(base, dir).split(sep).join("/");
        rutas.push(r === "/." ? "/" : r);
      }
    }
  };
  recorrer(base);
  return rutas.filter((r) => !r.split("/").some((p) => p.startsWith("harness-"))).sort();
}

/** Vistas del tablero: los submenús registrados y los módulos NIIF. */
export function vistasDelTablero(): string[] {
  return [...new Set([...SUBMENUS.map((s) => s.vista as string), ...modulosNavegacionNIIF.map((m) => m.id as string)])].sort();
}

/** Fichas de `governance/tareas` (R4): `estado` y `propiedad` leídos como texto. */
const FICHAS_TAREAS = () => leerFichas(join(RAIZ, "..", "governance", "tareas"));

/** R2 (FE-44): líneas de `pendientes/FE-NN.txt`, una ruta (`/…`) o vista (`vista:<id>`) por línea. Solo admite archivos de la propiedad de su ficha. */
export function pendientes(): Map<string, string> {
  return pendientesPropias(join(__dirname, "pendientes"), FICHAS_TAREAS());
}

/** R3 (FE-44): líneas de `ajenas/FE-NN.txt`; quedan pendientes (`test.fixme`) mientras la ficha dueña del archivo no esté hecha. */
export function ajenas(): Map<string, Ajena> {
  return ajenasDe(join(__dirname, "ajenas"), FICHAS_TAREAS());
}

const PENDIENTES = pendientes();
const AJENAS = ajenas();
/** Razón de pendiente de una unidad: su propia lista (R2) o una ajena con la dueña sin hacer (R3); `undefined` si se mide. */
const razonDePendiente = (unidad: string) => {
  const propia = PENDIENTES.get(unidad);
  if (propia) return `pendiente de ${propia}`;
  const ajena = AJENAS.get(unidad);
  return ajena?.pendiente ? `${ajena.etiqueta}, anotada por ${ajena.ficha}` : undefined;
};
const concreta = (ruta: string) => ruta.replace(/\[[^\]]+\]/g, "ejemplo");

// ---------------------------------------------------------------- simulación de la API
const ORG = {
  id: "t-1", nombre_comercial: "Acme Ecuador", razon_social: "Acme Ecuador S.A.", ruc_identificacion: "0999999999001",
  activo: true, created_at: "2026-10-20T12:00:00Z", email_admin_inicial: "admin@acme.ec",
  invitacion_id: "inv-1", invitacion_expira_en: "2026-10-29T12:00:00Z", invitacion_estado: "emitida",
};
const PAQUETE = {
  id: "pqn-1", codigo: "LOPDP", nombre: "Ley Orgánica de Protección de Datos Personales", version: "1.0", estado: "borrador",
  creado_por: "op", creado_en: "2026-11-13T10:00:00Z", publicado_por: null, publicado_en: null, retirado_en: null, sin_verificar: 1,
};
const PARAMETRO = {
  clave: "plazo_derechos_dias", valor: "15", unidad: "calendario", termino_legal: "plazo", articulo: "LOPDP art. 13",
  fuente_url: "https://example.test/lopdp.pdf", verificado: false, verificado_por: null, verificado_por_nombre: null,
  verificado_en: null, actualizado_por: "op", actualizado_en: "2026-11-13T10:00:00Z",
};

async function simular(page: Page, estado: Estado) {
  const json = (r: import("@playwright/test").Route, status: number, cuerpo: unknown) =>
    r.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });
  const vacio = estado === "vacio";
  await page.route("**/api/v1/**", (r) => (estado === "error" ? json(r, 500, { detail: "error simulado" }) : json(r, 404, { detail: "No simulado" })));
  if (estado === "error") return;
  const resolver = async (r: import("@playwright/test").Route, cuerpo: unknown) => {
    if (estado === "carga") return; // la petición queda abierta: se mide la pantalla de carga
    return json(r, 200, cuerpo);
  };
  await page.route("**/api/v1/plataforma/organizaciones", (r) => resolver(r, vacio ? [] : [ORG]));
  await page.route("**/api/v1/plataforma/paquetes", (r) => resolver(r, { paquetes: vacio ? [] : [PAQUETE] }));
  await page.route(`**/api/v1/plataforma/paquetes/${PAQUETE.id}`, (r) => resolver(r, { paquete: PAQUETE, parametros: vacio ? [] : [PARAMETRO] }));
  await page.route("**/api/v1/biblioteca/editorial", (r) => resolver(r, { actor_id: "x", capacidades: ["editor"], versiones: [], revisiones: [] }));
  await page.route("**/api/v1/biblioteca/capacidades/equipo", (r) => resolver(r, vacio ? [] : [
    { usuario_id: "u-otro", nombre: "Operador Nuevo", email: "nuevo@plataforma.test", ha_entrado: false, capacidades: ["editor"] }]));
  await page.route("**/api/v1/biblioteca/capacidades/equipo/historial", (r) => resolver(r, []));
}

/**
 * Fija el tema por el estado guardado de la app (`jubys-audit-storage`), como QA-15 y QA-16, y espera a que `<html>` y el
 * div raíz del tablero lo lleven. Se llama antes de `page.goto` (para que la app lo lea al cargar) y otra vez después.
 */
async function ponerTema(page: Page, tema: string) {
  await page.addInitScript((t) => {
    try {
      window.localStorage.setItem("jubys-audit-storage", JSON.stringify({ state: { theme: t === "theme-dark" ? "dark" : "light" }, version: 6 }));
    } catch {
      // Almacenamiento bloqueado: se mide el tema por defecto.
    }
  }, tema);
  if (page.url() === "about:blank") return;
  await expect(page.locator("html")).toHaveClass(new RegExp(tema));
  const raiz = page.locator(".app-frame-canvas");
  if ((await raiz.count()) > 0) await expect(raiz).toHaveClass(new RegExp(tema));
}

/** Abre un menú y uno de sus submenús; a 375 px el submenú está en el cajón lateral, que se abre por su botón «Menú». */
async function abrirSubmenu(page: Page, submenu: Submenu) {
  const menu = MENUS.find((m) => m.id === submenu.menu);
  if (!menu) throw new Error(`Menú desconocido: ${submenu.menu}`);
  await barraDeMenus(page).getByRole("button", { name: menu.nombre, exact: true }).click();
  const grupo = page.getByRole("group", { name: `Submenús de ${menu.nombre}` });
  if (!(await grupo.isVisible())) await page.getByRole("button", { name: "Menú", exact: true }).click();
  await expect(grupo).toBeVisible();
  const escapado = submenu.nombre.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  await grupo.getByRole("button", { name: new RegExp(`^${escapado}`) }).click();
}

/** Razón de contraste del borde de cada control frente a su fondo efectivo (WCAG 1.4.11): debe ser >= 3. */
async function razonesDeBorde(page: Page, selector: string): Promise<number[]> {
  return page.evaluate((sel) => {
    const lienzo = document.createElement("canvas").getContext("2d", { willReadFrequently: true })!;
    const rgb = (c: string) => { lienzo.clearRect(0, 0, 1, 1); lienzo.fillStyle = c; lienzo.fillRect(0, 0, 1, 1); const d = lienzo.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
    const lum = ([r, g, b]: number[]) => { const f = (v: number) => { const s = v / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const fondo = (el: Element | null): number[] => {
      for (let n = el; n; n = n.parentElement) { const c = rgb(getComputedStyle(n).backgroundColor); if (c[3] > 0.5) return c; }
      return document.documentElement.classList.contains("theme-dark") ? [10, 10, 12, 1] : [255, 255, 255, 1];
    };
    // Un borde con estilo none/hidden, ancho 0 o alfa 0 no se ve: no es un indicador visual (WCAG 1.4.11).
    const visible = (el: Element) => {
      const e = getComputedStyle(el);
      return e.borderTopStyle !== "none" && e.borderTopStyle !== "hidden" && parseFloat(e.borderTopWidth) > 0 && rgb(e.borderTopColor)[3] > 0;
    };
    return Array.from(document.querySelectorAll(sel)).filter(visible)
      .map((el) => {
        const f = fondo(el.parentElement), [r, g, b, alfa] = rgb(getComputedStyle(el).borderTopColor);
        const sobre = [r, g, b].map((v, i) => v * alfa + f[i] * (1 - alfa)); // el color semitransparente se compone sobre el fondo efectivo
        const a = lum(sobre), c = lum(f);
        return (Math.max(a, c) + 0.05) / (Math.min(a, c) + 0.05);
      });
  }, selector);
}

/** Mide el texto (4,5:1) y los bordes de los controles (3:1) de lo que hay en pantalla. */
async function medir(page: Page, contexto: string) {
  expect(await medirContraste(page, "body"), `texto · ${contexto}`).toEqual([]);
  expect((await razonesDeBorde(page, "main input, main select, main textarea, main button")).filter((r) => r < 3), `bordes · ${contexto}`).toEqual([]);
}

async function medirEstado(page: Page, ruta: string, estado: Estado, tema: string, ancho: number, paso?: () => Promise<void>, nombreEstado?: string) {
  await page.setViewportSize({ width: ancho, height: 900 });
  await fijarAjustes(page, { modo: "headers", tenant: TENANT_PRUEBA });
  await simular(page, estado);
  await ponerTema(page, tema);
  await PREPARACIONES[ruta]?.(page);
  await page.goto(concreta(ruta));
  await ponerTema(page, tema);
  const contexto = `${ruta} · ${nombreEstado ?? estado} · ${tema} · ${ancho} px`;
  if (estado === "foco") {
    await page.locator("main a, main button, main input, main select").first().focus().catch(() => undefined);
  } else if (estado !== "carga") {
    await page.waitForLoadState("networkidle");
  }
  if (paso) await paso();
  await medir(page, contexto);
}

// ---------------------------------------------------------------- rutas
for (const ruta of rutasDeProducto()) {
  const razon = razonDePendiente(ruta);
  for (const tema of TEMAS) {
    for (const ancho of ANCHOS) {
      const nombre = `${ruta} · ${tema} · ${ancho} px`;
      if (razon) {
        test.fixme(`${nombre} (${razon})`, async () => {});
        continue;
      }
      test(nombre, async ({ page }) => {
        for (const estado of ESTADOS) await medirEstado(page, ruta, estado, tema, ancho);
        for (const [nombreEstado, paso] of estadosDeclarados(ruta)) await medirEstado(page, ruta, "datos", tema, ancho, async () => { await paso(page); }, nombreEstado);
      });
    }
  }
}

// ---------------------------------------------------------------- vistas del tablero
/** Abre una vista del tablero con el proyecto configurado y la mide en cada tema y ancho. */
async function medirVista(page: Page, vista: string, tema: string, ancho: number) {
  await page.setViewportSize({ width: ancho, height: 900 });
  await fijarAjustes(page, { modo: "headers", tenant: TENANT_PRUEBA });
  await simular(page, "datos");
  await ponerTema(page, tema);
  await PREPARACIONES[`vista:${vista}`]?.(page);
  await page.goto("/");
  if (!SIN_CONFIGURAR.has(`vista:${vista}`)) await configurarProyecto(page, "Entidad FE-32");
  const submenu = SUBMENUS.find((s) => s.vista === vista);
  const apertura = APERTURAS[`vista:${vista}`];
  if (submenu) await abrirSubmenu(page, submenu);
  else if (apertura) await apertura(page);
  else throw new Error(`La vista «${vista}» no es un submenú del tablero ni tiene apertura: la ficha que la migra la declara en APERTURAS de su módulo estados/FE-NN.ts.`);
  await ponerTema(page, tema);
  await medir(page, `vista ${vista} · ${tema} · ${ancho} px`);
  for (const [nombreEstado, paso] of estadosDeclarados(`vista:${vista}`)) {
    await paso(page);
    await medir(page, `vista ${vista} · ${nombreEstado} · ${tema} · ${ancho} px`);
  }
}

test.describe("cada vista del tablero se mide por separado", () => {
  for (const vista of vistasDelTablero()) {
    const razon = razonDePendiente(`vista:${vista}`);
    for (const tema of TEMAS) {
      for (const ancho of ANCHOS) {
        const nombre = `vista ${vista} · ${tema} · ${ancho} px`;
        if (razon) {
          test.fixme(`${nombre} (${razon})`, async () => {});
          continue;
        }
        test(nombre, async ({ page }) => medirVista(page, vista, tema, ancho));
      }
    }
  }
});

// ---------------------------------------------------------------- los archivos de pendientes
test("los archivos de pendientes solo nombran rutas y vistas que existen", () => {
  const rutas = new Set(rutasDeProducto());
  const vistas = new Set(vistasDelTablero());
  const huerfanas = [...PENDIENTES.keys(), ...AJENAS.keys()].filter((l) => (l.startsWith("vista:") ? !vistas.has(l.slice(6)) : !rutas.has(l)));
  expect(huerfanas, "líneas de pendientes sin ruta ni vista (¿se borró o se renombró?)").toEqual([]);
});

// ---------------------------------------------------------------- prueba de control del medidor (FE-43 R4)
test("el medidor de bordes distingue un borde bajo, uno suficiente y uno transparente", async ({ page }) => {
  const ruta = rutasDeProducto().find((r) => !PENDIENTES.has(r));
  if (!ruta) throw new Error("No hay una ruta ya medida donde abrir el control.");
  for (const tema of TEMAS) {
    await page.goto("about:blank"); // ponerTema solo espera la clase con una página ya cargada
    await page.setViewportSize({ width: 1280, height: 900 });
    await fijarAjustes(page, { modo: "headers", tenant: TENANT_PRUEBA });
    await simular(page, "datos");
    await ponerTema(page, tema);
    await page.goto(concreta(ruta));
    await ponerTema(page, tema);
    await page.evaluate(() => {
      const caja = document.createElement("div");
      caja.id = "control-fe43";
      caja.style.background = "var(--background)";
      caja.innerHTML =
        '<input id="c-bajo" style="border:1px solid var(--ui-borde)">' +
        '<input id="c-ok" style="border:1px solid var(--ui-borde-control)">' +
        '<button id="c-transparente" class="border border-transparent">x</button>';
      document.body.appendChild(caja);
    });
    expect((await razonesDeBorde(page, "#c-bajo")).every((r) => r < 3), `borde bajo · ${tema}`).toBe(true);
    expect((await razonesDeBorde(page, "#c-bajo")).length, `borde bajo medido · ${tema}`).toBe(1);
    expect((await razonesDeBorde(page, "#c-ok")).filter((r) => r >= 3).length, `borde suficiente · ${tema}`).toBe(1);
    expect(await razonesDeBorde(page, "#c-transparente"), `borde transparente · ${tema}`).toEqual([]);
  }
});
