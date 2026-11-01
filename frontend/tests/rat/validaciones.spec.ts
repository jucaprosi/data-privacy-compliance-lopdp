/**
 * RAT-05 (governance/especificaciones/RAT-05.md §4 y §5).
 *
 * Con la API simulada: una regla incumplida se ve en rojo con su mensaje y el enlace al hallazgo; la condición
 * habilitante la declara el coordinador; la pestaña «Versiones» lista y abre cada versión.
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const FICHA = {
  id: "rat-1",
  codigo: "RAT-001",
  nombre: "Historia clínica",
  area_responsable: "Salud",
  finalidad: "Atención",
  base_legal: "CONSENTIMIENTO",
  categorias_titulares: ["PACIENTES"],
  datos_sensibles: true,
  volumen_titulares_estimado: 100,
  transferencia_internacional: false,
  requiere_eipd: false,
  es_gran_escala: false,
};

// Color calculado, no la clase: una variable sin definir dejaría el texto sin color y la clase seguiría ahí.
const ROJO = "rgb(255, 23, 68)";
const VERDE = "rgb(0, 200, 83)";
const MENSAJE = "Los datos sensibles exigen una condición habilitante del artículo 26 de la LOPDP.";

function reglas(cumpleSens: boolean) {
  return {
    reglas: [
      { codigo: "RAT-SENS", cumple: cumpleSens, mensaje: MENSAJE },
      { codigo: "RAT-EIPD", cumple: true, mensaje: "Menores, perfilamiento o biometría exigen marcar la evaluación de impacto." },
      { codigo: "RAT-BASE", cumple: true, mensaje: "Indique la base de legitimación del tratamiento." },
      { codigo: "RAT-PLAZO", cumple: true, mensaje: "Indique el plazo de conservación de los datos." },
    ],
    hallazgo_id: cumpleSens ? null : "hallazgo-1",
  };
}

async function abrirPanel(page: Page, rol: string) {
  const envios: unknown[] = [];
  let corregida = false;
  await page.route("**/api/v1/organizacion/me/roles", (route) =>
    route.fulfill({ json: { user_id: "u-1", tenant_id: "t-1", roles: [{ role: rol }] } }),
  );
  await page.route("**/api/v1/rat/plantillas", (route) => route.fulfill({ json: { plantillas: [] } }));
  await page.route("**/api/v1/rat/actividades", (route) =>
    route.fulfill({ json: { total: 1, actividades: [FICHA] } }),
  );
  await page.route("**/api/v1/rat/actividades/rat-1", async (route) => {
    envios.push(route.request().postDataJSON());
    corregida = true;
    await route.fulfill({ json: { status: "SUCCESS", actividad: FICHA } });
  });
  await page.route("**/api/v1/rat/rat-1/validaciones", (route) => route.fulfill({ json: reglas(corregida) }));
  await page.route("**/api/v1/rat/rat-1/versiones", (route) =>
    route.fulfill({
      json: { versiones: [{ numero: 1, creado_por: "u-1", creado_en: "2026-10-31T12:00:00Z" }] },
    }),
  );
  await page.route("**/api/v1/rat/rat-1/versiones/1", (route) =>
    route.fulfill({ json: { ...FICHA, condicion_habilitante: null } }),
  );
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Consultorio de prueba");
  await irASala(page, /RAT Maestro/);
  await page.getByRole("button", { name: "Ver validaciones de Historia clínica" }).click();
  return { panel: page.getByRole("complementary", { name: "Validaciones" }), envios };
}

test.describe("Validaciones y versiones de la ficha (RAT-05)", () => {
  test("la regla incumplida se ve en rojo con su mensaje y el enlace al hallazgo", async ({ page }) => {
    const { panel } = await abrirPanel(page, "dpo");
    const regla = panel.getByRole("listitem").filter({ hasText: MENSAJE });
    await expect(regla).toHaveAttribute("data-cumple", "false");
    await expect(regla).toHaveCSS("color", ROJO);
    await expect(panel.getByRole("listitem").filter({ hasText: "Plazo de conservación" })).toHaveCSS("color", VERDE);
    await expect(panel.getByRole("button", { name: "Ver hallazgo" })).toHaveAttribute("title", "Hallazgo hallazgo-1");
    // Quien no es coordinador no corrige la ficha.
    await expect(panel.getByLabel(/Condición habilitante/)).toHaveCount(0);
  });

  test("el coordinador declara la condición del artículo 26 y la regla pasa a verde", async ({ page }) => {
    const { panel, envios } = await abrirPanel(page, "coordinador");
    await panel.getByLabel(/Condición habilitante/).selectOption("CONSENTIMIENTO_EXPLICITO");
    await panel.getByRole("button", { name: "Guardar condición" }).click();
    await expect.poll(() => envios).toEqual([{ condicion_habilitante: "CONSENTIMIENTO_EXPLICITO" }]);
    await expect(panel.getByRole("listitem").filter({ hasText: "Datos sensibles" })).toHaveAttribute("data-cumple", "true");
    await expect(panel.getByRole("button", { name: "Ver hallazgo" })).toHaveCount(0);
  });

  test("la pestaña Versiones lista y abre una versión", async ({ page }) => {
    const { panel } = await abrirPanel(page, "dpo");
    await panel.getByRole("tab", { name: "Versiones" }).click();
    await panel.getByRole("button", { name: "Versión 1" }).click();
    await expect(panel.getByRole("region", { name: "Contenido de la versión 1" })).toContainText("Historia clínica");
  });
});
