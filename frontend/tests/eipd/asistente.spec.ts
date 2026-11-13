/**
 * Árbitro de interfaz de MTGE-03: asistente de ocho pasos de la evaluación de impacto.
 *
 * Con la API simulada comprueba (spec §5):
 * 1. En el paso 7 con residual alto, «Cerrar la evaluación» queda con aria-disabled y no llama a la API
 *    hasta elegir una decisión; con decisión y justificación se cierra y se muestra la huella.
 * 2. Con la evaluación exigida por la ley, la casilla de obligatoriedad está deshabilitada con el motivo.
 * 3. El DPO ve la evaluación en solo lectura, sin «Nueva evaluación».
 * 4. A 375 px no hay desplazamiento horizontal.
 *
 * Mutación documentada: si `cierreBloqueado` devuelve siempre false, la prueba 1 falla (el cierre se pide
 * con residual alto y sin decisión).
 */
import { expect, test, type Page } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";

const TRATAMIENTO = { id: "rat-e2e-1", nombre: "Videovigilancia de sedes" };

function eipdBase(paso: number) {
  return {
    id: "eipd-e2e-1", tratamiento_id: TRATAMIENTO.id, obligatoria: true, obligatoria_por_ley: true,
    motivo_obligatoriedad: "el tratamiento es de gran escala según la calificación de la plataforma",
    paso_actual: paso, consulta_titulares: "Encuesta", ciclo_vida: { fases: ["uso"], amenazas: ["alteracion"] },
    necesidad: "Necesaria", riesgo_inherente: "alto", riesgo_residual: "alto", decision: null as string | null,
    decision_texto: null as string | null, informe_sha256: null as string | null, cerrada_en: null as string | null,
    creado_en: "2026-11-13T12:00:00Z", puntos: [],
  };
}

async function instalarApi(page: Page, roles: string[], paso: number) {
  const estado = { eipd: eipdBase(paso), cierres: 0 };
  await page.route("**/api/v1/**", async (route) => {
    const req = route.request();
    const ruta = new URL(req.url()).pathname.replace(/^\/api\/v1/, "");
    const metodo = req.method();
    const responder = (status: number, cuerpo: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(cuerpo) });
    if (ruta === "/organizacion/me/roles") return responder(200, roles.map((role) => ({ role })));
    if (ruta === "/rat/actividades") return responder(200, { tenant_id: "t", total: 1, actividades: [TRATAMIENTO] });
    if (ruta === "/eipd/catalogos") {
      return responder(200, { fases: { uso: "Uso y tratamiento" }, amenazas: { alteracion: "Alteración no autorizada" } });
    }
    if (ruta === "/eipd" && metodo === "GET") return responder(200, [estado.eipd]);
    const paso7 = ruta.match(/^\/eipd\/[^/]+\/paso\/(\d)$/);
    if (paso7 && metodo === "PUT") {
      const cuerpo = JSON.parse(req.postData() ?? "{}");
      if (paso7[1] === "7") Object.assign(estado.eipd, cuerpo);
      estado.eipd.paso_actual = Math.max(estado.eipd.paso_actual, Number(paso7[1]) + 1);
      return responder(200, estado.eipd);
    }
    if (/^\/eipd\/[^/]+\/cerrar$/.test(ruta)) {
      estado.cierres += 1;
      if (estado.eipd.riesgo_residual === "alto" && !estado.eipd.decision) {
        return responder(409, { code: "EIPD_SIN_DECISION", detail: "x" });
      }
      estado.eipd.informe_sha256 = "abcdef0123456789".repeat(4);
      estado.eipd.cerrada_en = "2026-11-13T13:00:00Z";
      return responder(200, { informe_sha256: estado.eipd.informe_sha256 });
    }
    return responder(200, {});
  });
  return estado;
}

async function abrir(page: Page) {
  await abrirAppLimpia(page);
  await configurarProyecto(page, "Organización EIPD");
  await irASala(page, /Evaluación de impacto guiada/);
  await expect(page.getByRole("heading", { name: "Evaluaciones de impacto" })).toBeVisible();
}

test.describe("Evaluación de impacto guiada (MTGE-03)", () => {
  test("con residual alto, Cerrar queda deshabilitado hasta elegir una decisión", async ({ page }) => {
    const estado = await instalarApi(page, ["implementador"], 7);
    await abrir(page);
    await expect(page.getByText("Borrador · paso 7 de 8")).toBeVisible();
    await page.getByRole("button", { name: "Abrir" }).click();
    await expect(page.getByRole("heading", { name: "Decisión" })).toBeVisible();
    await page.getByRole("button", { name: "Siguiente" }).click();
    const cerrar = page.getByTestId("eipd-cerrar");
    await expect(cerrar).toHaveAttribute("aria-disabled", "true");
    await expect(page.getByText("Con riesgo residual alto, elige una decisión antes de cerrar.")).toBeVisible();
    await cerrar.dispatchEvent("click");
    expect(estado.cierres).toBe(0);

    await page.getByRole("button", { name: "Anterior" }).click();
    await page.getByRole("radio", { name: "Aplicar nuevas medidas" }).click();
    await page.getByRole("button", { name: "Siguiente" }).click();
    await expect(page.getByText("Completa este paso antes de continuar: escribe la justificación.")).toBeVisible();
    await page.getByLabel("Justificación").fill("Cifrado en reposo y control de accesos");
    await page.getByRole("button", { name: "Siguiente" }).click();
    await expect(cerrar).toHaveAttribute("aria-disabled", "false");
    await cerrar.click();
    await expect(page.getByTestId("eipd-huella")).toHaveText("Huella de integridad: abcdef01");
    await expect(page.getByRole("button", { name: `Descargar el informe de la evaluación de ${TRATAMIENTO.nombre}` })).toBeVisible();
    expect(estado.cierres).toBe(1);
  });

  test("la obligatoriedad exigida por la ley no se puede desmarcar", async ({ page }) => {
    await instalarApi(page, ["implementador"], 1);
    await abrir(page);
    await page.getByRole("button", { name: "Abrir" }).click();
    const casilla = page.getByTestId("eipd-obligatoria");
    await expect(casilla).toBeDisabled();
    await expect(casilla).toHaveAttribute("aria-describedby", "eipd-motivo");
    await expect(page.locator("#eipd-motivo")).toContainText("La ley exige esta evaluación para este tratamiento");
  });

  test("el DPO revisa en solo lectura y no hay desplazamiento horizontal a 375 px", async ({ page }) => {
    await instalarApi(page, ["dpo"], 3);
    await abrir(page);
    await page.setViewportSize({ width: 375, height: 812 });
    await expect(page.getByRole("button", { name: "Nueva evaluación" })).toHaveCount(0);
    await expect(page.getByText("Puedes revisar la evaluación; la completa el equipo responsable.")).toBeVisible();
    const desborda = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    expect(desborda).toBe(false);
    await page.getByRole("button", { name: "Abrir" }).click();
    await expect(page.getByRole("heading", { name: "Ciclo de vida y amenazas" })).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)).toBe(false);
    await expect(page.locator("body")).not.toContainText(/[¤¦]/);
  });
});
