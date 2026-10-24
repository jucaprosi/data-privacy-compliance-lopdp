import { expect, test } from "@playwright/test";

test("las respuestas de referencia no se envían al servidor", async ({ page }) => {
  const cuerpos: unknown[] = [];
  await page.route("**/api/v1/diagnostico/respuestas", async (route) => {
    if (route.request().method() === "GET") return route.fulfill({ json: { respuestas: [] } });
    cuerpos.push(route.request().postDataJSON());
    return route.fulfill({ json: { respuestas: [] } });
  });
  await page.goto("/");
  await page.evaluate(async () => {
    const store = await import("/src/store/useAuditStore");
    store.useAuditStore.setState({ respuestas: [{ preguntaId: 1, cumple: "Conforme", evidenciaNivel: 3, esCritica: false, riesgoBase: 1, control: "P1", dimensionId: "D01", esReferencia: true }] });
  });
  await expect.poll(() => cuerpos.length).toBe(0);
});
