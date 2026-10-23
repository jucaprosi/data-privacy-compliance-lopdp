/**
 * FE-12: colores de la tarjeta de tarea en los dos temas.
 *
 * Hallazgo de las pruebas en físico (2026-10-23): en el tema claro los botones de la tarjeta
 * quedaban con texto casi negro sobre fondo casi negro. Se mide el contraste real (WCAG 2.1,
 * criterio 1.4.3: 4.5:1 para texto normal) de cada botón, chip y texto, y que cada dimensión
 * tenga su color de acento.
 */
import { expect, test, type Page } from "@playwright/test";

const RUTA = "/harness-roadmap/olas?rol=coordinador";
const TEMAS = ["theme-light", "theme-dark"] as const;

async function abrir(page: Page, tema: (typeof TEMAS)[number]): Promise<void> {
  await page.goto(RUTA);
  await expect(page.getByRole("region", { name: "Hoja de ruta" })).toBeVisible();
  await page.evaluate((t) => {
    document.documentElement.classList.remove("theme-light", "theme-dark");
    document.documentElement.classList.add(t);
  }, tema);
}

/** Contraste de cada elemento de texto de las tarjetas contra el fondo efectivo que tiene detrás. */
async function contrastes(page: Page): Promise<{ texto: string; ratio: number }[]> {
  return page.evaluate(() => {
    const rgb = (c: string): number[] | null => {
      const m = c.match(/rgba?\(([^)]+)\)/);
      if (!m) return null;
      const p = m[1].split(/[ ,/]+/).filter(Boolean).map(Number);
      return [p[0], p[1], p[2], p.length > 3 ? p[3] : 1];
    };
    const fondo = (el: Element | null): number[] => {
      for (let n = el; n; n = n.parentElement) {
        const c = rgb(getComputedStyle(n).backgroundColor);
        if (c && c[3] > 0.5) return c;
      }
      return [255, 255, 255, 1];
    };
    const lum = ([r, g, b]: number[]) => {
      const f = (v: number) => {
        const s = v / 255;
        return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
      };
      return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b);
    };
    const selector = "[data-testid^='tarea-'] :is(button, span, dt, dd, h4, p)";
    return Array.from(document.querySelectorAll(selector))
      .filter((el) => (el as HTMLElement).innerText?.trim() && !(el as HTMLButtonElement).disabled)
      .map((el) => {
        const a = lum(rgb(getComputedStyle(el).color) ?? [0, 0, 0]);
        const b = lum(fondo(el));
        const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
        return { texto: (el as HTMLElement).innerText.trim().slice(0, 40), ratio: Math.round(ratio * 100) / 100 };
      });
  });
}

test.describe("Colores de la tarjeta de tarea (FE-12)", () => {
  for (const tema of TEMAS) {
    test(`todo el texto de las tarjetas se lee en ${tema}`, async ({ page }) => {
      await abrir(page, tema);
      await expect(page.getByRole("button", { name: "Asignar responsable" }).first()).toBeVisible();
      const medidos = await contrastes(page);
      expect(medidos.length).toBeGreaterThan(10);
      const ilegibles = medidos.filter((m) => m.ratio < 4.5);
      expect(ilegibles, JSON.stringify(ilegibles)).toEqual([]);
    });

    test(`cada dimensión tiene su color de acento en ${tema}`, async ({ page }) => {
      await abrir(page, tema);
      const acentos = await page
        .locator("[data-testid^='tarea-'][data-dimension]")
        .evaluateAll((els) => els.map((el) => [el.getAttribute("data-dimension"), getComputedStyle(el).borderLeftColor]));
      expect(acentos.length).toBeGreaterThanOrEqual(3);
      const porDimension = new Map(acentos.map(([d, c]) => [d, c]));
      expect(new Set(porDimension.values()).size).toBe(porDimension.size);
      await expect(page.getByTestId("dimension-task-001")).toHaveText("D01");
    });
  }
});
