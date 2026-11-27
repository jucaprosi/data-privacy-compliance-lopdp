// © 2026 Juan Carlos Proaño. Todos los derechos reservados. Uso, copia o distribución prohibidos sin autorización escrita.
// ¤adpa ¤arbitro
// FE-40: los siete tokens de éxito, información y enlace existen en cada tema con sus valores y cumplen contraste.
import { expect, test } from "@playwright/test";

const TOKENS = [
  "--ui-exito-fondo", "--ui-exito-borde", "--ui-exito-texto",
  "--ui-info-fondo", "--ui-info-borde", "--ui-info-texto",
  "--ui-enlace", "--ui-superficie",
];

const ESPERADO: Record<string, Record<string, string>> = {
  claro: {
    "--ui-exito-fondo": "#ecfdf5", "--ui-exito-borde": "#047857", "--ui-exito-texto": "#065f46",
    "--ui-info-fondo": "#eff6ff", "--ui-info-borde": "#1d4ed8", "--ui-info-texto": "#1e40af",
    "--ui-enlace": "#2563eb", "--ui-superficie": "#ffffff",
  },
  oscuro: {
    "--ui-exito-fondo": "#052e1c", "--ui-exito-borde": "#34d399", "--ui-exito-texto": "#a7f3d0",
    "--ui-info-fondo": "#0b1b3a", "--ui-info-borde": "#60a5fa", "--ui-info-texto": "#bfdbfe",
    "--ui-enlace": "#60a5fa", "--ui-superficie": "#141417",
  },
};

// El navegador puede devolver #fff en vez de #ffffff: se expande antes de medir.
function normalizar(hex: string): string {
  return /^#[0-9a-f]{3}$/.test(hex) ? "#" + [...hex.slice(1)].map((c) => c + c).join("") : hex;
}

function luminancia(hex: string): number {
  const n = parseInt(normalizar(hex).slice(1), 16);
  const c = [(n >> 16) & 255, (n >> 8) & 255, n & 255].map((v) => {
    const s = v / 255;
    return s <= 0.03928 ? s / 12.92 : ((s + 0.055) / 1.055) ** 2.4;
  });
  return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}

function razon(a: string, b: string): number {
  const [x, y] = [luminancia(a), luminancia(b)].sort((p, q) => q - p);
  return (x + 0.05) / (y + 0.05);
}

for (const tema of ["claro", "oscuro"] as const) {
  test.describe(`tema ${tema}`, () => {
    test("los siete tokens tienen su valor de la especificación", async ({ page }) => {
      await page.goto("/");
      await page.evaluate((clase) => {
        document.documentElement.classList.remove("theme-light", "theme-dark");
        document.documentElement.classList.add(clase);
      }, tema === "claro" ? "theme-light" : "theme-dark");
      const valores: Record<string, string> = await page.evaluate((nombres) => {
        const cs = getComputedStyle(document.documentElement);
        return Object.fromEntries(nombres.map((n) => [n, cs.getPropertyValue(n).trim().toLowerCase()]));
      }, TOKENS);
      for (const [nombre, valor] of Object.entries(ESPERADO[tema])) {
        expect(normalizar(valores[nombre]), nombre).toBe(valor);
      }
    });

    test("contraste: éxito e información ≥ 4,5:1; enlace sobre superficie 5,17:1 (claro) o 7,23:1 (oscuro)", async ({ page }) => {
      await page.goto("/");
      await page.evaluate((clase) => {
        document.documentElement.classList.remove("theme-light", "theme-dark");
        document.documentElement.classList.add(clase);
      }, tema === "claro" ? "theme-light" : "theme-dark");
      const v: Record<string, string> = await page.evaluate((nombres) => {
        const cs = getComputedStyle(document.documentElement);
        return Object.fromEntries(nombres.map((n) => [n, cs.getPropertyValue(n).trim().toLowerCase()]));
      }, TOKENS);
      expect(razon(v["--ui-exito-texto"], v["--ui-exito-fondo"])).toBeGreaterThanOrEqual(4.5);
      expect(razon(v["--ui-info-texto"], v["--ui-info-fondo"])).toBeGreaterThanOrEqual(4.5);
      const esperadoEnlace = tema === "claro" ? 5.17 : 7.23;
      expect(razon(v["--ui-enlace"], v["--ui-superficie"])).toBeCloseTo(esperadoEnlace, 2);
    });
  });
}
