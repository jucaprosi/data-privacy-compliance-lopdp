import { expect, test, type Request } from "@playwright/test";

import { abrirAppLimpia, configurarProyecto, irASala } from "../utiles";
import { credencialSimulada, fijarAjustes, ruta, sembrarSesion } from "../auth/utilesAuth";

const solicitudReal = {
  id: "00000000-0000-0000-0000-000000000123",
  tenant_id: "00000000-0000-0000-0000-000000000008",
  tipo_solicitud: "RECTIFICACION",
  estado: "RECIBIDA",
  cedula_solicitante: "1712345678",
  nombre_solicitante: "Ana Titular",
  fecha_recepcion: new Date().toISOString(),
  fecha_vencimiento: new Date(Date.now() + 10 * 86_400_000).toISOString(),
  evidencia_respuesta_hash: null,
};

async function prepararApi(page: Parameters<typeof fijarAjustes>[0], estadoArco = 200) {
  const llamadas: Request[] = [];
  await page.route("**/api/v1/**", async (route) => {
    const peticion = route.request();
    llamadas.push(peticion);
    const destino = ruta(peticion.url());
    const json = (status: number, body: unknown) =>
      route.fulfill({ status, contentType: "application/json", body: JSON.stringify(body) });

    if (destino === "/organizacion/me/roles") {
      return json(200, { roles: [{ role: "coordinador", area_id: null, area_nombre: null, valid_to: null }] });
    }
    if (destino === "/arco/solicitudes") {
      return json(estadoArco, estadoArco === 200 ? [solicitudReal] : { detail: "Fallo controlado" });
    }
    return json(200, []);
  });
  return llamadas;
}

async function abrirArco(page: Parameters<typeof fijarAjustes>[0]) {
  await abrirAppLimpia(page);
  await configurarProyecto(page);
  await irASala(page, /Derechos ARCO/);
}

test("muestra el contrato persistente y envía la sesión verificada", async ({ page }) => {
  const credencial = credencialSimulada();
  await fijarAjustes(page, { modo: "oidc" });
  await sembrarSesion(page, credencial);
  const llamadas = await prepararApi(page);

  await abrirArco(page);

  await expect(page.getByRole("heading", { name: /Derechos ARCO/ })).toBeVisible();
  await expect(page.getByText("RECTIFICACION - Ana Titular")).toBeVisible();
  await expect(page.getByText(/CC: 1712345678/)).toBeVisible();
  await expect(page.getByText(/10 días restantes/)).toBeVisible();

  const peticion = llamadas.find((llamada) => ruta(llamada.url()) === "/arco/solicitudes");
  expect(peticion?.headers()["authorization"]).toBe(`Bearer ${credencial.token}`);
  expect(peticion?.headers()["x-tenant-id"]).toBeTruthy();
  expect(peticion?.headers()["x-user-id"]).toBeUndefined();
});

test("no presenta datos como válidos cuando la API falla", async ({ page }) => {
  await fijarAjustes(page, { modo: "oidc" });
  await sembrarSesion(page);
  await prepararApi(page, 500);

  await abrirArco(page);

  await expect(page.getByText("Error al obtener solicitudes ARCO+")).toBeVisible();
  await expect(page.getByText("Ana Titular")).toHaveCount(0);
});
