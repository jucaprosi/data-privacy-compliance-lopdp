/**
 * FE-13: el panel de administración se lee en los dos temas.
 *
 * Hallazgo de las pruebas en físico (2026-10-23): en el tema claro las pestañas y botones del
 * panel quedaban con fondo casi negro y texto oscurecido por el tema. Se mide el contraste real
 * (WCAG 2.1, criterio 1.4.3: 4.5:1) de cada texto del panel en cada sección del arnés.
 */
import { expect, test, type Page } from "@playwright/test";

const RUTA = "/harness-roadmap/admin";
const TEMAS = ["theme-light", "theme-dark"] as const;
const SECCIONES = ["usuarios", "areas", "roles", "configuracion"] as const;

async function abrir(page: Page, seccion: string, tema: (typeof TEMAS)[number]): Promise<void> {
  await page.goto(`${RUTA}?rol=admin_organizacion&seccion=${seccion}`);
  await expect(page.getByRole("region", { name: "Administración de la organización" })).toBeVisible();
  await page.evaluate((t) => {
    document.documentElement.classList.remove("theme-light", "theme-dark");
    document.documentElement.classList.add(t);
  }, tema);
}

/** Contraste de cada texto visible del panel contra el fondo efectivo que tiene detrás. */
async function ilegibles(page: Page): Promise<{ texto: string; ratio: number }[]> {
  return page.evaluate(() => {
    // El navegador puede devolver rgb(), lab() u oklch(): se pinta el color en un lienzo de 1 px y
    // se lee en sRGB, así cualquier formato se compara igual.
    const lienzo = document.createElement("canvas").getContext("2d", { willReadFrequently: true })!;
    const rgb = (c: string): number[] | null => {
      if (!c || c === "transparent") return null;
      lienzo.clearRect(0, 0, 1, 1);
      lienzo.fillStyle = c;
      lienzo.fillRect(0, 0, 1, 1);
      const [r, g, b, a] = lienzo.getImageData(0, 0, 1, 1).data;
      return [r, g, b, a / 255];
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
    const panel = document.querySelector("[aria-label='Administración de la organización']");
    if (!panel) return [{ texto: "sin panel", ratio: 0 }];
    return Array.from(panel.querySelectorAll("[role=tab], button, span, td, th, p, label, h2, h3, h4, dt, dd, li"))
      .filter((el) => {
        const h = el as HTMLElement;
        return h.innerText?.trim() && h.offsetParent !== null && !(el as HTMLButtonElement).disabled;
      })
      .map((el) => {
        const a = lum(rgb(getComputedStyle(el).color) ?? [0, 0, 0]);
        const b = lum(fondo(el));
        const ratio = (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
        return { texto: (el as HTMLElement).innerText.trim().slice(0, 40), ratio: Math.round(ratio * 100) / 100 };
      })
      .filter((m) => m.ratio < 4.5);
  });
}

test.describe("Colores del panel de administración (FE-13)", () => {
  for (const tema of TEMAS) {
    for (const seccion of SECCIONES) {
      test(`la sección ${seccion} se lee en ${tema}`, async ({ page }) => {
        await abrir(page, seccion, tema);
        await expect(page.getByRole("tab", { name: "Usuarios", exact: true })).toBeVisible();
        const malos = await ilegibles(page);
        expect(malos, JSON.stringify(malos)).toEqual([]);
      });
    }
  }
});
