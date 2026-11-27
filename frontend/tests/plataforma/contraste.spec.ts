// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤arbitro
// ¤¤frontend-ide
/**
 * FE-31 · Las pantallas de Plataforma usan los tokens del tema (governance/especificaciones/FE-31.md). API simulada.
 * Corre en el proyecto «desarrollo» (usa `fijarAjustes`). Mide con `tests/contraste.ts`.
 *
 * Mutaciones (cada una hace fallar la prueba que se indica):
 *  - m1: volver a `bg-zinc-900/70` en una tarjeta -> «sin clases de la paleta fija» y el contraste en claro.
 *  - m2: texto oscuro sobre el botón primario -> «contraste … /plataforma con código de invitación».
 *  - m3: añadir `bg-amber-950/20` -> «las tres pantallas no llevan clases de la paleta fija».
 *  - m4: mostrar el estado HTTP en el error -> «el error muestra su texto fijo…».
 *  - m5: mostrar «Todavía no hay organizaciones.» tras un fallo -> «una carga fallida…».
 */
import { readFileSync } from "node:fs";
import { join } from "node:path";
import { expect, test, type Page } from "@playwright/test";
import { medirContraste } from "../contraste";
import { fijarAjustes, TENANT_PRUEBA } from "../auth/utilesAuth";

const ORG = {
  id: "t-1", nombre_comercial: "Acme Ecuador", razon_social: "Acme Ecuador S.A.", ruc_identificacion: "0999999999001",
  activo: true, created_at: "2026-10-20T12:00:00Z", email_admin_inicial: "admin@acme.ec",
  invitacion_id: "inv-1", invitacion_expira_en: "2026-10-29T12:00:00Z", invitacion_estado: "emitida",
};
const CADUCADA = { ...ORG, id: "t-2", nombre_comercial: "Organización Caducada", invitacion_id: "inv-2", invitacion_estado: "caducada" };
const PAQUETE = {
  id: "pqn-1", codigo: "LOPDP", nombre: "Ley Orgánica de Protección de Datos Personales", version: "1.0", estado: "borrador",
  creado_por: "op", creado_en: "2026-11-13T10:00:00Z", publicado_por: null, publicado_en: null, retirado_en: null, sin_verificar: 1,
};
const PARAMETRO = {
  clave: "plazo_derechos_dias", valor: "15", unidad: "calendario", termino_legal: "plazo", articulo: "LOPDP art. 13",
  fuente_url: "https://example.test/lopdp.pdf", verificado: false, verificado_por: null, verificado_por_nombre: null,
  verificado_en: null, actualizado_por: "op", actualizado_en: "2026-11-13T10:00:00Z",
};
const TEMAS = ["theme-light", "theme-dark"] as const;
const ANCHOS = [375, 1280] as const;

interface Opciones { organizaciones?: unknown[]; fallo?: number; sinJson?: boolean; crear?: { estado: number; cuerpo?: unknown } }

async function simular(page: Page, { organizaciones = [ORG, CADUCADA], fallo, sinJson, crear }: Opciones = {}) {
  const json = (r: import("@playwright/test").Route, estado: number, cuerpo: unknown) =>
    r.fulfill({ status: estado, contentType: "application/json", body: JSON.stringify(cuerpo) });
  await page.route("**/api/v1/**", (r) => json(r, 404, { detail: "No simulado" }));
  await page.route("**/api/v1/plataforma/organizaciones", (r) => {
    if (r.request().method() === "POST") {
      return crear ? json(r, crear.estado, crear.cuerpo ?? {}) : json(r, 200, {
        tenant_id: "t-9", invitacion_id: "inv-9", codigo_invitacion: "codigo-de-invitacion-1234567890",
        expira_en: "2026-12-01T00:00:00Z", email_invitado: "admin@nueva.ec" });
    }
    if (fallo) return sinJson ? r.fulfill({ status: fallo, contentType: "text/html", body: "<h1>Error</h1>" }) : json(r, fallo, { detail: "TEXTO CRUDO" });
    return json(r, 200, organizaciones);
  });
  await page.route("**/api/v1/plataforma/paquetes", (r) => json(r, 200, { paquetes: [PAQUETE] }));
  await page.route(`**/api/v1/plataforma/paquetes/${PAQUETE.id}`, (r) => json(r, 200, { paquete: PAQUETE, parametros: [PARAMETRO] }));
  await page.route("**/api/v1/biblioteca/editorial", (r) => json(r, 200, { actor_id: "x", capacidades: ["editor"], versiones: [], revisiones: [] }));
  await page.route("**/api/v1/biblioteca/capacidades/equipo", (r) => json(r, 200, [
    { usuario_id: "u-otro", nombre: "Operador Nuevo", email: "nuevo@plataforma.test", ha_entrado: false, capacidades: ["editor"] }]));
  await page.route("**/api/v1/biblioteca/capacidades/equipo/historial", (r) => json(r, 200, []));
}

async function abrir(page: Page, ruta: string, tema: string, ancho: number, opciones?: Opciones) {
  await page.setViewportSize({ width: ancho, height: 900 });
  await fijarAjustes(page, { modo: "headers", tenant: TENANT_PRUEBA });
  await simular(page, opciones);
  await page.goto(ruta);
  await page.evaluate((t) => { document.documentElement.classList.remove("theme-light", "theme-dark"); document.documentElement.classList.add(t); }, tema);
}

/** Razón de contraste del borde de cada control frente a su fondo efectivo (WCAG): debe ser >= 3. */
async function razonesDeBorde(page: Page, selector: string): Promise<number[]> {
  return page.evaluate((sel) => {
    const lienzo = document.createElement("canvas").getContext("2d", { willReadFrequently: true })!;
    const rgb = (c: string) => { lienzo.clearRect(0, 0, 1, 1); lienzo.fillStyle = c; lienzo.fillRect(0, 0, 1, 1); const d = lienzo.getImageData(0, 0, 1, 1).data; return [d[0], d[1], d[2], d[3] / 255]; };
    const lum = ([r, g, b]: number[]) => { const f = (v: number) => { const s = v / 255; return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4; }; return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b); };
    const fondo = (el: Element | null): number[] => {
      for (let n = el; n; n = n.parentElement) { const c = rgb(getComputedStyle(n).backgroundColor); if (c[3] > 0.5) return c; }
      return document.documentElement.classList.contains("theme-dark") ? [10, 10, 12, 1] : [255, 255, 255, 1];
    };
    return Array.from(document.querySelectorAll(sel)).map((el) => {
      const a = lum(rgb(getComputedStyle(el).borderTopColor)), b = lum(fondo(el.parentElement));
      return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    });
  }, selector);
}

for (const tema of TEMAS) {
  for (const ancho of ANCHOS) {
    test.describe(`${tema} a ${ancho} px`, () => {
      test("contraste en /plataforma con código de invitación y tabla con filas", async ({ page }) => {
        await abrir(page, "/plataforma", tema, ancho);
        await expect(page.getByTestId("organizacion-t-1")).toBeVisible();
        await page.getByLabel("Nombre comercial").fill("Nueva SA");
        await page.getByLabel("Razón social").fill("Nueva SA");
        await page.getByLabel("RUC o identificación").fill("0999999999001");
        await page.getByLabel("Sector").fill("Servicios");
        await page.getByLabel("Correo del administrador inicial").fill("admin@nueva.ec");
        await page.getByRole("button", { name: "Crear y emitir invitación" }).click();
        await expect(page.getByTestId("codigo-invitacion")).toBeVisible();
        expect(await medirContraste(page, "main")).toEqual([]);
        expect((await razonesDeBorde(page, "main input, main select")).filter((r) => r < 3)).toEqual([]);
        await page.getByLabel("Nombre comercial").focus();
        expect(await medirContraste(page, "main")).toEqual([]);
      });

      test("contraste en /plataforma con error y con la lista vacía", async ({ page }) => {
        await abrir(page, "/plataforma", tema, ancho, { organizaciones: [], crear: { estado: 500 } });
        await expect(page.getByText("Todavía no hay organizaciones.")).toBeVisible();
        expect(await medirContraste(page, "main")).toEqual([]);
        for (const [etiqueta, valor] of [["Nombre comercial", "A"], ["Razón social", "A"], ["RUC o identificación", "1"], ["Sector", "S"], ["Correo del administrador inicial", "a@b.ec"]])
          await page.getByLabel(etiqueta).fill(valor);
        await page.getByRole("button", { name: "Crear y emitir invitación" }).click();
        await expect(page.locator("main [role='alert']")).toBeVisible();
        expect(await medirContraste(page, "main")).toEqual([]);
      });

      test("contraste en /plataforma/paquetes y en el detalle", async ({ page }) => {
        await abrir(page, "/plataforma/paquetes", tema, ancho);
        await expect(page.getByRole("row", { name: /Ley Orgánica/ })).toBeVisible();
        expect(await medirContraste(page, "main")).toEqual([]);
        await page.getByRole("link", { name: /Ley Orgánica/ }).click();
        await expect(page.getByText("Pendiente de verificar").first()).toBeVisible();
        expect(await medirContraste(page, "main")).toEqual([]);
        expect((await razonesDeBorde(page, "main input, main select")).filter((r) => r < 3)).toEqual([]);
      });

      test("contraste en /plataforma/biblioteca y /plataforma/capacidades (R6)", async ({ page }) => {
        await abrir(page, "/plataforma/biblioteca", tema, ancho);
        await expect(page.getByRole("heading", { name: "Administración editorial", level: 1 })).toBeVisible();
        expect(await medirContraste(page, "main")).toEqual([]);
        await page.getByRole("link", { name: "Capacidades editoriales" }).click();
        await expect(page.getByRole("heading", { name: "Capacidades editoriales", level: 1 })).toBeVisible();
        expect(await medirContraste(page, "main")).toEqual([]);
      });
    });
  }
}

test("las tres pantallas no llevan clases de color de la paleta fija", () => {
  const base = join(__dirname, "..", "..", "src", "app", "plataforma");
  for (const f of ["page.tsx", join("paquetes", "page.tsx"), join("paquetes", "[id]", "page.tsx")]) {
    const fuente = readFileSync(join(base, f), "utf8");
    expect(fuente.match(/\b[a-z:-]*(zinc|amber|red|violet|emerald)-\d{2,3}[\w/.-]*|\bbg-black\/[\w.]+/g) ?? [], f).toEqual([]);
  }
});

test.describe("errores legibles (R4) y vacío solo si está vacío (R5)", () => {
  const rellenar = async (page: Page) => {
    for (const [etiqueta, valor] of [["Nombre comercial", "A"], ["Razón social", "A"], ["RUC o identificación", "1"], ["Sector", "S"], ["Correo del administrador inicial", "a@b.ec"]])
      await page.getByLabel(etiqueta).fill(valor);
    await page.getByRole("button", { name: "Crear y emitir invitación" }).click();
  };

  test("el error muestra su texto fijo, sin el estado HTTP ni el texto del servidor", async ({ page }) => {
    await abrir(page, "/plataforma", "theme-light", 1280, { crear: { estado: 403, cuerpo: { code: "OPERADOR_NO_AUTORIZADO", detail: "TEXTO CRUDO" } } });
    await rellenar(page);
    await expect(page.locator("main [role='alert']")).toHaveText("No tienes permiso para administrar organizaciones.");
    await expect(page.getByText(/403|TEXTO CRUDO/)).toHaveCount(0);
  });

  test("una respuesta sin JSON muestra el texto genérico, sin el estado HTTP", async ({ page }) => {
    await abrir(page, "/plataforma", "theme-light", 1280, { crear: { estado: 502 } });
    await rellenar(page);
    await expect(page.locator("main [role='alert']")).toHaveText("No se pudo completar la operación. Inténtalo de nuevo.");
    await expect(page.getByText(/502|TEXTO CRUDO/)).toHaveCount(0);
  });

  test("una carga fallida muestra el error y «Reintentar», no el vacío", async ({ page }) => {
    await abrir(page, "/plataforma", "theme-light", 1280, { fallo: 500, sinJson: true });
    await expect(page.locator("main [role='alert']")).toHaveText("No se pudo completar la operación. Inténtalo de nuevo.");
    await expect(page.getByRole("button", { name: "Reintentar" })).toBeVisible();
    await expect(page.getByText("Todavía no hay organizaciones.")).toHaveCount(0);
  });
});
