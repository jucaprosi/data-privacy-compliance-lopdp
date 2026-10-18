/**
 * Arnés de verificación de citas normativas coherentes con la LOPDP (LEG-01).
 *
 * Valida:
 * 1. Las citas corregidas en la interfaz:
 *    - DpoCockpitModule: la supervisión independiente cita los Arts. 49 y 50 LOPDP (funciones y garantías de independencia), no el Art. 48.
 *    - MtgeRelacionalModule: la separación de funciones (SoD) del DPO cita el Art. 50 LOPDP (conflicto de intereses), no el Art. 48.
 * 2. Las citas del Art. 48 que versan legítimamente sobre la obligatoriedad de designación del delegado de protección de datos:
 *    - MtgeModule: "DPO Obligatorio (Art. 48):" permanece intacta.
 *    - RagCopilotPanel: citas normativas y referencias al Art. 48 sobre designación obligatoria.
 *    - Banco de preguntas (bloque1, perfil): citas de obligatoriedad del Art. 48 intactas.
 */
import { expect, test } from "@playwright/test";
import * as fs from "fs";
import * as path from "path";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

test.describe("LEG-01: Citas normativas coherentes con la LOPDP en la interfaz", () => {
  test.beforeEach(async ({ page }) => {
    await abrirAppLimpia(page);
    await configurarProyecto(page);
  });

  test("DpoCockpitModule muestra la cita correcta de los Arts. 49 y 50 LOPDP en la interfaz", async ({ page }) => {
    // Navegar al módulo del DPO
    await irASala(page, /Cockpit DPD \/ DPO/i);

    // Verificar que el encabezado del módulo contiene la cita corregida
    const descripcionDpo = page.getByText(/Supervisión independiente y registro histórico/i);
    await expect(descripcionDpo).toBeVisible();
    await expect(descripcionDpo).toContainText("(Arts. 49 y 50 LOPDP)");
    await expect(descripcionDpo).not.toContainText("(Art. 48 LOPDP)");
  });

  test("MtgeModule mantiene la cita de DPO Obligatorio bajo el Art. 48 en la interfaz", async ({ page }) => {
    // Navegar al módulo de Riesgos & MTGE
    await irASala(page, /Riesgos & MTGE/i);

    // Verificar que la etiqueta de designación obligatoria sigue citando el Art. 48
    const etiquetaDpoObligatorio = page.getByText(/DPO Obligatorio \(Art\. 48\):/i);
    await expect(etiquetaDpoObligatorio).toBeVisible();
  });
});

test.describe("LEG-01: Verificación estática e invariante de citas normativas", () => {
  const rootFrontend = path.resolve(__dirname, "../../src");

  test("fija las dos citas corregidas en los componentes de origen", () => {
    const dpoCockpitPath = path.join(rootFrontend, "components/modules/DpoCockpitModule.tsx");
    const dpoCockpitContent = fs.readFileSync(dpoCockpitPath, "utf-8");
    expect(dpoCockpitContent).toContain("Supervisión independiente y registro histórico de asesorías con acuse de recibo directivo (Arts. 49 y 50 LOPDP).");
    expect(dpoCockpitContent).not.toContain("Supervisión independiente y registro histórico de asesorías con acuse de recibo directivo (Art. 48 LOPDP).");

    const mtgeRelacionalPath = path.join(rootFrontend, "components/modules/MtgeRelacionalModule.tsx");
    const mtgeRelacionalContent = fs.readFileSync(mtgeRelacionalPath, "utf-8");
    expect(mtgeRelacionalContent).toContain("RAT Maestro. No puede revertirse sin aprobación del DPO (Art. 50 LOPDP — SoD).");
    expect(mtgeRelacionalContent).not.toContain("RAT Maestro. No puede revertirse sin aprobación del DPO (Art. 48 LOPDP — SoD).");
  });

  test("comprueba que las citas de obligatoriedad del Art. 48 permanecen intactas en los módulos designados", () => {
    // MtgeModule.tsx
    const mtgePath = path.join(rootFrontend, "components/modules/MtgeModule.tsx");
    const mtgeContent = fs.readFileSync(mtgePath, "utf-8");
    expect(mtgeContent).toContain("DPO Obligatorio (Art. 48):");

    // RagCopilotPanel.tsx
    const ragPath = path.join(rootFrontend, "components/modules/RagCopilotPanel.tsx");
    const ragContent = fs.readFileSync(ragPath, "utf-8");
    expect(ragContent).toContain("Artículo 48 de la LOPDP");
    expect(ragContent).toContain("Ley Orgánica de Protección de Datos Personales (Artículo 48, emisor: Asamblea Nacional)");

    // Banco de preguntas (bloque1.ts y perfil.ts)
    const bloque1Path = path.join(rootFrontend, "lib/bancoPreguntas/bloque1.ts");
    const bloque1Content = fs.readFileSync(bloque1Path, "utf-8");
    expect(bloque1Content).toContain("LOPDP Art. 48 y Resolución SPDP-SPD-2026-0005-R");

    const perfilPath = path.join(rootFrontend, "lib/bancoPreguntas/perfil.ts");
    const perfilContent = fs.readFileSync(perfilPath, "utf-8");
    expect(perfilContent).toContain("El Art. 48 obliga a designar Delegado");
    expect(perfilContent).toContain("LOPDP Art. 48");
  });
});
