/**
 * DIAG-11: diagnóstico de prueba y diagnóstico real. ¤diagnostico
 *
 * Con la API simulada en memoria: el botón dice «Sellar diagnóstico de prueba» y luego «Sellar
 * diagnóstico real», que pide confirmación; tras el real desaparece y la pantalla muestra la etapa. Un rol que no es DPO
 * ve la etapa pero no el botón. Solo valores generados.
 *
 * Mutación documentada: si `etapaDesdeSellos` devuelve `siguiente: "real"` tras el real (sin límite),
 * la primera prueba falla porque el botón sigue visible.
 */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";
import { abrirCierreDelDiagnostico, filaDePrueba, simularApiDiagnostico } from "./simulador";

test.describe("Diagnóstico de prueba y diagnóstico real (DIAG-11)", () => {
  test("el DPO sella el de prueba, después el real, y el botón desaparece", async ({ page, context }) => {
    // DIAG-07: lo respondió el administrador (filas ya guardadas); el DPO no responde, sella.
    const servidor = await simularApiDiagnostico(context, { roles: ["dpo"], filas: [filaDePrueba(1)] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);

    const cierre = await abrirCierreDelDiagnostico(context, page);
    const etapa = cierre.getByTestId("etapa-diagnostico");
    await expect(etapa).toHaveText("Etapa: todavía no hay un diagnóstico sellado.");
    await expect(cierre.getByRole("button", { name: "Sellar diagnóstico real" })).toHaveCount(0);

    await cierre.getByRole("button", { name: "Sellar diagnóstico de prueba" }).click();
    await expect(etapa).toContainText("diagnóstico de prueba sellado");
    await expect(cierre.getByRole("button", { name: "Sellar diagnóstico de prueba" })).toHaveCount(0);

    await expect(etapa).toContainText("Puedes revisar y corregir respuestas");
    // El real no se deshace: pide confirmación y «Cancelar» no sella.
    await cierre.getByRole("button", { name: "Sellar diagnóstico real" }).click();
    const dialogo = cierre.getByRole("dialog", { name: "¿Sellar el diagnóstico real?" });
    await expect(dialogo).toContainText("Quedará como línea base y nadie podrá cambiar sus respuestas.");
    await expect(dialogo.getByRole("button", { name: "Cancelar" })).toBeFocused();
    await dialogo.getByRole("button", { name: "Cancelar" }).click();
    await expect(dialogo).toHaveCount(0);
    expect(servidor.cuerposSellado).toHaveLength(1);

    await cierre.getByRole("button", { name: "Sellar diagnóstico real" }).click();
    await dialogo.getByRole("button", { name: "Sellar diagnóstico real" }).click();
    await expect(etapa).toContainText("diagnóstico real sellado. Es la línea base con la que se medirá el avance");
    await expect(cierre.getByRole("button", { name: /Sellar diagnóstico/ })).toHaveCount(0);
    expect(servidor.cuerposSellado).toHaveLength(2);
    await cierre.screenshot({ path: "test-results/diag11-real-sellado.png", fullPage: true });
  });

  test("un rol que no es DPO ve la etapa y no puede sellar", async ({ page, context }) => {
    const servidor = await simularApiDiagnostico(context, { roles: ["implementador"], filas: [filaDePrueba(1)] });
    await abrirAppLimpia(page);
    await configurarProyecto(page);
    await irASala(page, /Normativa/);

    const cierre = await abrirCierreDelDiagnostico(context, page);
    await expect(cierre.getByTestId("etapa-diagnostico")).toHaveText("Etapa: todavía no hay un diagnóstico sellado.");
    await expect(cierre.getByRole("button", { name: /Sellar diagnóstico/ })).toHaveCount(0);
    expect(servidor.cuerposSellado).toEqual([]);
  });
});
