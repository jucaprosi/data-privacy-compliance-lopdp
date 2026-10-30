/**
 * FE-22 · Navegación por los nueve menús (governance/especificaciones/FE-22.md, R1, R2 y R4).
 *
 * La tabla R2 se copia aquí a propósito, en lugar de leer `menus/base.ts`: si alguien quita o
 * mueve una vista del mapa, la prueba «cada vista desde su menú» falla (prueba de mutación).
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, barraDeMenus, configurarProyecto } from "../utiles";

/** R1, en orden. */
const MENUS_R1 = [
  "Inicio",
  "Diagnóstico",
  "Inventario",
  "Biblioteca",
  "Operación",
  "Riesgos y auditoría",
  "DPO",
  "Conocimiento",
  "Configuración",
] as const;

/** R2: vista, menú y nombre del submenú. */
const TABLA_R2: ReadonlyArray<readonly [vista: string, menu: (typeof MENUS_R1)[number], submenu: string]> = [
  ["dashboard", "Inicio", "Tablero de la organización"],
  ["diagnostico", "Diagnóstico", "Assessment"],
  ["reportes", "Diagnóstico", "Reporte"],
  ["roadmap", "Diagnóstico", "Hoja de ruta"],
  ["rat", "Inventario", "Tratamientos (RAT)"],
  ["terceros", "Inventario", "Encargados y terceros"],
  ["evidencias", "Biblioteca", "Evidencias"],
  ["arco", "Operación", "Solicitudes de titulares"],
  ["incidentes", "Operación", "Vulneraciones"],
  ["riesgos", "Riesgos y auditoría", "Matriz de riesgos"],
  ["mtge_relacional", "Riesgos y auditoría", "Evaluaciones de impacto"],
  ["auditoria", "Riesgos y auditoría", "Auditorías"],
  ["dpo", "DPO", "Panel del DPO"],
  ["mitigacion_ia", "Conocimiento", "Copiloto"],
  ["configuracion", "Configuración", "Perfil de la organización"],
];

const escapar = (texto: string) => texto.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");

/** Pestaña del lienzo central: nombra la vista montada. */
function pestanaDeVista(page: Page, vista: string) {
  return page.getByText(vista === "configuracion" ? "PerfilOrganizacional.view" : `${vista}.adpa.view`, {
    exact: true,
  });
}

async function abrirDesdeMenu(page: Page, menu: string, submenu: string): Promise<void> {
  await barraDeMenus(page).getByRole("button", { name: menu, exact: true }).click();
  await page
    .getByRole("group", { name: `Submenús de ${menu}` })
    .getByRole("button", { name: new RegExp(`^${escapar(submenu)}`) })
    .click();
}

async function menusVisibles(page: Page): Promise<string[]> {
  return (await barraDeMenus(page).getByRole("button").allInnerTexts()).map((t) => t.trim());
}

test.describe("Navegación por los nueve menús (FE-22)", () => {
  test.beforeEach(async ({ page }) => {
    // Las vistas consultan la API al montarse; aquí solo importa qué vista se monta.
    await page.route("**/api/v1/**", (route) => route.fulfill({ status: 503, json: { detail: "API simulada" } }));
  });

  test("nueve menús en orden", async ({ page }) => {
    await abrirAppLimpia(page);
    // Durante el alta solo se puede abrir el perfil: el único menú es Configuración.
    expect(await menusVisibles(page)).toEqual(["Configuración"]);

    await configurarProyecto(page, "Entidad FE-22");
    // Tras el alta el perfil queda cerrado (como antes de FE-22), así que Configuración no tiene
    // submenú visible (R4). El resto aparece en el orden R1.
    const visibles = await menusVisibles(page);
    expect(visibles).toEqual(MENUS_R1.filter((m) => m !== "Configuración"));
    expect(visibles).toEqual(MENUS_R1.filter((m) => visibles.includes(m)));

    // El menú de la vista montada lleva aria-current="page".
    await expect(barraDeMenus(page).locator('[aria-current="page"]')).toHaveText("Diagnóstico");
  });

  test("cada vista desde su menú", async ({ page }) => {
    await abrirAppLimpia(page);

    // El perfil solo se abre durante el alta.
    const [vistaPerfil, menuPerfil, submenuPerfil] = TABLA_R2.find(([v]) => v === "configuracion")!;
    await abrirDesdeMenu(page, menuPerfil, submenuPerfil);
    await expect(pestanaDeVista(page, vistaPerfil)).toBeVisible();

    await configurarProyecto(page, "Entidad FE-22");
    for (const [vista, menu, submenu] of TABLA_R2.filter(([v]) => v !== "configuracion")) {
      await abrirDesdeMenu(page, menu, submenu);
      await expect(pestanaDeVista(page, vista), `${menu} › ${submenu}`).toBeVisible();
      await expect(barraDeMenus(page).locator('[aria-current="page"]')).toHaveText(menu);
      // Al volver al assessment, la primera pregunta de D01 abre de nuevo su aviso modal
      // (AlertaDimension.tsx), que bloquea la página hasta cerrarlo.
      if (vista === "diagnostico") await page.getByRole("button", { name: "Cerrar alerta" }).click();
    }
  });

  test("el dock muestra solo los submenús del menú abierto, en su orden", async ({ page }) => {
    await abrirAppLimpia(page);
    await configurarProyecto(page, "Entidad FE-22");
    await barraDeMenus(page).getByRole("button", { name: "Riesgos y auditoría", exact: true }).click();
    const dock = page.getByRole("group", { name: "Submenús de Riesgos y auditoría" });
    const nombres = (await dock.getByRole("button").allInnerTexts()).map((t) => t.split("\n")[0].trim());
    expect(nombres).toEqual(["Matriz de riesgos", "Evaluaciones de impacto", "Auditorías", "Controles periódicos"]);
    await expect(page.getByRole("group", { name: /^Submenús de / })).toHaveCount(1);
  });
});
