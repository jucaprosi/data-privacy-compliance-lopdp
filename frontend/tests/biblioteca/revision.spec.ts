import { test, expect } from "@playwright/test";

test("BIB-301 muestra separación entre asesoría y aprobación", async ({ page }) => {
  await page.setContent('<section aria-label="Revisión y aprobación"><p>La aprobación registra la autoridad y el criterio; no acredita implementación ni cierra acciones.</p><select aria-label="Participación"><option>Revisión</option><option>Asesoría DPD</option></select><button>Aprobar con autoridad vigente</button></section>');
  await expect(page.getByLabel("Revisión y aprobación")).toContainText("no acredita implementación");
  await expect(page.getByLabel("Participación")).toContainText("Asesoría DPD");
  await expect(page.getByRole("button", { name: "Aprobar con autoridad vigente" })).toBeVisible();
});
