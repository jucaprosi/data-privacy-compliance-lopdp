/**
 * FE-28 · Textos de interfaz sin jerga técnica (governance/tareas/FE-28.md, árbitro 1).
 *
 * Recorre cada vista del menú a 1280 px y falla si un texto visible, un `title` o un `aria-label`
 * nombra la arquitectura interna. Las excepciones viven en `excepciones/<FICHA>.txt`, una por ficha
 * dueña, con líneas «vista → cadena»; `*` en la cadena vale por cualquier texto. La cadena debe
 * coincidir con el texto entero, no con un trozo: una aparición nueva de la misma palabra falla.
 */
import { readdirSync, readFileSync } from "node:fs";
import path from "node:path";

import { expect, test, type Page } from "@playwright/test";

import { MENUS, SUBMENUS } from "../../src/components/layout/menus";
import { abrirAppLimpia, abrirSubmenu, barraDeMenus, configurarProyecto } from "../utiles";

export const JERGA =
  /adpa\.view|Zustand|useAuditStore|FastAPI|endpoint|Store:|tenant-|Invariante|timebox|Poka-Yoke|\bSoD\b|INV_|Mutaci[oó]n/i;

const CARPETA = path.join(__dirname, "excepciones");

function leerExcepciones(): RegExp[] {
  return readdirSync(CARPETA)
    .filter((archivo) => archivo.endsWith(".txt"))
    .flatMap((archivo) => readFileSync(path.join(CARPETA, archivo), "utf-8").split(/\r?\n/))
    .filter((linea) => linea.trim() && !linea.startsWith("#"))
    .map((linea) => {
      const cadena = linea.split(" → ").slice(1).join(" → ").trim();
      const patron = cadena.replace(/[.+?^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*");
      return new RegExp(`^${patron}$`);
    });
}

const EXCEPCIONES = leerExcepciones();

/**
 * Guarda cada texto que aparece en la página, aunque dure poco (un «Cargando…» desaparece antes de que
 * el recorrido lo lea).
 */
function vigilarTextos() {
  const vistos = new Set<string>();
  (window as unknown as { __textosFe28: Set<string> }).__textosFe28 = vistos;
  const anotar = (nodo: Node) => {
    const texto = (nodo.textContent ?? "").replace(/\s+/g, " ").trim();
    if (texto) vistos.add(texto);
  };
  new MutationObserver((cambios) => {
    for (const cambio of cambios) {
      if (cambio.type === "characterData") anotar(cambio.target);
      for (const nodo of Array.from(cambio.addedNodes)) {
        if (nodo.nodeType === Node.TEXT_NODE) anotar(nodo);
        else if (nodo instanceof Element) {
          const recorrido = document.createTreeWalker(nodo, NodeFilter.SHOW_TEXT);
          for (let t = recorrido.nextNode(); t; t = recorrido.nextNode()) anotar(t);
        }
      }
    }
  }).observe(document, { childList: true, subtree: true, characterData: true });
}

/** Textos visibles (nodo a nodo), los que aparecieron desde la última lectura y `title`/`aria-label`. */
async function textosDeLaPagina(page: Page): Promise<string[]> {
  return page.evaluate(() => {
    const ventana = window as unknown as { __textosFe28?: Set<string> };
    const textos: string[] = [...(ventana.__textosFe28 ?? [])];
    ventana.__textosFe28?.clear();
    const recorrido = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let nodo = recorrido.nextNode(); nodo; nodo = recorrido.nextNode()) {
      const padre = nodo.parentElement;
      const texto = (nodo.textContent ?? "").replace(/\s+/g, " ").trim();
      if (!texto || !padre || ["SCRIPT", "STYLE", "NOSCRIPT"].includes(padre.tagName)) continue;
      if (padre.getClientRects().length === 0) continue; // no visible
      textos.push(texto);
    }
    for (const elemento of Array.from(document.querySelectorAll("[title], [aria-label]"))) {
      for (const atributo of ["title", "aria-label"]) {
        const valor = elemento.getAttribute(atributo);
        if (valor) textos.push(valor.replace(/\s+/g, " ").trim());
      }
    }
    return textos;
  });
}

function conJerga(textos: string[]): string[] {
  return [...new Set(textos)].filter((t) => JERGA.test(t) && !EXCEPCIONES.some((e) => e.test(t)));
}

test.describe("FE-28 · textos sin jerga", () => {
  test.use({ viewport: { width: 1280, height: 900 } });

  test("ninguna vista del menú muestra jerga técnica", async ({ page }) => {
    test.setTimeout(180_000);
    await page.addInitScript(vigilarTextos);
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await textosDeLaPagina(page); // lo visto al configurar no pertenece a ninguna vista del menú
    const hallazgos: string[] = [];
    const visitadas: string[] = [];
    for (const submenu of SUBMENUS) {
      // El menú oculta los submenús que el rol o la edición no ofrecen: solo se recorren los visibles.
      const menu = MENUS.find((m) => m.id === submenu.menu)!;
      await barraDeMenus(page).getByRole("button", { name: menu.nombre, exact: true }).click();
      const grupo = page.getByRole("group", { name: `Submenús de ${menu.nombre}` });
      const boton = grupo.getByRole("button", { name: new RegExp(`^${submenu.nombre.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")}`) });
      if ((await boton.count()) === 0) continue;
      await abrirSubmenu(page, submenu);
      visitadas.push(submenu.vista);
      await page.waitForLoadState("networkidle").catch(() => undefined);
      for (const texto of conJerga(await textosDeLaPagina(page))) hallazgos.push(`${submenu.vista} → ${texto}`);
      // El diagnóstico abre un <dialog> modal de perspectiva ejecutiva que bloquea el menú (ver utiles.ts).
      const cerrarAlerta = page.getByRole("button", { name: "Cerrar alerta" });
      if (await cerrarAlerta.isVisible()) await cerrarAlerta.click();
    }
    expect(visitadas.length, "el recorrido debe abrir vistas").toBeGreaterThan(10);
    expect(hallazgos, "textos con jerga técnica (corríjalos o anótelos en excepciones/<FICHA>.txt)").toEqual([]);
  });

  test("el filtro detecta cada término y respeta las excepciones", () => {
    for (const termino of ["adpa.view", "Zustand", "useAuditStore", "FastAPI", "endpoint", "Store:", "tenant-",
      "Invariante", "timebox", "Poka-Yoke", "SoD", "INV_", "Mutación"]) {
      expect(conJerga([`texto con ${termino} dentro`]), termino).toHaveLength(1);
    }
    // FE-27 borró su excepción: «adpa.view» ya se marca; «timebox» sigue exceptuado por DIAG-15.txt.
    expect(conJerga(["diagnostico.adpa.view", "timebox"])).toEqual(["diagnostico.adpa.view"]);
    expect(conJerga(["12:00 timebox"])).toEqual(["12:00 timebox"]);
  });
});
