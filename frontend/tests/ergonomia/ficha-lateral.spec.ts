/**
 * Pie de la barra lateral: las etiquetas de la ficha no se montan sobre su valor.
 *
 * Caso real (2026-10-27): con una columna de etiquetas de 3,5 rem, «ORGANIZACIÓN:» invadía el nombre
 * («ORGANIZACIÓNxyz»). Prueba de mutación: volver a `w-14` en `dashboard/page.tsx` la hace fallar.
 */
import { expect, test } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto } from "../utiles";

test("las etiquetas del pie lateral no invaden el nombre, el sector ni el tenant", async ({ page }) => {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "xyz");

  for (const etiqueta of ["Organización:", "Sector:", "Tenant ID:"]) {
    const rotulo = page.getByText(etiqueta, { exact: true });
    const valor = rotulo.locator("xpath=following-sibling::span[1]");
    const cajaRotulo = await rotulo.boundingBox();
    const cajaValor = await valor.boundingBox();
    expect(cajaRotulo && cajaValor, etiqueta).toBeTruthy();
    // El ancho del texto de la etiqueta cabe en su columna y el valor empieza después.
    const anchoTexto = await rotulo.evaluate((el) => el.scrollWidth);
    expect(anchoTexto, `${etiqueta} desborda su columna`).toBeLessThanOrEqual(Math.ceil(cajaRotulo!.width));
    expect(cajaValor!.x, `${etiqueta} se monta sobre su valor`).toBeGreaterThanOrEqual(cajaRotulo!.x + cajaRotulo!.width - 1);
  }
});
