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
import { abrirSubmenu, configurarProyecto } from "../utiles";
import { SUBMENUS } from "@/components/layout/menus";
import { modulosNavegacionNIIF } from "@/components/layout/dashboardNavigation";
import { ESTADOS as E33 } from "./estados/FE-33";
import { ESTADOS as E34 } from "./estados/FE-34";
import { ESTADOS as E35 } from "./estados/FE-35";
import { ESTADOS as E36 } from "./estados/FE-36";
import { ESTADOS as E37 } from "./estados/FE-37";
import { ESTADOS as E38 } from "./estados/FE-38";
import { ESTADOS as E39 } from "./estados/FE-39";

const RAIZ = join(__dirname, "..", "..");
const TEMAS = ["theme-light", "theme-dark"] as const; // claro primero (R1)
const ANCHOS = [375, 1280] as const;
const ESTADOS = ["carga", "vacio", "error", "datos", "foco"] as const;
type Estado = (typeof ESTADOS)[number];
const MODULOS = [E33, E34, E35, E36, E37, E38, E39];
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

/** Líneas de `pendientes/FE-NN.txt`: una ruta (`/…`) o vista (`vista:<id>`) por línea; `#` abre un comentario. */
export function pendientes(): Map<string, string> {
  const dir = join(__dirname, "pendientes");
  const mapa = new Map<string, string>();
  for (const f of readdirSync(dir).filter((n) => /^FE-\d+\.txt$/.test(n)).sort()) {
    for (const linea of readFileSync(join(dir, f), "utf8").split(/\r?\n/)) {
      const t = linea.split("#")[0].trim(); // «<ruta o vista>  # <archivo que la justifica>»
      if (t && !mapa.has(t)) mapa.set(t, f.replace(".txt", "")); // en varias listas: se mide cuando salga de la última
    }
  }
  return mapa;
}

const PENDIENTES = pendientes();
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

async function ponerTema(page: Page, tema: string) {
  await page.evaluate((t) => { document.documentElement.classList.remove("theme-light", "theme-dark"); document.documentElement.classList.add(t); }, tema);
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
    return Array.from(document.querySelectorAll(sel)).filter((el) => parseFloat(getComputedStyle(el).borderTopWidth) > 0)
      .map((el) => { const a = lum(rgb(getComputedStyle(el).borderTopColor)), b = lum(fondo(el.parentElement)); return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05); });
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
  const dueña = PENDIENTES.get(ruta);
  for (const tema of TEMAS) {
    for (const ancho of ANCHOS) {
      const nombre = `${ruta} · ${tema} · ${ancho} px`;
      if (dueña) {
        test.fixme(`${nombre} (pendiente de ${dueña})`, async () => {});
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
  await page.goto("/");
  await configurarProyecto(page, "Entidad FE-32");
  const submenu = SUBMENUS.find((s) => s.vista === vista);
  if (!submenu) throw new Error(`La vista «${vista}» no es un submenú del tablero: la ficha que la migra añade aquí cómo se abre.`);
  await abrirSubmenu(page, submenu);
  await ponerTema(page, tema);
  await medir(page, `vista ${vista} · ${tema} · ${ancho} px`);
  for (const [nombreEstado, paso] of estadosDeclarados(`vista:${vista}`)) {
    await paso(page);
    await medir(page, `vista ${vista} · ${nombreEstado} · ${tema} · ${ancho} px`);
  }
}

test.describe("cada vista del tablero se mide por separado", () => {
  for (const vista of vistasDelTablero()) {
    const dueña = PENDIENTES.get(`vista:${vista}`);
    for (const tema of TEMAS) {
      for (const ancho of ANCHOS) {
        const nombre = `vista ${vista} · ${tema} · ${ancho} px`;
        if (dueña) {
          test.fixme(`${nombre} (pendiente de ${dueña})`, async () => {});
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
  const huerfanas = [...PENDIENTES.keys()].filter((l) => (l.startsWith("vista:") ? !vistas.has(l.slice(6)) : !rutas.has(l)));
  expect(huerfanas, "líneas de pendientes sin ruta ni vista (¿se borró o se renombró?)").toEqual([]);
});
