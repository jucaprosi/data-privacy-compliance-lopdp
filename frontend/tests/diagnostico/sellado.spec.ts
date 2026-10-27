/**
 * DIAG-03: solo el DPO responde y sella el diagnóstico; los demás roles lo ven en modo lectura y
 * el historial muestra lo sellado en el servidor.
 */
import { expect, test } from "@playwright/test";

import { etiquetaEstadoCumplimiento } from "../../src/lib/estadosCumplimiento";
import { abrirAppLimpia, configurarProyecto, irASala, responderControlActual } from "../utiles";
import { abrirCierreDelDiagnostico, filaDePrueba, simularApiDiagnostico } from "./simulador";

test.describe("Diagnóstico del DPO y resultado sellado (DIAG-03)", () => {
  test("el DPO responde, sella y ve el resultado en el historial; solo envía el perfil", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["dpo"] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);
    await expect(page.getByText(/Modo lectura/)).toHaveCount(0);
    await responderControlActual(page, "Parcial");
    await expect.poll(() => servidor.filas.length).toBe(1);

    const cierre = await abrirCierreDelDiagnostico(context, page);
    await cierre.getByRole("button", { name: "Guardar resultado definitivo" }).click();

    await expect(cierre.getByText(/Resultado sellado n\.º 1: no se puede editar ni borrar/)).toBeVisible();
    expect(servidor.cuerposSellado).toHaveLength(1);
    const cuerpo = servidor.cuerposSellado[0] as Record<string, unknown>;
    expect(Object.keys(cuerpo)).toEqual(["perfil"]);
    // La ficha de prueba responde «No» a todo el perfil de operación.
    expect(Object.values(cuerpo.perfil as Record<string, string>).every((v) => v === "no")).toBe(true);
    await expect(cierre.getByRole("button", { name: "Guardar resultado definitivo" })).toHaveCount(0);

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

    await expect(page.getByText("Modo lectura: el diagnóstico lo responde y lo sella el DPO")).toBeVisible();
    for (const estado of ["Conforme", "Parcial", "No Conforme"] as const) {
      await expect(page.getByRole("button", { name: etiquetaEstadoCumplimiento(estado), exact: true })).toBeDisabled();
    }
    await expect(page.getByRole("button", { name: "Pendiente de Validación" })).toBeDisabled();
    // La navegación sigue disponible para revisar.
    await expect(page.getByRole("button", { name: "Siguiente", exact: true })).toBeEnabled();

    const cierre = await abrirCierreDelDiagnostico(context, page);
    await expect(cierre.getByRole("button", { name: "Guardar resultado definitivo" })).toHaveCount(0);
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
      page.getByRole("button", { name: etiquetaEstadoCumplimiento("Conforme"), exact: true })
    ).toBeDisabled();
  });
});
