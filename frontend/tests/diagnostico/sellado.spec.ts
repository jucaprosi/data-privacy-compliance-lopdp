/**
 * DIAG-03, con la regla de DIAG-07: responde el administrador (o la persona asignada), el DPO sella y
 * los demás roles lo ven en modo lectura; el historial muestra lo sellado en el servidor.
 *
 * Mutación documentada: volver a atar el botón de `SelloPorEtapa` a `puedeResponder` hace fallar las dos
 * primeras pruebas (el DPO no lo ve y el administrador sí).
 */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala, responderControlActual } from "../utiles";
import { abrirCierreDelDiagnostico, filaDePrueba, simularApiDiagnostico } from "./simulador";

test.describe("Diagnóstico del DPO y resultado sellado (DIAG-03)", () => {
  test("el administrador responde y no ve el botón de sellar", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["admin_organizacion"] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);
    await expect(page.getByTestId("aviso-modo-diagnostico")).toHaveCount(0);
    await responderControlActual(page, 3);
    await expect.poll(() => servidor.filas.length).toBe(1);

    const cierre = await abrirCierreDelDiagnostico(context, page);
    await expect(cierre.getByTestId("etapa-diagnostico")).toBeVisible();
    await expect(cierre.getByRole("button", { name: /Sellar diagnóstico/ })).toHaveCount(0);
    expect(servidor.cuerposSellado).toEqual([]);
  });

  test("el DPO no puede editar respuestas, sella y ve el resultado en el historial; solo envía el perfil", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["dpo"], filas: [filaDePrueba(1)] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);
    await expect(page.getByTestId("aviso-modo-diagnostico")).toContainText("Revisas y sellas el diagnóstico");
    await expect(page.locator("[data-nivel]").first()).toHaveAttribute("aria-disabled", "true");

    const cierre = await abrirCierreDelDiagnostico(context, page);
    await cierre.getByRole("button", { name: "Sellar diagnóstico de prueba" }).click();

    await expect(cierre.getByText(/Resultado sellado n\.º 1: no se puede editar ni borrar/)).toBeVisible();
    expect(servidor.cuerposSellado).toHaveLength(1);
    const cuerpo = servidor.cuerposSellado[0] as Record<string, unknown>;
    expect(Object.keys(cuerpo)).toEqual(["perfil"]);
    // La ficha de prueba responde «No» a todo el perfil de operación.
    expect(Object.values(cuerpo.perfil as Record<string, string>).every((v) => v === "no")).toBe(true);
    await expect(cierre.getByRole("button", { name: "Sellar diagnóstico de prueba" })).toHaveCount(0);

    await cierre.getByRole("button", { name: /Ver en el historial/ }).click();
    const lista = cierre.getByRole("list", { name: "Resultados sellados" });
    await expect(lista.getByRole("button", { name: "Resultado sellado n.º 1" })).toBeVisible();
    await expect(cierre.getByText(/Cadena de huellas verificada: 1 resultado/)).toBeVisible();
  });

  test("el implementador ve el diagnóstico en modo lectura y no puede sellar", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["implementador"], filas: [filaDePrueba(1)] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);

    await expect(page.getByTestId("aviso-modo-diagnostico")).toContainText("Modo lectura");
    const niveles = page.getByRole("radiogroup", { name: /Nivel de madurez/ }).getByRole("radio");
    await expect(niveles).toHaveCount(5);
    for (const nivel of await niveles.all()) await expect(nivel).toBeDisabled();
    await expect(page.getByRole("button", { name: "Pendiente de Validación" })).toBeDisabled();
    // La navegación sigue disponible para revisar.
    await expect(page.getByRole("button", { name: "Siguiente", exact: true })).toBeEnabled();

    const cierre = await abrirCierreDelDiagnostico(context, page);
    await expect(cierre.getByRole("button", { name: "Sellar diagnóstico de prueba" })).toHaveCount(0);
    expect(servidor.envios).toEqual([]);
    expect(servidor.cuerposSellado).toEqual([]);
  });

  test("sin un DPO con rol vigente, la pantalla lo explica y no habilita a otro rol", async ({ page, context }) => {
    await simularApiDiagnostico(context, { roles: ["coordinador"], dpoVigente: false });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);

    await expect(page.getByText(/no tiene un DPO con rol vigente/)).toBeVisible();
    await expect(
      page.getByRole("radiogroup", { name: /Nivel de madurez/ }).getByRole("radio", { name: /^4\b/ })
    ).toBeDisabled();
  });
});
